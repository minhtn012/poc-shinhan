import apiClient from '@/lib/api-client'
import type { Bundle, BundleDetail, CreateBundleRequest } from '@/types/bundle.types'

export const bundleService = {
  list: () =>
    apiClient.get<Bundle[]>('/bundles').then(r => r.data),

  get: (id: string) =>
    apiClient.get<BundleDetail>(`/bundles/${id}`).then(r => r.data),

  create: (data: CreateBundleRequest) =>
    apiClient.post<Bundle>('/bundles', data).then(r => r.data),

  update: (id: string, data: Partial<CreateBundleRequest>) =>
    apiClient.put<Bundle>(`/bundles/${id}`, data).then(r => r.data),

  delete: (id: string) =>
    apiClient.delete(`/bundles/${id}`),
}
