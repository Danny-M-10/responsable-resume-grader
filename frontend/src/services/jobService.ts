import { apiClient } from '../api/client'

export interface JobParsed {
  job_title: string
  location: string
  required_skills: string[]
  preferred_skills: string[]
  experience_level: string
  certifications: Array<{ name: string; category: string }>
  industry_context?: string
  soft_skills?: string[]
  technical_stack?: string[]
  full_description?: string
}

export interface JobResponse {
  id: string
  user_id: string
  title: string
  location: string
  parsed_data: JobParsed | null
  created_at: string
  updated_at: string
}

export const jobService = {
  async uploadJob(file: File, clientId?: string): Promise<JobResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<JobResponse>('/api/jobs/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: clientId ? { client_id: clientId } : undefined,
    })
    return response.data
  },

  async createJobManual(data: {
    title: string
    location: string
    description: string
    certifications?: Array<{ name: string; category: string }>
  }): Promise<JobResponse> {
    const response = await apiClient.post<JobResponse>('/api/jobs/create', {
      title: data.title,
      location: data.location,
      description: data.description,
    })
    return response.data
  },

  async getJob(jobId: string): Promise<JobResponse> {
    const response = await apiClient.get<JobResponse>(`/api/jobs/${jobId}`)
    return response.data
  },

  async listJobs(): Promise<JobResponse[]> {
    const response = await apiClient.get<JobResponse[]>('/api/jobs')
    return response.data
  },
}
