# Phase 2: Version Update Flow

## Context Links

- Plan overview: [plan.md](./plan.md)
- Phase 1 (prerequisite): [phase-01-template-edit.md](./phase-01-template-edit.md)
- Template create wizard: `src/views/template-create-view.vue` (242 lines)
- Template detail view: `src/views/template-detail-view.vue` (94 lines)
- Annotation canvas: `src/components/annotation/annotation-canvas.vue`
- Field sidebar: `src/components/annotation/field-sidebar.vue`
- Image store: `src/composables/use-image-store.ts`
- Service: `src/services/template.service.ts`

## Overview

- **Priority:** P2
- **Status:** done
- **Effort:** 2h
- **Description:** Enable creating a new version from an existing version (cloning fields + image) and viewing/editing version annotations

## Key Insights

- `template-create-view.vue` already implements the full 3-step wizard (upload, annotate, confirm). The version update flow should **reuse** this view by passing a `from` query param referencing a source version
- When cloning from an existing version: skip image upload (reuse imageKey), pre-fill fields, auto-increment version string
- A separate "version edit" route is also needed to view an existing version's annotations (read-only or editable if we add draft status -- but per YAGNI, read-only view + clone-to-new-version is simpler)
- Current `TemplateVersion.status` is `'active' | 'inactive'` -- no draft concept. Adding draft would require significant schema changes. **Decision: keep it simple -- clone-to-new-version pattern only**

## Requirements

### Functional
- FR-1: "New Version" button on template-detail-view that clones from the active (or selected) version
- FR-2: When cloning, template-create-view receives `from` query param, loads source version's image + fields as starting state
- FR-3: Version string auto-increments (e.g., existing "v1" -> suggest "v2")
- FR-4: User can modify fields in the annotation step before saving
- FR-5: User can optionally upload a new image instead of reusing the cloned one
- FR-6: "View Fields" button on each version row in detail view to see annotations read-only
- FR-7: Version annotation viewer shows image with field overlays (reuses annotation-canvas in read-only mode)

### Non-Functional
- No new npm packages
- Reuse existing annotation components
- No breaking changes to localStorage schema
- Files under 200 lines

## Architecture

### Flow A: New Version from Existing

```
template-detail-view.vue
  -> "New Version" button (per version row)
  -> router.push('/templates/create?from=<versionId>&templateId=<templateId>')

template-create-view.vue (modified)
  -> onMounted: if route.query.from exists:
       1. Load source version via getVersion(from)
       2. Load image URL via useImageStore().getImageUrl(version.imageKey)
       3. Pre-fill: templateName (from template), versionString (auto-incremented), fields (cloned), imageUrl
       4. Start at step 1 (user can change image) or step 2 (annotate) directly
  -> Save flow unchanged -- createVersion() deactivates previous and creates new active
```

### Flow B: View Version Annotations

```
template-detail-view.vue
  -> "View" button on version row
  -> router.push('/templates/:id/versions/:vid')

version-view.vue (NEW, small view ~80 lines)
  -> Load version + image
  -> Display annotation-canvas in read-only mode (no draw events)
  -> Field sidebar in read-only mode
  -> "Clone to New Version" button -> navigates to Flow A
```

### Route Additions (router/index.ts)

```ts
{
  path: 'templates/:id/versions/:vid',
  name: 'version-view',
  component: () => import('@/views/version-view.vue')
}
```

## Related Code Files

### Files to Modify
| File | Change |
|------|--------|
| `src/views/template-create-view.vue` | Add clone-from-version logic via `route.query.from` |
| `src/views/template-detail-view.vue` | Add "New Version" + "View" buttons per version row |
| `src/router/index.ts` | Add `version-view` route |
| `src/components/annotation/annotation-canvas.vue` | Add optional `readonly` prop to disable drawing |
| `src/composables/use-annotation.ts` | Support readonly mode (skip wiring draw events) |

### Files to Create
| File | Purpose |
|------|---------|
| `src/views/version-view.vue` | Read-only version annotation viewer (~80 lines) |

### Files to Delete
None.

## Implementation Steps

### Step 1: Add readonly mode to annotation system

**use-annotation.ts** -- Add `readonly` option:

```ts
export function useAnnotation(
  containerRef: Ref<HTMLDivElement | null>,
  options: { initialFields?: TemplateField[]; readonly?: boolean } = {}
) {
```

In `initCanvas`, conditionally skip `wireSvgEvents()`:

```ts
if (!options.readonly) {
  wireSvgEvents()
}
// Change cursor to 'default' when readonly
if (options.readonly) {
  svg.value.style('cursor', 'default')
}
```

**annotation-canvas.vue** -- Add `readonly` prop:

```ts
const props = defineProps<{
  imageUrl: string | null
  modelValue: TemplateField[]
  readonly?: boolean
}>()

const annotation = useAnnotation(containerRef, {
  initialFields: props.modelValue,
  readonly: props.readonly
})
```

Skip keyboard event listener when readonly. Skip emitting `update:modelValue` on field changes when readonly.

### Step 2: Add version helper to service (template.service.ts)

Add a helper to suggest next version string:

```ts
export function suggestNextVersion(templateId: string): string {
  const versions = getVersionsByTemplate(templateId)
  if (!versions.length) return 'v1'
  const nums = versions
    .map(v => parseInt(v.version.replace(/\D/g, ''), 10))
    .filter(n => !isNaN(n))
  const max = nums.length ? Math.max(...nums) : 0
  return `v${max + 1}`
}
```

### Step 3: Update template-detail-view.vue

Add action buttons per version row. Widen Actions column:

```html
<el-table-column label="Actions" width="260">
  <template #default="{ row }">
    <el-button size="small" plain @click="viewVersion(row.id)">
      View
    </el-button>
    <el-button size="small" type="success" plain @click="cloneVersion(row.id)">
      New Version
    </el-button>
    <el-button
      v-if="row.status === 'inactive'"
      size="small" type="primary" plain
      @click="handleActivate(row.id)"
    >
      Set Active
    </el-button>
    <el-tag v-else type="success" size="small">Active</el-tag>
  </template>
</el-table-column>
```

Script additions:

```ts
function viewVersion(versionId: string): void {
  router.push(`/templates/${route.params.id}/versions/${versionId}`)
}

function cloneVersion(versionId: string): void {
  router.push(`/templates/create?from=${versionId}&templateId=${route.params.id}`)
}
```

### Step 4: Create version-view.vue

New view that loads a version and renders annotation-canvas in readonly mode with the field sidebar. Includes breadcrumb, back button, and "Clone to New Version" action.

Key structure:

```html
<template>
  <div class="version-view">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/templates' }">Templates</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/templates/' + templateId }">{{ templateName }}</el-breadcrumb-item>
      <el-breadcrumb-item>{{ version?.version }}</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="page-header">
      <h2>{{ version?.version }} <version-badge v-if="version" :status="version.status" /></h2>
      <div style="display: flex; gap: 8px">
        <el-button type="success" size="small" @click="cloneToNew">New Version from This</el-button>
        <el-button @click="router.push('/templates/' + templateId)">Back</el-button>
      </div>
    </div>

    <div class="version-view__canvas" v-if="imageUrl && version">
      <annotation-canvas :image-url="imageUrl" :model-value="version.fields" readonly />
    </div>

    <el-table :data="version?.fields ?? []" border stripe>
      <el-table-column label="Color" width="70" align="center">...</el-table-column>
      <el-table-column prop="name" label="Field Name" />
      <el-table-column label="BBox" min-width="200">...</el-table-column>
    </el-table>
  </div>
</template>
```

Script loads version + image on mount:

```ts
const templateId = route.params.id as string
const versionId = route.params.vid as string
const version = ref<TemplateVersion>()
const templateName = ref('')
const imageUrl = ref<string | null>(null)

onMounted(async () => {
  version.value = templateService.getVersion(versionId)
  const tmpl = templateService.getTemplate(templateId)
  templateName.value = tmpl?.name ?? ''
  if (version.value) {
    imageUrl.value = await imageStore.getImageUrl(version.value.imageKey)
  }
})
```

### Step 5: Update template-create-view.vue for clone flow

Add `onMounted` logic to detect `route.query.from`:

```ts
const route = useRoute()

onMounted(async () => {
  const fromVersionId = route.query.from as string | undefined
  const fromTemplateId = route.query.templateId as string | undefined

  if (fromVersionId && fromTemplateId) {
    const sourceVersion = templateService.getVersion(fromVersionId)
    const sourceTemplate = templateService.getTemplate(fromTemplateId)
    if (sourceVersion && sourceTemplate) {
      templateName.value = sourceTemplate.name
      versionString.value = templateService.suggestNextVersion(fromTemplateId)
      fields.value = sourceVersion.fields.map(f => ({ ...f, id: crypto.randomUUID() }))
      // Load existing image
      const url = await imageStore.getImageUrl(sourceVersion.imageKey)
      if (url) {
        imageUrl.value = url
        sourceImageKey.value = sourceVersion.imageKey
      }
    }
  }
})
```

Add `sourceImageKey` ref to track reused image:

```ts
const sourceImageKey = ref<string | null>(null)
```

Modify `canProceedStep1` to allow proceeding without new image upload when cloning:

```ts
const canProceedStep1 = computed(
  () => templateName.value.trim() && versionString.value.trim()
    && (imageFile.value !== null || sourceImageKey.value !== null)
)
```

Modify `saveTemplate` to reuse imageKey when no new image uploaded:

```ts
async function saveTemplate(): Promise<void> {
  saving.value = true
  try {
    let template = templateService.getTemplates().find(t => t.name === templateName.value)
    if (!template) {
      template = templateService.createTemplate(templateName.value)
    }

    let imageKey: string
    if (imageFile.value) {
      imageKey = `img:${crypto.randomUUID()}`
      await imageStore.saveImage(imageKey, imageFile.value)
    } else if (sourceImageKey.value) {
      imageKey = sourceImageKey.value
    } else {
      ElMessage.error('No image provided')
      return
    }

    templateService.createVersion(template.id, versionString.value, imageKey, fields.value)
    ElMessage.success('Template saved successfully')
    router.push('/templates')
  } catch {
    ElMessage.error('Failed to save template')
  } finally {
    saving.value = false
  }
}
```

### Step 6: Add version-view route (router/index.ts)

Insert after the `template-detail` route:

```ts
{
  path: 'templates/:id/versions/:vid',
  name: 'version-view',
  component: () => import('@/views/version-view.vue')
}
```

## Todo List

- [x] Add `readonly` option to `use-annotation.ts`
- [x] Add `readonly` prop to `annotation-canvas.vue`
- [x] Add `suggestNextVersion()` to `template.service.ts`
- [x] Add "View" + "New Version" buttons to `template-detail-view.vue`
- [x] Create `version-view.vue` with readonly annotation display
- [x] Update `template-create-view.vue` with clone-from-version logic
- [x] Add `version-view` route to `router/index.ts`
- [x] Manual test: view existing version annotations
- [x] Manual test: clone version -> modify fields -> save as new version
- [x] Manual test: clone version with new image upload
- [x] Run `npx vue-tsc --noEmit` to verify no type errors

## Success Criteria

- "View" on a version row shows read-only annotation view with correct image + field overlays
- "New Version" clones fields + image into the create wizard with auto-incremented version
- User can modify cloned fields and optionally replace the image
- Saving creates a new version that becomes active; old version becomes inactive
- All existing functionality (create new template, delete, activate version) still works
- `vue-tsc --noEmit` passes

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| template-create-view.vue exceeds 200 lines | Medium | Low | Currently 242 lines (already over). Clone logic adds ~20 lines. Acceptable for POC; could extract step components later |
| Image URL revoked before canvas loads | Low | Medium | getImageUrl creates new objectURL each call; no revocation in the flow |
| Cloned field IDs conflict | Low | High | Fields get new UUIDs via `crypto.randomUUID()` in clone step |

## Security Considerations

- No new auth/permission requirements
- Version IDs in URL params are UUIDs, validated against localStorage data
- No user-generated HTML rendered

## Next Steps

- After both phases complete, run full `npm run build` + `npx vue-tsc --noEmit`
- Consider future enhancement: version diff view (compare field changes between versions)
- Consider future enhancement: version deletion
