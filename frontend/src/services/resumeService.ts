import { apiClient } from '../api/client'

export interface ResumeUploadResponse {
  message: string
  candidate_ids: string[]
  parsed_data: any[]
  client_id?: string  // Client ID for WebSocket progress updates
}

export const resumeService = {
  async uploadResumes(files: File[], clientId?: string): Promise<ResumeUploadResponse> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    // Don't set Content-Type header - axios automatically sets it with boundary for FormData
    const response = await apiClient.post<ResumeUploadResponse>('/api/resumes/upload', formData, {
      params: clientId ? { client_id: clientId } : undefined,
    })
    return response.data
  },
}
