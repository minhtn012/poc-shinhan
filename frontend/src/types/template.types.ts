export interface NormalizedBBox {
  x: number // 0-1, left edge relative to image width
  y: number // 0-1, top edge relative to image height
  w: number // 0-1, width relative to image width
  h: number // 0-1, height relative to image height
}

export interface TemplateField {
  id: string
  name: string
  color: string // hex color for bbox display
  bbox: NormalizedBBox
}

export interface Template {
  id: string
  name: string
  description?: string
  activeVersionId: string | null
  versionCount?: number
  createdAt: string // ISO
}

export interface TemplateVersion {
  id: string
  templateId: string
  version: string // e.g. "v1", "v2"
  status: 'active' | 'inactive'
  imageUrl: string // server URL: /api/images/{filename}
  fields: TemplateField[]
  createdAt: string
}
