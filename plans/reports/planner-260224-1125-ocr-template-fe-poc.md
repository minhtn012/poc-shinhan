# Planner Report: OCR Template FE POC

**Date**: 2026-02-24 | **Status**: Complete

## Plan Created

**Location**: `/data/data/poc-shinhan/plans/260224-1108-ocr-template-fe-poc/`

## Files

| File | Purpose |
|------|---------|
| `plan.md` | Overview with phase table, dependency graph, key risks |
| `phase-01-project-scaffold.md` | Vite + Vue 3 + TS init, router, auth guard, login, app layout |
| `phase-02-data-layer.md` | Types, localStorage/localforage services, mock API |
| `phase-03-annotation-canvas.md` | D3 annotation canvas adapted from reference project |
| `phase-04-template-views.md` | Template list, 3-step wizard, version history |
| `phase-05-ocr-views.md` | OCR list, upload+processing flow, split-view review |
| `phase-06-polish-ux.md` | Loading states, empty states, keyboard shortcuts, UX |

## Reference Code Analysis

Read and analyzed from `/data/data/lable-table/frontend-vue/`:
- `render-rectangles.ts` (200 lines) — D3 rect rendering with selection, move, resize, rotation, labels
- `use-d3-canvas.ts` (224 lines) — SVG canvas init, zoom/pan, coordinate transforms
- `use-rectangle-annotations.ts` (107 lines) — Draw state machine (start/update/finish)
- `annotation-shapes.ts` (25 lines) — ShapePoint, RectAnnotation types
- `types.ts` (60 lines) — RendererContext, GridSettings

### Adaptation Strategy
- **Keep**: SVG canvas + zoom/pan, rect draw state machine, move/resize handles, label rendering
- **Drop**: Rotation, polygon, table grid, erase mode, category system, auxlines
- **Adapt**: 4-point polygon coords → NormalizedBBox {x,y,w,h} (0-1 relative)
- **Simplify**: RendererContext → lighter RenderContext without gridSettings

## Effort Estimate

| Phase | Effort |
|-------|--------|
| 1. Project scaffold | 1h |
| 2. Data layer | 1h |
| 3. Annotation canvas | 2h |
| 4. Template views | 2h |
| 5. OCR views | 2h |
| 6. Polish | 1h |
| **Total** | **9h** |

## Dependency Graph

```
Phase 1 (scaffold)
  └─> Phase 2 (data layer)
        ├─> Phase 3 (annotation canvas)
        │     └─> Phase 4 (template views)
        │           └─> Phase 6 (polish)
        └─> Phase 5 (OCR views)
              └─> Phase 6 (polish)
```

## Key Design Decisions

1. **NormalizedBBox (0-1)** as storage format — decouples annotation from display resolution
2. **localStorage for metadata, localforage for images** — avoids 5MB limit
3. **Composable-heavy architecture** — keeps .vue files thin, logic testable
4. **Simplified D3 renderer** — no rotation/polygon, just rect with move/resize
5. **Mock API with delays** — simulates real async processing for demo UX

## File Count

~25 source files total across `src/`:
- 7 views, 5 components, 3 composables, 3 services, 2 type files
- Plus router, stores, main.ts, App.vue, styles, env
