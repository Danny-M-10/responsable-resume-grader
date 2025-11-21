import React, { useState } from 'react';
import { JobDetails } from '../types';
import { Plus, X, Briefcase, MapPin, ArrowRight, Globe } from 'lucide-react';

interface JobFormProps {
  onSubmit: (details: JobDetails) => void;
}

export const JobForm: React.FC<JobFormProps> = ({ onSubmit }) => {
  // Default values cleared to show placeholders
  const [title, setTitle] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  
  const [reqCerts, setReqCerts] = useState<string[]>([]);
  const [prefCerts, setPrefCerts] = useState<string[]>([]);
  const [userEmail, setUserEmail] = useState('hiring@responsablestaffing.com');
  
  // New state for source selection
  const [resumeSource, setResumeSource] = useState<'UPLOAD' | 'DRIVE'>('UPLOAD');
  const [driveFolderUrl, setDriveFolderUrl] = useState('');

  const [newReqCert, setNewReqCert] = useState('');
  const [newPrefCert, setNewPrefCert] = useState('');

  const addReqCert = () => {
    if (newReqCert.trim()) {
      setReqCerts([...reqCerts, newReqCert.trim()]);
      setNewReqCert('');
    }
  };

  const removeReqCert = (index: number) => {
    setReqCerts(reqCerts.filter((_, i) => i !== index));
  };

  const addPrefCert = () => {
    if (newPrefCert.trim()) {
      setPrefCerts([...prefCerts, newPrefCert.trim()]);
      setNewPrefCert('');
    }
  };

  const removePrefCert = (index: number) => {
    setPrefCerts(prefCerts.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      title,
      location,
      description,
      requiredCerts: reqCerts,
      preferredCerts: prefCerts,
      userEmail,
      resumeSource,
      driveFolderUrl: resumeSource === 'DRIVE' ? driveFolderUrl : undefined
    });
  };

  return (
    <div className="max-w-4xl mx-auto bg-white shadow-sm border border-gray-200">
      <div className="bg-black p-6 border-b border-gray-200">
        <h2 className="text-xl font-bold text-white flex items-center gap-3 uppercase tracking-widest">
          <Briefcase className="w-5 h-5 text-white" />
          Role Definition
        </h2>
        <p className="text-gray-400 mt-2 text-xs uppercase tracking-wide">Configure evaluation criteria</p>
      </div>
      
      <form onSubmit={handleSubmit} className="p-8 space-y-10">
        
        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <label className="block text-xs font-bold text-black uppercase tracking-widest mb-3">Job Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 rounded-none bg-gray-50 border-b-2 border-gray-200 focus:border-black outline-none transition text-black placeholder-gray-500 font-medium"
              placeholder="e.g. Site Safety Manager"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-black uppercase tracking-widest mb-3">Location</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-none bg-gray-50 border-b-2 border-gray-200 focus:border-black outline-none transition text-black placeholder-gray-500 font-medium"
                placeholder="e.g. Baton Rouge, LA"
                required
              />
            </div>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-bold text-black uppercase tracking-widest mb-3">Job Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-4 py-3 rounded-none bg-gray-50 border-b-2 border-gray-200 focus:border-black outline-none transition h-48 resize-y font-mono text-sm text-black placeholder-gray-500"
            placeholder={`We are seeking a Safety Coordinator for an industrial turnaround.

Responsibilities:
- Conduct daily safety audits and toolbox talks.
- Ensure compliance with OSHA 1910/1926 standards.
- Manage confined space entry permits.

Requirements:
- 5+ years of field safety experience.
- Experience with hot work and LOTO procedures.`}
            required
          />
        </div>

        {/* Certifications */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Required */}
          <div className="bg-white p-0">
            <label className="block text-xs font-bold text-black uppercase tracking-widest mb-3 border-b border-gray-200 pb-2">Required Certifications</label>
            <div className="flex gap-0 mb-4 border border-gray-300">
              <input
                type="text"
                value={newReqCert}
                onChange={(e) => setNewReqCert(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addReqCert())}
                className="flex-1 px-4 py-2 bg-white outline-none text-sm text-black placeholder-gray-500"
                placeholder="e.g. CSP (Certified Safety Professional)"
              />
              <button
                type="button"
                onClick={addReqCert}
                className="bg-black text-white px-4 py-2 hover:bg-gray-800 transition"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <ul className="space-y-2">
              {reqCerts.map((cert, idx) => (
                <li key={idx} className="flex items-center justify-between bg-gray-50 px-3 py-2 text-sm text-black font-medium border-l-4 border-black">
                  <span>{cert}</span>
                  <button type="button" onClick={() => removeReqCert(idx)} className="text-gray-400 hover:text-black">
                    <X className="w-4 h-4" />
                  </button>
                </li>
              ))}
              {reqCerts.length === 0 && <li className="text-xs text-gray-400 italic">No required certifications added.</li>}
            </ul>
          </div>

          {/* Preferred */}
          <div className="bg-white p-0">
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-200 pb-2">Preferred Certifications</label>
            <div className="flex gap-0 mb-4 border border-gray-300">
              <input
                type="text"
                value={newPrefCert}
                onChange={(e) => setNewPrefCert(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addPrefCert())}
                className="flex-1 px-4 py-2 bg-white outline-none text-sm text-black placeholder-gray-500"
                placeholder="e.g. OSHA 30 Construction"
              />
              <button
                type="button"
                onClick={addPrefCert}
                className="bg-gray-200 text-black px-4 py-2 hover:bg-gray-300 transition"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <ul className="space-y-2">
              {prefCerts.map((cert, idx) => (
                <li key={idx} className="flex items-center justify-between bg-gray-50 px-3 py-2 text-sm text-gray-700 border-l-4 border-gray-300">
                  <span>{cert}</span>
                  <button type="button" onClick={() => removePrefCert(idx)} className="text-gray-400 hover:text-black">
                    <X className="w-4 h-4" />
                  </button>
                </li>
              ))}
              {prefCerts.length === 0 && <li className="text-xs text-gray-400 italic">No preferred certifications added.</li>}
            </ul>
          </div>
        </div>

        {/* Resume Source */}
        <div className="pt-6 border-t border-gray-100">
           <label className="block text-xs font-bold text-black uppercase tracking-widest mb-4">Resume Source</label>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div 
               onClick={() => setResumeSource('UPLOAD')}
               className={`cursor-pointer border-2 p-5 flex items-center gap-4 transition-all ${resumeSource === 'UPLOAD' ? 'border-black bg-gray-50' : 'border-gray-200 hover:border-gray-300'}`}
             >
                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${resumeSource === 'UPLOAD' ? 'border-black' : 'border-gray-300'}`}>
                  {resumeSource === 'UPLOAD' && <div className="w-2 h-2 bg-black rounded-full" />}
                </div>
                <div>
                  <span className="block font-bold text-sm text-black uppercase">Manual Upload</span>
                  <span className="text-xs text-gray-500">Drag & drop PDF/TXT files</span>
                </div>
             </div>

             <div 
               onClick={() => setResumeSource('DRIVE')}
               className={`cursor-pointer border-2 p-5 flex items-center gap-4 transition-all ${resumeSource === 'DRIVE' ? 'border-black bg-gray-50' : 'border-gray-200 hover:border-gray-300'}`}
             >
                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${resumeSource === 'DRIVE' ? 'border-black' : 'border-gray-300'}`}>
                  {resumeSource === 'DRIVE' && <div className="w-2 h-2 bg-black rounded-full" />}
                </div>
                <div>
                  <span className="block font-bold text-sm text-black uppercase">Google Drive</span>
                  <span className="text-xs text-gray-500">Connect a shared folder</span>
                </div>
             </div>
           </div>

           {resumeSource === 'DRIVE' && (
             <div className="mt-6 animate-in fade-in slide-in-from-top-2">
                <label className="block text-xs font-bold text-black uppercase tracking-widest mb-2">
                  Google Drive Folder Link
                </label>
                <div className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-gray-400" />
                  <input 
                    type="text" 
                    value={driveFolderUrl}
                    onChange={(e) => setDriveFolderUrl(e.target.value)}
                    placeholder="https://drive.google.com/drive/folders/..."
                    className="flex-1 px-4 py-3 bg-gray-50 border-b-2 border-gray-200 focus:border-black outline-none text-sm"
                  />
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  <span className="font-bold">Note:</span> The folder must be set to <span className="text-black font-medium">"Anyone with the link"</span> for this demo to access it without OAuth.
                </p>
             </div>
           )}
        </div>

        <div className="pt-6 flex justify-end">
          <button
            type="submit"
            className="bg-black text-white px-8 py-4 text-sm font-bold uppercase tracking-widest hover:bg-gray-900 transition flex items-center gap-3"
          >
            Next: Upload Resumes <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
