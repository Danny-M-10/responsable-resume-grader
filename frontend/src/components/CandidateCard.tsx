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
}

interface CandidateCardProps {
  candidate: Candidate
}

const CandidateCard: React.FC<CandidateCardProps> = ({ candidate }) => {
  const [expanded, setExpanded] = useState(false)

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

  return (
    <div className={`candidate-card ${expanded ? 'expanded' : ''}`}>
      <div className="candidate-header" onClick={() => setExpanded(!expanded)}>
        <div className="candidate-rank">
          <span className="rank-number">#{candidate.rank}</span>
        </div>
        <div className="candidate-info">
          <div className="candidate-name">
            {candidate.name}
            {candidate.email && (
              <span className="contact-info">
                <Mail size={14} />
                {candidate.email}
              </span>
            )}
            {candidate.phone && (
              <span className="contact-info">
                <Phone size={14} />
                {candidate.phone}
              </span>
            )}
          </div>
        </div>
        <div className={`score-badge ${scoreClass}`}>
          <div className="score-value">{candidate.score.toFixed(1)}</div>
          <div className="score-label">{scoreLabel}</div>
        </div>
        <div className="expand-icon">
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
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
