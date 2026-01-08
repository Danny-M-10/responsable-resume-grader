import React, { useEffect, useState } from 'react'
import { ProgressWebSocket } from '../api/websocket'
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import './AnalysisProgress.css'

interface ProgressData {
  type: 'progress'
  step: string
  progress: number
  current?: number
  total?: number
  message?: string
}

interface AnalysisProgressProps {
  clientId: string
  onComplete?: () => void
  onError?: (error: string) => void
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  clientId,
  onComplete,
  onError,
}) => {
  const [, setWs] = useState<ProgressWebSocket | null>(null)
  const [progressData, setProgressData] = useState<ProgressData | null>(null)
  const [error, setError] = useState<string>('')
  const [completed, setCompleted] = useState(false)

  useEffect(() => {
    if (!clientId) return

    const websocket = new ProgressWebSocket(clientId)
    setWs(websocket)

    websocket.onProgress((data: ProgressData) => {
      setProgressData(data)
      setError('')

      // Check if complete
      if (data.progress >= 1.0 || data.step === 'complete') {
        setCompleted(true)
        if (onComplete) {
          setTimeout(() => onComplete(), 1000)
        }
      }
    })

    websocket.onError(() => {
      const errorMsg = 'Connection error. Progress updates may not be available.'
      setError(errorMsg)
      if (onError) {
        onError(errorMsg)
      }
    })

    websocket.onClose(() => {
      // Only show error if not completed
      if (!completed) {
        const errorMsg = 'Connection closed. Analysis may still be running.'
        setError(errorMsg)
      }
    })

    websocket.connect()

    return () => {
      websocket.disconnect()
    }
  }, [clientId, onComplete, onError, completed])

  if (!progressData && !error && !completed) {
    return (
      <div className="analysis-progress">
        <div className="progress-loading">
          <Loader2 className="spinner" />
          <span>Connecting to analysis server...</span>
        </div>
      </div>
    )
  }

  if (completed) {
    return (
      <div className="analysis-progress">
        <div className="progress-complete">
          <CheckCircle2 className="check-icon" />
          <span>Analysis Complete!</span>
        </div>
      </div>
    )
  }

  const stepMessages: Record<string, string> = {
    reading_file: 'Reading job description file...',
    ai_extraction: 'Extracting job details with AI...',
    parsing_resumes: 'Parsing candidate resumes...',
    scoring: 'Scoring candidates...',
    ranking: 'Ranking candidates...',
    generating_report: 'Generating PDF report...',
    complete: 'Complete!',
  }

  const currentStep = progressData?.step || 'unknown'
  const message = progressData?.message || stepMessages[currentStep] || 'Processing...'
  const progress = progressData?.progress || 0
  const current = progressData?.current
  const total = progressData?.total

  return (
    <div className="analysis-progress">
      <div className="progress-container">
        <div className="progress-header">
          <h3>Analysis in Progress</h3>
          {error && (
            <div className="progress-error">
              <AlertCircle size={16} />
              {error}
            </div>
          )}
        </div>

        <div className="progress-content">
          <div className="progress-bar-container">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
            <div className="progress-text">
              {Math.round(progress * 100)}%
              {current !== undefined && total !== undefined && (
                <span className="progress-count">
                  {' '}({current}/{total})
                </span>
              )}
            </div>
          </div>

          <div className="progress-message">
            <Loader2 className="spinner" size={16} />
            <span>{message}</span>
          </div>

          {/* Step indicators */}
          <div className="progress-steps">
            {Object.entries(stepMessages)
              .filter(([key]) => key !== 'complete')
              .map(([key, label]) => {
                const stepProgress = progressData?.step || ''
                const isActive = stepProgress === key
                const isComplete =
                  stepProgress === 'complete' ||
                  (stepProgress !== key &&
                    Object.keys(stepMessages).indexOf(stepProgress) >
                      Object.keys(stepMessages).indexOf(key))

                return (
                  <div
                    key={key}
                    className={`progress-step ${isActive ? 'active' : ''} ${isComplete ? 'complete' : ''}`}
                  >
                    <div className="step-indicator">
                      {isComplete ? (
                        <CheckCircle2 size={16} />
                      ) : isActive ? (
                        <Loader2 className="spinner" size={16} />
                      ) : (
                        <div className="step-dot" />
                      )}
                    </div>
                    <span className="step-label">{label}</span>
                  </div>
                )
              })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnalysisProgress
