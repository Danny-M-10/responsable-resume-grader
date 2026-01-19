import React from 'react'
import './LoadingSkeleton.css'

interface SkeletonProps {
  width?: string | number
  height?: string | number
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height,
  className = '',
  variant = 'rectangular',
}) => {
  const style: React.CSSProperties = {}
  if (width) style.width = typeof width === 'number' ? `${width}px` : width
  if (height) style.height = typeof height === 'number' ? `${height}px` : height

  return (
    <div
      className={`skeleton skeleton-${variant} ${className}`}
      style={style}
      aria-label="Loading"
    />
  )
}

export const CandidateCardSkeleton: React.FC = () => {
  return (
    <div className="candidate-card-skeleton">
      <div className="skeleton-card-header">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="skeleton-card-info">
          <Skeleton width="60%" height={20} />
          <Skeleton width="40%" height={16} className="skeleton-margin-top" />
        </div>
        <Skeleton width={80} height={60} />
      </div>
      <div className="skeleton-card-content">
        <Skeleton width="100%" height={16} />
        <Skeleton width="90%" height={16} className="skeleton-margin-top" />
        <Skeleton width="80%" height={16} className="skeleton-margin-top" />
      </div>
    </div>
  )
}

export const AnalysisItemSkeleton: React.FC = () => {
  return (
    <div className="analysis-item-skeleton">
      <div className="skeleton-analysis-header">
        <Skeleton width="40%" height={20} />
        <Skeleton width={100} height={24} />
      </div>
      <Skeleton width="60%" height={16} className="skeleton-margin-top" />
      <Skeleton width="80%" height={16} className="skeleton-margin-top" />
    </div>
  )
}

export const AssetCardSkeleton: React.FC = () => {
  return (
    <div className="asset-card-skeleton">
      <Skeleton width={40} height={40} />
      <div className="skeleton-asset-info">
        <Skeleton width="70%" height={18} />
        <Skeleton width="50%" height={14} className="skeleton-margin-top" />
      </div>
      <Skeleton width={24} height={24} />
    </div>
  )
}

export const FormSectionSkeleton: React.FC = () => {
  return (
    <div className="form-section-skeleton">
      <Skeleton width="30%" height={24} />
      <Skeleton width="100%" height={40} className="skeleton-margin-top" />
      <Skeleton width="100%" height={40} className="skeleton-margin-top" />
      <Skeleton width="80%" height={120} className="skeleton-margin-top" />
    </div>
  )
}
