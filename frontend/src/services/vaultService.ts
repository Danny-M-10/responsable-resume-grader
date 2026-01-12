import { apiClient } from '../api/client'

export interface Asset {
  id: string
  original_name: string
  stored_path: string
  metadata: Record<string, any>
  created_at: string
}

export interface AssetListResponse {
  assets: Asset[]
}

export interface AssetFilters {
  search?: string
  tags?: string[]
  skills?: string[]
  name?: string
}

export const vaultService = {
  async listAssets(
    kind: 'job_description' | 'resume',
    filters?: AssetFilters
  ): Promise<Asset[]> {
    const params = new URLSearchParams({ kind })
    
    if (filters?.search) {
      params.append('search', filters.search)
    }
    if (filters?.tags && filters.tags.length > 0) {
      params.append('tags', filters.tags.join(','))
    }
    if (filters?.skills && filters.skills.length > 0) {
      params.append('skills', filters.skills.join(','))
    }
    if (filters?.name) {
      params.append('name', filters.name)
    }
    
    const response = await apiClient.get<AssetListResponse>(`/api/vault/assets?${params.toString()}`)
    return response.data.assets
  },

  async saveAsset(file: File, kind: 'job_description' | 'resume'): Promise<Asset> {
    const formData = new FormData()
    formData.append('file', file)
    // kind should be sent as a query parameter, not form data

    // Don't set Content-Type header - axios automatically sets it with boundary for FormData
    const response = await apiClient.post<Asset>('/api/vault/assets', formData, {
      params: { kind },
    })
    return response.data
  },

  async getAsset(assetId: string): Promise<Asset> {
    const response = await apiClient.get<Asset>(`/api/vault/assets/${assetId}`)
    return response.data
  },

  async downloadAsset(assetId: string): Promise<Blob> {
    const response = await apiClient.get(`/api/vault/assets/${assetId}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  async deleteAsset(assetId: string): Promise<void> {
    await apiClient.delete(`/api/vault/assets/${assetId}`)
  },

  async updateTags(assetId: string, tags: string[]): Promise<Asset> {
    const response = await apiClient.put<Asset>(`/api/vault/assets/${assetId}/tags`, { tags })
    return response.data
  },
}
