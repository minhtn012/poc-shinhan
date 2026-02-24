# Phase 5: OCR Management Views

## Context Links

- Plan overview: [plan.md](./plan.md)
- Depends on: [Phase 2](./phase-02-data-layer.md) (services, mock API)
- Depends on: [Phase 4](./phase-04-template-views.md) (needs templates to exist for OCR)

## Overview

- **Priority**: P1
- **Status**: completed
- **Effort**: 2h
- **Description**: Build OCR job list, upload + processing flow, and split-view review with editable results and JSON export.

## Key Insights

- OCR upload flow is linear: upload → mockPreprocess → detect template → mockOcr → redirect to review
- Processing states managed via OcrJob.status: pending → processing → done | error
- Split-view review: left panel = image with bbox overlays (hover highlight), right panel = editable table
- Hover interaction: hover row in table → highlight corresponding bbox, and vice versa
- Export JSON: download OcrFieldResult[] as .json file

## Requirements

### Functional
- `/ocr` — List all OCR jobs: template name, status, created date, action buttons
- `/ocr/new` — Upload image → processing pipeline with progress feedback
- `/ocr/:id` — Split-view: image with bbox overlays | editable results table | export JSON

### Non-Functional
- Processing feedback: el-steps or el-progress showing current stage
- Hover highlight smooth (opacity transition)
- Table inline editing with el-input
- JSON export formatted and downloadable

## Architecture

```
src/
├── views/
│   ├── ocr-list-view.vue        # Job list table
│   ├── ocr-upload-view.vue      # Upload + processing flow
│   └── ocr-review-view.vue      # Split-view review
├── components/ocr/
│   ├── image-overlay.vue        # Image + bbox highlight overlays
│   └── results-table.vue        # Editable results table
```

### Processing Flow
```
Upload Image
     │
     ▼
[mockPreprocess] ──1.5s──> { templateId, confidence }
     │                            │
     │                      No match? → Error message
     ▼
Get active version for matched template
     │
     ▼
[mockOcr] ──2s──> OcrFieldResult[]
     │
     ▼
Create OcrJob (status: done)
Save image to localforage
     │
     ▼
router.push('/ocr/' + job.id)
```

### Split-View Interaction
```
┌─────────────────────┬──────────────────────┐
│  Image + Overlays   │  Results Table       │
│                     │                      │
│  ┌──────┐           │  Field  │ Value │ %  │
│  │ Name │ ←hover──→ │  Name ● │ Nguy… │92% │
│  └──────┘           │  Date   │ 2026  │87% │
│  ┌──────┐           │  Amt    │ 15M   │95% │
│  │ Date │           │                      │
│  └──────┘           │  [Export JSON]       │
└─────────────────────┴──────────────────────┘
```

Hover state shared via `hoveredFieldId` ref, passed to both components.

## Related Code Files

### Create
- `src/views/ocr-list-view.vue`
- `src/views/ocr-upload-view.vue`
- `src/views/ocr-review-view.vue`
- `src/components/ocr/image-overlay.vue`
- `src/components/ocr/results-table.vue`

### Consume
- `src/services/ocr.service.ts`
- `src/services/mock-api.ts`
- `src/services/template.service.ts`
- `src/composables/use-image-store.ts`

## Implementation Steps

### 1. Create `src/views/ocr-list-view.vue`

```vue
<template>
  <div class="ocr-list">
    <div class="ocr-list__header">
      <h2>OCR Jobs</h2>
      <el-button type="primary" @click="router.push('/ocr/new')">
        + New OCR Job
      </el-button>
    </div>
    <el-table :data="jobs" border @row-click="goToJob">
      <el-table-column prop="templateName" label="Template" />
      <el-table-column label="Status">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Fields" :formatter="r => r.results.length" />
      <el-table-column prop="createdAt" label="Created" />
      <el-table-column label="Actions" width="120">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click.stop="deleteJob(row.id)">
            Delete
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!jobs.length" description="No OCR jobs yet" />
  </div>
</template>
```

Status type mapping: done=success, processing=warning, error=danger, pending=info.

### 2. Create `src/views/ocr-upload-view.vue`

Processing pipeline with visual feedback:

```vue
<template>
  <div class="ocr-upload">
    <h2>New OCR Job</h2>

    <!-- Upload step -->
    <div v-if="stage === 'upload'">
      <el-upload drag :auto-upload="false" :limit="1" accept="image/*"
                 :on-change="handleFile">
        <el-icon size="40"><Upload /></el-icon>
        <div>Drop document image here</div>
      </el-upload>
      <el-button type="primary" :disabled="!file" @click="startProcessing"
                 style="margin-top: 16px">
        Start OCR Processing
      </el-button>
    </div>

    <!-- Processing step -->
    <div v-if="stage === 'processing'" class="processing-status">
      <el-steps :active="processingStep" finish-status="success">
        <el-step title="Preprocessing" description="Detecting template..." />
        <el-step title="Template Match" :description="matchDesc" />
        <el-step title="OCR Extraction" description="Reading fields..." />
      </el-steps>
      <div class="processing-spinner">
        <el-icon class="is-loading" size="32"><Loading /></el-icon>
        <p>{{ processingMessage }}</p>
      </div>
    </div>

    <!-- Error step -->
    <div v-if="stage === 'error'">
      <el-result icon="error" title="Processing Failed" :sub-title="errorMessage">
        <template #extra>
          <el-button @click="reset">Try Again</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>
```

Processing logic:
```typescript
type Stage = 'upload' | 'processing' | 'error'
const stage = ref<Stage>('upload')
const processingStep = ref(0)

async function startProcessing() {
  stage.value = 'processing'
  processingStep.value = 0

  // Step 1: Preprocess
  const match = await mockPreprocess(file.value!)
  if (!match) {
    stage.value = 'error'
    errorMessage.value = 'No matching template found. Create a template first.'
    return
  }
  processingStep.value = 1

  // Step 2: Get template version
  const version = templateService.getActiveVersion(match.templateId)
  if (!version) {
    stage.value = 'error'
    errorMessage.value = 'Matched template has no active version.'
    return
  }
  processingStep.value = 2

  // Step 3: OCR
  const results = await mockOcr(file.value!, version)
  processingStep.value = 3

  // Save job
  const imageKey = `img:${crypto.randomUUID()}`
  await imageStore.saveImage(imageKey, file.value!)
  const template = templateService.getTemplate(match.templateId)!
  const job = ocrService.createJob({
    templateVersionId: version.id,
    templateName: template.name,
    imageKey
  })
  ocrService.updateJobStatus(job.id, 'done')
  ocrService.updateJobResults(job.id, results)

  router.push(`/ocr/${job.id}`)
}
```

### 3. Create `src/components/ocr/image-overlay.vue`

D3-based read-only image viewer with bbox overlays:

```vue
<template>
  <div ref="container" class="image-overlay" />
</template>
```

Uses simplified D3 canvas (reuse useD3Canvas pattern):
- Load image into SVG
- For each OcrFieldResult, draw rect overlay (denormalize bbox)
- Highlight hovered field: brighter fill + thicker stroke
- On rect hover → emit `hover(fieldId)`
- On rect click → emit `select(fieldId)`

Props: `imageUrl`, `results: OcrFieldResult[]`, `hoveredFieldId`, `fieldColors: Record<string, string>`
Emits: `hover(fieldId | null)`, `select(fieldId)`

Rendering (simpler than annotation canvas — no drawing, no resize):
```typescript
function renderOverlays() {
  clearOverlays()
  const content = getContent()
  const group = content.append('g').attr('class', 'ocr-overlays')

  for (const result of props.results) {
    const px = result.bbox.x * imgWidth.value
    const py = result.bbox.y * imgHeight.value
    const pw = result.bbox.w * imgWidth.value
    const ph = result.bbox.h * imgHeight.value
    const isHovered = result.fieldId === props.hoveredFieldId
    const color = props.fieldColors[result.fieldId] ?? '#2196F3'

    group.append('rect')
      .attr('x', px).attr('y', py).attr('width', pw).attr('height', ph)
      .attr('fill', color)
      .attr('fill-opacity', isHovered ? 0.4 : 0.15)
      .attr('stroke', color)
      .attr('stroke-width', isHovered ? 3 / transform.k : 1.5 / transform.k)
      .attr('cursor', 'pointer')
      .on('mouseenter', () => emit('hover', result.fieldId))
      .on('mouseleave', () => emit('hover', null))
      .on('click', () => emit('select', result.fieldId))

    // Field name label
    group.append('text')
      .attr('x', px + 4).attr('y', py - 4)
      .attr('fill', color).attr('font-size', 11 / transform.k)
      .style('pointer-events', 'none')
      .text(result.fieldName)
  }
}
```

### 4. Create `src/components/ocr/results-table.vue`

```vue
<template>
  <div class="results-table">
    <el-table :data="results" border highlight-current-row
              @cell-mouse-enter="onRowHover" @cell-mouse-leave="onRowLeave">
      <el-table-column prop="fieldName" label="Field" width="140" />
      <el-table-column label="Value">
        <template #default="{ row }">
          <el-input v-model="row.value" @change="onValueChange(row)" />
        </template>
      </el-table-column>
      <el-table-column label="Confidence" width="100">
        <template #default="{ row }">
          <el-tag :type="confidenceType(row.confidence)" size="small">
            {{ (row.confidence * 100).toFixed(0) }}%
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Edited" width="70">
        <template #default="{ row }">
          <el-icon v-if="row.edited" color="#67C23A"><Check /></el-icon>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
```

Props: `results: OcrFieldResult[]`, `hoveredFieldId`
Emits: `update:results`, `hover(fieldId | null)`, `valueChange(fieldId, value)`

Confidence color: >= 0.9 success, >= 0.7 warning, < 0.7 danger.

Row hover: highlight by adding `hovered` class when `row.fieldId === hoveredFieldId`. Emit hover on mouse enter/leave.

### 5. Create `src/views/ocr-review-view.vue`

Split-view layout:

```vue
<template>
  <div class="ocr-review">
    <div class="ocr-review__header">
      <el-button @click="router.push('/ocr')">← Back</el-button>
      <h2>OCR Review: {{ job?.templateName }}</h2>
      <el-button type="success" @click="exportJson">Export JSON</el-button>
    </div>
    <div class="ocr-review__content">
      <div class="ocr-review__image">
        <image-overlay
          :image-url="imageUrl"
          :results="job.results"
          :hovered-field-id="hoveredFieldId"
          :field-colors="fieldColors"
          @hover="hoveredFieldId = $event"
        />
      </div>
      <div class="ocr-review__results">
        <results-table
          :results="job.results"
          :hovered-field-id="hoveredFieldId"
          @hover="hoveredFieldId = $event"
          @value-change="onValueChange"
        />
      </div>
    </div>
  </div>
</template>
```

CSS: `.ocr-review__content { display: flex; height: calc(100vh - 120px); }`
Image panel: 55%, Results panel: 45%.

Field colors: load from matched TemplateVersion fields (by fieldId → color mapping).

Export JSON:
```typescript
function exportJson() {
  const data = JSON.stringify(job.value.results, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ocr-${job.value.id}.json`
  a.click()
  URL.revokeObjectURL(url)
}
```

Value change handler:
```typescript
function onValueChange(fieldId: string, value: string) {
  ocrService.updateFieldValue(job.value.id, fieldId, value)
  // Reload job to reflect edited flag
  job.value = ocrService.getJob(route.params.id as string)!
}
```

## Todo List

- [ ] Create ocr-list-view.vue
- [ ] Create ocr-upload-view.vue with processing pipeline
- [ ] Create image-overlay.vue (D3 read-only overlays)
- [ ] Create results-table.vue (editable)
- [ ] Create ocr-review-view.vue (split-view)
- [ ] Implement hover highlight sync between image + table
- [ ] Implement inline value editing + edited flag
- [ ] Implement JSON export download
- [ ] Test: full upload → process → review flow
- [ ] Test: hover highlight works both directions
- [ ] Test: edit value → edited flag appears → export includes edit

## Success Criteria

- OCR list shows all jobs with correct status tags
- Upload flow: shows processing steps with progress
- No template match → clear error with "try again"
- Review: image loads with bbox overlays
- Hover row → corresponding bbox highlights on image
- Hover bbox → corresponding row highlights in table
- Inline edit → value updates, edited flag shown
- Export JSON → downloads .json file with all results
- Delete job from list works

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| No templates → OCR always fails | Med | Show warning on upload page if no templates exist |
| Large image slow to render overlays | Low | POC scope, < 20 fields typical |
| Hover sync laggy | Low | Use CSS transitions, avoid re-rendering entire SVG |

## Security Considerations

- Downloaded JSON contains only field names + OCR values (no PII in POC mock data)
- Image stays in browser, never sent to server

## Next Steps

- Phase 6: Polish & UX refinement
