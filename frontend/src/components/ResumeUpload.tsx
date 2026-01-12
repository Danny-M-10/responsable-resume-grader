import React, { useState } from 'react'
import { Upload, X, FileText, Loader2 } from 'lucide-react'
import { vaultService, Asset } from '../services/vaultService'
import './ResumeUpload.css'

export interface UploadedFile {
  file: File
  id: string
  size: number
}

interface ResumeUploadProps {
  uploadedFiles: UploadedFile[]
  onFilesChange: (files: UploadedFile[]) => void
  selectedVaultResumeIds?: string[]
  onVaultResumesChange?: (ids: string[]) => void
}

const ResumeUpload: React.FC<ResumeUploadProps> = ({
  uploadedFiles,
  onFilesChange,
  selectedVaultResumeIds = [],
  onVaultResumesChange,
}) => {
  const [uploading, setUploading] = useState(false)
  const [vaultResumes, setVaultResumes] = useState<Asset[]>([])
  const [loadingVault, setLoadingVault] = useState(false)

  React.useEffect(() => {
    loadVaultResumes()
  }, [])

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

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files) return

    setUploading(true)
    try {
      const newFiles: UploadedFile[] = Array.from(files).map((file) => ({
        file,
        id: Math.random().toString(36).substring(7),
        size: file.size,
      }))

      onFilesChange([...uploadedFiles, ...newFiles])
    } finally {
      setUploading(false)
      // Reset file input to allow selecting the same file again
      event.target.value = ''
    }
  }

  const handleRemoveFile = (id: string) => {
    onFilesChange(uploadedFiles.filter((f) => f.id !== id))
  }

  const handleVaultResumeToggle = (assetId: string) => {
    if (!onVaultResumesChange) return

    const isSelected = selectedVaultResumeIds.includes(assetId)
    if (isSelected) {
      onVaultResumesChange(selectedVaultResumeIds.filter((id) => id !== assetId))
    } else {
      onVaultResumesChange([...selectedVaultResumeIds, assetId])
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const totalFiles = uploadedFiles.length + selectedVaultResumeIds.length

  return (
    <div className="resume-upload">
      <div className="resume-upload-section">
        <h3>Candidate Resumes</h3>

        {/* File Upload */}
        <div className="file-upload-area">
          <label htmlFor="resume-file-upload" className="upload-label">
            <Upload size={20} />
            <span>Upload Resume Files</span>
          </label>
          <input
            id="resume-file-upload"
            type="file"
            accept=".pdf,.docx,.txt"
            multiple
            onChange={handleFileSelect}
            disabled={uploading}
            style={{ display: 'none' }}
          />
          <p className="upload-help">
            Upload candidate resumes in PDF, DOCX, or TXT format. You can upload multiple files at
            once.
          </p>
        </div>

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            <h4>Uploaded Files ({uploadedFiles.length})</h4>
            <ul className="files-list">
              {uploadedFiles.map((uploadedFile) => (
                <li key={uploadedFile.id} className="file-item">
                  <div className="file-info">
                    <FileText size={16} />
                    <div>
                      <div className="file-name">{uploadedFile.file.name}</div>
                      <div className="file-size">{formatFileSize(uploadedFile.size)}</div>
                    </div>
                  </div>
                  <button
                    className="remove-btn"
                    onClick={() => handleRemoveFile(uploadedFile.id)}
                    title="Remove"
                  >
                    <X size={16} />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Vault Resumes */}
        {vaultResumes.length > 0 && (
          <div className="vault-resumes">
            <h4>Select from Saved Resumes</h4>
            {loadingVault ? (
              <div className="loading-indicator">
                <Loader2 className="spinner" />
                <span>Loading saved resumes...</span>
              </div>
            ) : (
              <ul className="files-list">
                {vaultResumes.map((resume) => (
                  <li
                    key={resume.id}
                    className={`file-item ${selectedVaultResumeIds.includes(resume.id) ? 'selected' : ''}`}
                  >
                    <label className="file-checkbox">
                      <input
                        type="checkbox"
                        checked={selectedVaultResumeIds.includes(resume.id)}
                        onChange={() => handleVaultResumeToggle(resume.id)}
                      />
                      <div className="file-info">
                        <FileText size={16} />
                        <div>
                          <div className="file-name">{resume.original_name}</div>
                          <div className="file-date">{resume.created_at.slice(0, 10)}</div>
                        </div>
                      </div>
                    </label>
                  </li>
                ))}
              </ul>
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
