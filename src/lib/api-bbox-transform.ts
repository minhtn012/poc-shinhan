import type { ApiBoxQuad, ApiResult, OcrFieldResult, ApiTemplateField } from '@/types/ocr.types'
import type { TemplateField } from '@/types/template.types'
import { yoloToNormalized, normalizedToYolo } from './bbox-convert'

/** Convert a File to a base64-encoded data string (without the data: prefix). */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result.split(',')[1] ?? result)
    }
    reader.onerror = () => reject(new Error('Failed to read file as base64'))
    reader.readAsDataURL(file)
  })
}

/** Convert a Blob to a base64-encoded data string (without the data: prefix). */
export function blobToBase64(blob: Blob): Promise<string> {
  return fileToBase64(new File([blob], 'image'))
}

/** Load image from URL, return natural dimensions */
export function loadImageDimensions(url: string): Promise<{ w: number; h: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload  = () => resolve({ w: img.naturalWidth, h: img.naturalHeight })
    img.onerror = () => reject(new Error(`Failed to load image: ${url}`))
    img.src = url
  })
}

/** Convert 4-corner quad → axis-aligned bounding box (pixel coords) */
function quadToAabb(box: ApiBoxQuad): { x: number; y: number; w: number; h: number } {
  const xs = box.map(p => p[0])
  const ys = box.map(p => p[1])
  const minX = Math.min(...xs), maxX = Math.max(...xs)
  const minY = Math.min(...ys), maxY = Math.max(...ys)
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY }
}

/** Convert BE YOLO fields → internal TemplateField[] */
export function apiFieldsToTemplate(apiFields: ApiTemplateField[]): TemplateField[] {
  return apiFields.map(f => ({
    id: f.id,
    name: f.name,
    color: f.color,
    bbox: yoloToNormalized(f.bbox),
  }))
}

/** Convert internal TemplateField[] → BE YOLO format */
export function templateFieldsToApi(fields: TemplateField[]): ApiTemplateField[] {
  return fields.map(f => ({
    id: f.id,
    name: f.name,
    color: f.color,
    bbox: normalizedToYolo(f.bbox),
  }))
}

/**
 * Transform API results into OcrFieldResult[].
 * imgW/imgH: dimensions of the processed image (for normalization).
 */
export function transformApiResults(
  results: ApiResult[],
  imgW: number,
  imgH: number
): OcrFieldResult[] {
  return results.map((item, i) => {
    const aabb = quadToAabb(item.box)
    return {
      fieldId:   `field_${i}`,
      fieldName: `Field ${i + 1}`,
      bbox: {
        x: aabb.x / imgW,
        y: aabb.y / imgH,
        w: aabb.w / imgW,
        h: aabb.h / imgH
      },
      value:      item.text,
      confidence: 1.0,
      edited:     false
    }
  })
}
