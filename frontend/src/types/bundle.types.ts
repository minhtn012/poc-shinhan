export interface Bundle {
  id: string
  name: string
  description?: string
  templateCount: number
  createdAt: string
}

export interface BundleDetail extends Bundle {
  items: BundleItem[]
}

export interface BundleItem {
  id: string
  templateId: string
  templateName: string
  activeVersionId: string | null
  sortOrder: number
}

export interface CreateBundleRequest {
  name: string
  description?: string
  templateIds: string[]
}
