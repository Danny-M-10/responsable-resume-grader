import { apiClient } from '../api/client'

export interface Template {
  name: string
  description: string
  weights: Record<string, number>
}

export const templateService = {
  async listTemplates(): Promise<Record<string, Template>> {
    const response = await apiClient.get<Record<string, Template>>('/api/templates')
    return response.data
  },

  async getTemplate(templateName: string): Promise<Template> {
    const response = await apiClient.get<Template>(`/api/templates/${templateName}`)
    return response.data
  },
}
