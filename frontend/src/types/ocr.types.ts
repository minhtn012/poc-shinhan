import type { NormalizedBBox } from './template.types'

// ── YOLO bbox ─────────────────────────────────────────────────────────────────

/** YOLO bbox: [center_x, center_y, width, height], all normalized 0–1 */
export type YoloBBox = [cx: number, cy: number, w: number, h: number]

// ── Real API types ────────────────────────────────────────────────────────────

/** Raw 4-corner quad from /matching_and_ocr */
export type ApiBoxQuad = [[number,number],[number,number],[number,number],[number,number]]

/** YOLO box with class ID: [class_id, cx, cy, w, h] — used in /get_templates and /update_template */
export type ApiBox5 = [classId: number, cx: number, cy: number, w: number, h: number]

export interface ApiLayoutField {
  field_name: string
  box: ApiBox5
}

export interface ApiLayoutVersion {
  version: string
  fields: ApiLayoutField[]
  status: 'active' | 'inactive'
}

export interface ApiLayout {
  layout_id: string
  layout_name: string
  image_base64?: string
  versions: ApiLayoutVersion[]
}

export interface GetTemplatesResponse {
  status: 'success' | 'error'
  templates: ApiLayout[]
}

export interface UpdateTemplateRequest {
  action: 'add' | 'update'
  layout_id: string | null
  layout_name: string
  image_base64: string
  versions: ApiLayoutVersion[]
}

export interface UpdateTemplateResponse {
  status: 'success' | 'error'
  layout_id?: string
  message?: string
}

export interface ApiResult {
  box: ApiBoxQuad
  crop_path: string
  text: string
}

/** BE field definition with YOLO bbox (sent/received from template API) */
export interface ApiTemplateField {
  id: string
  name: string
  color: string
  bbox: YoloBBox
}

/** Payload to send template fields to BE */
export interface SaveTemplateFieldsRequest {
  template_id: string
  version: string
  fields: ApiTemplateField[]
}

export interface MatchingAndOcrResponse {
  status: 'success' | 'error'
  form_id: string
  processed_image: string // relative path e.g. "/static/outputs/.../xxx_unwarped.jpg"
  metrics: { coverage: number; covered_cells: number; entropy: number }
  results: ApiResult[]
}

// ── App types ─────────────────────────────────────────────────────────────────

export interface OcrFieldResult {
  fieldId: string
  fieldName: string
  bbox: NormalizedBBox
  value: string
  confidence: number // 0-1
  edited: boolean
}

export type OcrJobStatus = 'pending' | 'processing' | 'done' | 'error'

export interface OcrJob {
  id: string
  templateVersionId: string
  templateName: string
  imageKey: string
  processedImageUrl?: string // full URL to API-processed image (if real API used)
  status: OcrJobStatus
  results: OcrFieldResult[]
  createdAt: string
}
