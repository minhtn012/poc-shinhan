import type {
  MatchingAndOcrResponse,
  GetTemplatesResponse,
  UpdateTemplateRequest,
  UpdateTemplateResponse,
} from '@/types/ocr.types'
import type { TemplateField } from '@/types/template.types'
import { templateFieldsToApi } from '@/lib/api-bbox-transform'

const BASE = import.meta.env.VITE_OCR_API_URL ?? 'http://10.3.11.150:8000'

/** Returns base URL of the OCR API server */
export function getApiBase(): string {
  return BASE
}

/**
 * Fetch all layout templates from BE.
 * GET /get_templates
 */
export async function getTemplates(): Promise<GetTemplatesResponse> {
  const res = await fetch(`${BASE}/get_templates`)
  if (!res.ok) throw new Error(`Get templates failed: ${res.status}`)
  return res.json() as Promise<GetTemplatesResponse>
}

/**
 * Create or update a layout template.
 * POST /update_template
 * action: "add" = tạo mới, "edit" = chỉnh sửa
 */
export async function updateTemplate(payload: UpdateTemplateRequest): Promise<UpdateTemplateResponse> {
  const res = await fetch(`${BASE}/update_template`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Update template failed: ${res.status}`)
  return res.json() as Promise<UpdateTemplateResponse>
}

/**
 * Send template fields to BE in YOLO format.
 * POST /templates/fields — stub until BE implements this endpoint.
 */
export async function saveTemplateFields(
  templateId: string,
  version: string,
  fields: TemplateField[]
): Promise<void> {
  const res = await fetch(`${BASE}/templates/fields`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template_id: templateId, version, fields: templateFieldsToApi(fields) }),
  })
  if (!res.ok) throw new Error(`Save fields failed: ${res.status}`)
}

/**
 * Upload image → preprocess + match template + extract text in one shot.
 * POST /matching_and_ocr (multipart/form-data, field: "file")
 */
export async function matchingAndOcr(file: File): Promise<MatchingAndOcrResponse> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/matching_and_ocr`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`OCR API error: ${res.status} ${res.statusText}`)
  const data = await res.json() as MatchingAndOcrResponse
  if (data.status !== 'success') throw new Error(`OCR failed: ${JSON.stringify(data)}`)
  return data
}
