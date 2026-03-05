import apiClient from '@/lib/api-client'
import type { Template, TemplateVersion, TemplateField } from '@/types/template.types'

interface TemplateDetail extends Template {
  versions: TemplateVersion[]
}

export const templateService = {
  list: () =>
    apiClient.get<Template[]>('/templates').then(r => r.data),

  get: (id: string) =>
    apiClient.get<TemplateDetail>(`/templates/${id}`).then(r => r.data),

  create: (name: string, description?: string) =>
    apiClient.post<Template>('/templates', { name, description }).then(r => r.data),

  update: (id: string, patch: { name?: string; description?: string }) =>
    apiClient.put<Template>(`/templates/${id}`, patch).then(r => r.data),

  delete: (id: string) =>
    apiClient.delete(`/templates/${id}`),

  getVersions: (templateId: string) =>
    apiClient.get<TemplateVersion[]>(`/templates/${templateId}/versions`).then(r => r.data),

  createVersion: (templateId: string, version: string, fields: TemplateField[], imageFile: File) => {
    const form = new FormData()
    form.append('image', imageFile)
    form.append('version', version)
    form.append('fields', JSON.stringify(fields.map(f => ({
      name: f.name, color: f.color, bbox: f.bbox,
    }))))
    return apiClient.post<TemplateVersion>(`/templates/${templateId}/versions`, form).then(r => r.data)
  },

  suggestVersion: (templateId: string) =>
    apiClient.get<{ version: string }>(`/templates/${templateId}/suggest-version`).then(r => r.data.version),

  activateVersion: (versionId: string) =>
    apiClient.put<TemplateVersion>(`/versions/${versionId}/activate`).then(r => r.data),

  updateFields: (versionId: string, fields: TemplateField[]) =>
    apiClient.put<TemplateVersion>(`/versions/${versionId}/fields`, {
      fields: fields.map(f => ({ name: f.name, color: f.color, bbox: f.bbox })),
    }).then(r => r.data),
}
