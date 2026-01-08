import { apiClient } from '../api/client'

export interface AnalysisConfig {
  job_id: string
  candidate_ids: string[]
  industry_template?: string
  custom_scoring_weights?: Record<string, number>
  dealbreakers?: string[]
  bias_reduction_enabled?: boolean
}

export interface AnalysisResponse {
  id: string
  user_id: string
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  results: any | null
  created_at: string
  updated_at: string
}

export const analysisService = {
  async startAnalysis(config: AnalysisConfig): Promise<AnalysisResponse> {
    const response = await apiClient.post<AnalysisResponse>('/api/analysis/start', config)
    return response.data
  },

  async getAnalysis(analysisId: string): Promise<AnalysisResponse> {
    const response = await apiClient.get<AnalysisResponse>(`/api/analysis/${analysisId}`)
    return response.data
  },

  async listAnalyses(): Promise<AnalysisResponse[]> {
    const response = await apiClient.get<AnalysisResponse[]>('/api/analysis')
    return response.data
  },
}
