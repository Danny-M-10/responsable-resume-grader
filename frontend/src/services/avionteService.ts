/**
 * Avionté API Service
 * Frontend service for interacting with Avionté integration endpoints
 */

const API_BASE = '/api/avionte';

export interface AvionteHealthStatus {
  status: 'healthy' | 'unhealthy' | 'error';
  avionte_configured: boolean;
  error?: string;
}

export interface SyncResult {
  success: boolean;
  candidate_id?: string;
  job_id?: string;
  avionte_talent_id?: string;
  avionte_job_id?: string;
  action: 'created' | 'updated' | 'skipped';
}

export interface BatchSyncRequest {
  sync_type: 'candidates' | 'jobs';
  candidate_ids?: string[];
  job_ids?: string[];
  force_update?: boolean;
}

export interface BatchSyncResult {
  success: boolean;
  total: number;
  succeeded: number;
  failed: number;
  results: SyncResult[];
  errors: Array<{ candidate_id?: string; job_id?: string; error: string }>;
}

export interface TalentData {
  talentId?: string;
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
  [key: string]: any;
}

class AvionteService {
  /**
   * Check Avionté API health
   */
  async checkHealth(): Promise<AvionteHealthStatus> {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Sync a candidate to Avionté
   */
  async syncCandidate(
    candidateId: string,
    forceUpdate: boolean = false
  ): Promise<SyncResult> {
    const response = await fetch(
      `${API_BASE}/sync/candidate/${candidateId}?force_update=${forceUpdate}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to sync candidate: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Sync a job to Avionté
   */
  async syncJob(
    jobId: string,
    forceUpdate: boolean = false
  ): Promise<SyncResult> {
    const response = await fetch(
      `${API_BASE}/sync/job/${jobId}?force_update=${forceUpdate}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to sync job: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get a talent from Avionté
   */
  async getTalent(talentId: string): Promise<TalentData> {
    const response = await fetch(`${API_BASE}/talent/${talentId}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to get talent: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Sync a talent from Avionté to internal system
   */
  async syncTalentFromAvionte(talentId: string): Promise<SyncResult> {
    const response = await fetch(
      `${API_BASE}/sync/from-avionte/talent/${talentId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to sync talent from Avionté: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Batch sync candidates or jobs
   */
  async batchSync(request: BatchSyncRequest): Promise<BatchSyncResult> {
    const response = await fetch(`${API_BASE}/sync/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to batch sync: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Query talents from Avionté
   */
  async queryTalents(
    filters?: Record<string, any>,
    page: number = 1,
    pageSize: number = 50
  ): Promise<{
    talents?: TalentData[];
    total?: number;
    page?: number;
    pageSize?: number;
    totalPages?: number;
  }> {
    const response = await fetch(`${API_BASE}/talent/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filters: filters || {},
        page,
        page_size: pageSize,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to query talents: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get documents (resumes) for a talent
   */
  async getTalentDocuments(talentId: string): Promise<Array<{
    documentId?: string;
    fileName: string;
    fileType?: string;
    fileSize?: number;
    uploadDate?: string;
    documentType?: string;
    url?: string;
  }>> {
    const response = await fetch(`${API_BASE}/talent/${talentId}/documents`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to get documents: ${response.statusText}`);
    }

    const data = await response.json();
    return data.documents || [];
  }

  /**
   * Download a document (resume) from Avionté
   */
  async downloadTalentDocument(
    talentId: string,
    documentId: string
  ): Promise<Blob> {
    const response = await fetch(
      `${API_BASE}/talent/${talentId}/document/${documentId}/download`
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to download document: ${response.statusText}`);
    }

    return response.blob();
  }
}

export const avionteService = new AvionteService();
