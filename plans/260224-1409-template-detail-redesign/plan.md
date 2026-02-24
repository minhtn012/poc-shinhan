# Plan: Template Detail Page Redesign

**Date:** 2026-02-24
**Status:** Ready
**Scope:** `src/views/template-detail-view.vue` (single file)

---

## Context

User feedback:
- Create new template: OK
- Update version UX: **not good** — buried in dropdown
- Header "Edit" button: misleading (edits metadata, not version)

---

## Requirements

1. **Header:** Replace `Edit` (pencil, opens metadata dialog) → `Update Version` button
   - Navigates to `/templates/create?from={activeVersionId}&templateId={id}`
   - If no active version, use latest version ID as `from`
   - If no versions at all, disable button

2. **Versions table dropdown — remove** `New Version` option (relocated to header)

3. **Versions table dropdown — Set Active** always visible (remove conditional `v-if="ver.status === 'inactive'"`)
   - Disable the item (not clickable) when `ver.status === 'active'`

4. **Remove** Edit dialog and all its supporting code (form, openEditDialog, saveEdit, editDialogOpen, editForm refs) — no longer needed in this page

---

## Changes to `template-detail-view.vue`

### Template section

| Before | After |
|--------|-------|
| `<Button @click="openEditDialog">Edit</Button>` | `<Button @click="updateVersion">Update Version</Button>` |
| `<DropdownMenuItem @click="cloneVersion(ver.id)">New Version</DropdownMenuItem>` | _(removed)_ |
| `<template v-if="ver.status === 'inactive'">Set Active</template>` | Always shown; disable via `:disabled="ver.status === 'active'"` on the item |
| Edit Dialog block (lines 97–118) | _(removed)_ |

### Script section

**Add** `updateVersion()` function:
```ts
function updateVersion(): void {
  const id = route.params.id as string
  const baseVersionId = template.value?.activeVersionId ?? versions.value[0]?.id
  if (!baseVersionId) return
  router.push(`/templates/create?from=${baseVersionId}&templateId=${id}`)
}
```

**Remove:**
- `editDialogOpen`, `editForm` refs
- `openEditDialog()`, `saveEdit()` functions
- Unused imports: `Pencil`, Dialog components, `Input`, `Label`, `Textarea`

---

## Phase

| # | Task | File |
|---|------|------|
| 1 | Replace Edit → Update Version in header | `template-detail-view.vue` |
| 2 | Add `updateVersion()` logic | `template-detail-view.vue` |
| 3 | Remove "New Version" from dropdown | `template-detail-view.vue` |
| 4 | Make "Set Active" always visible, disable for active | `template-detail-view.vue` |
| 5 | Remove edit dialog + dead code | `template-detail-view.vue` |
| 6 | Clean up unused imports | `template-detail-view.vue` |

---

## Success Criteria

- [ ] `/templates/:id` header shows "Update Version" button (no "Edit" button)
- [ ] "Update Version" navigates to annotation canvas with active/latest version as base
- [ ] "Update Version" disabled (or hidden) when no versions exist
- [ ] Versions table rows: no "New Version" option in dropdown
- [ ] Versions table rows: "Set Active" always visible; disabled for already-active row
- [ ] No edit dialog or dead code remains
- [ ] `npx vue-tsc --noEmit` passes
