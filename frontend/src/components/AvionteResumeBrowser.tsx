import React, { useState, useEffect } from 'react'
import { Search, Download, User, FileText, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { avionteService, TalentData } from '../services/avionteService'
import { useToast } from '../contexts/ToastContext'
import './AvionteResumeBrowser.css'

interface AvionteResumeBrowserProps {
  onResumeImport: (file: File) => void
  disabled?: boolean
}

interface TalentDocument {
  documentId?: string
  fileName: string
  fileType?: string
  fileSize?: number
  uploadDate?: string
  documentType?: string
}

const AvionteResumeBrowser: React.FC<AvionteResumeBrowserProps> = ({
  onResumeImport,
  disabled = false,
}) => {
  const { showToast } = useToast()
  const [expanded, setExpanded] = useState(false)
  const [talents, setTalents] = useState<TalentData[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTalent, setSelectedTalent] = useState<string | null>(null)
  const [documents, setDocuments] = useState<Record<string, TalentDocument[]>>({})
  const [loadingDocuments, setLoadingDocuments] = useState<Record<string, boolean>>({})
  const [downloading, setDownloading] = useState<Record<string, boolean>>({})
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [avionteConfigured, setAvionteConfigured] = useState(false)

  useEffect(() => {
    checkAvionteHealth()
  }, [])

  useEffect(() => {
    if (expanded && avionteConfigured) {
      searchTalents()
    }
  }, [expanded, searchQuery, page])

  const checkAvionteHealth = async () => {
    try {
      const health = await avionteService.checkHealth()
      setAvionteConfigured(health.avionte_configured)
    } catch (err) {
      console.error('Failed to check Avionté health:', err)
      setAvionteConfigured(false)
    }
  }

  const searchTalents = async () => {
    if (!avionteConfigured) return

    setLoading(true)
    try {
      const filters: Record<string, any> = {}
      
      // Add search filters if query provided
      // Note: Avionté API filter format may vary - adjust based on actual API documentation
      if (searchQuery.trim()) {
        const query = searchQuery.trim()
        // Try simple name/email search - adjust filter format based on Avionté API
        // Common patterns: exact match, contains, or regex
        // For now, we'll search by firstName (most common field)
        filters.firstName = query
        // Alternative: filters.firstName = { $contains: query } or similar
      }

      const results = await avionteService.queryTalents(filters, page, 50)
      setTalents(results.talents || [])
      setTotalPages(results.totalPages || 1)
    } catch (err: any) {
      console.error('Failed to search talents:', err)
      showToast({
        message: 'Failed to search Avionté talents. Try a different search or check API configuration.',
        type: 'error'
      })
    } finally {
      setLoading(false)
    }
  }

  const loadDocuments = async (talentId: string) => {
    if (documents[talentId] || loadingDocuments[talentId]) return

    setLoadingDocuments((prev) => ({ ...prev, [talentId]: true }))
    try {
      const docs = await avionteService.getTalentDocuments(talentId)
      setDocuments((prev) => ({ ...prev, [talentId]: docs }))
    } catch (err: any) {
      console.error('Failed to load documents:', err)
      showToast({
        message: 'Failed to load documents',
        type: 'error'
      })
    } finally {
      setLoadingDocuments((prev => {
        const next = { ...prev }
        delete next[talentId]
        return next
      }))
    }
  }

  const handleTalentClick = (talentId: string) => {
    if (selectedTalent === talentId) {
      setSelectedTalent(null)
    } else {
      setSelectedTalent(talentId)
      loadDocuments(talentId)
    }
  }

  const handleDownloadResume = async (talentId: string, documentId: string, fileName: string) => {
    const key = `${talentId}-${documentId}`
    if (downloading[key]) return

    setDownloading((prev) => ({ ...prev, [key]: true }))
    try {
      const blob = await avionteService.downloadTalentDocument(talentId, documentId)
      
      // Convert blob to File
      const file = new File([blob], fileName, { type: blob.type })
      
      onResumeImport(file)
      showToast({
        message: `Imported resume: ${fileName}`,
        type: 'success'
      })
    } catch (err: any) {
      console.error('Failed to download resume:', err)
      showToast({
        message: 'Failed to download resume',
        type: 'error'
      })
    } finally {
      setDownloading((prev => {
        const next = { ...prev }
        delete next[key]
        return next
      }))
    }
  }

  if (!avionteConfigured) {
    return null // Don't show if Avionté is not configured
  }

  return (
    <div className="avionte-resume-browser">
      <button
        className="avionte-toggle"
        onClick={() => setExpanded(!expanded)}
        disabled={disabled}
      >
        <FileText size={16} />
        <span>Import from Avionté</span>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {expanded && (
        <div className="avionte-browser-content">
          <div className="avionte-search">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setPage(1) // Reset to first page on new search
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  searchTalents()
                }
              }}
            />
            <button onClick={searchTalents} disabled={loading}>
              {loading ? <Loader2 size={16} className="spinning" /> : 'Search'}
            </button>
          </div>

          {loading && talents.length === 0 ? (
            <div className="avionte-loading">
              <Loader2 size={24} className="spinning" />
              <p>Loading talents...</p>
            </div>
          ) : talents.length === 0 ? (
            <div className="avionte-empty">
              <p>No talents found. Try a different search.</p>
            </div>
          ) : (
            <>
              <div className="avionte-talents-list">
                {talents.map((talent) => (
                  <div key={talent.talentId} className="avionte-talent-item">
                    <div
                      className="avionte-talent-header"
                      onClick={() => handleTalentClick(talent.talentId || '')}
                    >
                      <User size={16} />
                      <div className="avionte-talent-info">
                        <span className="avionte-talent-name">
                          {talent.firstName} {talent.lastName}
                        </span>
                        {talent.email && (
                          <span className="avionte-talent-email">{talent.email}</span>
                        )}
                      </div>
                      {selectedTalent === talent.talentId ? (
                        <ChevronUp size={16} />
                      ) : (
                        <ChevronDown size={16} />
                      )}
                    </div>

                    {selectedTalent === talent.talentId && (
                      <div className="avionte-documents">
                        {loadingDocuments[talent.talentId || ''] ? (
                          <div className="avionte-documents-loading">
                            <Loader2 size={16} className="spinning" />
                            <span>Loading documents...</span>
                          </div>
                        ) : documents[talent.talentId || '']?.length === 0 ? (
                          <div className="avionte-documents-empty">
                            <p>No documents found for this talent.</p>
                          </div>
                        ) : (
                          documents[talent.talentId || '']?.map((doc) => {
                            const key = `${talent.talentId}-${doc.documentId}`
                            const isDownloading = downloading[key]
                            return (
                              <div key={doc.documentId} className="avionte-document-item">
                                <FileText size={16} />
                                <div className="avionte-document-info">
                                  <span className="avionte-document-name">{doc.fileName}</span>
                                  {doc.fileSize && (
                                    <span className="avionte-document-size">
                                      {(doc.fileSize / 1024).toFixed(1)} KB
                                    </span>
                                  )}
                                </div>
                                <button
                                  className="avionte-download-btn"
                                  onClick={() =>
                                    handleDownloadResume(
                                      talent.talentId || '',
                                      doc.documentId || '',
                                      doc.fileName
                                    )
                                  }
                                  disabled={isDownloading || disabled}
                                >
                                  {isDownloading ? (
                                    <Loader2 size={16} className="spinning" />
                                  ) : (
                                    <Download size={16} />
                                  )}
                                  <span>Import</span>
                                </button>
                              </div>
                            )
                          })
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="avionte-pagination">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1 || loading}
                  >
                    Previous
                  </button>
                  <span>
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages || loading}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default AvionteResumeBrowser
