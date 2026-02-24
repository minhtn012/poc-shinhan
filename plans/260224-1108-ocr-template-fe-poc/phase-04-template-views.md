# Phase 4: Template Management Views

## Context Links

- Plan overview: [plan.md](./plan.md)
- Depends on: [Phase 3](./phase-03-annotation-canvas.md) (annotation canvas)
- Depends on: [Phase 2](./phase-02-data-layer.md) (services)

## Overview

- **Priority**: P1
- **Status**: completed
- **Effort**: 2h
- **Description**: Build template list, 3-step creation wizard, and version history views using Element Plus components and annotation canvas.

## Key Insights

- El-Steps wizard manages step state + validation before advancing
- Step 2 (annotate) is the largest — embeds annotation-canvas + field-sidebar
- On save (step 3 confirm): create version, store image in localforage, deactivate previous active version
- Template list needs status badge showing active version info
- Version history is a simple el-table with status badges

## Requirements

### Functional
- `/templates` — List all templates with name, active version, field count, date
- `/templates/create` — 3-step wizard:
  - Step 1: Upload image (el-upload), enter template name + version string
  - Step 2: Annotation canvas + field sidebar, must have >= 1 field to proceed
  - Step 3: Review all fields in table, confirm save
- `/templates/:id` — Version history table for specific template
- Version badge: green=active, gray=inactive

### Non-Functional
- Wizard state preserved when navigating steps (no data loss on back)
- Upload accepts image/* only (jpg, png, webp, tiff)
- Responsive layout for annotation step

## Architecture

```
src/
├── views/
│   ├── template-list-view.vue    # Template list
│   ├── template-create-view.vue  # 3-step wizard
│   └── template-detail-view.vue  # Version history
├── components/common/
│   └── version-badge.vue         # active/inactive badge
```

### Wizard State Flow
```
Step 1 (Upload)        Step 2 (Annotate)       Step 3 (Confirm)
┌─────────────┐       ┌──────────────────┐     ┌──────────────┐
│ name         │──────>│ annotation-canvas │────>│ fields table │
│ version      │       │ field-sidebar     │     │ [Save]       │
│ image (File) │       │ fields[]          │     │              │
└─────────────┘       └──────────────────┘     └──────────────┘
                                                      │
                                                      ▼
                                            template.service.createVersion()
                                            imageStore.saveImage()
                                            router.push('/templates')
```

## Related Code Files

### Create
- `src/views/template-list-view.vue`
- `src/views/template-create-view.vue`
- `src/views/template-detail-view.vue`
- `src/components/common/version-badge.vue`

### Consume
- `src/components/annotation/annotation-canvas.vue`
- `src/components/annotation/field-sidebar.vue`
- `src/services/template.service.ts`
- `src/composables/use-image-store.ts`

## Implementation Steps

### 1. Create `src/components/common/version-badge.vue`

```vue
<template>
  <el-tag :type="status === 'active' ? 'success' : 'info'" size="small">
    {{ status }}
  </el-tag>
</template>
<script setup lang="ts">
defineProps<{ status: 'active' | 'inactive' }>()
</script>
```

### 2. Create `src/views/template-list-view.vue`

Layout:
```
┌─────────────────────────────────────────┐
│ Templates               [+ New Template] │
├─────────────────────────────────────────┤
│ Name    │ Active Ver │ Fields │ Created  │
│ Invoice │ v2 ●       │ 6      │ 2026-02  │
│ Receipt │ v1 ●       │ 4      │ 2026-02  │
└─────────────────────────────────────────┘
```

Implementation:
- `el-table` with columns: name, active version (with version-badge), field count, createdAt
- Row click → `router.push('/templates/' + id)`
- Top-right button: `router.push('/templates/create')`
- Load data from `templateService.getTemplates()` + `getActiveVersion()` for each
- `el-empty` when no templates

### 3. Create `src/views/template-create-view.vue`

This is the largest view. Uses `el-steps` + conditional rendering.

#### Local state:
```typescript
const activeStep = ref(0)
const templateName = ref('')
const versionString = ref('v1')
const imageFile = ref<File | null>(null)
const imageUrl = ref<string | null>(null)  // object URL for preview
const fields = ref<TemplateField[]>([])
const selectedFieldId = ref<string | null>(null)
const saving = ref(false)
```

#### Step 1: Upload
```vue
<el-form v-if="activeStep === 0">
  <el-form-item label="Template Name" required>
    <el-input v-model="templateName" placeholder="e.g. Invoice" />
  </el-form-item>
  <el-form-item label="Version" required>
    <el-input v-model="versionString" placeholder="e.g. v1" />
  </el-form-item>
  <el-form-item label="Template Image" required>
    <el-upload
      :auto-upload="false"
      :limit="1"
      accept="image/*"
      :on-change="handleImageChange"
      drag>
      <el-icon><Upload /></el-icon>
      <div>Drop image here or click to upload</div>
    </el-upload>
  </el-form-item>
  <el-button type="primary" @click="nextStep" :disabled="!canProceedStep1">
    Next: Annotate Fields
  </el-button>
</el-form>
```

Validation: `canProceedStep1 = templateName && versionString && imageFile`

On `handleImageChange`: store File, create object URL for preview.

#### Step 2: Annotate
```vue
<div v-if="activeStep === 1" class="annotate-step">
  <div class="annotate-step__canvas">
    <annotation-canvas
      :image-url="imageUrl"
      v-model="fields"
      @field-selected="selectedFieldId = $event"
    />
  </div>
  <div class="annotate-step__sidebar">
    <field-sidebar
      :fields="fields"
      :selected-field-id="selectedFieldId"
      @update:fields="fields = $event"
      @select="selectedFieldId = $event"
      @delete="deleteField"
    />
  </div>
  <div class="annotate-step__actions">
    <el-button @click="activeStep = 0">Back</el-button>
    <el-button type="primary" @click="nextStep" :disabled="fields.length === 0">
      Next: Review
    </el-button>
  </div>
</div>
```

CSS: flex layout, canvas takes ~70% width, sidebar ~30%.

#### Step 3: Confirm
```vue
<div v-if="activeStep === 2">
  <h3>Review Template: {{ templateName }} ({{ versionString }})</h3>
  <el-table :data="fields" border>
    <el-table-column prop="name" label="Field Name" />
    <el-table-column label="Color">
      <template #default="{ row }">
        <span class="color-dot" :style="{ background: row.color }" />
      </template>
    </el-table-column>
    <el-table-column label="BBox">
      <template #default="{ row }">
        {{ formatBBox(row.bbox) }}
      </template>
    </el-table-column>
  </el-table>
  <div class="confirm-actions">
    <el-button @click="activeStep = 1">Back</el-button>
    <el-button type="primary" :loading="saving" @click="saveTemplate">
      Save Template
    </el-button>
  </div>
</div>
```

#### Save logic:
```typescript
async function saveTemplate() {
  saving.value = true
  try {
    // Check if template with same name exists
    let template = templateService.getTemplates()
      .find(t => t.name === templateName.value)
    if (!template) {
      template = templateService.createTemplate(templateName.value)
    }
    // Save image to localforage
    const imageKey = `img:${crypto.randomUUID()}`
    await imageStore.saveImage(imageKey, imageFile.value!)
    // Create version (service handles deactivating previous)
    templateService.createVersion(
      template.id, versionString.value, imageKey, fields.value
    )
    ElMessage.success('Template saved!')
    router.push('/templates')
  } finally {
    saving.value = false
  }
}
```

### 4. Create `src/views/template-detail-view.vue`

```vue
<template>
  <div class="template-detail">
    <div class="template-detail__header">
      <el-button @click="router.push('/templates')">← Back</el-button>
      <h2>{{ template?.name }}</h2>
    </div>
    <el-table :data="versions" border>
      <el-table-column prop="version" label="Version" />
      <el-table-column label="Status">
        <template #default="{ row }">
          <version-badge :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column label="Fields" :formatter="row => row.fields.length" />
      <el-table-column prop="createdAt" label="Created" />
    </el-table>
  </div>
</template>
```

- Load template by route param `id`
- Load versions via `templateService.getVersionsByTemplate(id)`
- Show el-empty if template not found

### 5. Register routes for views

Ensure router/index.ts imports all view components (lazy loaded):
```typescript
{
  path: '/templates',
  component: () => import('@/views/template-list-view.vue')
}
```

## Todo List

- [ ] Create version-badge.vue component
- [ ] Create template-list-view.vue
- [ ] Create template-create-view.vue (Step 1: upload)
- [ ] Create template-create-view.vue (Step 2: annotate)
- [ ] Create template-create-view.vue (Step 3: confirm + save)
- [ ] Create template-detail-view.vue
- [ ] Wire save logic: localStorage + localforage
- [ ] Test: full wizard flow end-to-end
- [ ] Test: version deactivation on new version save
- [ ] Test: template list shows correct active version info

## Success Criteria

- Template list shows all templates with active version badge
- Click row navigates to version history
- Create wizard: Step 1 validates required fields
- Create wizard: Step 2 shows canvas, can draw fields, sidebar works
- Create wizard: Step 3 shows review table, save persists to localStorage + localforage
- Previous active version deactivated on new version save
- Version history shows all versions with correct status badges
- Navigate back/forward in wizard without losing state

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large image upload causes memory issues | Med | Limit file size in el-upload (10MB max) |
| Object URL memory leak | Low | Revoke on component unmount |
| Wizard state lost on browser back | Low | Acceptable for POC |
| Template name collision | Low | Service checks existing templates, reuses |

## Security Considerations

- File upload: accept only image/* MIME types
- No server upload, stays in browser
- Template name sanitized (no HTML rendering, just text)

## Next Steps

- Phase 5: OCR Management views (parallel-ready once Phase 2 done)
