import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { analysisService, AnalysisResponse } from '../services/analysisService'
import { Loader2, AlertCircle, FileText, Calendar } from 'lucide-react'
import './History.css'

const History: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([])

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await analysisService.listAnalyses()
      setAnalyses(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'status-completed'
      case 'processing':
        return 'status-processing'
      case 'failed':
        return 'status-failed'
      default:
        return 'status-pending'
    }
  }

  const handleViewResults = (analysisId: string) => {
    navigate(`/results/${analysisId}`)
  }

  if (loading) {
    return (
      <div className="history-page">
        <div className="loading-container">
          <Loader2 className="spinner" />
          <span>Loading analysis history...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="history-page">
        <div className="error-container">
          <AlertCircle size={24} />
          <h2>Error Loading History</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>Analysis History</h1>
        <p>View and access your past candidate analyses</p>
      </div>

      {analyses.length === 0 ? (
        <div className="no-analyses">
          <FileText size={48} />
          <h2>No analyses yet</h2>
          <p>Start analyzing candidates from the dashboard to see your history here.</p>
          <button onClick={() => navigate('/')} className="go-to-dashboard-btn">
            Go to Dashboard
          </button>
        </div>
      ) : (
        <div className="analyses-list">
          {analyses.map((analysis) => (
            <div key={analysis.id} className="analysis-card">
              <div className="analysis-card-header">
                <div className="analysis-info">
                  <h3>Analysis #{analysis.id.slice(0, 8)}</h3>
                  <div className="analysis-meta">
                    <span className="meta-item">
                      <Calendar size={14} />
                      {formatDate(analysis.created_at)}
                    </span>
                    <span className={`status-badge ${getStatusColor(analysis.status)}`}>
                      {analysis.status}
                    </span>
                  </div>
                </div>
                {analysis.status === 'completed' && (
                  <button
                    className="view-results-btn"
                    onClick={() => handleViewResults(analysis.id)}
                  >
                    View Results
                  </button>
                )}
              </div>
              {analysis.results && (
                <div className="analysis-summary">
                  {analysis.results.candidate_count && (
                    <span>
                      {analysis.results.candidate_count} candidate
                      {analysis.results.candidate_count !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default History
