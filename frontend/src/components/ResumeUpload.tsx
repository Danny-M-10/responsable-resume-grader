import React, { useState, useRef, useEffect } from 'react'
import { Upload, X, FileText, Loader2, CheckCircle2, AlertCircle, ChevronDown } from 'lucide-react'
import { vaultService, Asset } from '../services/vaultService'
import { useToast } from '../contexts/ToastContext'
import { apiClient } from '../api/client'
import './ResumeUpload.css'

export interface UploadedFile {
  file: File
  id: string
  size: number
}

export interface ProcessedResume {
  id: string  // Unique ID for this processed resume (matches UploadedFile.id)
  file: File
  status: 'uploading' | 'parsing' | 'complete' | 'error'
  candidateId?: string
  assetId?: string
  parsedData?: any
  error?: string
  uploadProgress?: number // Upload progress percentage (0-100)
  isDuplicate?: boolean // True if this resume was already in the system
}

interface ResumeUploadProps {
  processedResumes: ProcessedResume[]
  onProcessedResumesChange: (resumes: ProcessedResume[]) => void
  selectedVaultResumeIds?: string[]
  onVaultResumesChange?: (ids: string[]) => void
  disabled?: boolean
}

const ResumeUpload: React.FC<ResumeUploadProps> = ({
  processedResumes,
  onProcessedResumesChange,
  selectedVaultResumeIds = [],
  onVaultResumesChange,
  disabled = false,
}) => {
  const { showToast } = useToast()
  const [vaultResumes, setVaultResumes] = useState<Asset[]>([])
  const [loadingVault, setLoadingVault] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const processedResumesRef = useRef(processedResumes)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const dragCounterRef = useRef(0) // Track drag enter/leave to prevent flickering

  // Keep ref in sync with props
  useEffect(() => {
    processedResumesRef.current = processedResumes
  }, [processedResumes])

  useEffect(() => {
    loadVaultResumes()
  }, [])

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false)
      }
    }

    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [dropdownOpen])

  const loadVaultResumes = async () => {
    setLoadingVault(true)
    try {
      const resumes = await vaultService.listAssets('resume')
      setVaultResumes(resumes)
    } catch (err) {
      console.error('Failed to load vault resumes:', err)
    } finally {
      setLoadingVault(false)
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

  // Shared function to process files (used by both file input and drag-drop)
  const processFiles = async (files: File[]) => {
    // Check if currently processing by checking the ref
    const currentProcessingCount = processedResumesRef.current.filter(
      (r) => r.status === 'uploading' || r.status === 'parsing'
    ).length
    
    if (currentProcessingCount > 0 || disabled) {
      return
    }

    // Filter valid file types
    const validFiles = files.filter(isValidFileType)
    const invalidFiles = files.filter((file) => !isValidFileType(file))

    // Show toast for invalid files
    if (invalidFiles.length > 0) {
      showToast({
        message: `${invalidFiles.length} file(s) ignored. Only PDF, DOCX, and TXT files are supported.`,
        type: 'warning',
      })
    }

    if (validFiles.length === 0) {
      return
    }

    // Create initial processed resume entries with 'uploading' status
    const newProcessedResumes: ProcessedResume[] = validFiles.map((file) => ({
      id: Math.random().toString(36).substring(7),
      file,
      status: 'uploading' as const,
      uploadProgress: 0,
    }))

    // Add new resumes to the list immediately so user sees them
    // Use ref to get the latest state to avoid stale closures
    const currentResumes = processedResumesRef.current
    const updatedResumes = [...currentResumes, ...newProcessedResumes]
    // Update ref synchronously before async processing starts
    processedResumesRef.current = updatedResumes
    onProcessedResumesChange(updatedResumes)

    // Process all files in parallel so user can see multiple progress bars
    await Promise.all(newProcessedResumes.map((processedResume) => processResumeFile(processedResume)))
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files) return

    const fileArray = Array.from(files)
    await processFiles(fileArray)

    // Reset file input to allow selecting the same file again
    event.target.value = ''
  }

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Check if currently processing by checking the ref
    const currentProcessingCount = processedResumesRef.current.filter(
      (r) => r.status === 'uploading' || r.status === 'parsing'
    ).length
    
    if (currentProcessingCount > 0 || disabled) {
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
    
    // Check if currently processing by checking the ref
    const currentProcessingCount = processedResumesRef.current.filter(
      (r) => r.status === 'uploading' || r.status === 'parsing'
    ).length
    
    if (currentProcessingCount > 0 || disabled) {
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

    // Check if currently processing by checking the ref
    const currentProcessingCount = processedResumesRef.current.filter(
      (r) => r.status === 'uploading' || r.status === 'parsing'
    ).length
    
    if (currentProcessingCount > 0 || disabled) {
      return
    }

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      const fileArray = Array.from(files)
      await processFiles(fileArray)
    }
  }

  const processResumeFile = async (processedResume: ProcessedResume) => {
    // Initialize upload progress
    updateProcessedResumeProgress(processedResume.id, 0)

    try {
      // Upload and parse the resume with progress tracking
      const formData = new FormData()
      formData.append('files', processedResume.file)

      const response = await apiClient.post('/api/resumes/upload', formData, {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            updateProcessedResumeProgress(processedResume.id, percentCompleted)
          }
        },
      })

      const uploadResponse = response.data
      
      // Update status to parsing (upload complete, now parsing)
      updateProcessedResumeStatus(processedResume.id, 'parsing')

      if (uploadResponse.candidate_ids && uploadResponse.candidate_ids.length > 0 && uploadResponse.parsed_data && uploadResponse.parsed_data.length > 0) {
        const candidateId = uploadResponse.candidate_ids[0]
        const assetId = uploadResponse.asset_ids && uploadResponse.asset_ids.length > 0 ? uploadResponse.asset_ids[0] : undefined
        const parsedData = uploadResponse.parsed_data[0]

        if (!candidateId) {
          throw new Error('No candidate ID returned from server')
        }
        if (!parsedData) {
          throw new Error('No parsed data returned from server')
        }

        // Check if this was a duplicate
        const isDuplicate = uploadResponse.duplicates && uploadResponse.duplicates.length > 0

        // Update to complete status
        updateProcessedResumeStatus(processedResume.id, 'complete', {
          candidateId,
          assetId,
          parsedData,
          isDuplicate,
        })

        if (isDuplicate) {
          const dupInfo = uploadResponse.duplicates[0]
          showToast({
            message: `Resume "${processedResume.file.name}" already exists (${dupInfo.name || 'candidate'}) - using existing`,
            type: 'info',
          })
        } else {
          showToast({
            message: `Resume "${processedResume.file.name}" processed successfully`,
            type: 'success',
          })
        }
      } else {
        throw new Error('Invalid response from server')
      }
    } catch (error: any) {
      console.error('Failed to process resume:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to process resume'
      updateProcessedResumeStatus(processedResume.id, 'error', undefined, errorMessage)
      showToast({
        message: `Failed to process "${processedResume.file.name}": ${errorMessage}`,
        type: 'error',
      })
    }
  }

  const updateProcessedResumeProgress = (id: string, progress: number) => {
    // Use ref to get latest state to avoid stale closures
    const currentResumes = processedResumesRef.current
    const updatedResumes = currentResumes.map((resume) => {
      if (resume.id === id) {
        return {
          ...resume,
          uploadProgress: progress,
        }
      }
      return resume
    })
    // Update ref synchronously
    processedResumesRef.current = updatedResumes
    onProcessedResumesChange(updatedResumes)
  }

  const updateProcessedResumeStatus = (
    id: string,
    status: ProcessedResume['status'],
    data?: { candidateId?: string; assetId?: string; parsedData?: any; isDuplicate?: boolean },
    error?: string
  ) => {
    // Use ref to get latest state to avoid stale closures
    const currentResumes = processedResumesRef.current
    const updatedResumes = currentResumes.map((resume) => {
      if (resume.id === id) {
        return {
          ...resume,
          status,
          candidateId: data?.candidateId || resume.candidateId,
          assetId: data?.assetId || resume.assetId,
          parsedData: data?.parsedData || resume.parsedData,
          isDuplicate: data?.isDuplicate || resume.isDuplicate,
          error: error || resume.error,
          // Clear progress when status changes to parsing or complete
          uploadProgress: status === 'parsing' || status === 'complete' || status === 'error' ? undefined : resume.uploadProgress,
        }
      }
      return resume
    })
    // Update ref synchronously
    processedResumesRef.current = updatedResumes
    onProcessedResumesChange(updatedResumes)
  }

  const handleRemoveProcessedResume = (id: string) => {
    onProcessedResumesChange(processedResumes.filter((r) => r.id !== id))
  }

  const handleRetryProcessing = async (processedResume: ProcessedResume) => {
    await processResumeFile(processedResume)
  }

  const handleVaultResumeToggle = (assetId: string) => {
    if (disabled) return
    if (!onVaultResumesChange) return

    const isSelected = selectedVaultResumeIds.includes(assetId)
    if (isSelected) {
      onVaultResumesChange(selectedVaultResumeIds.filter((id) => id !== assetId))
    } else {
      onVaultResumesChange([...selectedVaultResumeIds, assetId])
    }
  }

  const handleDropdownToggle = () => {
    if (disabled) return
    setDropdownOpen(!dropdownOpen)
  }

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }

  const handleTagRemove = (assetId: string, e: React.MouseEvent) => {
    if (disabled) return
    e.stopPropagation()
    if (!onVaultResumesChange) return
    onVaultResumesChange(selectedVaultResumeIds.filter((id) => id !== assetId))
  }

  // Filter resumes based on search query
  const filteredResumes = vaultResumes.filter((resume) =>
    resume.original_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Get selected resume objects for tag display
  const selectedResumes = vaultResumes.filter((resume) =>
    selectedVaultResumeIds.includes(resume.id)
  )

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const totalFiles = processedResumes.length + selectedVaultResumeIds.length
  const processingCount = processedResumes.filter((r) => r.status === 'uploading' || r.status === 'parsing').length
  const completedCount = processedResumes.filter((r) => r.status === 'complete').length
  const errorCount = processedResumes.filter((r) => r.status === 'error').length
  const duplicateCount = processedResumes.filter((r) => r.status === 'complete' && r.isDuplicate).length

  return (
    <div className="resume-upload">
      <div className="resume-upload-section">
        <h3>Candidate Resumes</h3>

        {/* File Upload */}
        <div 
          className={`file-upload-area ${isDragging ? 'dragging' : ''} ${disabled || processingCount > 0 ? 'disabled' : ''}`}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <label 
            htmlFor="resume-file-upload" 
            className={`upload-label ${disabled || processingCount > 0 ? 'disabled' : ''}`}
          >
            <Upload size={20} />
            <span>Upload Resume Files</span>
          </label>
          <input
            id="resume-file-upload"
            type="file"
            accept=".pdf,.docx,.txt"
            multiple
            onChange={handleFileSelect}
            disabled={processingCount > 0 || disabled}
            style={{ display: 'none' }}
          />
          <p className="upload-help">
            {isDragging ? (
              <span>Drop files here to upload...</span>
            ) : (
              <>
                Upload candidate resumes in PDF, DOCX, or TXT format. They will be processed immediately.
                {processingCount > 0 && <span className="processing-indicator"> ({processingCount} processing...)</span>}
              </>
            )}
          </p>
        </div>

        {/* Processed Resumes List */}
        {processedResumes.length > 0 && (
          <div className="processed-resumes">
            <h4>
              Processed Resumes ({completedCount} ready
              {duplicateCount > 0 && `, ${duplicateCount} existing`}
              {processingCount > 0 && `, ${processingCount} processing`}
              {errorCount > 0 && `, ${errorCount} errors`})
            </h4>
            <ul className="files-list">
              {processedResumes.map((processedResume) => {
                const statusClass =
                  processedResume.status === 'uploading' || processedResume.status === 'parsing'
                    ? 'uploading'
                    : processedResume.status === 'complete' && processedResume.isDuplicate
                    ? 'duplicate'
                    : processedResume.status === 'complete'
                    ? 'complete'
                    : processedResume.status === 'error'
                    ? 'error'
                    : ''
                return (
                <li key={processedResume.id} className={`file-item ${statusClass}`}>
                  <div className="file-info">
                    <FileText size={16} />
                    <div className="file-details">
                      <div className="file-name">{processedResume.file.name}</div>
                      <div className="file-size">{formatFileSize(processedResume.file.size)}</div>
                      {processedResume.status === 'complete' && processedResume.parsedData && (
                        <div className="file-parsed-info">
                          {processedResume.parsedData.name && (
                            <span className="parsed-name">{processedResume.parsedData.name}</span>
                          )}
                          {processedResume.parsedData.email && (
                            <span className="parsed-email">{processedResume.parsedData.email}</span>
                          )}
                          {processedResume.parsedData.skills && processedResume.parsedData.skills.length > 0 && (
                            <span className="parsed-skills">{processedResume.parsedData.skills.length} skills</span>
                          )}
                        </div>
                      )}
                      {processedResume.status === 'error' && processedResume.error && (
                        <div className="file-error">{processedResume.error}</div>
                      )}
                      {/* Upload Progress Bar */}
                      {processedResume.status === 'uploading' && processedResume.uploadProgress !== undefined && (
                        <div className="upload-progress-container">
                          <div className="upload-progress-bar">
                            <div 
                              className="upload-progress-fill" 
                              style={{ width: `${processedResume.uploadProgress}%` }}
                            />
                          </div>
                          <span className="upload-progress-text">{processedResume.uploadProgress}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="file-status-actions">
                    {processedResume.status === 'uploading' ? (
                      <div className="status-with-progress">
                        <Loader2 className="spinner" size={16} />
                        <span className="status-text">Uploading{processedResume.uploadProgress !== undefined ? ` ${processedResume.uploadProgress}%` : ''}</span>
                      </div>
                    ) : processedResume.status === 'parsing' ? (
                      <div className="status-with-progress">
                        <Loader2 className="spinner" size={16} />
                        <span className="status-text">Parsing...</span>
                      </div>
                    ) : processedResume.status === 'complete' ? (
                      <div className="status-complete">
                        <CheckCircle2 size={16} className={processedResume.isDuplicate ? 'status-duplicate' : 'status-success'} />
                        {processedResume.isDuplicate && <span className="duplicate-badge">Existing</span>}
                      </div>
                    ) : (
                      <>
                        <AlertCircle size={16} className="status-error" />
                        <button
                          className="retry-btn"
                          onClick={() => handleRetryProcessing(processedResume)}
                          title="Retry"
                          aria-label="Retry processing this resume"
                        >
                          Retry
                        </button>
                      </>
                    )}
                    <button
                      className="remove-btn"
                      onClick={() => handleRemoveProcessedResume(processedResume.id)}
                      title="Remove"
                      aria-label={`Remove ${processedResume.file.name}`}
                      disabled={processedResume.status === 'uploading' || processedResume.status === 'parsing'}
                    >
                      <X size={16} aria-hidden="true" />
                    </button>
                  </div>
                </li>
              )})}
            </ul>
          </div>
        )}

        {/* Vault Resumes Dropdown */}
        {vaultResumes.length > 0 && (
          <div className="vault-resumes-dropdown" ref={dropdownRef}>
            <h4>Select from Saved Resumes</h4>
            {loadingVault ? (
              <div className="loading-indicator">
                <Loader2 className="spinner" />
                <span>Loading saved resumes...</span>
              </div>
            ) : (
              <>
                <div
                  className="vault-dropdown-trigger"
                  onClick={handleDropdownToggle}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      handleDropdownToggle()
                    }
                  }}
                  aria-expanded={dropdownOpen}
                  aria-haspopup="listbox"
                  aria-disabled={disabled}
                >
                  <div className="vault-tags-container">
                    {selectedResumes.length > 0 ? (
                      selectedResumes.map((resume) => (
                        <span key={resume.id} className="vault-tag">
                          <span className="vault-tag-text">{resume.original_name}</span>
                          <button
                            type="button"
                            className="vault-tag-remove"
                            onClick={(e) => handleTagRemove(resume.id, e)}
                            aria-label={`Remove ${resume.original_name}`}
                          >
                            <X size={14} aria-hidden="true" />
                          </button>
                        </span>
                      ))
                    ) : (
                      <span className="vault-dropdown-placeholder">Select from saved resumes...</span>
                    )}
                  </div>
                  <ChevronDown
                    size={20}
                    className={`vault-dropdown-icon ${dropdownOpen ? 'open' : ''}`}
                    aria-hidden="true"
                  />
                </div>
                {dropdownOpen && !disabled && (
                  <div className="vault-dropdown-menu" role="listbox">
                    <input
                      type="text"
                      className="vault-dropdown-search"
                      placeholder="Search resumes..."
                      value={searchQuery}
                      onChange={handleSearchChange}
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => e.stopPropagation()}
                      aria-label="Search resumes"
                    />
                    <ul className="vault-dropdown-list">
                      {filteredResumes.length > 0 ? (
                        filteredResumes.map((resume) => (
                          <li
                            key={resume.id}
                            className="vault-dropdown-item"
                            role="option"
                            aria-selected={selectedVaultResumeIds.includes(resume.id)}
                          >
                            <label className="vault-dropdown-item-label">
                              <input
                                type="checkbox"
                                checked={selectedVaultResumeIds.includes(resume.id)}
                                onChange={() => handleVaultResumeToggle(resume.id)}
                                onClick={(e) => e.stopPropagation()}
                              />
                              <div className="vault-dropdown-item-info">
                                <FileText size={16} aria-hidden="true" />
                                <div>
                                  <div className="vault-dropdown-item-name">{resume.original_name}</div>
                                  <div className="vault-dropdown-item-date">{resume.created_at.slice(0, 10)}</div>
                                </div>
                              </div>
                            </label>
                          </li>
                        ))
                      ) : (
                        <li className="vault-dropdown-empty">No resumes found matching "{searchQuery}"</li>
                      )}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Summary */}
        {totalFiles > 0 && (
          <div className="files-summary">
            <strong>Total files selected: {totalFiles}</strong>
          </div>
        )}
      </div>
    </div>
  )
}

export default ResumeUpload
