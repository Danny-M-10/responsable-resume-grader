import React, { useState } from 'react'
import { ChevronDown, ChevronUp, Mail, Phone, Award, Star } from 'lucide-react'
import './CandidateCard.css'

export interface Candidate {
  id: string
  name: string
  email?: string
  phone?: string
  score: number
  certifications?: Array<{ name: string; category: string }>
  rationale: string
  rank: number
  tieStatus?: 'tie' | 'near-tie' | null
  componentScores?: Record<string, number>
  calibrationApplied?: boolean
  calibrationFactor?: number
}

interface CandidateCardProps {
  candidate: Candidate
}

const CandidateCard: React.FC<CandidateCardProps> = ({ candidate }) => {
  const [expanded, setExpanded] = useState(false)

  const componentScoreLabels: Record<string, string> = {
    experience_level: 'Experience level',
    job_title_match: 'Job title match',
    required_skills: 'Required skills',
    transferrable_skills: 'Transferable skills',
    location: 'Location',
    preferred_skills: 'Preferred skills',
    certifications_education: 'Certifications / education',
  }

  const getScoreColor = (score: number): string => {
    if (score >= 8.0) return 'excellent' // Green
    if (score >= 6.5) return 'good' // Blue
    if (score >= 5.0) return 'fair' // Yellow
    return 'poor' // Red
  }

  const getScoreLabel = (score: number): string => {
    if (score >= 8.0) return 'Excellent'
    if (score >= 6.5) return 'Good'
    if (score >= 5.0) return 'Fair'
    return 'Poor'
  }

  const scoreClass = getScoreColor(candidate.score)
  const scoreLabel = getScoreLabel(candidate.score)
  const tieLabel = candidate.tieStatus === 'tie' ? 'Tied' : candidate.tieStatus === 'near-tie' ? 'Near tie' : null
  const scoreBreakdownEntries = Object.entries(candidate.componentScores || {})
    .filter(([, value]) => typeof value === 'number' && !Number.isNaN(value))
    .map(([key, value]) => ({
      key,
      label: componentScoreLabels[key] || key.replace(/_/g, ' '),
      value,
    }))

  return (
    <div className={`candidate-card ${expanded ? 'expanded' : ''}`}>
      <div 
        className="candidate-header" 
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setExpanded(!expanded)
          }
        }}
        aria-label={`${expanded ? 'Collapse' : 'Expand'} details for ${candidate.name}`}
        aria-expanded={expanded}
      >
        <div className="candidate-rank">
          <span className="rank-number">#{candidate.rank}</span>
        </div>
        <div className="candidate-info">
          <div className="candidate-name">
            {candidate.name}
            {candidate.email && (
              <span className="contact-info">
                <Mail size={14} aria-hidden="true" />
                {candidate.email}
              </span>
            )}
            {candidate.phone && (
              <span className="contact-info">
                <Phone size={14} aria-hidden="true" />
                {candidate.phone}
              </span>
            )}
          </div>
        </div>
        <div className={`score-badge ${scoreClass}`}>
          <div className="score-value">{candidate.score.toFixed(2)}</div>
          <div className="score-label">{scoreLabel}</div>
          {tieLabel && <div className="tie-indicator">{tieLabel}</div>}
        </div>
        <div className="expand-icon">
          {expanded ? <ChevronUp size={20} aria-hidden="true" /> : <ChevronDown size={20} aria-hidden="true" />}
        </div>
      </div>

      {expanded && (
        <div className="candidate-details">
          {/* Certifications */}
          {candidate.certifications && candidate.certifications.length > 0 && (
            <div className="certifications-section">
              <h4>
                <Award size={16} />
                Certifications
              </h4>
              <div className="certifications-list">
                {candidate.certifications.map((cert, idx) => (
                  <div
                    key={idx}
                    className={`cert-badge ${cert.category === 'must-have' ? 'required' : 'bonus'}`}
                  >
                    {cert.name}
                    <span className="cert-category">
                      ({cert.category === 'must-have' ? 'Required' : 'Bonus'})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Score breakdown */}
          <div className="score-breakdown-section">
            <h4>
              <Star size={16} />
              Score Breakdown
            </h4>
            <div className="score-breakdown-card">
              <div className="score-breakdown-row score-breakdown-total">
                <span>Final weighted score</span>
                <strong>{candidate.score.toFixed(2)}</strong>
              </div>
              {scoreBreakdownEntries.map((entry) => (
                <div key={entry.key} className="score-breakdown-row">
                  <span>{entry.label}</span>
                  <strong>{entry.value.toFixed(1)}/10</strong>
                </div>
              ))}
              {candidate.calibrationApplied && (
                <div className="score-breakdown-note">
                  Final score adjusted for score distribution.
                </div>
              )}
            </div>
          </div>

          {/* Rationale */}
          <div className="rationale-section">
            <h4>
              <Star size={16} />
              Scoring Rationale
            </h4>
            <div className="rationale-text">{candidate.rationale}</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CandidateCard
