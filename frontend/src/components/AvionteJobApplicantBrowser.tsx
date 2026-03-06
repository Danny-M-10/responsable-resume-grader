import React, { useState, useEffect } from 'react'
import { Briefcase, Download, Loader2, ChevronDown, ChevronUp, Users } from 'lucide-react'
import { avionteService, JobData, WebApplicant, ImportApplicantsResult } from '../services/avionteService'
import { useToast } from '../contexts/ToastContext'
import './AvionteJobApplicantBrowser.css'

interface AvionteJobApplicantBrowserProps {
  onApplicantsImported: (candidateIds: string[]) => void
  disabled?: boolean
}

const AvionteJobApplicantBrowser: React.FC<AvionteJobApplicantBrowserProps> = ({
  onApplicantsImported,
  disabled = false,
}) => {
  const { showToast } = useToast()
  const [expanded, setExpanded] = useState(false)
  const [jobs, setJobs] = useState<JobData[]>([])
  const [selectedJob, setSelectedJob] = useState<JobData | null>(null)
  const [applicants, setApplicants] = useState<WebApplicant[]>([])
  const [loadingJobs, setLoadingJobs] = useState(false)
  const [loadingApplicants, setLoadingApplicants] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importProgress, setImportProgress] = useState<{ imported: number; failed: number; total: number } | null>(null)
  const [avionteConfigured, setAvionteConfigured] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    checkAvionteHealth()
  }, [])

  useEffect(() => {
    if (expanded && avionteConfigured) {
      loadJobs()
    }
  }, [expanded, avionteConfigured])

  useEffect(() => {
    if (selectedJob) {
      loadApplicants(selectedJob.jobId!)
    }
  }, [selectedJob])

  const checkAvionteHealth = async () => {
    try {
      const health = await avionteService.checkHealth()
      setAvionteConfigured(health.avionte_configured)
    } catch (error) {
      console.error('Failed to check Avionté health:', error)
      setAvionteConfigured(false)
    }
  }

  const loadJobs = async () => {
    try {
      setLoadingJobs(true)
      const filters: Record<string, any> = {}
      if (searchQuery) {
        filters.title = searchQuery
      }
      const result = await avionteService.queryJobs(filters, 1, 50)
      setJobs(result.jobs || [])
    } catch (error: any) {
      console.error('Failed to load jobs:', error)
      showToast({
        message: error.message || 'Failed to load jobs from Avionté',
        type: 'error',
      })
    } finally {
      setLoadingJobs(false)
    }
  }

  const loadApplicants = async (jobId: string) => {
    try {
      setLoadingApplicants(true)
      const result = await avionteService.getJobApplicants(jobId)
      setApplicants(result.applicants || [])
    } catch (error: any) {
      console.error('Failed to load applicants:', error)
      showToast({
        message: error.message || 'Failed to load applicants',
        type: 'error',
      })
      setApplicants([])
    } finally {
      setLoadingApplicants(false)
    }
  }

  const handleImportApplicants = async () => {
    if (!selectedJob?.jobId) return

    try {
      setImporting(true)
      setImportProgress({ imported: 0, failed: 0, total: applicants.length })
      
      const clientId = `import-${Date.now()}`
      const result: ImportApplicantsResult = await avionteService.importJobApplicants(
        selectedJob.jobId,
        undefined, // Import all applicants
        clientId
      )

      setImportProgress({
        imported: result.imported,
        failed: result.failed,
        total: applicants.length,
      })

      if (result.candidate_ids && result.candidate_ids.length > 0) {
        onApplicantsImported(result.candidate_ids)
        showToast({
          message: `Successfully imported ${result.imported} applicant${result.imported !== 1 ? 's' : ''}`,
          type: 'success',
        })
      } else {
        showToast({
          message: result.message || 'No applicants were imported',
          type: 'warning',
        })
      }

      if (result.errors && result.errors.length > 0) {
        console.warn('Import errors:', result.errors)
        if (result.failed > 0) {
          showToast({
            message: `${result.failed} applicant${result.failed !== 1 ? 's' : ''} failed to import`,
            type: 'error',
          })
        }
      }
    } catch (error: any) {
      console.error('Failed to import applicants:', error)
      showToast({
        message: error.message || 'Failed to import applicants',
        type: 'error',
      })
    } finally {
      setImporting(false)
      // Keep progress visible for a moment
      setTimeout(() => setImportProgress(null), 3000)
    }
  }

  if (!avionteConfigured) {
    return null // Don't show if Avionté is not configured
  }

  const filteredJobs = searchQuery
    ? jobs.filter(
        (job) =>
          job.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          job.company?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : jobs

  return (
    <div className="avionte-job-applicant-browser">
      <button
        className="avionte-toggle"
        onClick={() => setExpanded(!expanded)}
        disabled={disabled}
      >
        <Briefcase size={16} />
        <span>Import Applicants from Avionté Job</span>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {expanded && !avionteConfigured && (
        <div className="avionte-browser-content">
          <div className="avionte-not-configured">
            <p>Avionté integration is not configured.</p>
            <p className="avionte-config-help">
              To enable Avionté job applicant import, configure the following environment variables:
              <br />
              <code>AVIONTE_CLIENT_ID</code>, <code>AVIONTE_CLIENT_SECRET</code>, <code>AVIONTE_API_BASE_URL</code>, and <code>AVIONTE_TENANT_ID</code>
            </p>
          </div>
        </div>
      )}

      {expanded && avionteConfigured && (
        <div className="avionte-browser-content">
          {/* Job Search */}
          <div className="avionte-search">
            <input
              type="text"
              placeholder="Search jobs by title or company..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                if (e.target.value) {
                  loadJobs()
                }
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  loadJobs()
                }
              }}
            />
            <button onClick={loadJobs} disabled={loadingJobs}>
              {loadingJobs ? <Loader2 size={16} className="spinning" /> : 'Search'}
            </button>
          </div>

          {/* Job Selection */}
          {loadingJobs ? (
            <div className="avionte-loading">
              <Loader2 size={24} className="spinning" />
              <p>Loading jobs...</p>
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="avionte-empty">
              <p>No jobs found. Try a different search.</p>
            </div>
          ) : (
            <div className="avionte-job-selector">
              <label htmlFor="job-select">Select a Job:</label>
              <select
                id="job-select"
                value={selectedJob?.jobId || ''}
                onChange={(e) => {
                  const job = jobs.find((j) => j.jobId === e.target.value)
                  setSelectedJob(job || null)
                }}
                disabled={disabled}
              >
                <option value="">-- Select a job --</option>
                {filteredJobs.map((job) => (
                  <option key={job.jobId} value={job.jobId}>
                    {job.title} {job.company ? `- ${job.company}` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Selected Job Details */}
          {selectedJob && (
            <div className="avionte-job-details">
              <h4>{selectedJob.title}</h4>
              {selectedJob.company && <p className="avionte-job-company">{selectedJob.company}</p>}
              {loadingApplicants ? (
                <div className="avionte-loading">
                  <Loader2 size={16} className="spinning" />
                  <span>Loading applicants...</span>
                </div>
              ) : (
                <div className="avionte-applicant-count">
                  <Users size={16} />
                  <span>{applicants.length} applicant{applicants.length !== 1 ? 's' : ''} found</span>
                </div>
              )}

              {applicants.length > 0 && (
                <button
                  className="avionte-import-btn"
                  onClick={handleImportApplicants}
                  disabled={importing || disabled}
                >
                  {importing ? (
                    <>
                      <Loader2 size={16} className="spinning" />
                      <span>Importing...</span>
                    </>
                  ) : (
                    <>
                      <Download size={16} />
                      <span>Import All Applicants</span>
                    </>
                  )}
                </button>
              )}

              {importProgress && (
                <div className="avionte-import-progress">
                  <p>
                    Imported: {importProgress.imported} / {importProgress.total}
                  </p>
                  {importProgress.failed > 0 && (
                    <p className="avionte-error-text">Failed: {importProgress.failed}</p>
                  )}
                </div>
              )}

              {applicants.length === 0 && !loadingApplicants && (
                <div className="avionte-empty">
                  <p>No applicants found for this job.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AvionteJobApplicantBrowser
