# Phase 3: Annotation Canvas

## Context Links

- Plan overview: [plan.md](./plan.md)
- Depends on: [Phase 2](./phase-02-data-layer.md)
- D3 render reference: `/data/data/lable-table/frontend-vue/src/lib/d3-renderers/render-rectangles.ts`
- Canvas composable ref: `/data/data/lable-table/frontend-vue/src/composables/use-d3-canvas.ts`
- Rect annotations ref: `/data/data/lable-table/frontend-vue/src/composables/use-rectangle-annotations.ts`
- Shape types ref: `/data/data/lable-table/frontend-vue/src/types/annotation-shapes.ts`

## Overview

- **Priority**: P1 (core complex piece)
- **Status**: completed
- **Effort**: 2h
- **Description**: Adapt D3 annotation canvas from reference project. Simplified for OCR use case: draw bbox rectangles, label fields, select/move/resize. No rotation, polygon, or table grid.

## Key Insights from Reference Code

### What to KEEP (adapt)
- `use-d3-canvas.ts`: SVG creation, zoom/pan, image loading, coordinate transforms, fitToContainer — **reuse almost entirely**
- `use-rectangle-annotations.ts`: Draw state machine (startDraw→updateDraw→finishDraw), selection — **reuse core logic**
- `render-rectangles.ts`: Rect rendering, color fill, label text, selection highlight, resize handles, drag-to-move — **adapt significantly**

### What to DROP
- Rotation handle + rotation logic (no `rotation` field in our model)
- Polygon support, auxlines, auxcurves, corners, PV modules, table grid
- Erase mode, delete mode (we use sidebar delete button instead)
- Category system (we use simple field name + color)
- `gridSettings` dependency (replace with simpler config)

### Key Adaptation: Coordinate Normalization
Reference uses pixel coordinates (ShapePoint). We need NormalizedBBox (0-1).
- On draw finish: convert pixel rect → NormalizedBBox by dividing by imgWidth/imgHeight
- On render: convert NormalizedBBox → pixel rect by multiplying by imgWidth/imgHeight
- This is the critical bridge between storage format and display format

### Simplified Data Model
Reference `RectAnnotation` has 4-point polygon + rotation. Our model:
```typescript
// Internal canvas state (pixel coords during drawing)
interface CanvasRect {
  id: string
  x: number; y: number; w: number; h: number  // pixel coords
  fieldName: string
  color: string
}
// Storage format
interface TemplateField { id, name, color, bbox: NormalizedBBox }
```

## Requirements

### Functional
- Load image into D3 SVG canvas with zoom/pan
- Draw rectangles via mouse drag (mousedown → drag → mouseup)
- Each rectangle gets auto-assigned a color, user provides field name
- Select rectangle by click → show resize handles + highlight
- Move selected rectangle by drag
- Resize via corner/edge handles
- Label overlay showing field name at rect center
- Delete selected rectangle (via external trigger, not erase mode)
- Convert between NormalizedBBox (storage) ↔ pixel coords (display)

### Non-Functional
- Smooth rendering at 60fps during draw/resize
- Handle images up to 4000x4000px
- Canvas responsive to container resize

## Architecture

```
src/
├── composables/
│   └── use-annotation.ts      # Combines D3 canvas + rect drawing + normalization
├── components/annotation/
│   ├── annotation-canvas.vue  # D3 SVG container + mouse event wiring
│   └── field-sidebar.vue      # Field list panel: name editor, delete, color
├── lib/
│   └── render-fields.ts       # D3 renderer for field rectangles (adapted)
```

### Component Communication
```
annotation-canvas.vue
  ├── Props: imageUrl, fields (TemplateField[])
  ├── Emits: update:fields, fieldSelected(id)
  └── Uses: use-annotation composable internally

field-sidebar.vue
  ├── Props: fields (TemplateField[]), selectedFieldId
  ├── Emits: update:fields, select(id), delete(id)
  └── Inline editing of field names
```

Parent (template-create-view Step 2) orchestrates both via v-model.

## Related Code Files

### Create
- `src/composables/use-annotation.ts`
- `src/components/annotation/annotation-canvas.vue`
- `src/components/annotation/field-sidebar.vue`
- `src/lib/render-fields.ts`

## Implementation Steps

### 1. Create `src/lib/render-fields.ts` — D3 field renderer

Adapted from reference `render-rectangles.ts`. Simplified:

```typescript
import * as d3 from 'd3'
import type { NormalizedBBox } from '@/types/template.types'

interface FieldRect {
  id: string
  name: string
  color: string
  bbox: NormalizedBBox  // 0-1
}

interface RenderContext {
  content: d3.Selection<SVGGElement, unknown, null, undefined>
  transform: d3.ZoomTransform
  imgWidth: number
  imgHeight: number
}

interface FieldCallbacks {
  onSelect: (id: string) => void
  onMove: (id: string, dx: number, dy: number) => void
  onResize: (id: string, handleIndex: number, x: number, y: number) => void
}

export function renderFields(
  ctx: RenderContext,
  fields: FieldRect[],
  selectedId: string | null,
  drawPreview: { x: number; y: number; w: number; h: number } | null,
  callbacks: FieldCallbacks,
  svgNode: SVGSVGElement | null
): void
```

Key differences from reference:
- No rotation (remove rotation transform, rotation handle)
- No erase mode click handling
- Rect drawn from `{x, y, w, h}` pixel coords (denormalized from NormalizedBBox) instead of 4-point polygon
- Label shows `field.name` directly instead of category lookup
- Resize handles: 4 corners + 4 edge midpoints (same as reference)
- Move: drag on rect body (same as reference)

Denormalize for rendering:
```typescript
const px = field.bbox.x * ctx.imgWidth
const py = field.bbox.y * ctx.imgHeight
const pw = field.bbox.w * ctx.imgWidth
const ph = field.bbox.h * ctx.imgHeight
```

### 2. Create `src/composables/use-annotation.ts`

Combines adapted `use-d3-canvas` + `use-rectangle-annotations` logic:

```typescript
export function useAnnotation(
  containerRef: Ref<HTMLDivElement | null>,
  options: { initialFields?: TemplateField[] } = {}
) {
  // --- D3 Canvas state (from use-d3-canvas) ---
  const svg = shallowRef<d3.Selection<...> | null>(null)
  const currentTransform = ref<d3.ZoomTransform>(d3.zoomIdentity)
  const imgWidth = ref(0)
  const imgHeight = ref(0)
  const panEnabled = ref(true)

  // --- Drawing state (from use-rectangle-annotations) ---
  const isDrawing = ref(false)
  const drawStart = ref<{x:number,y:number} | null>(null)
  const drawCurrent = ref<{x:number,y:number} | null>(null)
  const selectedFieldId = ref<string | null>(null)

  // --- Field data ---
  const fields = ref<TemplateField[]>(options.initialFields ?? [])

  // Color palette for auto-assignment
  const COLORS = ['#2196F3','#4CAF50','#FF9800','#E91E63','#9C27B0','#00BCD4','#FF5722','#607D8B']

  // --- Core methods ---
  async function initCanvas(imageUrl: string): Promise<void>   // from use-d3-canvas
  function render(): void                                       // clear + renderFields
  function startDraw(x, y): void                               // from use-rectangle-annotations
  function updateDraw(x, y): void
  function finishDraw(): TemplateField | null                   // Create field with NormalizedBBox
  function selectField(id: string): void
  function deleteField(id: string): void
  function updateFieldName(id: string, name: string): void
  function moveField(id: string, dx: number, dy: number): void // Update bbox
  function resizeField(id: string, handleIdx, x, y): void      // Update bbox

  // --- Normalization helpers ---
  function toNormalized(px, py, pw, ph): NormalizedBBox
  function toPixel(bbox: NormalizedBBox): {x,y,w,h}

  return {
    fields, selectedFieldId, isDrawing,
    imgWidth, imgHeight,
    initCanvas, selectField, deleteField, updateFieldName,
    render  // Called by watchEffect in canvas component
  }
}
```

Key flow for drawing:
1. Canvas component wires mousedown/mousemove/mouseup on SVG
2. On mousedown (when not on existing rect): `startDraw(imgX, imgY)`, set `panEnabled=false`
3. On mousemove: `updateDraw(imgX, imgY)`, re-render shows preview dashed rect
4. On mouseup: `finishDraw()` → creates TemplateField with NormalizedBBox, auto-assigns color, name="Field N"
5. Set `panEnabled=true`

### 3. Create `src/components/annotation/annotation-canvas.vue`

```vue
<template>
  <div ref="canvasContainer" class="annotation-canvas" />
</template>

<script setup lang="ts">
// Props: imageUrl (string), modelValue (TemplateField[])
// Emits: update:modelValue, fieldSelected(id)
// Uses useAnnotation composable
// watchEffect → calls render() on any reactive change
// Wires SVG mouse events for drawing
// Syncs fields ↔ modelValue via watch
</script>
```

Keep under 100 lines. All logic in composable.

### 4. Create `src/components/annotation/field-sidebar.vue`

```vue
<template>
  <div class="field-sidebar">
    <div class="field-sidebar__header">
      <span>Fields ({{ fields.length }})</span>
    </div>
    <div v-for="field in fields" :key="field.id" class="field-item"
         :class="{ selected: field.id === selectedFieldId }"
         @click="$emit('select', field.id)">
      <span class="color-dot" :style="{ background: field.color }" />
      <el-input v-model="field.name" size="small" @change="updateName(field)" />
      <el-button type="danger" :icon="Delete" circle size="small"
                 @click.stop="$emit('delete', field.id)" />
    </div>
    <el-empty v-if="!fields.length" description="Draw rectangles on the image" />
  </div>
</template>
```

Props: `fields`, `selectedFieldId`. Emits: `update:fields`, `select`, `delete`.

### 5. Wire mouse events in canvas component

In annotation-canvas.vue setup:
```typescript
// After initCanvas completes:
const svgEl = annotation.getSvgNode()
if (svgEl) {
  d3.select(svgEl)
    .on('mousedown.draw', (event) => {
      if (event.button !== 0) return
      const [sx, sy] = d3.pointer(event)
      const { x, y } = screenToImage(sx, sy)
      annotation.startDraw(x, y)
    })
    .on('mousemove.draw', (event) => {
      const [sx, sy] = d3.pointer(event)
      const { x, y } = screenToImage(sx, sy)
      annotation.updateDraw(x, y)
    })
    .on('mouseup.draw', () => {
      const newField = annotation.finishDraw()
      if (newField) emit('fieldCreated', newField)
    })
}
```

### 6. Integration test

- Load a sample image into canvas
- Draw 3 rectangles → verify fields array has 3 items with NormalizedBBox 0-1
- Select rect → highlight + handles appear
- Move rect → bbox updates
- Resize rect → bbox updates
- Delete via sidebar → field removed, rect disappears

## Todo List

- [ ] Create render-fields.ts (adapted from render-rectangles.ts)
- [ ] Create use-annotation.ts composable
- [ ] Create annotation-canvas.vue component
- [ ] Create field-sidebar.vue component
- [ ] Wire mouse events for draw/select
- [ ] Implement move + resize handlers
- [ ] Implement NormalizedBBox ↔ pixel conversion
- [ ] Test: draw rect → verify normalized coords
- [ ] Test: load fields → verify pixel rendering matches
- [ ] Test: move/resize → verify bbox updates correctly

## Success Criteria

- Image loads in D3 SVG with zoom/pan working
- Drawing: mousedown→drag→mouseup creates a visible rectangle
- Created field has NormalizedBBox with values between 0-1
- Selection shows white dashed border + 8 resize handles
- Drag on selected rect body moves it, bbox updates
- Drag on handle resizes rect, bbox updates
- Field name label renders at center of each rect
- Sidebar shows all fields with editable names
- Delete from sidebar removes rect from canvas

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| D3 event conflicts between zoom and draw | High | panEnabled flag (proven in reference code) |
| Coordinate normalization drift | Med | Unit test: draw → normalize → denormalize → compare |
| Performance with many rects | Low | POC typically < 20 fields, D3 handles fine |
| SVG not responsive on resize | Med | Add ResizeObserver → fitToContainer() |

## Security Considerations

- Image loaded from local blob URL — no external fetch
- No user input rendered as HTML (field names in SVG text elements = safe)

## Next Steps

- Phase 4: Template Management views (uses annotation-canvas component)
