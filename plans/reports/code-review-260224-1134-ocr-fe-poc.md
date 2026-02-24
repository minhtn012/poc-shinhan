# Code Review: Vue 3 OCR Template FE POC

**Date:** 2026-02-24
**Reviewer:** code-reviewer agent
**Scope:** `/data/data/poc-shinhan/src/` — full codebase

---

## Scope

| Area | Files Reviewed |
|---|---|
| Composables | `use-annotation.ts`, `use-image-store.ts` |
| Lib | `render-fields.ts` |
| Services | `template.service.ts`, `ocr.service.ts`, `mock-api.ts` |
| Views | `template-create-view.vue`, `ocr-review-view.vue`, `ocr-upload-view.vue`, `login-view.vue` |
| Components | `annotation-canvas.vue`, `field-sidebar.vue`, `image-overlay.vue`, `results-table.vue` |
| Stores/Router | `auth.store.ts`, `router/index.ts` |
| Types | `template.types.ts`, `ocr.types.ts` |

**Total LOC reviewed:** ~1,500 lines across 17 files
**LOC per file:** all within 200-line guideline

---

## Overall Assessment

Well-structured POC. Composable decomposition is clean, types are coherent, and Vue 3 patterns are used correctly. The main issues are clustered in three areas: D3 lifecycle management, localStorage non-atomicity, and a handful of boundary conditions that will surface under real usage. No critical XSS or credential-exposure issues exist — these are controlled correctly. The credential concern is a medium-severity architectural weakness, not an active leak.

---

## Critical Issues

None. No active security exploits, no data-loss bugs in single-user usage.

---

## High Priority

### H1 — `image-overlay.vue`: Incomplete D3 cleanup on unmount

**File:** `src/components/ocr/image-overlay.vue`, line 150–152

```typescript
onUnmounted(() => {
  zoomBehavior = null   // only nulls the JS reference
})
```

`zoomBehavior = null` does NOT detach D3 zoom listeners from the SVG node. If the component unmounts while the SVG is still in the DOM (e.g., during route transition), the zoom handler closure holds references to `content`, `currentTransform`, and the container element. This is a memory leak.

Compare to the correct pattern in `use-annotation.ts` `destroy()` which explicitly calls `.on('...', null)` for each named event.

**Fix:**
```typescript
onUnmounted(() => {
  if (svg && zoomBehavior) {
    svg.on('.zoom', null)
  }
  if (containerRef.value) {
    d3.select(containerRef.value).selectAll('*').remove()
  }
  svg = null
  zoomBehavior = null
})
```

---

### H2 — `image-overlay.vue`: `initCanvas` race condition on rapid `imageUrl` prop changes

**File:** `src/components/ocr/image-overlay.vue`, lines 30–70, 141–148

The `watch` on `imageUrl` fires `initCanvas` immediately. `initCanvas` calls `d3.select(container).selectAll('*').remove()` at the top — but `new Image().onload` is async. If `imageUrl` changes again while the first image is loading, the second call removes the first SVG and starts a new load. The first `onload` then fires against a container that has already been re-initialized, appending a second `g.content` group to the new SVG.

```typescript
// Both fire in sequence if imageUrl changes twice quickly:
img.onload = () => {
  const content = svg!.append('g').attr('class', 'content')  // appended TWICE
  ...
}
```

**Fix:** Track a cancel token or abort flag:
```typescript
let loadId = 0
async function initCanvas(imageUrl: string): Promise<void> {
  const myId = ++loadId
  const container = containerRef.value
  if (!container) return
  d3.select(container).selectAll('*').remove()
  // ...
  return new Promise(resolve => {
    const img = new Image()
    img.onload = () => {
      if (myId !== loadId) return  // stale load, abort
      // ... rest of setup
    }
    img.src = imageUrl
  })
}
```

The same race exists in `use-annotation.ts` `initCanvas` but is less likely to trigger since annotation images are set once per session.

---

### H3 — `use-annotation.ts`: Division by zero when `imgWidth`/`imgHeight` is 0

**File:** `src/composables/use-annotation.ts`, lines 219–224

```typescript
const bbox: NormalizedBBox = {
  x: Math.min(s.x, c.x) / imgWidth.value,   // NaN if imgWidth.value === 0
  y: Math.min(s.y, c.y) / imgHeight.value,
  w: w / imgWidth.value,
  h: h / imgHeight.value
}
```

The guard at line 214 checks `w < MIN_RECT_PX || h < MIN_RECT_PX` — both are pixel values from draw coordinates and will pass as non-zero even if the image never loaded (`imgWidth.value` stays 0). A `NaN`/`Infinity` bbox is then stored and emitted to the parent and eventually written to localStorage.

**Fix:** Add an early-out guard in `finishDraw`:
```typescript
if (!imgWidth.value || !imgHeight.value) {
  cancelDraw()
  return null
}
```

Same guard should be added in `moveField` and `resizeField` — both divide by `imgWidth.value`/`imgHeight.value` unconditionally.

---

### H4 — `template.service.ts` / `ocr.service.ts`: No orphaned image cleanup

**File:** `src/services/template.service.ts`, line 41–46

`deleteTemplate` removes template and version records from localStorage but never calls `imageStore.removeImage(version.imageKey)` for any version. Every deleted template leaves its image blob in localforage permanently. For a POC with large TIFF files this will silently fill the user's storage quota.

`deleteJob` in `ocr.service.ts` has the same problem (line 76–78).

**Fix:** Both delete functions need access to `useImageStore` and must call `removeImage` for each affected `imageKey` before removing the record. Since services are plain modules (not composables), inject `removeImage` as a parameter, or call it at the call site in the view before delegating to the service.

---

## Medium Priority

### M1 — `template.service.ts`: Non-atomic read-modify-write pattern

**File:** `src/services/template.service.ts`, lines 71–96 (`createVersion`), 101–122 (`activateVersion`)

Both functions do: `readList` → mutate in memory → `writeList`. In a multi-tab browser scenario, a concurrent write from another tab between the read and write silently wins and the other tab's changes are lost.

This is acceptable for a single-user POC but should be documented with a `// WARNING: not multi-tab safe` comment, or the localStorage key should use `storage` event listeners to invalidate cached reads. The same issue exists in `ocr.service.ts`.

---

### M2 — `template-create-view.vue`: Duplicate template name silent merge

**File:** `src/views/template-create-view.vue`, lines 162–165

```typescript
let template = templateService.getTemplates().find(t => t.name === templateName.value)
if (!template) {
  template = templateService.createTemplate(templateName.value)
}
```

If the user creates two templates with the same name, the second `saveTemplate` call silently reuses the first template's record and adds a new version to it. This is not communicated to the user and will confuse them when they see the first template gain a new version. At minimum, show a confirmation dialog or prevent duplicate names.

---

### M3 — `use-annotation.ts` `resizeField`: Missing `default` branch in switch

**File:** `src/composables/use-annotation.ts`, lines 284–293

```typescript
switch (handleIndex) {
  case 0: l = imgX; t = imgY; break
  // ... cases 1-7
}
// no default
```

An out-of-range `handleIndex` (e.g., 8 or -1) silently leaves `[l, t, r, b]` unchanged. The `MIN_RECT_PX` guard at line 300 will then produce a zero-dimension rect check against the original, always passing, and `resizeField` returns the field unchanged. Silent no-op is acceptable but should be an explicit `default: return f` or `default: break` to make intent clear.

---

### M4 — `image-overlay.vue`: `fieldColors` computed re-reads localStorage on every hover

**File:** `src/views/ocr-review-view.vue`, lines 71–80

`fieldColors` is a `computed()` that calls `templateService.getVersion()` which calls `JSON.parse(localStorage.getItem(...))`. The computed recalculates whenever `job.value` changes — but in the hover flow, `hoveredFieldId` changes do not trigger it (correct). However, `onValueChange` reassigns `job.value = ocrService.getJob(...)` on every field edit, causing `fieldColors` to re-parse localStorage. For a small dataset this is negligible, but it is a code smell. Cache `version` outside the computed or use a separate `onMounted` call.

---

### M5 — `ocr-upload-view.vue`: `startProcessing` saves image before confirming OCR success

**File:** `src/views/ocr-upload-view.vue`, lines 155–164

```typescript
const imageKey = `img:${crypto.randomUUID()}`
await imageStore.saveImage(imageKey, file.value)  // saved first

const job = ocrService.createJob({ ..., imageKey })
ocrService.updateJobStatus(job.id, 'done')
ocrService.updateJobResults(job.id, results)      // results already computed
```

The image is saved before `createJob` — if `createJob` or the subsequent writes throw, the image is orphaned in localforage with no job referencing it. Swap order: create the job record first, then save image, or wrap in a try/finally that calls `removeImage(imageKey)` on failure.

---

### M6 — Authentication: plain-text credential comparison in client-side code

**File:** `src/stores/auth.store.ts`, lines 10–13

```typescript
if (user === import.meta.env.VITE_AUTH_USER && pass === import.meta.env.VITE_AUTH_PASS) {
```

`VITE_*` variables are inlined into the JS bundle at build time. Any user who opens DevTools and searches the bundle source will find the cleartext username and password. This is the **only** POC auth mechanism.

`.env` is correctly gitignored (confirmed in `.gitignore`). However:
- The credentials live in the distributed bundle, not just the server.
- `sessionStorage.setItem(SESSION_KEY, 'true')` is trivially forgeable — any user can type `sessionStorage.setItem('ocr:auth', 'true')` in the console and bypass auth entirely.

For a POC with no real backend this is acceptable, but it must be replaced with server-side session auth before any production or staging deployment. Add a comment to `auth.store.ts` documenting this limitation.

---

## Low Priority

### L1 — `render-fields.ts`: Label width heuristic uses fixed character width

**File:** `src/lib/render-fields.ts`, line 86

```typescript
const tw = Math.max(40, label.length * 6 + 12)
```

`label.length * 6` assumes a fixed monospace character width. Wide characters (CJK, emoji) will overflow the background rect. For OCR template names that may include Vietnamese or other multi-byte characters, use `SVGTextElement.getComputedTextLength()` after appending, or accept the visual glitch for a POC.

---

### L2 — `annotation-canvas.vue`: Sync watcher comparison is order-sensitive

**File:** `src/components/annotation/annotation-canvas.vue`, lines 60–67

```typescript
const currentIds = annotation.fields.value.map(f => f.id).join(',')
const incomingIds = incoming.map(f => f.id).join(',')
if (currentIds !== incomingIds) {
  annotation.fields.value = [...incoming]
}
```

This guards against emit loops but breaks if the parent reorders fields without adding/removing — the internal order stays stale. More importantly, if the parent changes a field's `name` or `color` without changing its `id`, the sync is skipped and the canvas shows outdated data. The guard should compare by content (or use a deep-equality check) rather than by ID list.

---

### L3 — `ocr-review-view.vue`: Anchor click without DOM append

**File:** `src/views/ocr-review-view.vue`, lines 107–111

```typescript
const a = document.createElement('a')
a.href = url
a.download = `ocr-${job.value.id}.json`
a.click()
```

The anchor is never appended to the document. This works in Chrome/Edge but is unreliable in Firefox (requires the element to be in the document for `download` attribute to take effect). Standard fix: `document.body.appendChild(a); a.click(); document.body.removeChild(a)`.

---

### L4 — `template-create-view.vue`: Duplicate CSS block for `.annotate-step`

**File:** `src/views/template-create-view.vue`, lines 191–217

`.annotate-step` is defined twice in `<style scoped>` — first as `flex-direction: column` and then overridden as `display: grid`. The first block is a dead rule. Remove it.

---

### L5 — `use-annotation.ts`: `destroy()` does not null `svg.value`

**File:** `src/composables/use-annotation.ts`, lines 319–327

```typescript
function destroy(): void {
  if (svg.value) {
    svg.value.on('mousedown.draw', null)
    // ...
  }
  zoomBehavior = null
  // svg.value is not nulled
}
```

After `destroy()`, `svg.value` still holds the D3 selection. Any caller that retains a reference to the composable return value and calls `render()` or `getSvgNode()` post-unmount will operate on a detached DOM node. Set `svg.value = null` at the end of `destroy()`.

---

### L6 — Missing `.env.example` file

There is no `.env.example` in the repository. `VITE_AUTH_USER` and `VITE_AUTH_PASS` are referenced in `auth.store.ts` but a new developer cloning the repo will get no guidance on what variables are required. Add an `.env.example`:

```
VITE_AUTH_USER=admin
VITE_AUTH_PASS=changeme
```

---

## Edge Cases Found by Scout (Summary)

| # | Location | Condition | Risk |
|---|---|---|---|
| 1 | `image-overlay.vue` `onUnmounted` | D3 zoom listeners not removed | Memory leak |
| 2 | `image-overlay.vue` `initCanvas` | Rapid imageUrl prop change | Double `g.content` append |
| 3 | `use-annotation.ts` `finishDraw` | imgWidth/imgHeight = 0 | NaN bbox written to storage |
| 4 | `use-annotation.ts` `resizeField` | handleIndex out of 0-7 range | Silent no-op, no crash |
| 5 | `template.service.ts` multi-tab | Concurrent read-write | Last-write-wins data loss |
| 6 | `deleteTemplate` / `deleteJob` | imageKey not cleaned up | localforage storage leak |
| 7 | `template-create-view.vue` | Duplicate template name | Silent version hijack |
| 8 | `annotation-canvas.vue` watcher | Field reorder with same IDs | Stale canvas state |
| 9 | `ocr-review-view.vue` | objectUrl overwrite on re-mount | Blob URL leak |
| 10 | `exportJson` | Anchor not in DOM | Firefox download failure |

---

## Positive Observations

- **Composable design is correct.** `useAnnotation` cleanly separates D3 state, drawing state machine, and field CRUD. The `onUnmounted(destroy)` pattern is the right hook to use.
- **`destroy()` in `use-annotation.ts` properly uses D3 named events** (`.draw`, `.deselect`) so removal is safe without affecting other listeners.
- **NormalizedBBox design is correct.** Storing 0-1 coordinates decoupled from pixel dimensions is the right approach for resolution-independent templates.
- **`readList` wraps JSON.parse in try/catch.** Defensive against corrupted localStorage.
- **`render-fields.ts` uses `transform.k` for stroke and handle sizing** — handles stay visually consistent at all zoom levels.
- **Auth store uses `sessionStorage` not `localStorage`** — credentials clear on tab close.
- **`.env` is gitignored.** Credentials are not committed.
- **All views use `onUnmounted` for object URL revocation** in `ocr-review-view.vue`.
- **`annotation-canvas.vue` uses named keydown handler** stored in closure, so `removeEventListener` removes the correct function reference.
- **`mock-api.ts` uses `_blob` prefix** on unused parameters — clean TypeScript hygiene.

---

## Recommended Actions (Prioritized)

1. **[H1]** Fix `image-overlay.vue` unmount: call `svg.on('.zoom', null)` and `selectAll('*').remove()` in `onUnmounted`.
2. **[H2]** Add load-cancellation token to both `initCanvas` implementations (image-overlay and use-annotation).
3. **[H3]** Guard `finishDraw`, `moveField`, `resizeField` against `imgWidth/imgHeight === 0`.
4. **[H4]** Add image cleanup to `deleteTemplate` and `deleteJob` — iterate versions and call `imageStore.removeImage`.
5. **[M2]** Show duplicate-name warning in `saveTemplate` rather than silently merging.
6. **[M5]** Reorder `startProcessing` to create job record before saving image, with cleanup on failure.
7. **[M6]** Add a comment to `auth.store.ts` flagging the bundle-embedded credential limitation.
8. **[L2]** Widen `annotation-canvas.vue` sync guard to detect content changes (name/color), not just ID list changes.
9. **[L3]** Append anchor to `document.body` before `.click()` in `exportJson`.
10. **[L6]** Add `.env.example` with placeholder values.

---

## Metrics

| Metric | Value |
|---|---|
| Files reviewed | 17 |
| Total LOC | ~1,500 |
| Critical issues | 0 |
| High priority | 4 |
| Medium priority | 6 |
| Low priority | 6 |
| Type coverage | Good — all major interfaces typed, no `any` found |
| Test coverage | 0% (no tests — POC scope) |
| Linting issues | Not run — no lint script observed in vite.config |

---

## Unresolved Questions

1. Is there a `deleteTemplate` call site that already handles image cleanup separately? Searched views and found none — the only caller in `template-detail-view.vue` was not reviewed (file not in scope list but exists in the file tree).
2. Is multi-tab isolation intentional for this POC, or is the localStorage shared-state conflict expected to be a non-issue because it is single-user demo only?
3. Will the mock auth (`VITE_AUTH_*`) be replaced before any external demo? If so, a tracking issue should be created.
