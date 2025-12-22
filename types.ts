export interface JobDetails {
  title: string;
  location: string;
  description: string;
  requiredCerts: string[];
  preferredCerts: string[];
  userEmail: string;
  resumeSource: 'UPLOAD' | 'DRIVE';
  driveFolderUrl?: string;
}

export interface AnalysisResult {
  id: string; // Unique ID for list key
  fileName: string;
  candidateName: string;
  score: number;
  rationale: string;
  eligible: boolean;
  skillsFound: string[];
  resumeUrl?: string; // Simulated Drive Link or Local Object URL
}

export enum AppState {
  INPUT_DETAILS = 'INPUT_DETAILS',
  UPLOADING = 'UPLOADING',
  PROCESSING = 'PROCESSING',
  RESULTS = 'RESULTS',
}

export interface ProcessingStatus {
  total: number;
  completed: number;
  currentFile: string;
}