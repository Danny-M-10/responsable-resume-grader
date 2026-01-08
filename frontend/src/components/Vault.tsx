import React, { useState, useEffect } from 'react'
import { vaultService, Asset } from '../services/vaultService'
import { Upload, Trash2, Loader2, FileText } from 'lucide-react'
import './Vault.css'

interface VaultProps {
  onJobSelect?: (assetId: string) => void
  onResumeSelect?: (assetIds: string[]) => void
  selectedJobId?: string
  selectedResumeIds?: string[]
}

const Vault: React.FC<VaultProps> = ({
  onJobSelect,
  onResumeSelect,
  selectedJobId,
  selectedResumeIds = [],
}) => {
  const [expanded, setExpanded] = useState(false)
  const [jobAssets, setJobAssets] = useState<Asset[]>([])
  const [resumeAssets, setResumeAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(false)
  const [uploadingJob, setUploadingJob] = useState(false)
  const [uploadingResume, setUploadingResume] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (expanded) {
      loadAssets()
    }
  }, [expanded])

  const loadAssets = async () => {
    setLoading(true)
    setError('')
    try {
      const [jobs, resumes] = await Promise.all([
        vaultService.listAssets('job_description'),
        vaultService.listAssets('resume'),
      ])
      setJobAssets(jobs)
      setResumeAssets(resumes)
    } catch (err: any) {
      setError('Failed to load saved files')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleJobUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadingJob(true)
    setError('')

    try {
      await vaultService.saveAsset(file, 'job_description')
      await loadAssets()
    } catch (err: any) {
      setError('Failed to save job description to vault')
      console.error(err)
    } finally {
      setUploadingJob(false)
      event.target.value = ''
    }
  }

  const handleResumeUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setUploadingResume(true)
    setError('')

    try {
      await Promise.all(
        Array.from(files).map((file) => vaultService.saveAsset(file, 'resume'))
      )
      await loadAssets()
    } catch (err: any) {
      setError('Failed to save resume to vault')
      console.error(err)
    } finally {
      setUploadingResume(false)
      event.target.value = ''
    }
  }

  const handleDeleteJob = async (assetId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    if (!confirm('Are you sure you want to delete this job description?')) return

    try {
      await vaultService.deleteAsset(assetId)
      await loadAssets()
      if (selectedJobId === assetId && onJobSelect) {
        onJobSelect('')
      }
    } catch (err: any) {
      setError('Failed to delete job description')
      console.error(err)
    }
  }

  const handleDeleteResume = async (assetId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    if (!confirm('Are you sure you want to delete this resume?')) return

    try {
      await vaultService.deleteAsset(assetId)
      await loadAssets()
      if (onResumeSelect) {
        onResumeSelect(selectedResumeIds.filter((id) => id !== assetId))
      }
    } catch (err: any) {
      setError('Failed to delete resume')
      console.error(err)
    }
  }

  const handleJobSelect = (assetId: string) => {
    if (onJobSelect) {
      onJobSelect(assetId)
    }
  }

  const handleResumeToggle = (assetId: string) => {
    if (!onResumeSelect) return

    const isSelected = selectedResumeIds.includes(assetId)
    if (isSelected) {
      onResumeSelect(selectedResumeIds.filter((id) => id !== assetId))
    } else {
      onResumeSelect([...selectedResumeIds, assetId])
    }
  }

  return (
    <div className="vault-container">
      <details
        className="vault-expander"
        open={expanded}
        onToggle={(e) => setExpanded((e.target as HTMLDetailsElement).open)}
      >
        <summary className="vault-summary">My Saved Files (Vault)</summary>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading-indicator">
            <Loader2 className="spinner" />
            <span>Loading saved files...</span>
          </div>
        ) : (
          <div className="vault-content">
            <div className="vault-column">
              <h4>Job Descriptions</h4>

              {jobAssets.length > 0 && (
                <div className="asset-selector">
                  <label htmlFor="vault-job-select">Use saved job description:</label>
                  <select
                    id="vault-job-select"
                    value={selectedJobId || ''}
                    onChange={(e) => handleJobSelect(e.target.value)}
                  >
                    <option value="">None</option>
                    {jobAssets.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.original_name} ({job.created_at.slice(0, 10)})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {jobAssets.map((job) => (
                <div
                  key={job.id}
                  className={`asset-item ${selectedJobId === job.id ? 'selected' : ''}`}
                >
                  <div className="asset-info">
                    <FileText size={16} />
                    <div>
                      <div className="asset-name">{job.original_name}</div>
                      <div className="asset-date">{job.created_at.slice(0, 10)}</div>
                    </div>
                  </div>
                  <button
                    className="delete-btn"
                    onClick={(e) => handleDeleteJob(job.id, e)}
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}

              <div className="upload-section">
                <label htmlFor="vault-job-upload" className="upload-label">
                  {uploadingJob ? (
                    <>
                      <Loader2 className="spinner" size={16} />
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      <span>Add job description to vault</span>
                    </>
                  )}
                </label>
                <input
                  id="vault-job-upload"
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleJobUpload}
                  disabled={uploadingJob}
                  style={{ display: 'none' }}
                />
              </div>
            </div>

            <div className="vault-column">
              <h4>Resumes</h4>

              {resumeAssets.length > 0 && (
                <div className="asset-list">
                  {resumeAssets.map((resume) => (
                    <div
                      key={resume.id}
                      className={`asset-item ${
                        selectedResumeIds.includes(resume.id) ? 'selected' : ''
                      }`}
                    >
                      <label className="asset-checkbox">
                        <input
                          type="checkbox"
                          checked={selectedResumeIds.includes(resume.id)}
                          onChange={() => handleResumeToggle(resume.id)}
                        />
                        <div className="asset-info">
                          <FileText size={16} />
                          <div>
                            <div className="asset-name">{resume.original_name}</div>
                            <div className="asset-date">{resume.created_at.slice(0, 10)}</div>
                          </div>
                        </div>
                      </label>
                      <button
                        className="delete-btn"
                        onClick={(e) => handleDeleteResume(resume.id, e)}
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="upload-section">
                <label htmlFor="vault-resume-upload" className="upload-label">
                  {uploadingResume ? (
                    <>
                      <Loader2 className="spinner" size={16} />
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      <span>Add resume to vault</span>
                    </>
                  )}
                </label>
                <input
                  id="vault-resume-upload"
                  type="file"
                  accept=".pdf,.docx,.txt"
                  multiple
                  onChange={handleResumeUpload}
                  disabled={uploadingResume}
                  style={{ display: 'none' }}
                />
              </div>
            </div>
          </div>
        )}
      </details>
    </div>
  )
}

export default Vault
