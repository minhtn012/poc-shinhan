import type { TemplateVersion } from '@/types/template.types'
import type { OcrFieldResult } from '@/types/ocr.types'
import { getTemplates } from './template.service'

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/** Simulate template detection from uploaded image (~1.5s) */
export async function mockPreprocess(
  _blob: Blob
): Promise<{ templateId: string; confidence: number } | null> {
  await delay(1500)
  const templates = getTemplates()
  if (templates.length === 0) return null
  const match = templates.find(t => t.activeVersionId)
  if (!match) return null
  return { templateId: match.id, confidence: 0.92 }
}

/** Simulate OCR extraction using template fields (~2s) */
export async function mockOcr(
  _blob: Blob,
  version: TemplateVersion
): Promise<OcrFieldResult[]> {
  await delay(2000)
  const sampleValues: Record<string, string> = {
    name: 'Nguyen Van A',
    date: '2026-01-15',
    amount: '15,000,000',
    account: '1234-5678-9012',
    id_number: '079012345678',
    address: '123 Le Loi, Q1, HCM'
  }
  return version.fields.map(field => ({
    fieldId: field.id,
    fieldName: field.name,
    bbox: { ...field.bbox },
    value: sampleValues[field.name.toLowerCase()] ?? `Sample ${field.name}`,
    confidence: 0.75 + Math.random() * 0.2,
    edited: false
  }))
}
