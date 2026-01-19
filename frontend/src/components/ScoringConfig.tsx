import React, { useState, useEffect } from 'react'
import { templateService, Template } from '../services/templateService'
import { Loader2, AlertCircle } from 'lucide-react'
import './ScoringConfig.css'

export interface ScoringWeights {
  experience_level: number
  job_title_match: number
  required_skills: number
  transferrable_skills: number
  location: number
  preferred_skills: number
  certifications_education: number
}

export interface ScoringConfigData {
  industryTemplate: string
  customWeights?: ScoringWeights
  dealbreakers: string[]
  biasReductionEnabled: boolean
}

interface ScoringConfigProps {
  value: ScoringConfigData
  onChange: (config: ScoringConfigData) => void
  disabled?: boolean
}

const DEFAULT_WEIGHTS: ScoringWeights = {
  experience_level: 0.25,
  job_title_match: 0.20,
  required_skills: 0.18,
  transferrable_skills: 0.15,
  location: 0.10,
  preferred_skills: 0.07,
  certifications_education: 0.05,
}

const WEIGHT_LABELS: Record<keyof ScoringWeights, string> = {
  experience_level: 'Experience Level',
  job_title_match: 'Job Title Match',
  required_skills: 'Required Skills',
  transferrable_skills: 'Transferrable Skills',
  location: 'Location',
  preferred_skills: 'Preferred Skills',
  certifications_education: 'Certifications/Education',
}

const ScoringConfig: React.FC<ScoringConfigProps> = ({ value, onChange, disabled = false }) => {
  const [templates, setTemplates] = useState<Record<string, Template>>({})
  const [loading, setLoading] = useState(true)
  const [useCustomWeights, setUseCustomWeights] = useState(false)
  const [dealbreakerInput, setDealbreakerInput] = useState('')
  const [weightsError, setWeightsError] = useState<string>('')

  useEffect(() => {
    loadTemplates()
  }, [])

  useEffect(() => {
    if (value.industryTemplate && templates[value.industryTemplate]) {
      const template = templates[value.industryTemplate]
      if (!useCustomWeights && !value.customWeights) {
        // Auto-apply template weights
        onChange({
          ...value,
          customWeights: template.weights as unknown as ScoringWeights,
        })
      }
    }
  }, [value.industryTemplate, templates, useCustomWeights])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      const loadedTemplates = await templateService.listTemplates()
      if (loadedTemplates && Object.keys(loadedTemplates).length > 0) {
        setTemplates(loadedTemplates)
        // Ensure a default template is selected if none is set
        if (!value.industryTemplate && Object.keys(loadedTemplates).includes('general')) {
          handleTemplateChange('general')
        }
      } else {
        console.error('Templates API returned empty result')
      }
    } catch (err: any) {
      console.error('Failed to load templates:', err)
      console.error('Error details:', err.response?.data || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleTemplateChange = (templateName: string) => {
    const template = templates[templateName]
    const newConfig: ScoringConfigData = {
      ...value,
      industryTemplate: templateName,
    }

    if (template && !useCustomWeights) {
      newConfig.customWeights = template.weights as unknown as ScoringWeights
    }

    onChange(newConfig)
    setWeightsError('')
  }

  const handleWeightChange = (key: keyof ScoringWeights, newValue: number) => {
    if (!value.customWeights) return

    const updated = {
      ...value.customWeights,
      [key]: newValue,
    }

    // Validate sum
    const total = Object.values(updated).reduce((sum, val) => sum + val, 0)
    if (Math.abs(total - 1.0) > 0.01) {
      setWeightsError(`Weights sum to ${(total * 100).toFixed(1)}% (must equal 100%)`)
    } else {
      setWeightsError('')
    }

    onChange({
      ...value,
      customWeights: updated,
    })
  }

  const handleUseCustomWeightsToggle = (enabled: boolean) => {
    setUseCustomWeights(enabled)
    if (enabled && !value.customWeights) {
      // Initialize with current template weights or defaults
      const template = templates[value.industryTemplate]
      onChange({
        ...value,
        customWeights: (template?.weights as unknown as ScoringWeights) || DEFAULT_WEIGHTS,
      })
    } else if (!enabled && value.customWeights) {
      onChange({
        ...value,
        customWeights: undefined,
      })
    }
  }

  const handleAddDealbreaker = () => {
    if (dealbreakerInput.trim()) {
      onChange({
        ...value,
        dealbreakers: [...value.dealbreakers, dealbreakerInput.trim()],
      })
      setDealbreakerInput('')
    }
  }

  const handleRemoveDealbreaker = (index: number) => {
    onChange({
      ...value,
      dealbreakers: value.dealbreakers.filter((_, i) => i !== index),
    })
  }

  const handleBiasReductionToggle = () => {
    onChange({
      ...value,
      biasReductionEnabled: !value.biasReductionEnabled,
    })
  }

  const currentTemplate = templates[value.industryTemplate]
  const displayWeights = useCustomWeights && value.customWeights
    ? value.customWeights
    : (currentTemplate?.weights as unknown as ScoringWeights) || DEFAULT_WEIGHTS

  const weightsSum = Object.values(displayWeights).reduce((sum, val) => sum + val, 0)

  return (
    <div className={`scoring-config ${disabled ? 'disabled' : ''}`}>
      <div className="scoring-config-section">
        <h3>Scoring Configuration</h3>

        {loading ? (
          <div className="loading-indicator">
            <Loader2 className="spinner" />
            <span>Loading templates...</span>
          </div>
        ) : (
          <>
            {/* Industry Template Selection */}
            <div className="template-selector">
              <label htmlFor="industry-template">
                <strong>Industry Template:</strong>
              </label>
              <select
                id="industry-template"
                value={value.industryTemplate || ''}
                onChange={(e) => handleTemplateChange(e.target.value)}
                disabled={Object.keys(templates).length === 0 || disabled}
              >
                {Object.keys(templates).length === 0 ? (
                  <option value="">Loading templates...</option>
                ) : (
                  Object.entries(templates).map(([name, template]) => (
                    <option key={name} value={name}>
                      {template.name} - {template.description}
                    </option>
                  ))
                )}
              </select>
              {currentTemplate && (
                <p className="template-description">{currentTemplate.description}</p>
              )}
            </div>

            {/* Custom Weights Toggle */}
            <div className="custom-weights-toggle">
              <label>
                <input
                  type="checkbox"
                  checked={useCustomWeights}
                  onChange={(e) => handleUseCustomWeightsToggle(e.target.checked)}
                  disabled={disabled}
                />
                <span>Use Custom Scoring Weights</span>
              </label>
            </div>

            {/* Weights Display/Editor */}
            {(useCustomWeights || currentTemplate) && (
              <div className="weights-section">
                <h4>Scoring Weights</h4>
                {useCustomWeights && (
                  <p className="weights-help">
                    Adjust the weights below. They must sum to exactly 100%.
                  </p>
                )}

                {Object.entries(displayWeights).map(([key, weight]) => (
                  <div key={key} className="weight-item">
                    <label>{WEIGHT_LABELS[key as keyof ScoringWeights]}</label>
                    <div className="weight-controls">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        step="1"
                        value={weight * 100}
                        onChange={(e) =>
                          handleWeightChange(
                            key as keyof ScoringWeights,
                            parseFloat(e.target.value) / 100
                          )
                        }
                        disabled={!useCustomWeights || disabled}
                      />
                      <span className="weight-value">
                        {useCustomWeights ? (
                          <input
                            type="number"
                            min="0"
                            max="100"
                            step="1"
                            value={(weight * 100).toFixed(0)}
                            onChange={(e) =>
                              handleWeightChange(
                                key as keyof ScoringWeights,
                                parseFloat(e.target.value || '0') / 100
                              )
                            }
                            disabled={disabled}
                          />
                        ) : (
                          `${(weight * 100).toFixed(1)}%`
                        )}
                      </span>
                    </div>
                  </div>
                ))}

                <div className="weights-summary">
                  <strong>Total: {(weightsSum * 100).toFixed(1)}%</strong>
                  {Math.abs(weightsSum - 1.0) > 0.01 && useCustomWeights && (
                    <span className="error-text">
                      {' '}
                      - Must equal 100%
                    </span>
                  )}
                </div>

                {weightsError && (
                  <div className="error-message">
                    <AlertCircle size={16} />
                    {weightsError}
                  </div>
                )}
              </div>
            )}

            {/* Dealbreakers */}
            <div className="dealbreakers-section">
              <h4>Dealbreakers</h4>
              <p className="section-help">
                Candidates missing these requirements will be automatically disqualified.
              </p>
              <div className="dealbreaker-input">
                <input
                  type="text"
                  placeholder="e.g., Must have valid driver's license"
                  value={dealbreakerInput}
                  onChange={(e) => setDealbreakerInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddDealbreaker()
                    }
                  }}
                  disabled={disabled}
                />
                <button
                  type="button"
                  onClick={handleAddDealbreaker}
                  className="add-btn"
                  disabled={disabled}
                >
                  Add
                </button>
              </div>
              {value.dealbreakers.length > 0 && (
                <ul className="dealbreakers-list">
                  {value.dealbreakers.map((dealbreaker, index) => (
                    <li key={index} className="dealbreaker-item">
                      <span>{dealbreaker}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveDealbreaker(index)}
                        className="remove-btn"
                        disabled={disabled}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Bias Reduction */}
            <div className="bias-reduction-section">
              <label className="bias-toggle">
                <input
                  type="checkbox"
                  checked={value.biasReductionEnabled}
                  onChange={handleBiasReductionToggle}
                  disabled={disabled}
                />
                <span>
                  <strong>Enable Bias Reduction</strong>
                  <small>
                    Blind screening mode - hides candidate names and personal information
                    during scoring
                  </small>
                </span>
              </label>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default ScoringConfig
