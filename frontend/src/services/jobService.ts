import { apiClient } from '../api/client'
import { debugLog } from '../utils/debugLog'

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
    // #region agent log
    debugLog({location:'jobService.ts:27',message:'uploadJob entry',data:{fileName:file.name,fileSize:file.size,hasClientId:!!clientId},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
    // #endregion
    const formData = new FormData()
    formData.append('file', file)

    try {
      // #region agent log
      debugLog({location:'jobService.ts:32',message:'Making API request',data:{url:'/api/jobs/upload',hasClientId:!!clientId},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
      // #endregion
      // Don't set Content-Type header - axios automatically sets it with boundary for FormData
      const response = await apiClient.post<JobResponse>('/api/jobs/upload', formData, {
        params: clientId ? { client_id: clientId } : undefined,
      })
      // #region agent log
      debugLog({location:'jobService.ts:36',message:'API response received',data:{status:response.status,hasData:!!response.data,dataKeys:response.data?Object.keys(response.data):null,hasParsedData:!!response.data?.parsed_data},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
      // #endregion
      return response.data
    } catch (err: any) {
      // #region agent log
      debugLog({location:'jobService.ts:40',message:'uploadJob error',data:{errorMessage:err?.message,errorName:err?.name,hasResponse:!!err?.response,responseStatus:err?.response?.status,responseData:err?.response?.data},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
      // #endregion
      throw err
    }
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
      certifications: data.certifications || [],
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
