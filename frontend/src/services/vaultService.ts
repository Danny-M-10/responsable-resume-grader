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

export const vaultService = {
  async listAssets(kind: 'job_description' | 'resume'): Promise<Asset[]> {
    const response = await apiClient.get<AssetListResponse>(`/api/vault/assets?kind=${kind}`)
    return response.data.assets
  },

  async saveAsset(file: File, kind: 'job_description' | 'resume'): Promise<Asset> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('kind', kind)

    const response = await apiClient.post<Asset>('/api/vault/assets', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
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
}
