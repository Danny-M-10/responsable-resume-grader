import React from 'react';
import { AnalysisResult, JobDetails } from '../types';
import { CheckCircle, AlertTriangle, Download, ExternalLink, Mail } from 'lucide-react';

interface ResultsViewProps {
  results: AnalysisResult[];
  jobDetails: JobDetails;
  onReset: () => void;
}

export const ResultsView: React.FC<ResultsViewProps> = ({ results, jobDetails, onReset }) => {
  const sortedResults = [...results].sort((a, b) => {
    if (a.eligible !== b.eligible) return a.eligible ? -1 : 1;
    return b.score - a.score;
  });

  const eligibleCount = sortedResults.filter(r => r.eligible).length;

  const downloadJson = () => {
    const payload = {
      job_title: jobDetails.title,
      location: jobDetails.location,
      summary: `Ranked ${eligibleCount} eligible candidates out of ${results.length} total applicants.`,
      candidates: sortedResults.map((r, i) => ({
        rank: i + 1,
        name: r.candidateName,
        score: r.score,
        rationale: r.rationale,
        resume_url: r.resumeUrl
      }))
    };
    
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `responsable-staffing-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const sendEmailReport = () => {
      alert(`Report sent to ${jobDetails.userEmail}! (Simulation)`);
  };

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="flex items-center justify-between mb-10 pb-6 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-black uppercase tracking-widest">Analysis Report</h1>
          <p className="text-gray-500 mt-1 text-xs uppercase tracking-wide">
            Role: <span className="text-black font-bold">{jobDetails.title}</span> • 
            Evaluated: <span className="text-black font-bold">{results.length}</span>
          </p>
        </div>
        <div className="flex gap-3">
           <button 
            onClick={downloadJson}
            className="flex items-center gap-2 px-5 py-2 bg-white border border-gray-300 text-black hover:bg-gray-50 text-xs font-bold uppercase tracking-wide transition"
          >
            <Download className="w-4 h-4" />
            Export JSON
          </button>
          <button 
            onClick={sendEmailReport}
            className="flex items-center gap-2 px-5 py-2 bg-black text-white hover:bg-gray-800 text-xs font-bold uppercase tracking-wide transition"
          >
            <Mail className="w-4 h-4" />
            Email Report
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {sortedResults.map((candidate, index) => (
          <div 
            key={candidate.id}
            className={`bg-white p-6 border transition-all
              ${candidate.eligible 
                ? 'border-gray-200 hover:border-black' 
                : 'border-gray-100 bg-gray-50 opacity-80'}`}
          >
            <div className="flex flex-col md:flex-row gap-8">
              
              {/* Score Badge */}
              <div className="flex-shrink-0 pt-1">
                <div className={`w-16 h-16 flex flex-col items-center justify-center border-2 
                  ${candidate.eligible 
                    ? 'border-black text-black' 
                    : 'border-gray-300 text-gray-400'}`}
                >
                  <span className="text-2xl font-bold leading-none">{candidate.score}</span>
                  <span className="text-[9px] font-bold uppercase tracking-widest mt-1">Score</span>
                </div>
                <div className="mt-2 text-center font-mono text-xs text-gray-400">Rank #{index + 1}</div>
              </div>

              {/* Content */}
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-black uppercase tracking-wide">{candidate.candidateName}</h3>
                    <div className="flex items-center gap-3 mt-2 text-xs uppercase tracking-wider font-medium">
                       {candidate.eligible ? (
                         <span className="flex items-center gap-1 text-black">
                           <CheckCircle className="w-4 h-4" /> Eligible
                         </span>
                       ) : (
                         <span className="flex items-center gap-1 text-gray-400">
                           <AlertTriangle className="w-4 h-4" /> Missing Requirements
                         </span>
                       )}
                       <span className="text-gray-300">|</span>
                       <a 
                          href={candidate.resumeUrl} 
                          target="_blank" 
                          rel="noreferrer"
                          className="text-gray-600 hover:text-black flex items-center gap-1 transition"
                       >
                          View Resume <ExternalLink className="w-3 h-3" />
                       </a>
                    </div>
                  </div>
                </div>

                <div className="mt-4 border-l-2 border-gray-200 pl-4">
                  <p className="text-sm text-gray-800 leading-relaxed">
                    {candidate.rationale}
                  </p>
                </div>

                {candidate.skillsFound && candidate.skillsFound.length > 0 && (
                  <div className="mt-5 flex flex-wrap gap-2">
                    {candidate.skillsFound.slice(0, 6).map((skill, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-black text-[10px] font-bold uppercase tracking-wide border border-gray-200">
                        {skill}
                      </span>
                    ))}
                    {candidate.skillsFound.length > 6 && (
                       <span className="px-2 py-1 text-gray-400 text-[10px] font-bold uppercase tracking-wide border border-transparent">
                        +{candidate.skillsFound.length - 6} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-12 text-center">
         <button onClick={onReset} className="text-gray-400 hover:text-black text-xs font-bold uppercase tracking-widest border-b border-transparent hover:border-black transition pb-1">
            Start New Analysis
         </button>
      </div>

      <div className="mt-16 pt-8 border-t border-gray-200 text-[10px] text-gray-400 uppercase tracking-widest space-y-2">
        <p className="font-bold text-black">Trusted Normalization Sources:</p>
        <ul className="flex gap-4">
          <li>O*NET OnLine</li>
          <li>NIST NICE Framework</li>
          <li>Standard Vendor Certifications</li>
        </ul>
      </div>
    </div>
  );
};
