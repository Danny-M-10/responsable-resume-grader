import React, { useState, useEffect, useRef } from 'react'
import { jobService, JobParsed } from '../services/jobService'
import { vaultService, Asset } from '../services/vaultService'
// import { useToast } from '../contexts/ToastContext' // Reserved for future toast notifications
import { Upload, Loader2 } from 'lucide-react'
import { debugLog } from '../utils/debugLog'
import './JobInput.css'

export interface Certification {
  name: string
  category: 'must-have' | 'bonus'
}

export interface JobInputData {
  jobTitle: string
  location: string
  certifications: Certification[]
  jobDescription: string
  parsedData?: JobParsed
  jobId?: string
}

interface JobInputProps {
  value: JobInputData
  onChange: (data: JobInputData) => void
  onVaultAssetSelect?: (assetId: string) => void
  selectedVaultJobId?: string
  disabled?: boolean
}

const JobInput: React.FC<JobInputProps> = ({
  value,
  onChange,
  onVaultAssetSelect,
  selectedVaultJobId,
  disabled = false,
}) => {
  // const { showToast } = useToast() // Reserved for future toast notifications
  const [inputMethod, setInputMethod] = useState<'upload' | 'manual'>('upload')
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [vaultJobs, setVaultJobs] = useState<Asset[]>([])
  const [selectedVaultJob, setSelectedVaultJob] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [isDragging, setIsDragging] = useState(false)
  const dragCounterRef = useRef(0) // Track drag enter/leave to prevent flickering

  useEffect(() => {
    loadVaultJobs()
    if (selectedVaultJobId) {
      loadVaultJob(selectedVaultJobId)
    }
  }, [selectedVaultJobId])

  const loadVaultJobs = async () => {
    try {
      const assets = await vaultService.listAssets('job_description')
      setVaultJobs(assets)
    } catch (err: any) {
      console.error('Failed to load vault jobs:', err)
    }
  }

  // Helper function to validate file type
  const isValidFileType = (file: File): boolean => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ]
    const validExtensions = ['.pdf', '.docx', '.txt']
    
    // Check MIME type
    if (validTypes.includes(file.type)) {
      return true
    }
    
    // Check file extension as fallback
    const fileName = file.name.toLowerCase()
    return validExtensions.some((ext) => fileName.endsWith(ext))
  }

  const loadVaultJob = async (assetId: string) => {
    try {
      setParsing(true)
      const asset = await vaultService.getAsset(assetId)
      const blob = await vaultService.downloadAsset(assetId)
      const file = new File([blob], asset.original_name, { type: blob.type })
      
      const jobResponse = await jobService.uploadJob(file)
      if (jobResponse.parsed_data) {
        onChange({
          jobTitle: jobResponse.parsed_data.job_title,
          location: jobResponse.parsed_data.location,
          certifications: (jobResponse.parsed_data.certifications || []).map((c: any) => ({
            name: c.name || '',
            category: (c.category || 'must-have') as 'must-have' | 'bonus',
          })),
          jobDescription: jobResponse.parsed_data.full_description || '',
          parsedData: jobResponse.parsed_data,
          jobId: jobResponse.id,
        })
        if (onVaultAssetSelect) {
          onVaultAssetSelect(assetId)
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load job from vault')
    } finally {
      setParsing(false)
    }
  }

  // Shared function to process file (used by both file input and drag-drop)
  const processFile = async (file: File) => {
    if (uploading || parsing || disabled) {
      return
    }

    // Validate file type
    if (!isValidFileType(file)) {
      setError('Invalid file type. Only PDF, DOCX, and TXT files are supported.')
      return
    }

    setError('')
    setUploading(true)
    setParsing(true)

    try {
      // #region agent log
      debugLog({location:'JobInput.tsx:processFile',message:'Calling uploadJob',data:{fileName:file.name,fileSize:file.size,fileType:file.type},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
      // #endregion
      const jobResponse = await jobService.uploadJob(file)
      // #region agent log
      debugLog({location:'JobInput.tsx:processFile',message:'uploadJob response received',data:{hasParsedData:!!jobResponse.parsed_data,hasId:!!jobResponse.id,parsedDataType:typeof jobResponse.parsed_data,parsedDataKeys:jobResponse.parsed_data?Object.keys(jobResponse.parsed_data):null},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'B'});
      // #endregion
      if (jobResponse.parsed_data) {
        // #region agent log
        debugLog({location:'JobInput.tsx:processFile',message:'Before onChange call',data:{hasFullDescription:!!jobResponse.parsed_data.full_description,certificationsType:typeof jobResponse.parsed_data.certifications,isCertificationsArray:Array.isArray(jobResponse.parsed_data.certifications)},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'C'});
        // #endregion
        try {
          onChange({
            jobTitle: jobResponse.parsed_data.job_title,
            location: jobResponse.parsed_data.location,
            certifications: (jobResponse.parsed_data.certifications || []).map((c: any) => ({
              name: c.name || '',
              category: (c.category || 'must-have') as 'must-have' | 'bonus',
            })),
            jobDescription: jobResponse.parsed_data.full_description || '',
            parsedData: jobResponse.parsed_data,
            jobId: jobResponse.id,
          })
          // #region agent log
          debugLog({location:'JobInput.tsx:processFile',message:'onChange completed successfully',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'C'});
          // #endregion
        } catch (onChangeErr: any) {
          // #region agent log
          debugLog({location:'JobInput.tsx:processFile',message:'onChange error caught',data:{errorMessage:onChangeErr?.message,errorStack:onChangeErr?.stack?.substring(0,200),errorName:onChangeErr?.name},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'C'});
          // #endregion
          throw onChangeErr
        }
      } else {
        // #region agent log
        debugLog({location:'JobInput.tsx:processFile',message:'parsed_data is null/undefined',data:{responseId:jobResponse.id,responseKeys:Object.keys(jobResponse)},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'B'});
        // #endregion
      }
    } catch (err: any) {
      // #region agent log
      debugLog({location:'JobInput.tsx:processFile',message:'Error caught in processFile',data:{errorMessage:err?.message,errorStack:err?.stack?.substring(0,300),errorName:err?.name,hasResponse:!!err?.response,responseStatus:err?.response?.status,responseDetail:err?.response?.data?.detail},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
      // #endregion
      setError(err.response?.data?.detail || 'Failed to parse job description')
    } finally {
      setUploading(false)
      setParsing(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    // #region agent log
    debugLog({location:'JobInput.tsx:handleFileUpload',message:'handleFileUpload entry',data:{hasFile:!!event.target.files?.[0],fileName:event.target.files?.[0]?.name},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
    // #endregion
    const file = event.target.files?.[0]
    if (!file) return

    await processFile(file)

    // Reset file input
    event.target.value = ''
    // #region agent log
    debugLog({location:'JobInput.tsx:handleFileUpload',message:'handleFileUpload finally block',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'A'});
    // #endregion
  }

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (uploading || parsing || disabled) {
      return
    }

    dragCounterRef.current++
    if (e.dataTransfer.types.includes('Files')) {
      setIsDragging(true)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (uploading || parsing || disabled) {
      return
    }

    // Set dropEffect to show visual feedback
    if (e.dataTransfer.types.includes('Files')) {
      e.dataTransfer.dropEffect = 'copy'
    }
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    dragCounterRef.current--
    
    // Only set isDragging to false when we actually leave the drop zone
    // This prevents flickering when moving between child elements
    if (dragCounterRef.current === 0) {
      setIsDragging(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    setIsDragging(false)
    dragCounterRef.current = 0

    if (uploading || parsing || disabled) {
      return
    }

    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) {
      return
    }

    // Process the first file (job descriptions are typically single files)
    const file = files[0]
    if (isValidFileType(file)) {
      await processFile(file)
    } else {
      setError('Invalid file type. Only PDF, DOCX, and TXT files are supported.')
    }
  }

  const handleVaultJobSelect = async (assetId: string) => {
    if (!assetId) return
    setSelectedVaultJob(assetId)
    await loadVaultJob(assetId)
  }

  const handleManualInputChange = (field: keyof JobInputData, newValue: any) => {
    onChange({
      ...value,
      [field]: newValue,
    })
  }

  const addCertification = () => {
    onChange({
      ...value,
      certifications: [...value.certifications, { name: '', category: 'must-have' }],
    })
  }

  const removeCertification = (index: number) => {
    onChange({
      ...value,
      certifications: value.certifications.filter((_, i) => i !== index),
    })
  }

  const updateCertification = (index: number, field: keyof Certification, newValue: any) => {
    const updated = [...value.certifications]
    updated[index] = { ...updated[index], [field]: newValue }
    onChange({
      ...value,
      certifications: updated,
    })
  }

  return (
    <div className={`job-input ${disabled ? 'disabled' : ''}`}>
      <div className="job-input-section">
        <h3>Job Information</h3>
        
        {/* Input Method Selection */}
        <div className="input-method-selector">
          <label>
            <input
              type="radio"
              name="inputMethod"
              value="upload"
              checked={inputMethod === 'upload'}
              onChange={(e) => setInputMethod(e.target.value as 'upload' | 'manual')}
              disabled={disabled}
            />
            <span>Upload Job Description File (Recommended)</span>
          </label>
          <label>
            <input
              type="radio"
              name="inputMethod"
              value="manual"
              checked={inputMethod === 'manual'}
              onChange={(e) => setInputMethod(e.target.value as 'upload' | 'manual')}
              disabled={disabled}
            />
            <span>Enter Details Manually</span>
          </label>
        </div>

        {error && <div className="error-message">{error}</div>}

        {inputMethod === 'upload' ? (
          <div className="upload-section">
            {parsing && (
              <div className="loading-indicator">
                <Loader2 className="spinner" />
                <span>Analyzing job description...</span>
              </div>
            )}

            {/* Vault Job Selection */}
            {vaultJobs.length > 0 && (
              <div className="vault-selector">
                <label htmlFor="vault-job">Use saved job description:</label>
                <select
                  id="vault-job"
                  value={selectedVaultJob}
                  onChange={(e) => handleVaultJobSelect(e.target.value)}
                  disabled={parsing || disabled}
                >
                  <option value="">None</option>
                  {vaultJobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.original_name} ({job.created_at.slice(0, 10)})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* File Upload */}
            <div 
              className={`file-upload ${isDragging ? 'dragging' : ''} ${disabled || uploading || parsing ? 'disabled' : ''}`}
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <label htmlFor="job-file-upload" className={`upload-label ${disabled || uploading || parsing ? 'disabled' : ''}`}>
                <Upload size={20} />
                <span>Upload Job Description</span>
              </label>
              <input
                id="job-file-upload"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={uploading || parsing || disabled}
                style={{ display: 'none' }}
              />
              <p className="upload-help">
                {isDragging ? (
                  <span>Drop file here to upload...</span>
                ) : (
                  <>Supported formats: PDF, DOCX, TXT. The system will automatically extract all requirements.</>
                )}
              </p>
            </div>

            {/* Display Extracted Information */}
            {value.parsedData && (
              <div className="extracted-info">
                <h4>Extracted Information:</h4>
                <div className="info-grid">
                  <div>
                    <strong>Job Title:</strong> {value.jobTitle}
                  </div>
                  <div>
                    <strong>Location:</strong> {value.location}
                  </div>
                  <div>
                    <strong>Experience:</strong>{' '}
                    {value.parsedData.experience_level || 'Not specified'}
                  </div>
                </div>

                {value.certifications.length > 0 && (
                  <div className="certifications-list">
                    <strong>Certifications Found:</strong>
                    <ul>
                      {value.certifications.map((cert, idx) => (
                        <li key={idx}>
                          [{cert.category === 'must-have' ? 'Required' : 'Preferred'}] {cert.name}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <details className="edit-section">
                  <summary>Edit Extracted Information (Optional)</summary>
                  <div className="edit-form">
                    <div className="form-row">
                      <div className="form-group">
                        <label>Job Title</label>
                        <input
                          type="text"
                          value={value.jobTitle}
                          onChange={(e) => handleManualInputChange('jobTitle', e.target.value)}
                          disabled={disabled}
                        />
                      </div>
                      <div className="form-group">
                        <label>Location</label>
                        <input
                          type="text"
                          value={value.location}
                          onChange={(e) => handleManualInputChange('location', e.target.value)}
                          disabled={disabled}
                        />
                      </div>
                    </div>

                    <div className="certifications-edit">
                      <label>
                        <strong>Modify Certifications:</strong>
                      </label>
                      {value.certifications.map((cert, idx) => (
                        <div key={idx} className="cert-item">
                          <input
                            type="text"
                            placeholder="Certification name"
                            value={cert.name}
                            onChange={(e) =>
                              updateCertification(idx, 'name', e.target.value)
                            }
                            disabled={disabled}
                          />
                          <select
                            value={cert.category}
                            onChange={(e) =>
                              updateCertification(
                                idx,
                                'category',
                                e.target.value as 'must-have' | 'bonus'
                              )
                            }
                            disabled={disabled}
                          >
                            <option value="must-have">Must-Have</option>
                            <option value="bonus">Bonus</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => removeCertification(idx)}
                            className="remove-btn"
                            disabled={disabled}
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={addCertification}
                        className="add-btn"
                        disabled={disabled}
                      >
                        Add Certification
                      </button>
                    </div>
                  </div>
                </details>
              </div>
            )}
          </div>
        ) : (
          <div className="manual-entry-section">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="job-title">Job Title *</label>
                <input
                  id="job-title"
                  type="text"
                  placeholder="e.g., Data Scientist"
                  value={value.jobTitle}
                  onChange={(e) => handleManualInputChange('jobTitle', e.target.value)}
                  disabled={disabled}
                />
              </div>
              <div className="form-group">
                <label htmlFor="location">Location *</label>
                <input
                  id="location"
                  type="text"
                  placeholder="e.g., New York, NY"
                  value={value.location}
                  onChange={(e) => handleManualInputChange('location', e.target.value)}
                  disabled={disabled}
                />
              </div>
            </div>

            <div className="certifications-section">
              <label>
                <strong>Certifications</strong>
                <button
                  type="button"
                  onClick={addCertification}
                  className="add-btn"
                  disabled={disabled}
                >
                  Add Certification
                </button>
              </label>
              {value.certifications.map((cert, idx) => (
                <div key={idx} className="cert-item">
                  <input
                    type="text"
                    placeholder={`Certification ${idx + 1} Name`}
                    value={cert.name}
                    onChange={(e) => updateCertification(idx, 'name', e.target.value)}
                    disabled={disabled}
                  />
                  <select
                    value={cert.category}
                    onChange={(e) =>
                      updateCertification(
                        idx,
                        'category',
                        e.target.value as 'must-have' | 'bonus'
                      )
                    }
                    disabled={disabled}
                  >
                    <option value="must-have">Must-Have</option>
                    <option value="bonus">Bonus</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => removeCertification(idx)}
                    className="remove-btn"
                    disabled={disabled}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>

            <div className="form-group">
              <label htmlFor="job-description">Full Job Description *</label>
              <textarea
                id="job-description"
                rows={10}
                placeholder="Enter the complete job description including required skills, preferred skills, experience requirements, technical stack, responsibilities, etc."
                value={value.jobDescription}
                onChange={(e) => handleManualInputChange('jobDescription', e.target.value)}
                disabled={disabled}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default JobInput
