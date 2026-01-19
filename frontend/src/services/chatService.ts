import { apiClient } from '../api/client'

export interface ChatMessageRequest {
  message: string
}

export interface ChatMessageResponse {
  response: string
}

export const chatService = {
  async sendMessage(analysisId: string, message: string): Promise<string> {
    const response = await apiClient.post<ChatMessageResponse>(
      `/api/chat/${analysisId}/message`,
      { message }
    )
    return response.data.response
  },
}
