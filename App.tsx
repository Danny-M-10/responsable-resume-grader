import React, { useState } from 'react';
import { AppState, JobDetails, ProcessingStatus, AnalysisResult } from './types';
import { JobForm } from './components/JobForm';
import { ResumeUploader } from './components/ResumeUploader';
import { ResultsView } from './components/ResultsView';
import { analyzeResume } from './services/geminiService';
import { Loader2 } from 'lucide-react';

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>(AppState.INPUT_DETAILS);
  const [jobDetails, setJobDetails] = useState<JobDetails | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    total: 0,
    completed: 0,
    currentFile: ''
  });

  const handleJobDetailsSubmit = (details: JobDetails) => {
    setJobDetails(details);
    setAppState(AppState.UPLOADING);
  };

  const handleUpload = async (files: File[]) => {
    if (!jobDetails) return;
    
    setAppState(AppState.PROCESSING);
    setProcessingStatus({
      total: files.length,
      completed: 0,
      currentFile: 'Initializing...'
    });

    const results: AnalysisResult[] = [];

    for (const file of files) {
      setProcessingStatus(prev => ({
        ...prev,
        currentFile: file.name
      }));

      // Process sequentially to avoid strict rate limits if any
      // In a real app, we might use Promise.all with a concurrency limit
      const result = await analyzeResume(file, jobDetails);
      results.push(result);

      setProcessingStatus(prev => ({
        ...prev,
        completed: prev.completed + 1
      }));
    }

    setAnalysisResults(results);
    setAppState(AppState.RESULTS);
  };

  const handleReset = () => {
    setAppState(AppState.INPUT_DETAILS);
    setJobDetails(null);
    setAnalysisResults([]);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="bg-black border-b border-gray-800 sticky top-0 z-10 shadow-md">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-none flex items-center justify-center text-black font-bold text-2xl border border-white">R</div>
            <div className="flex flex-col leading-none">
              <span className="font-bold text-xl tracking-widest text-white uppercase">Responsable</span>
              <span className="font-light text-xs tracking-[0.2em] text-gray-400 uppercase">Staffing AI</span>
            </div>
          </div>
          <div className="text-xs text-gray-400 font-medium uppercase tracking-wide hidden md:block">
             Intelligent Recruitment
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8 md:py-12">
        
        {appState === AppState.INPUT_DETAILS && (
          <JobForm onSubmit={handleJobDetailsSubmit} />
        )}

        {appState === AppState.UPLOADING && (
          <ResumeUploader 
            onUpload={handleUpload} 
            onBack={() => setAppState(AppState.INPUT_DETAILS)} 
            jobDetails={jobDetails || undefined}
          />
        )}

        {appState === AppState.PROCESSING && (
          <div className="flex flex-col items-center justify-center py-24">
             <div className="relative">
                <div className="absolute inset-0 bg-gray-200 rounded-full blur-xl opacity-30 animate-pulse"></div>
                <Loader2 className="w-16 h-16 text-black animate-spin relative z-10" />
             </div>
             <h2 className="mt-8 text-2xl font-bold text-black uppercase tracking-wide">Evaluating Candidates</h2>
             <p className="text-gray-600 mt-3 max-w-md text-center font-medium">
               Our AI is analyzing resumes against your specific requirements.
             </p>
             
             <div className="w-full max-w-md mt-10">
               <div className="flex justify-between text-xs font-bold text-black uppercase tracking-wider mb-3">
                 <span>Processing {processingStatus.currentFile}</span>
                 <span>{Math.round((processingStatus.completed / processingStatus.total) * 100)}%</span>
               </div>
               <div className="h-1 bg-gray-200 rounded-none overflow-hidden">
                 <div 
                    className="h-full bg-black transition-all duration-500 ease-out"
                    style={{ width: `${(processingStatus.completed / processingStatus.total) * 100}%` }}
                 ></div>
               </div>
               <div className="mt-3 text-center text-xs text-gray-500 font-medium">
                 {processingStatus.completed} of {processingStatus.total} resumes processed
               </div>
             </div>
          </div>
        )}

        {appState === AppState.RESULTS && jobDetails && (
          <ResultsView 
            results={analysisResults} 
            jobDetails={jobDetails} 
            onReset={handleReset}
          />
        )}

      </main>
    </div>
  );
};

export default App;