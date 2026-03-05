# Template Management API — BE Implementation Guide

> Tài liệu này mô tả toàn bộ API contract giữa FE và BE cho hệ thống OCR Template.
> BE đọc doc này để biết chính xác cần implement gì.

---

## BBox Format — YOLO

**Tất cả** tọa độ vùng trích xuất (bbox) dùng **YOLO format**:

```
bbox = [cx, cy, w, h]
```

| Trường | Ý nghĩa | Range |
|--------|---------|-------|
| `cx` | x tâm / image width | 0.0 – 1.0 |
| `cy` | y tâm / image height | 0.0 – 1.0 |
| `w`  | width / image width | 0.0 – 1.0 |
| `h`  | height / image height | 0.0 – 1.0 |

Ví dụ: vùng ở giữa ảnh, chiếm 40% chiều ngang, 6% chiều dọc:
```json
"bbox": [0.50, 0.23, 0.40, 0.06]
```

FE tự convert sang top-left origin khi render — BE không cần quan tâm.

---

## Base URL

```
https://{host}/api
```

---

## Data Models

### Template
```json
{
  "id": "string (UUID)",
  "name": "string",
  "description": "string | null",
  "activeVersionId": "string (UUID) | null",
  "createdAt": "ISO 8601"
}
```

### TemplateVersion
```json
{
  "id": "string (UUID)",
  "templateId": "string (UUID)",
  "version": "string",
  "status": "active | inactive",
  "imageUrl": "string (absolute URL)",
  "fields": "TemplateField[]",
  "createdAt": "ISO 8601"
}
```

### TemplateField
```json
{
  "id": "string (UUID)",
  "name": "string",
  "color": "string (hex, e.g. #3B82F6)",
  "bbox": [0.30, 0.23, 0.40, 0.06]
}
```

---

## Error Response Format

```json
{
  "error": "Human-readable message",
  "code": "MACHINE_CODE"
}
```

| HTTP | Dùng khi |
|------|---------|
| 400 | Input không hợp lệ |
| 404 | Resource không tồn tại |
| 409 | Conflict (vd: không thể xóa version duy nhất) |
| 500 | Server error |

---

## Endpoints

---

### Template CRUD

#### `GET /templates`

List tất cả templates.

**Response 200:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "CMND Mặt Trước",
      "description": null,
      "activeVersionId": "660e8400-e29b-41d4-a716-446655440001",
      "createdAt": "2026-02-27T09:00:00Z"
    }
  ]
}
```

---

#### `POST /templates`

Tạo template mới.

**Request body:**
```json
{
  "name": "CMND Mặt Trước",
  "description": "optional"
}
```

**Validation:**
- `name`: required, non-empty string

**Response 201:** Template object

---

#### `GET /templates/:id`

**Response 200:** Template object
**Response 404:** `{ "error": "Template not found", "code": "TEMPLATE_NOT_FOUND" }`

---

#### `PATCH /templates/:id`

Update name / description (partial update).

**Request body:**
```json
{
  "name": "New name",
  "description": "New desc"
}
```

**Response 200:** Updated Template object

---

#### `DELETE /templates/:id`

Xóa template và **cascade xóa tất cả versions** liên quan.

**Response 204:** no body

---

### Template Versions

#### `GET /templates/:templateId/versions`

List tất cả versions của một template.

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "templateId": "uuid",
      "version": "v1",
      "status": "active",
      "imageUrl": "https://cdn.example.com/templates/uuid/v1.jpg",
      "fields": [
        {
          "id": "uuid",
          "name": "Số CMND",
          "color": "#3B82F6",
          "bbox": [0.30, 0.23, 0.40, 0.06]
        },
        {
          "id": "uuid",
          "name": "Ngày sinh",
          "color": "#10B981",
          "bbox": [0.25, 0.35, 0.30, 0.05]
        }
      ],
      "createdAt": "2026-02-27T09:00:00Z"
    }
  ]
}
```

---

#### `POST /templates/:templateId/versions`

Tạo version mới — upload ảnh mẫu + field definitions.

**Request:** `multipart/form-data`

| Field | Type | Required | Note |
|-------|------|----------|------|
| `image` | file | ✅ | jpg/png, ảnh mẫu dùng để matching |
| `version` | string | ✅ | e.g. "v1", "v2" — unique per templateId |
| `fields` | string (JSON) | ✅ | `JSON.stringify(TemplateField[])` |

**`fields` value example:**
```json
[
  { "id": "uuid", "name": "Số CMND",   "color": "#3B82F6", "bbox": [0.30, 0.23, 0.40, 0.06] },
  { "id": "uuid", "name": "Ngày sinh", "color": "#10B981", "bbox": [0.25, 0.35, 0.30, 0.05] }
]
```

> **Note:** Nếu FE không gửi `id` trong field, BE tự generate UUID.

**Behavior khi tạo:**
1. Lưu ảnh, trả về `imageUrl`
2. Set tất cả versions cũ của `templateId` → `status: "inactive"`
3. Version mới → `status: "active"`
4. Cập nhật `Template.activeVersionId = newVersion.id`

**Validation:**
- `version` phải unique trong cùng `templateId`
- `fields[].bbox` — mảng 4 số, mỗi số trong [0, 1]

**Response 201:** TemplateVersion object

---

#### `GET /templates/:templateId/versions/:versionId`

**Response 200:** TemplateVersion object (full fields included)

---

#### `PATCH /templates/:templateId/versions/:versionId/activate`

Activate một version cụ thể.

**Request body:** `{}` (no body needed)

**Behavior:**
1. Set version này → `status: "active"`
2. Set các versions khác cùng templateId → `status: "inactive"`
3. Cập nhật `Template.activeVersionId = versionId`

**Response 200:** Updated TemplateVersion object

---

#### `PATCH /templates/:templateId/versions/:versionId/fields`

Cập nhật danh sách fields (re-annotate không cần upload ảnh mới).

**Request body:**
```json
{
  "fields": [
    { "id": "uuid", "name": "Số CMND", "color": "#3B82F6", "bbox": [0.30, 0.23, 0.40, 0.06] }
  ]
}
```

**Response 200:** Updated TemplateVersion object

---

#### `DELETE /templates/:templateId/versions/:versionId`

**Constraint:** Không xóa được nếu là version `active` duy nhất của template.

**Response 204:** no body
**Response 409:** `{ "error": "Cannot delete the only active version", "code": "LAST_ACTIVE_VERSION" }`

---

### Template Fields (Batch Send)

#### `POST /templates/fields`

Gửi toàn bộ fields của một version lên BE (dùng khi sync sau khi annotate).

**Request body:**
```json
{
  "template_id": "uuid",
  "version": "v1",
  "fields": [
    { "id": "uuid", "name": "Số CMND", "color": "#3B82F6", "bbox": [0.30, 0.23, 0.40, 0.06] }
  ]
}
```

**Response 200:** `{ "ok": true }`

---

## Existing OCR Endpoint (đã có)

#### `POST /matching_and_ocr`

Upload ảnh → preprocessing + template matching + OCR.

**Request:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `file` | file | ✅ |

**Response 200:**
```json
{
  "status": "success",
  "form_id": "string",
  "processed_image": "/static/outputs/.../xxx_unwarped.jpg",
  "metrics": {
    "coverage": 0.87,
    "covered_cells": 12,
    "entropy": 0.43
  },
  "results": [
    {
      "box": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]],
      "crop_path": "/static/crops/...",
      "text": "extracted text"
    }
  ]
}
```

> `box` là 4-corner quad (pixel coords), không phải YOLO. FE tự normalize.

---

## Notes cho BE

1. `bbox` luôn là `[cx, cy, w, h]` YOLO format, tất cả trong khoảng `[0.0, 1.0]`
2. `imageUrl` trong TemplateVersion phải là **absolute URL** (FE load trực tiếp bằng `<img src>`)
3. Cascade delete: `DELETE /templates/:id` → xóa hết versions liên quan
4. `version` string unique per `templateId` — BE nên validate và trả 400 nếu trùng
5. `id` của TemplateField: FE có thể gửi UUID sẵn, BE dùng luôn; nếu không có thì BE generate
