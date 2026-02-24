import type { NormalizedBBox } from './template.types'

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
  status: OcrJobStatus
  results: OcrFieldResult[]
  createdAt: string
}
