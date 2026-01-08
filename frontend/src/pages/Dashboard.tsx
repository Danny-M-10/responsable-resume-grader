import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import JobInput, { JobInputData } from '../components/JobInput'
import Vault from '../components/Vault'
import ResumeUpload, { UploadedFile } from '../components/ResumeUpload'
import ScoringConfig, { ScoringConfigData } from '../components/ScoringConfig'
import AnalysisProgress from '../components/AnalysisProgress'
import { jobService } from '../services/jobService'
import { analysisService } from '../services/analysisService'
import { resumeService } from '../services/resumeService'
import { vaultService } from '../services/vaultService'
import { AlertCircle } from 'lucide-react'
import './Dashboard.css'

const Dashboard: React.FC = () => {
  const navigate = useNavigate()

  // Job input state
  const [jobData, setJobData] = useState<JobInputData>({
    jobTitle: '',
    location: '',
    certifications: [],
    jobDescription: '',
  })
  const [selectedVaultJobId, setSelectedVaultJobId] = useState<string>('')

  // Resume upload state
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
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

    const totalResumes = uploadedFiles.length + selectedVaultResumeIds.length
    if (totalResumes === 0) {
      errors.push('At least one resume file is required')
    }

    return errors
  }

  const handleProcessCandidates = async () => {
    setError('')
    setValidationErrors([])

    // Validate form
    const errors = validateForm()
    if (errors.length > 0) {
      setValidationErrors(errors)
      return
    }

    setProcessing(true)
    const clientId = `client_${Date.now()}_${Math.random().toString(36).substring(7)}`
    setAnalysisClientId(clientId)

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

      // Step 2: Upload and parse resumes
      const newCandidateIds: string[] = []

      // Upload new files
      if (uploadedFiles.length > 0) {
        const files = uploadedFiles.map((uf) => uf.file)
        const uploadResponse = await resumeService.uploadResumes(files, clientId)
        newCandidateIds.push(...uploadResponse.candidate_ids)
      }

      // Load resumes from vault
      if (selectedVaultResumeIds.length > 0) {
        for (const assetId of selectedVaultResumeIds) {
          try {
            const asset = await vaultService.getAsset(assetId)
            const blob = await vaultService.downloadAsset(assetId)
            const file = new File([blob], asset.original_name, { type: blob.type })
            const uploadResponse = await resumeService.uploadResumes([file], clientId)
            newCandidateIds.push(...uploadResponse.candidate_ids)
          } catch (err) {
            console.error(`Failed to load resume from vault ${assetId}:`, err)
          }
        }
      }

      if (newCandidateIds.length === 0) {
        throw new Error('No candidates were successfully processed')
      }

      setCandidateIds(newCandidateIds)

      // Step 3: Start analysis
      const analysisResponse = await analysisService.startAnalysis({
        job_id: jobId,
        candidate_ids: newCandidateIds,
        industry_template: scoringConfig.industryTemplate,
        custom_scoring_weights: scoringConfig.customWeights as Record<string, number> | undefined,
        dealbreakers: scoringConfig.dealbreakers.length > 0 ? scoringConfig.dealbreakers : undefined,
        bias_reduction_enabled: scoringConfig.biasReductionEnabled,
      })

      setCurrentAnalysisId(analysisResponse.id)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to process candidates')
      setProcessing(false)
      setAnalysisClientId('')
    }
  }

  const handleAnalysisComplete = async () => {
    setProcessing(false)
    // Navigate to results page
    if (currentAnalysisId) {
      navigate(`/results/${currentAnalysisId}`)
    }
  }

  const handleAnalysisError = (errorMsg: string) => {
    setError(errorMsg)
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>CROSSROADS Professional Services</h1>
        <p className="subtitle">Universal Recruiting Tool</p>
      </div>

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

      {/* Vault Section */}
      <Vault
        onJobSelect={handleVaultJobSelect}
        onResumeSelect={setSelectedVaultResumeIds}
        selectedJobId={selectedVaultJobId}
        selectedResumeIds={selectedVaultResumeIds}
      />

      {/* Job Input Section */}
      <JobInput
        value={jobData}
        onChange={setJobData}
        onVaultAssetSelect={handleVaultJobSelect}
        selectedVaultJobId={selectedVaultJobId}
      />

      {/* Resume Upload Section */}
      <ResumeUpload
        uploadedFiles={uploadedFiles}
        onFilesChange={setUploadedFiles}
        selectedVaultResumeIds={selectedVaultResumeIds}
        onVaultResumesChange={setSelectedVaultResumeIds}
      />

      {/* Scoring Configuration */}
      <ScoringConfig value={scoringConfig} onChange={setScoringConfig} />

      {/* Process Candidates Button */}
      {!processing && (
        <div className="process-section">
          <button
            className="process-btn"
            onClick={handleProcessCandidates}
            disabled={processing}
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
