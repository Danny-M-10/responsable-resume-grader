import React, { useState, useEffect, useMemo } from 'react'
import { vaultService, Asset, AssetFilters } from '../services/vaultService'
import { Upload, Trash2, Loader2, FileText, Tag, Edit2, Search, X } from 'lucide-react'
import './VaultPage.css'

const VaultPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'jobs' | 'resumes'>('jobs')
  const [jobAssets, setJobAssets] = useState<Asset[]>([])
  const [resumeAssets, setResumeAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string>('')
  const [editingTags, setEditingTags] = useState<string | null>(null)
  const [tagInput, setTagInput] = useState<string>('')
  
  // Search/filter state
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedSkills, setSelectedSkills] = useState<string[]>([])
  const [nameFilter, setNameFilter] = useState<string>('')

  useEffect(() => {
    loadAssets()
  }, [activeTab])

  const loadAssets = async () => {
    setLoading(true)
    setError('')
    try {
      const filters: AssetFilters = {}
      if (searchQuery) filters.search = searchQuery
      if (selectedTags.length > 0) filters.tags = selectedTags
      if (selectedSkills.length > 0) filters.skills = selectedSkills
      if (nameFilter) filters.name = nameFilter

      const [jobs, resumes] = await Promise.all([
        vaultService.listAssets('job_description', activeTab === 'jobs' ? filters : undefined),
        vaultService.listAssets('resume', activeTab === 'resumes' ? filters : undefined),
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

  // Extract unique tags and skills from resume assets
  const availableTags = useMemo(() => {
    const tags = new Set<string>()
    resumeAssets.forEach(asset => {
      const assetTags = asset.metadata?.tags || []
      assetTags.forEach((tag: string) => tags.add(tag))
    })
    return Array.from(tags).sort()
  }, [resumeAssets])

  const availableSkills = useMemo(() => {
    const skills = new Set<string>()
    resumeAssets.forEach(asset => {
      const assetSkills = asset.metadata?.skills || []
      assetSkills.forEach((skill: string | number) => skills.add(String(skill)))
    })
    return Array.from(skills).sort()
  }, [resumeAssets])

  // Apply filters when they change (with debounce for search)
  useEffect(() => {
    const timer = setTimeout(() => {
      loadAssets()
    }, searchQuery ? 300 : 0) // Debounce search input

    return () => clearTimeout(timer)
  }, [searchQuery, selectedTags, selectedSkills, nameFilter, activeTab])

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    setError('')

    try {
      const kind = activeTab === 'jobs' ? 'job_description' : 'resume'
      await Promise.all(
        Array.from(files).map((file) => vaultService.saveAsset(file, kind))
      )
      await loadAssets()
    } catch (err: any) {
      setError(`Failed to save ${activeTab === 'jobs' ? 'job description' : 'resume'} to vault`)
      console.error(err)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleDelete = async (assetId: string) => {
    const assetType = activeTab === 'jobs' ? 'job description' : 'resume'
    if (!confirm(`Are you sure you want to delete this ${assetType}?`)) return

    try {
      await vaultService.deleteAsset(assetId)
      await loadAssets()
    } catch (err: any) {
      setError(`Failed to delete ${assetType}`)
      console.error(err)
    }
  }

  const startEditingTags = (asset: Asset) => {
    setEditingTags(asset.id)
    setTagInput((asset.metadata?.tags || []).join(', '))
  }

  const cancelEditingTags = () => {
    setEditingTags(null)
    setTagInput('')
  }

  const saveTags = async (assetId: string) => {
    try {
      // Parse tags from comma-separated string
      const tags = tagInput
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0)

      await vaultService.updateTags(assetId, tags)
      await loadAssets()
      setEditingTags(null)
      setTagInput('')
    } catch (err: any) {
      setError('Failed to update tags')
      console.error(err)
    }
  }

  const getTags = (asset: Asset): string[] => {
    return asset.metadata?.tags || []
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedTags([])
    setSelectedSkills([])
    setNameFilter('')
  }

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    )
  }

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev =>
      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
    )
  }

  const hasActiveFilters = searchQuery || selectedTags.length > 0 || selectedSkills.length > 0 || nameFilter

  const assets = activeTab === 'jobs' ? jobAssets : resumeAssets

  return (
    <div className="vault-page">
      <div className="vault-page-header">
        <h1>My Saved Files (Vault)</h1>
        <p>Manage your saved job descriptions and resumes</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="vault-tabs">
        <button
          className={`tab-button ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          Job Descriptions ({jobAssets.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'resumes' ? 'active' : ''}`}
          onClick={() => setActiveTab('resumes')}
        >
          Resumes ({resumeAssets.length})
        </button>
      </div>

      {/* Search and Filter Section - Only show for resumes */}
      {activeTab === 'resumes' && (
        <div className="vault-filters">
          <div className="filter-section">
            <div className="search-box">
              <Search size={18} className="search-icon" />
              <input
                type="text"
                placeholder="Search resumes by name, skills, tags, certifications..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              {searchQuery && (
                <button
                  className="clear-search-btn"
                  onClick={() => setSearchQuery('')}
                  title="Clear search"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          </div>

          {availableTags.length > 0 && (
            <div className="filter-section">
              <label className="filter-label">Filter by Tags:</label>
              <div className="filter-chips">
                {availableTags.map(tag => (
                  <button
                    key={tag}
                    className={`filter-chip ${selectedTags.includes(tag) ? 'active' : ''}`}
                    onClick={() => toggleTag(tag)}
                  >
                    <Tag size={12} />
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {availableSkills.length > 0 && (
            <div className="filter-section">
              <label className="filter-label">Filter by Skills:</label>
              <div className="filter-chips">
                {availableSkills.slice(0, 20).map(skill => (
                  <button
                    key={skill}
                    className={`filter-chip ${selectedSkills.includes(skill) ? 'active' : ''}`}
                    onClick={() => toggleSkill(skill)}
                  >
                    {skill}
                  </button>
                ))}
                {availableSkills.length > 20 && (
                  <span className="filter-more">+{availableSkills.length - 20} more</span>
                )}
              </div>
            </div>
          )}

          {hasActiveFilters && (
            <div className="filter-actions">
              <button className="clear-filters-btn" onClick={clearFilters}>
                Clear All Filters
              </button>
            </div>
          )}
        </div>
      )}

      <div className="vault-upload-section">
        <label htmlFor="vault-upload" className="upload-button">
          {uploading ? (
            <>
              <Loader2 className="spinner" size={16} />
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <Upload size={16} />
              <span>Add {activeTab === 'jobs' ? 'job description' : 'resume'} to vault</span>
            </>
          )}
        </label>
        <input
          id="vault-upload"
          type="file"
          accept=".pdf,.docx,.txt"
          multiple={activeTab === 'resumes'}
          onChange={handleUpload}
          disabled={uploading}
          style={{ display: 'none' }}
        />
      </div>

      {loading ? (
        <div className="loading-indicator">
          <Loader2 className="spinner" />
          <span>Loading saved files...</span>
        </div>
      ) : assets.length === 0 ? (
        <div className="empty-state">
          <FileText size={48} />
          <p>No {activeTab === 'jobs' ? 'job descriptions' : 'resumes'} {hasActiveFilters ? 'match your filters' : 'saved yet'}.</p>
          {!hasActiveFilters && (
            <p className="empty-state-hint">Upload files above to get started.</p>
          )}
          {hasActiveFilters && (
            <button className="clear-filters-link" onClick={clearFilters}>
              Clear filters to see all resumes
            </button>
          )}
        </div>
      ) : (
        <div className="vault-assets-grid">
          {assets.map((asset) => (
            <div key={asset.id} className="vault-asset-card">
              <div className="asset-card-header">
                <div className="asset-icon">
                  <FileText size={20} />
                </div>
                <div className="asset-title">
                  <div className="asset-name">{asset.original_name}</div>
                  {activeTab === 'resumes' && asset.metadata?.name && (
                    <div className="asset-candidate-name">{asset.metadata.name}</div>
                  )}
                  <div className="asset-date">{new Date(asset.created_at).toLocaleDateString()}</div>
                </div>
                <button
                  className="delete-button"
                  onClick={() => handleDelete(asset.id)}
                  title="Delete"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              {activeTab === 'resumes' && asset.metadata?.skills && asset.metadata.skills.length > 0 && (
                <div className="asset-skills">
                  <div className="asset-skills-label">Skills:</div>
                  <div className="asset-skills-list">
                    {(asset.metadata.skills as string[]).slice(0, 5).map((skill, idx) => (
                      <span key={idx} className="skill-badge">{String(skill)}</span>
                    ))}
                    {(asset.metadata.skills as string[]).length > 5 && (
                      <span className="skill-more">+{(asset.metadata.skills as string[]).length - 5}</span>
                    )}
                  </div>
                </div>
              )}

              <div className="asset-tags-section">
                {editingTags === asset.id ? (
                  <div className="tags-editor">
                    <input
                      type="text"
                      className="tag-input"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      placeholder="Enter tags separated by commas"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          saveTags(asset.id)
                        } else if (e.key === 'Escape') {
                          cancelEditingTags()
                        }
                      }}
                      autoFocus
                    />
                    <div className="tags-editor-actions">
                      <button
                        className="save-tags-btn"
                        onClick={() => saveTags(asset.id)}
                      >
                        Save
                      </button>
                      <button
                        className="cancel-tags-btn"
                        onClick={cancelEditingTags}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="tags-display">
                    <div className="tags-list">
                      {getTags(asset).length > 0 ? (
                        getTags(asset).map((tag, index) => (
                          <span key={index} className="tag">
                            <Tag size={12} />
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className="no-tags">No tags</span>
                      )}
                    </div>
                    <button
                      className="edit-tags-btn"
                      onClick={() => startEditingTags(asset)}
                      title="Edit tags"
                    >
                      <Edit2 size={14} />
                    </button>
                  </div>
                )}
              </div>

              <div className="asset-actions">
                <a
                  href={`/api/vault/assets/${asset.id}/download`}
                  download
                  className="download-link"
                >
                  Download
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default VaultPage
