# Brainstorm Report: OCR Template FE POC

**Date**: 2026-02-24 | **Status**: Agreed

---

## Problem Statement

Build FE POC cho ứng dụng OCR theo template:
- Quản lý template (upload ảnh, vẽ bbox cho các field, versioning)
- Quản lý OCR jobs (upload → detect template → OCR → review/edit kết quả)
- POC: không cần user management, login hardcoded, API mock

---

## Final Architecture

### Stack
- **Framework**: Vue 3 + TypeScript + Vite
- **UI Library**: Element Plus
- **State**: Pinia + TanStack Vue Query
- **Annotation**: D3.js (reuse từ `/data/data/label-table/frontend-vue`)
- **Image Storage**: `localforage` (IndexedDB) — tránh giới hạn 5MB của localStorage
- **Metadata Storage**: localStorage (template info, bbox data)

### Data Model

```typescript
interface Template { id, name, activeVersionId, createdAt }
interface TemplateVersion { id, templateId, version, status('active'|'inactive'), imageKey, fields[], createdAt }
interface TemplateField { id, name, color, bbox: NormalizedBBox }
interface NormalizedBBox { x, y, w, h }  // 0-1 relative to image

interface OcrJob { id, templateVersionId, templateName, imageKey, status, results[], createdAt }
interface OcrFieldResult { fieldId, fieldName, bbox, value, confidence, edited }
```

### Routing
```
/login
/templates                   → List templates
/templates/create            → 3-step wizard (upload → annotate → confirm)
/templates/:id               → Version history
/ocr                         → List OCR jobs
/ocr/new                     → Upload → detect → OCR
/ocr/:id                     → Split-view review (image + editable table)
```

### Template Create: 3-Step Wizard (El-Steps)
1. **Upload**: Upload ảnh mẫu, nhập tên template, version
2. **Annotate**: D3 canvas vẽ bounding box, đặt tên field cho từng box
3. **Confirm**: Preview tất cả fields, lưu → active, version cũ → inactive

### OCR Review: Split View
- **Left**: Ảnh gốc với highlight overlay boxes (hover box → highlight row)
- **Right**: Editable table (field name, OCR value, confidence %)
- Export JSON

### Mock API
```typescript
mockPreprocess(image) → { templateId, confidence }  // delay 1.5s
mockOcr(image, template) → OcrFieldResult[]         // delay 2s
```

### Annotation Canvas (adapted from existing)
- Keep: draw rect, select/move/resize, label text, normalized bbox
- Drop: rotation, polygon, table grid, aux lines

---

## Key Decisions & Rationale

| Decision | Choice | Why |
|----------|--------|-----|
| LocalStorage vs IndexedDB | localforage (IndexedDB) | Ảnh base64 vượt 5MB limit |
| Annotation lib | D3.js (reuse) | Existing proven code, rectangle-ready |
| Template Create UX | 3-step wizard | Rõ ràng, guided flow |
| OCR Review UX | Split view (image + table) | Best UX cho review |
| New project vs extend | New standalone project | Domain khác, tránh conflict |

---

## Risks
- IndexedDB có thể bị xóa khi browser clear storage (acceptable for POC)
- D3 adaptation cần test coordinate normalization kỹ
- Bbox normalization phải consistent giữa annotation → OCR display

---

## Next Steps
→ Create implementation plan with phased breakdown
