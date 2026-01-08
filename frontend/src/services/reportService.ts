import { apiClient } from '../api/client'

export interface ReportResponse {
  id: string
  analysis_id: string
  pdf_path: string
  created_at: string
}

export const reportService = {
  async generateReport(analysisId: string): Promise<ReportResponse> {
    const response = await apiClient.post<ReportResponse>(
      `/api/reports/generate/${analysisId}`
    )
    return response.data
  },

  async downloadReport(reportId: string): Promise<void> {
    const response = await apiClient.get(`/api/reports/${reportId}/download`, {
      responseType: 'blob',
    })

    // Create blob and download
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `candidate_report_${reportId}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },
}
