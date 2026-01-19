import React, { useEffect, useState, useRef } from 'react'
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
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdateTime, setLastUpdateTime] = useState<number | null>(null)
  const [startTime] = useState<number>(Date.now())
  const [elapsedTime, setElapsedTime] = useState<number>(0)
  // Use ref to track completed state for onClose callback without causing re-renders
  const completedRef = useRef(false)
  
  // Update elapsed time every second
  useEffect(() => {
    if (completed) return
    
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    
    return () => clearInterval(interval)
  }, [completed, startTime])

  useEffect(() => {
    if (!clientId) return

    const websocket = new ProgressWebSocket(clientId)
    setWs(websocket)

    websocket.onProgress((data: ProgressData) => {
      setProgressData(data)
      setError('')
      setIsConnected(true)
      setLastUpdateTime(Date.now())

      // Check if complete
      // Only 'complete' step indicates analysis completion - intermediate steps can reach 100% progress
      if (data.step === 'complete') {
        setCompleted(true)
        completedRef.current = true  // Update ref to track latest state
        if (onComplete) {
          setTimeout(() => onComplete(), 1000)
        }
      }
    })

    websocket.onError((error: Event) => {
      setIsConnected(false)
      const errorMsg = `Connection error: ${error.type}. Progress updates may not be available. The operation may still be running in the background.`
      setError(errorMsg)
      if (onError) {
        onError(errorMsg)
      }
    })

    websocket.onClose(() => {
      setIsConnected(false)
      // Only show error if not completed (use ref to get latest value)
      if (!completedRef.current) {
        const stepInfo = progressData?.step ? ` (Last step: ${progressData.step})` : ''
        const errorMsg = `Connection closed${stepInfo}. The operation may still be running in the background. Please check the results page or history after a few moments.`
        setError(errorMsg)
      }
    })

    // Note: connect() may not return a promise, so we track connection via onProgress
    // Connection state will be set when first progress update is received
    websocket.connect()

    return () => {
      websocket.disconnect()
    }
    // Note: completed is intentionally NOT in the dependency array to avoid circular re-renders
    // Use completedRef to access the latest completed state in callbacks
    // The effect should only re-run when clientId or callbacks change
  }, [clientId, onComplete, onError])

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
    // Resume parsing steps
    reading_resume: 'Reading resume file...',
    parsing_resume: 'Parsing candidate resumes...',
    all_complete: 'All resumes parsed successfully',
    // Job processing steps
    reading_file: 'Reading job description file...',
    // AI extraction (used for both job and resume parsing)
    ai_extraction: 'Extracting information with AI...',
    // Analysis steps
    initializing: 'Initializing analysis...',
    loading_resumes: 'Loading candidate resumes...',
    initializing_ai: 'Initializing AI components...',
    parsing: 'Parsing resumes...',
    scoring: 'Scoring candidates...',
    ranking: 'Ranking candidates...',
    generating: 'Generating PDF report...',
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
          <div className="progress-header-row">
            <h3>Processing in Progress</h3>
            <div className="connection-status">
              {isConnected ? (
                <span className="status-connected" title="Connected and receiving updates">
                  ● Connected
                </span>
              ) : (
                <span className="status-disconnected" title="Not connected">
                  ○ Disconnected
                </span>
              )}
            </div>
          </div>
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

          {/* Elapsed time display */}
          {!completed && (
            <div className="progress-time">
              <span>Elapsed: {elapsedTime}s</span>
              {lastUpdateTime && (
                <span className="last-update">
                  {' '}• Last update: {Math.floor((Date.now() - lastUpdateTime) / 1000)}s ago
                </span>
              )}
            </div>
          )}

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
