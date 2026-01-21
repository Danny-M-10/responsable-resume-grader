import React, { useState } from 'react';
import { avionteService, SyncResult } from '../services/avionteService';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';

interface AvionteSyncButtonProps {
  type: 'candidate' | 'job';
  id: string;
  onSyncComplete?: (result: SyncResult) => void;
  forceUpdate?: boolean;
  className?: string;
}

export const AvionteSyncButton: React.FC<AvionteSyncButtonProps> = ({
  type,
  id,
  onSyncComplete,
  forceUpdate = false,
  className = '',
}) => {
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState<SyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSync = async () => {
    setSyncing(true);
    setError(null);
    setResult(null);

    try {
      let syncResult: SyncResult;
      if (type === 'candidate') {
        syncResult = await avionteService.syncCandidate(id, forceUpdate);
      } else {
        syncResult = await avionteService.syncJob(id, forceUpdate);
      }

      setResult(syncResult);
      if (onSyncComplete) {
        onSyncComplete(syncResult);
      }
    } catch (err: any) {
      setError(err.message || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const getButtonText = () => {
    if (syncing) return 'Syncing...';
    if (result) {
      if (result.action === 'skipped') return 'Already Synced';
      return result.action === 'created' ? 'Synced (Created)' : 'Synced (Updated)';
    }
    return 'Sync to Avionté';
  };

  const getButtonIcon = () => {
    if (syncing) return <RefreshCw className="animate-spin" size={16} />;
    if (result) {
      if (result.action === 'skipped') return <Check size={16} />;
      return <Check size={16} className="text-green-500" />;
    }
    return <RefreshCw size={16} />;
  };

  return (
    <div className={`avionte-sync-button ${className}`}>
      <button
        onClick={handleSync}
        disabled={syncing || (result?.action === 'skipped' && !forceUpdate)}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium
          transition-colors
          ${syncing
            ? 'bg-gray-400 text-white cursor-not-allowed'
            : result?.action === 'skipped' && !forceUpdate
            ? 'bg-gray-200 text-gray-600 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
          }
        `}
      >
        {getButtonIcon()}
        {getButtonText()}
      </button>

      {error && (
        <div className="mt-2 flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {result && result.action !== 'skipped' && (
        <div className="mt-2 text-sm text-green-600">
          {type === 'candidate' ? (
            <span>Avionté Talent ID: {result.avionte_talent_id}</span>
          ) : (
            <span>Avionté Job ID: {result.avionte_job_id}</span>
          )}
        </div>
      )}
    </div>
  );
};
