
import React, { useCallback, useEffect, useState } from 'react';
import { UploadCloud, FileText, AlertCircle, Folder, Loader2, RefreshCw, AlertTriangle, Info } from 'lucide-react';
import { JobDetails } from '../types';

interface ResumeUploaderProps {
  onUpload: (files: File[]) => void;
  onBack: () => void;
  jobDetails?: JobDetails; 
}

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({ onUpload, onBack, jobDetails }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [driveLoading, setDriveLoading] = useState(false);
  const [driveConnected, setDriveConnected] = useState(false);
  const [driveError, setDriveError] = useState<string | null>(null);

  const isDriveMode = jobDetails?.resumeSource === 'DRIVE';

  useEffect(() => {
    if (isDriveMode && !driveConnected && !driveLoading && !driveError) {
      fetchFromGoogleDrive();
    }
  }, [isDriveMode]);

  const extractFolderId = (url: string): string | null => {
    const folderRegex = /folders\/([a-zA-Z0-9_-]+)|id=([a-zA-Z0-9_-]+)/;
    const match = url.match(folderRegex);
    if (match) {
      return match[1] || match[2];
    }
    if (/^[a-zA-Z0-9_-]+$/.test(url)) {
      return url;
    }
    return null;
  };

  const fetchFromGoogleDrive = async () => {
    const apiKey = process.env.API_KEY;
    const folderUrl = jobDetails?.driveFolderUrl;
    
    if (!folderUrl || !apiKey) {
      setDriveError("Configuration Error: Missing API Key or Folder URL.");
      return;
    }

    const folderId = extractFolderId(folderUrl);
    if (!folderId) {
      setDriveError("Invalid Google Drive Folder URL format.");
      return;
    }

    setDriveLoading(true);
    setDriveError(null);

    try {
      // Note: Using 'q' requires the file to be publicly visible or the API key to have specific Drive scopes.
      const q = `'${folderId}' in parents and trashed = false and (mimeType = 'application/pdf' or mimeType = 'text/plain' or mimeType = 'application/vnd.google-apps.document')`;
      const listUrl = `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&key=${apiKey}&fields=files(id,name,mimeType,size)`;
      
      const listResp = await fetch(listUrl);
      
      if (!listResp.ok) {
        const errData = await listResp.json().catch(() => ({}));
        const errorMessage = errData?.error?.message || listResp.statusText || "Access Denied";
        throw new Error(errorMessage);
      }
      
      const listData = await listResp.json();
      const driveFiles = listData.files || [];
      
      if (driveFiles.length === 0) {
        throw new Error("No compatible files found in folder (looking for PDF, TXT, GDoc).");
      }

      const loadedFiles: File[] = [];
      const filesToProcess = driveFiles.slice(0, 10); // Limit to 10 for safety

      for (const f of filesToProcess) {
        try {
          let downloadUrl = '';
          let fetchMimeType = f.mimeType;

          if (f.mimeType === 'application/vnd.google-apps.document') {
            downloadUrl = `https://www.googleapis.com/drive/v3/files/${f.id}/export?mimeType=application/pdf&key=${apiKey}`;
            fetchMimeType = 'application/pdf';
          } else {
            downloadUrl = `https://www.googleapis.com/drive/v3/files/${f.id}?alt=media&key=${apiKey}`;
          }

          const fileResp = await fetch(downloadUrl);
          if (fileResp.ok) {
            const blob = await fileResp.blob();
            loadedFiles.push(new File([blob], f.name, { type: fetchMimeType }));
          } else {
             console.warn(`Failed to download ${f.name}: ${fileResp.statusText}`);
          }
        } catch (innerErr) {
          console.warn(`Skipping file ${f.name}`, innerErr);
        }
      }
      
      if (loadedFiles.length === 0) {
         throw new Error("Could not download content for any files in this folder. Check permissions.");
      }
      
      setFiles(loadedFiles);
      setDriveConnected(true);

    } catch (e: any) {
      console.error("Drive Connection Error:", e);
      // Display the actual error from Google
      setDriveError(e.message || "An unknown error occurred connecting to Google Drive.");
    } finally {
      setDriveLoading(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = (Array.from(e.dataTransfer.files) as File[]).filter(
      file => file.type === 'application/pdf' || file.type === 'text/plain'
    );
    setFiles(prev => [...prev, ...droppedFiles]);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = (Array.from(e.target.files) as File[]).filter(
         file => file.type === 'application/pdf' || file.type === 'text/plain'
      );
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleStartAnalysis = () => {
    if (files.length > 0) {
      onUpload(files);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow-sm border border-gray-200">
        <div className="bg-gray-50 p-6 border-b border-gray-200 flex justify-between items-center">
          <div>
             <h2 className="text-lg font-bold text-black flex items-center gap-2 uppercase tracking-widest">
              {isDriveMode ? <Folder className="w-5 h-5 text-black" /> : <UploadCloud className="w-5 h-5 text-black" />}
              {isDriveMode ? 'Google Drive Integration' : 'Upload Resumes'}
            </h2>
            <p className="text-gray-500 mt-1 text-xs uppercase tracking-wide">
              {isDriveMode 
                ? `Syncing with Folder: ${jobDetails?.driveFolderUrl?.substring(0, 30)}...` 
                : 'Supported formats: PDF, TXT'}
            </p>
          </div>
        </div>
        
        <div className="p-8">
          
          {isDriveMode ? (
            <div className="text-center py-6">
               {driveLoading ? (
                 <div className="flex flex-col items-center py-8">
                    <Loader2 className="w-12 h-12 text-black animate-spin mb-4" />
                    <h3 className="text-lg font-bold text-black uppercase tracking-widest">Scanning Drive Folder...</h3>
                    <p className="text-gray-500 text-sm mt-2">Locating and downloading compatible files...</p>
                 </div>
               ) : driveError ? (
                 <div className="bg-red-50 border border-red-200 p-6 text-center max-w-lg mx-auto">
                    <div className="flex justify-center mb-3">
                      <AlertTriangle className="w-8 h-8 text-red-600" />
                    </div>
                    <h3 className="text-red-900 font-bold uppercase tracking-wide mb-2">Connection Failed</h3>
                    <p className="text-red-800 text-sm mb-4">{driveError}</p>
                    <button 
                      onClick={fetchFromGoogleDrive}
                      className="bg-white border border-red-200 text-red-900 px-4 py-2 text-xs font-bold uppercase tracking-widest hover:bg-red-50"
                    >
                      Retry Connection
                    </button>
                 </div>
               ) : (
                 <div className="border border-gray-200 bg-gray-50 p-6 max-w-lg mx-auto mb-6">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-black text-white mx-auto mb-3">
                       <Folder className="w-5 h-5" />
                    </div>
                    <h3 className="text-sm font-bold text-black uppercase tracking-wide mb-1">Drive Folder Synced</h3>
                    <p className="text-gray-600 text-xs mb-4">Successfully imported {files.length} files.</p>
                    
                    <button 
                      onClick={fetchFromGoogleDrive}
                      className="text-xs font-bold text-black uppercase tracking-widest flex items-center gap-1 justify-center hover:underline"
                    >
                      <RefreshCw className="w-3 h-3" /> Refresh List
                    </button>
                 </div>
               )}
            </div>
          ) : (
            <div 
              className={`border-2 border-dashed p-12 flex flex-col items-center justify-center transition-all cursor-pointer
                ${isDragging ? 'border-black bg-gray-50' : 'border-gray-300 hover:border-black hover:bg-gray-50'}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('fileInput')?.click()}
            >
              <UploadCloud className={`w-12 h-12 mb-4 ${isDragging ? 'text-black' : 'text-gray-400'}`} />
              <h3 className="text-lg font-bold text-black uppercase tracking-widest">Click to upload or drag and drop</h3>
              <p className="text-gray-500 mt-2">PDF or TXT (Max 10MB)</p>
              <input 
                id="fileInput" 
                type="file" 
                className="hidden" 
                multiple 
                accept=".pdf,.txt" 
                onChange={handleFileChange}
              />
            </div>
          )}

          {files.length > 0 && (
            <div className="mt-8">
              <div className="flex items-center justify-between mb-4 border-b border-gray-200 pb-2">
                <h4 className="text-sm font-bold text-black uppercase tracking-widest">Ready for Analysis ({files.length})</h4>
                <button 
                  onClick={() => setFiles([])}
                  className="text-xs text-red-600 hover:text-red-800 font-medium uppercase tracking-wide"
                >
                  Clear All
                </button>
              </div>
              <div className="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto pr-2">
                {files.map((file, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-gray-50 p-3 border border-gray-100 group hover:border-black transition">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span className="text-sm text-black font-medium truncate">{file.name}</span>
                      <span className="text-xs text-gray-400">({(file.size / 1024).toFixed(0)} KB)</span>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); removeFile(idx); }}
                      className="text-gray-300 hover:text-black p-1"
                    >
                      <AlertCircle className="w-4 h-4 rotate-45" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-8 flex justify-between">
            <button
              onClick={onBack}
              className="px-6 py-3 border border-gray-300 text-black text-xs font-bold uppercase tracking-widest hover:bg-gray-50 transition"
            >
              Back
            </button>
            <button
              onClick={handleStartAnalysis}
              disabled={files.length === 0}
              className="bg-black text-white px-8 py-3 text-xs font-bold uppercase tracking-widest hover:bg-gray-900 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              Start Analysis <RefreshCw className={`w-4 h-4 ${files.length > 0 ? '' : 'hidden'}`} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
