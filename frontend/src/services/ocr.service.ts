import apiClient from '@/lib/api-client'
import type { OcrJob, OcrFieldResult } from '@/types/ocr.types'

interface PreprocessResult {
  templateId: string
  templateName: string
  confidence: number
}

export const ocrService = {
  preprocess: (imageFile: File) => {
    const form = new FormData()
    form.append('image', imageFile)
    return apiClient.post<PreprocessResult | null>('/ocr/preprocess', form).then(r => r.data)
  },

  extract: (templateVersionId: string, imageFile: File) => {
    const form = new FormData()
    form.append('image', imageFile)
    form.append('templateVersionId', templateVersionId)
    return apiClient.post<OcrJob>('/ocr/extract', form).then(r => r.data)
  },

  list: () =>
    apiClient.get<OcrJob[]>('/ocr/jobs').then(r => r.data),

  get: (id: string) =>
    apiClient.get<OcrJob>(`/ocr/jobs/${id}`).then(r => r.data),

  updateField: (jobId: string, fieldId: string, value: string) =>
    apiClient.patch<OcrFieldResult>(`/ocr/jobs/${jobId}/fields/${fieldId}`, { value }).then(r => r.data),

  extractBundle: (bundleId: string, files: File[]) => {
    const form = new FormData()
    form.append('bundleId', bundleId)
    files.forEach(f => form.append('images', f))
    return apiClient.post<OcrJob[]>('/ocr/extract-bundle', form).then(r => r.data)
  },

  listBundleJobs: (bundleId: string) =>
    apiClient.get<OcrJob[]>(`/ocr/jobs/bundle/${bundleId}`).then(r => r.data),

  delete: (id: string) =>
    apiClient.delete(`/ocr/jobs/${id}`),
}
