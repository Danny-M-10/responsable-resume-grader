import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { analysisService } from '../services/analysisService'
import { reportService } from '../services/reportService'
import CandidateCard, { Candidate } from '../components/CandidateCard'
import { CandidateCardSkeleton } from '../components/LoadingSkeleton'
import AnalysisChat from '../components/AnalysisChat'
import { Download, Loader2, AlertCircle, ArrowLeft, FileText } from 'lucide-react'
import './Results.css'

const Results: React.FC = () => {
  const { analysisId } = useParams<{ analysisId: string }>()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [analysis, setAnalysis] = useState<any>(null)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [downloadingReport, setDownloadingReport] = useState(false)

  useEffect(() => {
    let cancelled = false
    if (analysisId) {
      loadResults(() => cancelled)
    }
    return () => {
      cancelled = true
    }
  }, [analysisId])

  const loadResults = async (isCancelled: () => boolean) => {
    if (!analysisId) return

    setLoading(true)
    setError('')

    try {
      // Poll for completed analysis
      let attempts = 0
      const maxAttempts = 60 // 60 seconds
      let currentAnalysis = await analysisService.getAnalysis(analysisId)

      while (currentAnalysis.status === 'processing' && attempts < maxAttempts) {
        if (isCancelled()) return
        await new Promise((resolve) => setTimeout(resolve, 1000))
        if (isCancelled()) return
        currentAnalysis = await analysisService.getAnalysis(analysisId)
        attempts++
      }

      if (currentAnalysis.status === 'failed') {
        throw new Error('Analysis failed')
      }

      if (currentAnalysis.status !== 'completed') {
        throw new Error('Analysis is still processing')
      }

      if (isCancelled()) return
      setAnalysis(currentAnalysis)

      // Parse results
      if (currentAnalysis.results && currentAnalysis.results.candidates) {
        const parsedCandidates: Candidate[] = currentAnalysis.results.candidates
          .map((c: any, index: number) => ({
            id: c.id || `candidate-${index}`,
            name: c.name || 'Unknown',
            email: c.email,
            phone: c.phone,
            score: c.fit_score || c.score || 0,
            certifications: c.certifications || [],
            rationale: c.rationale || '',
            rank: index + 1, // Will be updated after sorting
          }))
          .sort((a, b) => b.score - a.score) // Sort by score descending (highest first)
          .map((candidate, index) => ({
            ...candidate,
            rank: index + 1, // Update rank based on sorted position
          }))
        if (isCancelled()) return
        setCandidates(parsedCandidates)
      }
    } catch (err: any) {
      if (!isCancelled()) {
        setError(err.response?.data?.detail || err.message || 'Failed to load results')
      }
    } finally {
      if (!isCancelled()) {
        setLoading(false)
      }
    }
  }

  const handleDownloadReport = async () => {
    if (!analysisId) return

    setDownloadingReport(true)
    try {
      // Download PDF directly from analysis results
      await reportService.downloadAnalysisPdf(analysisId)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to download report')
    } finally {
      setDownloadingReport(false)
    }
  }

  const avgScore =
    candidates.length > 0
      ? candidates.reduce((sum, c) => sum + c.score, 0) / candidates.length
      : 0

  if (loading) {
    return (
      <div className="results-page">
        <div className="results-header">
          <button onClick={() => navigate('/')} className="back-btn">
            <ArrowLeft size={20} />
            Back to Dashboard
          </button>
          <h1>Analysis Results</h1>
        </div>
        <div className="skeleton-loading-container">
          {[1, 2, 3, 4].map((i) => (
            <CandidateCardSkeleton key={i} />
          ))}
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
        <button onClick={() => navigate('/')} className="back-btn" aria-label="Back to Dashboard">
          <ArrowLeft size={16} aria-hidden="true" />
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
          <div className="metric-value">{avgScore.toFixed(2)}</div>
          <div className="metric-label">Average Score</div>
        </div>
      </div>

      {/* Candidates List */}
      <div className="candidates-section">
        <h2>All Candidates</h2>
          {candidates.length === 0 ? (
            <div className="no-candidates">
              <FileText size={64} className="empty-state-icon" />
              <h2>No candidates found</h2>
              <p>This analysis did not return any candidate results.</p>
              <button onClick={() => navigate('/')} className="back-btn">
                Back to Dashboard
              </button>
            </div>
        ) : (
          <div className="candidates-list">
            {candidates.map((candidate) => (
              <CandidateCard key={candidate.id} candidate={candidate} />
            ))}
          </div>
        )}
      </div>

      {/* AI Chat - Only show when analysis is completed */}
      {analysisId && candidates.length > 0 && (
        <AnalysisChat
          analysisId={analysisId}
          jobDetails={
            analysis?.results?.job_details
              ? {
                  title: analysis.results.job_details.title,
                  location: analysis.results.job_details.location,
                }
              : undefined
          }
        />
      )}
    </div>
  )
}

export default Results
