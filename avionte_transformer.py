"""
Avionté Data Transformer
Converts Avionté API data to application format
"""

import os
import tempfile
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from models import JobDetails, Certification
from avionte_client import AvionteClient

logger = logging.getLogger(__name__)


class AvionteTransformer:
    """Transform Avionté API data to application format"""
    
    def __init__(self, client: Optional[AvionteClient] = None):
        """
        Initialize transformer
        
        Args:
            client: Avionté API client instance (creates new one if not provided)
        """
        self.client = client or AvionteClient()
    
    def transform_talent_to_candidate(self, talent_data: Dict[str, Any], 
                                     download_resume: bool = True) -> Dict[str, Any]:
        """
        Transform Avionté talent data to candidate format expected by the application.
        
        Args:
            talent_data: Raw talent data from Avionté API
            download_resume: Whether to download and save resume documents
            
        Returns:
            Candidate dictionary in application format
        """
        # Extract basic information
        talent_id = talent_data.get('id') or talent_data.get('talentId') or talent_data.get('applicantId', '')
        first_name = talent_data.get('firstName') or talent_data.get('first_name') or ''
        last_name = talent_data.get('lastName') or talent_data.get('last_name') or ''
        name = f"{first_name} {last_name}".strip() or talent_data.get('name', 'Unknown')
        
        # Contact information
        email = talent_data.get('email') or talent_data.get('emailAddress', '')
        phone = talent_data.get('phone') or talent_data.get('phoneNumber') or talent_data.get('mobilePhone', '')
        
        # Location
        location = ''
        if 'location' in talent_data:
            location = talent_data['location']
        elif 'address' in talent_data:
            addr = talent_data['address']
            if isinstance(addr, dict):
                city = addr.get('city', '')
                state = addr.get('state', '')
                location = f"{city}, {state}".strip(', ')
            else:
                location = str(addr)
        
        # Skills
        skills = []
        if 'skills' in talent_data:
            if isinstance(talent_data['skills'], list):
                skills = [s.get('name', s) if isinstance(s, dict) else str(s) for s in talent_data['skills']]
        elif 'skillNames' in talent_data:
            skills = talent_data['skillNames'] if isinstance(talent_data['skillNames'], list) else []
        
        # Certifications
        certifications = []
        if 'certifications' in talent_data:
            certs = talent_data['certifications']
            if isinstance(certs, list):
                for cert in certs:
                    if isinstance(cert, dict):
                        cert_name = cert.get('name') or cert.get('certificationName') or cert.get('title', '')
                        if cert_name:
                            certifications.append(cert_name)
                    else:
                        certifications.append(str(cert))
        elif 'certificationNames' in talent_data:
            certifications = talent_data['certificationNames'] if isinstance(talent_data['certificationNames'], list) else []
        
        # Work history
        work_history = []
        if 'workHistory' in talent_data:
            work_history = talent_data['workHistory']
        elif 'workExperience' in talent_data:
            work_history = talent_data['workExperience']
        elif 'employmentHistory' in talent_data:
            work_history = talent_data['employmentHistory']
        
        # Education
        education = []
        if 'education' in talent_data:
            education = talent_data['education']
        elif 'educationHistory' in talent_data:
            education = talent_data['educationHistory']
        
        # Years of experience
        years_of_experience = 0
        if 'yearsOfExperience' in talent_data:
            years_of_experience = talent_data['yearsOfExperience']
        elif 'experienceYears' in talent_data:
            years_of_experience = talent_data['experienceYears']
        elif work_history:
            # Try to calculate from work history
            try:
                # This is a simplified calculation - real implementation would parse dates
                years_of_experience = len(work_history) * 2  # Rough estimate
            except:
                pass
        
        # Resume file path (if we download it)
        resume_file_path = None
        if download_resume and talent_id:
            resume_file_path = self._download_talent_resume(talent_id)
        
        # Build candidate dictionary in expected format
        candidate = {
            'name': name,
            'email': email,
            'phone': phone,
            'location': location,
            'skills': skills,
            'certifications': certifications,
            'work_history': work_history,
            'education': education,
            'years_of_experience': years_of_experience,
            'avionte_talent_id': talent_id,
            # Additional fields that might be useful
            'summary': talent_data.get('summary') or talent_data.get('profileSummary') or '',
            'linkedin': talent_data.get('linkedIn') or talent_data.get('linkedinUrl', ''),
            'resume_file_path': resume_file_path,
            # Store raw data for reference
            'raw_avionte_data': talent_data
        }
        
        return candidate
    
    def _download_talent_resume(self, talent_id: str) -> Optional[str]:
        """
        Download resume document for a talent.
        
        Args:
            talent_id: Avionté talent ID
            
        Returns:
            Path to downloaded resume file, or None if not found
        """
        try:
            documents = self.client.get_talent_documents(talent_id)
            
            # Find resume/document files
            resume_docs = []
            for doc in documents:
                doc_type = doc.get('type') or doc.get('documentType', '').lower()
                doc_name = doc.get('name') or doc.get('fileName', '').lower()
                
                # Look for resume-like documents
                if any(keyword in doc_type or keyword in doc_name for keyword in ['resume', 'cv', 'curriculum']):
                    resume_docs.append(doc)
            
            # If no resume found, try first document
            if not resume_docs and documents:
                resume_docs = [documents[0]]
            
            if not resume_docs:
                logger.warning(f"No resume documents found for talent {talent_id}")
                return None
            
            # Download the first resume found
            doc = resume_docs[0]
            doc_id = doc.get('id') or doc.get('documentId', '')
            
            if not doc_id:
                logger.warning(f"No document ID found for talent {talent_id}")
                return None
            
            content = self.client.get_talent_document_content(talent_id, doc_id)
            if not content:
                logger.warning(f"Failed to download document {doc_id} for talent {talent_id}")
                return None
            
            # Save to temporary file
            doc_name = doc.get('name') or doc.get('fileName') or f"resume_{talent_id}.pdf"
            # Ensure proper extension
            if not Path(doc_name).suffix:
                doc_name = f"{doc_name}.pdf"
            
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"avionte_resume_{talent_id}_{doc_name}")
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Downloaded resume for talent {talent_id} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading resume for talent {talent_id}: {e}", exc_info=True)
            return None
    
    def transform_job_to_job_details(self, job_data: Dict[str, Any]) -> JobDetails:
        """
        Transform Avionté job data to JobDetails format.
        
        Args:
            job_data: Raw job data from Avionté API
            
        Returns:
            JobDetails object
        """
        # Extract job title
        job_title = job_data.get('title') or job_data.get('jobTitle') or job_data.get('name', 'Untitled Job')
        
        # Extract location
        location = ''
        if 'location' in job_data:
            location = job_data['location']
        elif 'city' in job_data and 'state' in job_data:
            location = f"{job_data['city']}, {job_data['state']}"
        elif 'address' in job_data:
            addr = job_data['address']
            if isinstance(addr, dict):
                city = addr.get('city', '')
                state = addr.get('state', '')
                location = f"{city}, {state}".strip(', ')
        
        # Extract full description
        full_description = job_data.get('description') or job_data.get('jobDescription') or job_data.get('fullDescription', '')
        
        # Extract certifications
        certifications = []
        if 'requiredCertifications' in job_data:
            certs = job_data['requiredCertifications']
            if isinstance(certs, list):
                for cert in certs:
                    if isinstance(cert, dict):
                        cert_name = cert.get('name') or cert.get('certificationName', '')
                        category = cert.get('category', 'must-have')
                        if cert_name:
                            certifications.append(Certification(name=cert_name, category=category))
                    else:
                        certifications.append(Certification(name=str(cert), category='must-have'))
        elif 'certifications' in job_data:
            certs = job_data['certifications']
            if isinstance(certs, list):
                for cert in certs:
                    if isinstance(cert, dict):
                        cert_name = cert.get('name', '')
                        category = cert.get('required', True) and 'must-have' or 'bonus'
                        if cert_name:
                            certifications.append(Certification(name=cert_name, category=category))
        
        # Extract required skills
        required_skills = []
        if 'requiredSkills' in job_data:
            skills = job_data['requiredSkills']
            if isinstance(skills, list):
                required_skills = [s.get('name', s) if isinstance(s, dict) else str(s) for s in skills]
        elif 'skills' in job_data:
            skills = job_data['skills']
            if isinstance(skills, list):
                required_skills = [s.get('name', s) if isinstance(s, dict) else str(s) for s in skills]
        
        # Extract preferred skills
        preferred_skills = []
        if 'preferredSkills' in job_data:
            skills = job_data['preferredSkills']
            if isinstance(skills, list):
                preferred_skills = [s.get('name', s) if isinstance(s, dict) else str(s) for s in skills]
        
        # Extract experience level
        experience_level = job_data.get('experienceLevel') or job_data.get('experienceRequired', '')
        
        # Create JobDetails object
        job_details = JobDetails(
            job_title=job_title,
            location=location,
            full_description=full_description,
            certifications=certifications,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_level=experience_level
        )
        
        # Store Avionté job ID for reference
        job_details.avionte_job_id = job_data.get('id') or job_data.get('jobId', '')
        
        return job_details
    
    def transform_talents_to_candidates(self, talents: List[Dict[str, Any]], 
                                       download_resumes: bool = True) -> List[Dict[str, Any]]:
        """
        Transform multiple talents to candidates.
        
        Args:
            talents: List of talent dictionaries from Avionté
            download_resumes: Whether to download resume documents
            
        Returns:
            List of candidate dictionaries
        """
        candidates = []
        for talent in talents:
            try:
                candidate = self.transform_talent_to_candidate(talent, download_resumes)
                candidates.append(candidate)
            except Exception as e:
                logger.error(f"Error transforming talent {talent.get('id', 'unknown')}: {e}", exc_info=True)
                # Continue with other talents even if one fails
                continue
        
        return candidates

