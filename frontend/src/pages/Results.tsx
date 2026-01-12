import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { analysisService } from '../services/analysisService'
import { reportService } from '../services/reportService'
import CandidateCard, { Candidate } from '../components/CandidateCard'
import { Download, Loader2, AlertCircle, ArrowLeft } from 'lucide-react'
import './Results.css'

const Results: React.FC = () => {
  const { analysisId } = useParams<{ analysisId: string }>()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [, setAnalysis] = useState<any>(null)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [downloadingReport, setDownloadingReport] = useState(false)
  const [reportId, setReportId] = useState<string>('')

  useEffect(() => {
    if (analysisId) {
      loadResults()
    }
  }, [analysisId])

  const loadResults = async () => {
    if (!analysisId) return

    setLoading(true)
    setError('')

    try {
      // Poll for completed analysis
      let attempts = 0
      const maxAttempts = 60 // 60 seconds
      let currentAnalysis = await analysisService.getAnalysis(analysisId)

      while (currentAnalysis.status === 'processing' && attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        currentAnalysis = await analysisService.getAnalysis(analysisId)
        attempts++
      }

      if (currentAnalysis.status === 'failed') {
        throw new Error('Analysis failed')
      }

      if (currentAnalysis.status !== 'completed') {
        throw new Error('Analysis is still processing')
      }

      setAnalysis(currentAnalysis)

      // Parse results
      if (currentAnalysis.results && currentAnalysis.results.candidates) {
        const parsedCandidates: Candidate[] = currentAnalysis.results.candidates.map(
          (c: any, index: number) => ({
            id: c.id || `candidate-${index}`,
            name: c.name || 'Unknown',
            email: c.email,
            phone: c.phone,
            score: c.fit_score || c.score || 0,
            certifications: c.certifications || [],
            rationale: c.rationale || '',
            rank: index + 1,
          })
        )
        setCandidates(parsedCandidates)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load results')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadReport = async () => {
    if (!analysisId) return

    setDownloadingReport(true)
    try {
      // Generate report if not already generated, use the generated report ID
      let reportToDownload = reportId
      if (!reportToDownload) {
        const report = await reportService.generateReport(analysisId)
        reportToDownload = report.id
        setReportId(report.id)
      }

      // Download report using the determined report ID
      await reportService.downloadReport(reportToDownload)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to download report')
    } finally {
      setDownloadingReport(false)
    }
  }

  const viableCandidates = candidates.filter((c) => c.score >= 5.0)
  const topCandidates = viableCandidates.slice(0, 10)
  const avgScore =
    viableCandidates.length > 0
      ? viableCandidates.reduce((sum, c) => sum + c.score, 0) / viableCandidates.length
      : 0

  if (loading) {
    return (
      <div className="results-page">
        <div className="loading-container">
          <Loader2 className="spinner" />
          <span>Loading results...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="results-page">
        <div className="error-container">
          <AlertCircle size={24} />
          <h2>Error Loading Results</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/')} className="back-btn">
            <ArrowLeft size={16} />
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="results-page">
      <div className="results-header">
        <button onClick={() => navigate('/')} className="back-btn">
          <ArrowLeft size={16} />
          Back to Dashboard
        </button>
        <h1>Analysis Results</h1>
        <button
          className="download-btn"
          onClick={handleDownloadReport}
          disabled={downloadingReport}
        >
          {downloadingReport ? (
            <>
              <Loader2 className="spinner" size={16} />
              Generating...
            </>
          ) : (
            <>
              <Download size={16} />
              Download PDF Report
            </>
          )}
        </button>
      </div>

      {/* Summary Metrics */}
      <div className="metrics-section">
        <div className="metric-card">
          <div className="metric-value">{candidates.length}</div>
          <div className="metric-label">Total Candidates</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{topCandidates.length}</div>
          <div className="metric-label">Top Candidates (≥5.0)</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{avgScore.toFixed(2)}</div>
          <div className="metric-label">Average Score (Viable)</div>
        </div>
      </div>

      {/* Candidates List */}
      <div className="candidates-section">
        <h2>Top Candidates (Viable Only)</h2>
        {topCandidates.length === 0 ? (
          <div className="no-candidates">
            <p>No viable candidates (score ≥ 5.0) to display.</p>
          </div>
        ) : (
          <div className="candidates-list">
            {topCandidates.map((candidate) => (
              <CandidateCard key={candidate.id} candidate={candidate} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Results
