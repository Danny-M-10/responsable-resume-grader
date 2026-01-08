import { apiClient } from '../api/client'

export interface ResumeUploadResponse {
  message: string
  candidate_ids: string[]
  parsed_data: any[]
}

export const resumeService = {
  async uploadResumes(files: File[], clientId?: string): Promise<ResumeUploadResponse> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    const response = await apiClient.post<ResumeUploadResponse>('/api/resumes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: clientId ? { client_id: clientId } : undefined,
    })
    return response.data
  },
}
