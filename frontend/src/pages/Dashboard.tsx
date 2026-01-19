import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import JobInput, { JobInputData } from '../components/JobInput'
import ResumeUpload, { ProcessedResume } from '../components/ResumeUpload'
import ScoringConfig, { ScoringConfigData } from '../components/ScoringConfig'
import AnalysisProgress from '../components/AnalysisProgress'
import { jobService } from '../services/jobService'
import { analysisService } from '../services/analysisService'
import { resumeService } from '../services/resumeService'
import { vaultService } from '../services/vaultService'
import { useToast } from '../contexts/ToastContext'
import { AlertCircle, Loader2 } from 'lucide-react'
import { debugLog } from '../utils/debugLog'
import './Dashboard.css'

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { showToast } = useToast()

  // Job input state
  const [jobData, setJobData] = useState<JobInputData>({
    jobTitle: '',
    location: '',
    certifications: [],
    jobDescription: '',
  })
  const [selectedVaultJobId, setSelectedVaultJobId] = useState<string>('')

  // Resume upload state
  const [processedResumes, setProcessedResumes] = useState<ProcessedResume[]>([])
  const [selectedVaultResumeIds, setSelectedVaultResumeIds] = useState<string[]>([])

  // Scoring config state
  const [scoringConfig, setScoringConfig] = useState<ScoringConfigData>({
    industryTemplate: 'general',
    dealbreakers: [],
    biasReductionEnabled: false,
  })

  // Analysis state
  const [processing, setProcessing] = useState(false)
  const [analysisClientId, setAnalysisClientId] = useState<string>('')
  const [currentAnalysisId, setCurrentAnalysisId] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [validationErrors, setValidationErrors] = useState<string[]>([])

  // Candidate IDs from uploaded/selected resumes
  const [, setCandidateIds] = useState<string[]>([])

  const handleVaultJobSelect = useCallback(async (assetId: string) => {
    setSelectedVaultJobId(assetId)
  }, [])

  const validateForm = (): string[] => {
    const errors: string[] = []

    if (!jobData.jobTitle.trim()) {
      errors.push('Job title is required')
    }

    if (!jobData.location.trim()) {
      errors.push('Location is required')
    }

    if (!jobData.jobDescription.trim()) {
      errors.push('Job description is required')
    }

    // Check for processed resumes (completed status)
    const completedResumes = processedResumes.filter((r) => r.status === 'complete')
    const totalResumes = completedResumes.length + selectedVaultResumeIds.length
    if (totalResumes === 0) {
      errors.push('At least one processed resume is required')
    }
    
    // Check if any resumes are still processing
    const processingResumes = processedResumes.filter((r) => r.status === 'uploading' || r.status === 'parsing')
    if (processingResumes.length > 0) {
      errors.push('Please wait for all resumes to finish processing before starting analysis')
    }

    return errors
  }

  const handleProcessCandidates = async () => {
    setError('')
    setValidationErrors([])

    // Validate form
    const errors = validateForm()
    console.log('[Dashboard] Validation errors:', errors)
    console.log('[Dashboard] Job data state:', { jobTitle: jobData.jobTitle, location: jobData.location, jobDescription: jobData.jobDescription?.substring(0, 50) + '...', hasJobId: !!jobData.jobId })
    const completedResumes = processedResumes.filter((r) => r.status === 'complete')
    console.log('[Dashboard] Resume state:', { processedResumesCount: processedResumes.length, completedResumesCount: completedResumes.length, selectedVaultResumeIdsCount: selectedVaultResumeIds.length })
    if (errors.length > 0) {
      console.log('[Dashboard] Setting validation errors:', errors)
      setValidationErrors(errors)
      showToast({
        message: `Please fix ${errors.length} error${errors.length > 1 ? 's' : ''} before continuing`,
        type: 'error',
      })
      return
    }

    // Generate clientId and set processing state BEFORE starting any async operations
    // This ensures the progress component is shown immediately
    const clientId = `client_${Date.now()}_${Math.random().toString(36).substring(7)}`
    setAnalysisClientId(clientId)
    setProcessing(true)

    try {
      // Step 1: Create or get job
      let jobId = jobData.jobId
      if (!jobId) {
        // Create job from manual entry
        const jobResponse = await jobService.createJobManual({
          title: jobData.jobTitle,
          location: jobData.location,
          description: jobData.jobDescription,
          certifications: jobData.certifications,
        })
        jobId = jobResponse.id
        setJobData({ ...jobData, jobId })
      }

      // Step 2: Collect candidate IDs from processed resumes
      const newCandidateIds: string[] = []

      // Get candidate IDs from already-processed resumes
      const completedResumes = processedResumes.filter((r) => r.status === 'complete' && r.candidateId)
      completedResumes.forEach((resume) => {
        if (resume.candidateId) {
          newCandidateIds.push(resume.candidateId)
        }
      })
      console.log('[Dashboard] Using processed resumes:', {
        completedResumesCount: completedResumes.length,
        candidateIdsCount: newCandidateIds.length,
      })

      const vaultUploadErrors: string[] = []

      // Load resumes from vault (only if selected)
      if (selectedVaultResumeIds.length > 0) {
        console.log('[Dashboard] Processing vault resumes:', {
          selectedCount: selectedVaultResumeIds.length,
        })
        for (const assetId of selectedVaultResumeIds) {
          try {
            const asset = await vaultService.getAsset(assetId)
            const blob = await vaultService.downloadAsset(assetId)
            const file = new File([blob], asset.original_name, { type: blob.type })
            const uploadResponse = await resumeService.uploadResumes([file], clientId)
            const validIds = (uploadResponse.candidate_ids || []).filter((id) => Boolean(id)) as string[]
            if (validIds.length === 0) {
              throw new Error('No candidate IDs returned from vault resume upload')
            }
            newCandidateIds.push(...validIds)
          } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to process vault resume'
            vaultUploadErrors.push(errorMessage)
            console.error(`Failed to load resume from vault ${assetId}:`, err)
            showToast({
              message: errorMessage,
              type: 'error',
            })
          }
        }
      }

      console.log('[Dashboard] Total candidate IDs for analysis:', {
        totalCount: newCandidateIds.length,
        fromProcessed: completedResumes.length,
        fromVault: selectedVaultResumeIds.length > 0 ? selectedVaultResumeIds.length : 0,
      })

      if (newCandidateIds.length === 0) {
        if (vaultUploadErrors.length > 0) {
          throw new Error('Failed to process selected vault resumes. Please check the errors and try again.')
        }
        throw new Error('No candidates were successfully processed')
      }

      setCandidateIds(newCandidateIds)

      // Step 3: Start analysis (pass clientId so backend uses the same one)
      const analysisResponse = await analysisService.startAnalysis({
        job_id: jobId,
        candidate_ids: newCandidateIds,
        industry_template: scoringConfig.industryTemplate,
        custom_scoring_weights: scoringConfig.customWeights as Record<string, number> | undefined,
        dealbreakers: scoringConfig.dealbreakers.length > 0 ? scoringConfig.dealbreakers : undefined,
        bias_reduction_enabled: scoringConfig.biasReductionEnabled,
        client_id: clientId,  // Pass clientId to backend
      })

      // Use client_id from response (backend may have generated one if we didn't send it)
      const finalClientId = analysisResponse.client_id || clientId
      setAnalysisClientId(finalClientId)
      setCurrentAnalysisId(analysisResponse.id)
      showToast({
        message: 'Analysis started successfully!',
        type: 'success',
      })
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to process candidates'
      setError(errorMessage)
      showToast({
        message: errorMessage,
        type: 'error',
      })
      setProcessing(false)
      setAnalysisClientId('')
    }
  }

  const handleAnalysisComplete = async () => {
    setProcessing(false)
    // Navigate to results page
    if (currentAnalysisId) {
      console.log('[Dashboard] Analysis complete, navigating to results:', currentAnalysisId)
      navigate(`/results/${currentAnalysisId}`)
    } else {
      console.error('[Dashboard] Analysis complete but no analysis ID available')
      setError('Analysis completed but could not navigate to results page')
    }
  }

  const handleAnalysisError = (errorMsg: string) => {
    setError(errorMsg)
  }

  // Check if any resumes are currently processing
  const isProcessingResumes = processedResumes.some(
    (r) => r.status === 'uploading' || r.status === 'parsing'
  )

  return (
    <div className="dashboard">

      {validationErrors.length > 0 && (
        <div className="validation-errors">
          <AlertCircle size={20} />
          <div>
            <strong>Please fix the following errors:</strong>
            <ul>
              {validationErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Processing Indicator */}
      {isProcessingResumes && (
        <div className="processing-banner" role="status" aria-live="polite">
          <Loader2 className="spinner" size={20} />
          <div>
            <strong>Resumes are being processed</strong>
            <p>Please wait while resumes are processed. The form is locked to ensure your analysis uses the current settings.</p>
          </div>
        </div>
      )}

      {/* Job Input Section */}
      <JobInput
        value={jobData}
        onChange={(data) => {
          // #region agent log
          debugLog({location:'Dashboard.tsx:195',message:'setJobData called',data:{hasJobTitle:!!data.jobTitle,hasLocation:!!data.location,hasParsedData:!!data.parsedData,hasJobId:!!data.jobId,certificationsLength:data.certifications?.length},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'C'});
          // #endregion
          try {
            setJobData(data)
            // #region agent log
            debugLog({location:'Dashboard.tsx:199',message:'setJobData completed',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'C'});
            // #endregion
          } catch (err: any) {
            // #region agent log
            debugLog({location:'Dashboard.tsx:201',message:'setJobData error',data:{errorMessage:err?.message,errorStack:err?.stack?.substring(0,200)},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'C'});
            // #endregion
            throw err
          }
        }}
        onVaultAssetSelect={handleVaultJobSelect}
        selectedVaultJobId={selectedVaultJobId}
        disabled={isProcessingResumes || processing}
      />

      {/* Resume Upload Section */}
      <ResumeUpload
        processedResumes={processedResumes}
        onProcessedResumesChange={setProcessedResumes}
        selectedVaultResumeIds={selectedVaultResumeIds}
        onVaultResumesChange={setSelectedVaultResumeIds}
        disabled={isProcessingResumes}
      />

      {/* Scoring Configuration */}
      <ScoringConfig 
        value={scoringConfig} 
        onChange={setScoringConfig}
        disabled={isProcessingResumes || processing}
      />

      {/* Process Candidates Button */}
      {!processing && (
        <div className="process-section">
          <button
            className="process-btn"
            onClick={handleProcessCandidates}
            disabled={processing || isProcessingResumes}
            aria-label="Start candidate analysis"
            aria-busy={processing || isProcessingResumes}
          >
            Process Candidates
          </button>
          <p className="process-help">
            Click to start analyzing candidates. The system will parse resumes, score them against
            the job requirements, and generate a ranked list.
          </p>
        </div>
      )}

      {/* Analysis Progress */}
      {processing && analysisClientId && (
        <AnalysisProgress
          clientId={analysisClientId}
          onComplete={handleAnalysisComplete}
          onError={handleAnalysisError}
        />
      )}
    </div>
  )
}

export default Dashboard
