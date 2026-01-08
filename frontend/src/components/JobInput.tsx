import React, { useState, useEffect } from 'react'
import { jobService, JobParsed } from '../services/jobService'
import { vaultService, Asset } from '../services/vaultService'
import { Upload, Loader2 } from 'lucide-react'
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
}

const JobInput: React.FC<JobInputProps> = ({
  value,
  onChange,
  onVaultAssetSelect,
  selectedVaultJobId,
}) => {
  const [inputMethod, setInputMethod] = useState<'upload' | 'manual'>('upload')
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [vaultJobs, setVaultJobs] = useState<Asset[]>([])
  const [selectedVaultJob, setSelectedVaultJob] = useState<string>('')
  const [error, setError] = useState<string>('')

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
            name: c.name || c,
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

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setError('')
    setUploading(true)
    setParsing(true)

    try {
      const jobResponse = await jobService.uploadJob(file)
      if (jobResponse.parsed_data) {
        onChange({
          jobTitle: jobResponse.parsed_data.job_title,
          location: jobResponse.parsed_data.location,
          certifications: (jobResponse.parsed_data.certifications || []).map((c: any) => ({
            name: c.name || c,
            category: (c.category || 'must-have') as 'must-have' | 'bonus',
          })),
          jobDescription: jobResponse.parsed_data.full_description || '',
          parsedData: jobResponse.parsed_data,
          jobId: jobResponse.id,
        })
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse job description')
    } finally {
      setUploading(false)
      setParsing(false)
      // Reset file input
      event.target.value = ''
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
    <div className="job-input">
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
                  disabled={parsing}
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
            <div className="file-upload">
              <label htmlFor="job-file-upload" className="upload-label">
                <Upload size={20} />
                <span>Upload Job Description</span>
              </label>
              <input
                id="job-file-upload"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={uploading || parsing}
                style={{ display: 'none' }}
              />
              <p className="upload-help">
                Supported formats: PDF, DOCX, TXT. The system will automatically extract all requirements.
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
                        />
                      </div>
                      <div className="form-group">
                        <label>Location</label>
                        <input
                          type="text"
                          value={value.location}
                          onChange={(e) => handleManualInputChange('location', e.target.value)}
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
                          >
                            <option value="must-have">Must-Have</option>
                            <option value="bonus">Bonus</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => removeCertification(idx)}
                            className="remove-btn"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={addCertification}
                        className="add-btn"
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
                  >
                    <option value="must-have">Must-Have</option>
                    <option value="bonus">Bonus</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => removeCertification(idx)}
                    className="remove-btn"
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
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default JobInput
