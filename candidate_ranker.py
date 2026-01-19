"""
Recruitment Candidate Screening and Ranking Application
High-level recruitment advisor with advanced candidate screening capabilities
"""

import json
import os
import re
import hashlib
import uuid
import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

from models import Certification, JobDetails, CandidateScore
from ai_resume_parser import AIResumeParser
from ai_scoring_engine import HybridScoringEngine
from pdf_generator import PDFGenerator
from skills_researcher import SkillsResearcher
from ai_certification_researcher import AICertificationResearcher
from config import OpenAIConfig
from db import get_db, utcnow_str
from industry_templates import get_template_by_name, get_default_weights
from scoring_profiles import validate_weights

# Configure logging
logger = logging.getLogger(__name__)


class CandidateRankerApp:
    """Main application for candidate screening and ranking"""

    def __init__(self, logo_path: str = None, use_ai: bool = True, resume_cache: Dict[str, Dict[str, Any]] = None):
        """
        Initialize Candidate Ranker Application

        Args:
            logo_path: Deprecated - logo is now fixed. This parameter is ignored.
            use_ai: Must be True (AI is now required for all operations)
        """
        # Ensure OpenAI API key is configured
        if not OpenAIConfig.is_configured():
            raise ValueError(
                "OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable."
            )
        
        if not use_ai:
            raise ValueError("AI is now required. 'use_ai' must be True.")
        
        # Initialize AI-powered components (all required)
        try:
            self.resume_parser = AIResumeParser()
            self.scoring_engine = HybridScoringEngine(use_ai=use_ai)
            self.cert_researcher = AICertificationResearcher()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI components: {e}")
        
        # Logo is now fixed - PDF generator will use the fixed logo path
        self.pdf_generator = PDFGenerator()
        self.skills_researcher = SkillsResearcher()
        self.job_details: JobDetails = None
        self.candidate_scores: List[CandidateScore] = []
        self.use_ai = use_ai
        # In-memory cache for parsed resumes (hash -> candidate dict)
        self.resume_cache: Dict[str, Dict[str, Any]] = resume_cache if resume_cache is not None else {}

    def run(self, job_title: str, certifications: List[Dict[str, str]],
            location: str, job_description: str, resume_files: List[str],
            required_skills: List[str] = None, preferred_skills: List[str] = None,
            progress_callback=None, resume_cache: Dict[str, Dict[str, Any]] = None,
            user_id: str = None, resume_assets: List[Dict[str, Any]] = None,
            job_source_asset_id: str = None,
            industry_template: str = None,
            custom_scoring_weights: Dict[str, float] = None,
            dealbreakers: List[str] = None,
            bias_reduction_enabled: bool = False) -> str:
        """
        Main workflow execution
        
        Note: If industry_template is not specified, defaults to "general" (universal standard).
        The General template uses balanced weights suitable for most industries and roles.

        Args:
            job_title: The job title
            certifications: List of dicts with 'name' and 'category' ('must-have' or 'bonus')
            location: Job location
            job_description: Full job description
            resume_files: List of paths to resume files (PDF, DOCX, TXT)
            required_skills: Optional list of required skills from AI extraction
            preferred_skills: Optional list of preferred skills from AI extraction
            progress_callback: Optional callback function(step_name, progress, current, total) for progress updates
            resume_cache: Optional cache for parsed resumes
            user_id: Optional user ID for persistence
            resume_assets: Optional resume asset metadata
            job_source_asset_id: Optional job source asset ID
            industry_template: Optional industry template name (e.g., "healthcare", "technology"). Defaults to "general" (universal standard)
            custom_scoring_weights: Optional custom scoring weights dictionary. Overrides template if provided
            dealbreakers: Optional list of criteria that automatically disqualify candidates
            bias_reduction_enabled: Optional flag to enable blind screening (removes names, photos, etc.)

        Returns:
            Path to generated PDF report
        """
        logger.info("=" * 80)
        logger.info("RECRUITMENT CANDIDATE SCREENING AND RANKING SYSTEM")
        logger.info("=" * 80)
        logger.info("")

        # Step 1: Parse and structure job details (0-10%)
        if progress_callback:
            progress_callback("analyzing", 0.05, 0, 0)
        logger.info("STEP 1: Analyzing job requirements...")
        
        self.job_details = self._parse_job_details(
            job_title, certifications, location, job_description,
            required_skills=required_skills, preferred_skills=preferred_skills,
            industry_template=industry_template,
            custom_scoring_weights=custom_scoring_weights,
            dealbreakers=dealbreakers,
            bias_reduction_enabled=bias_reduction_enabled
        )
        
        # Apply industry template if specified
        # If no template specified, General template is already set as default in _parse_job_details
        if industry_template:
            self.apply_industry_template(industry_template)
        elif not self.job_details.industry_template:
            # Ensure General template is applied if not already set
            self.apply_industry_template("general")
        
        if progress_callback:
            progress_callback("analyzing", 0.10, 0, 0)

        # Step 2: Research equivalent terms, skills, and certifications (10-20%)
        if progress_callback:
            progress_callback("researching", 0.15, 0, 0)
        logger.info("STEP 2: Researching equivalent titles, skills, and certifications...")
        self._research_equivalents()
        
        # Step 2b: Expand certifications with AI if "or equivalent" mentioned
        logger.info("STEP 2b: Researching equivalent certifications...")
        self._expand_certification_equivalents()
        if progress_callback:
            progress_callback("researching", 0.20, 0, 0)

        # Step 3: Parse all resumes (20-40%) - now parallelized
        if resume_files:
            logger.info(f"STEP 3: Parsing {len(resume_files)} resume(s)...")
            # Merge external cache if provided (e.g., Streamlit session)
            if resume_cache is not None:
                # Use provided cache as backing store
                self.resume_cache = resume_cache
            candidates = self._parse_resumes(resume_files, progress_callback)
        else:
            candidates = []

        # Step 3b: Deduplicate candidates by name+email to prevent duplicate scoring
        candidates = self._deduplicate_candidates(candidates)

        # Step 4: Score each candidate (40-70%) - now parallelized
        logger.info(f"STEP 4: Scoring {len(candidates)} candidate(s)...")
        self._score_candidates(candidates, progress_callback)

        # Step 5: Rank and select top candidates (70-80%)
        if progress_callback:
            progress_callback("ranking", 0.75, 0, 0)
        logger.info("STEP 5: Ranking candidates...")
        top_candidates = self._rank_candidates()
        if progress_callback:
            progress_callback("ranking", 0.80, 0, 0)

        # Step 6: Generate PDF report (80-100%)
        if progress_callback:
            progress_callback("generating", 0.85, 0, 0)
        logger.info("STEP 6: Generating PDF report...")
        pdf_path = self._generate_report(top_candidates)
        if progress_callback:
            progress_callback("generating", 1.0, 0, 0)

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"REPORT GENERATED: {pdf_path}")
        logger.info("=" * 80)

        # Persist run metadata if user_id provided
        if user_id:
            try:
                self._persist_run(
                    user_id=user_id,
                    pdf_path=pdf_path,
                    job_source_asset_id=job_source_asset_id,
                    resume_assets=resume_assets,
                    top_candidates=top_candidates
                )
            except Exception as e:
                logger.warning(f"Failed to persist run metadata: {e}", exc_info=True)

        return pdf_path

    def _parse_job_details(self, job_title: str, certifications: List[Dict[str, str]],
                          location: str, job_description: str, required_skills: List[str] = None,
                          preferred_skills: List[str] = None,
                          industry_template: str = None,
                          custom_scoring_weights: Dict[str, float] = None,
                          dealbreakers: List[str] = None,
                          bias_reduction_enabled: bool = False) -> JobDetails:
        """Parse and structure job information"""

        # Convert certifications
        cert_objects = [
            Certification(name=c['name'], category=c['category'])
            for c in certifications
        ]

        # Create job details
        job = JobDetails(
            job_title=job_title,
            certifications=cert_objects,
            location=location,
            full_description=job_description,
            industry_template=industry_template or "",
            dealbreakers=dealbreakers or [],
            bias_reduction_enabled=bias_reduction_enabled
        )
        
        # Use AI-extracted skills if provided, otherwise set to empty arrays
        # NO FALLBACKS - skills must come from AI extraction or be empty
        if required_skills:
            job.required_skills = self._validate_and_filter_skills(required_skills)
        else:
            job.required_skills = []  # Empty array if not provided by AI
        
        if preferred_skills:
            job.preferred_skills = self._validate_and_filter_skills(preferred_skills)
        else:
            job.preferred_skills = []  # Empty array if not provided by AI

        # Extract structured information from description (for other fields)
        # Note: This does NOT populate required_skills or preferred_skills anymore
        self._extract_job_requirements(job)
        
        # Apply custom scoring weights if provided
        if custom_scoring_weights:
            if validate_weights(custom_scoring_weights):
                job.scoring_profile = custom_scoring_weights
                logger.info(f"Applied custom scoring weights: {custom_scoring_weights}")
            else:
                logger.warning(f"Invalid custom weights (sum={sum(custom_scoring_weights.values())}), using defaults")
                # Fall back to General template
                job.scoring_profile = get_default_weights()
                job.industry_template = "general"
        elif industry_template:
            # Will be applied by apply_industry_template() after job creation
            pass
        else:
            # Default to General/Universal template (universal standard for resume grading)
            # This ensures all jobs use a consistent, balanced scoring approach unless explicitly overridden
            job.scoring_profile = get_default_weights()
            job.industry_template = "general"
            logger.info("Using default General/Universal template (universal standard for resume grading)")

        return job

    def _validate_and_filter_skills(self, skills: List[str]) -> List[str]:
        """Validate and filter skills to remove invalid abbreviations and short words"""
        if not skills:
            return []
        
        invalid_abbreviations = ['ai', 'go', 'aws', 'it', 'hr', 'pr', 'ml', 'nlp', 'api', 'ui', 'ux', 'qa', 'pm']
        
        def is_valid_skill(skill: str) -> bool:
            """Validate that a skill is meaningful and not an invalid abbreviation"""
            if not skill or not isinstance(skill, str):
                return False
            
            skill = skill.strip()
            if not skill:
                return False
            
            skill_lower = skill.lower()
            
            # Reject if it's in the blacklist of invalid abbreviations
            if skill_lower in invalid_abbreviations:
                return False
            
            # Reject single words <= 3 characters (too short to be meaningful)
            if len(skill) <= 3 and ' ' not in skill:
                return False
            
            # Reject single letters
            if len(skill) == 1:
                return False
            
            # Accept multi-word skills (they're usually meaningful)
            if ' ' in skill:
                return True
            
            # Accept single words > 3 characters that aren't blacklisted
            if len(skill) > 3:
                return True
            
            # Reject everything else
            return False
        
        return [skill.strip() for skill in skills if is_valid_skill(skill)]

    def _extract_job_requirements(self, job: JobDetails):
        """Extract requirements from job description"""
        description = job.full_description.lower()

        # Extract technical skills (common patterns)
        tech_patterns = [
            r'(?:python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|php)',
            r'(?:react|angular|vue|node\.js|django|flask|spring|\.net)',
            r'(?:aws|azure|gcp|kubernetes|docker|jenkins|terraform)',
            r'(?:sql|nosql|mongodb|postgresql|mysql|redis|elasticsearch)',
            r'(?:machine learning|ml|ai|data science|nlp|computer vision)',
            r'(?:agile|scrum|devops|ci/cd|git|jira)'
        ]

        tech_stack = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            tech_stack.update([m.strip() for m in matches])

        job.technical_stack = list(tech_stack)

        # Extract experience level
        if re.search(r'senior|sr\.|lead|principal|staff', description, re.IGNORECASE):
            job.experience_level = "Senior"
        elif re.search(r'junior|jr\.|entry|associate', description, re.IGNORECASE):
            job.experience_level = "Junior"
        else:
            job.experience_level = "Mid-level"

        # Extract soft skills
        soft_skill_keywords = [
            'communication', 'leadership', 'teamwork', 'problem-solving',
            'analytical', 'creative', 'adaptable', 'collaborative',
            'detail-oriented', 'self-motivated', 'time management'
        ]

        job.soft_skills = [
            skill for skill in soft_skill_keywords
            if skill in description
        ]

        # NOTE: Skills extraction removed - required_skills and preferred_skills
        # are now ONLY populated by AI extraction in _parse_job_details()
        # No fallback to technical_stack - if AI doesn't extract, they remain empty arrays

        # Extract industry context with enhanced detection
        industry_keywords = {
            # Healthcare
            'healthcare': 'Healthcare',
            'health care': 'Healthcare',
            'medical': 'Healthcare',
            'hospital': 'Healthcare',
            'nursing': 'Healthcare',
            'physician': 'Healthcare',
            'clinical': 'Healthcare',
            'patient care': 'Healthcare',
            'pharmacy': 'Healthcare',
            'dental': 'Healthcare',
            # Technology
            'technology': 'Technology',
            'tech': 'Technology',
            'software': 'Technology',
            'programming': 'Technology',
            'developer': 'Technology',
            'engineer': 'Technology',
            'it ': 'Technology',
            'information technology': 'Technology',
            'computer science': 'Technology',
            'data science': 'Technology',
            'ai ': 'Technology',
            'machine learning': 'Technology',
            # Construction/Safety
            'construction': 'Construction',
            'safety': 'Construction',
            'osha': 'Construction',
            'trade': 'Construction',
            'electrician': 'Construction',
            'plumber': 'Construction',
            'welder': 'Construction',
            'crane': 'Construction',
            'heavy equipment': 'Construction',
            'lineman': 'Construction',
            'solar': 'Construction',
            # Finance
            'finance': 'Finance/Banking',
            'financial': 'Finance/Banking',
            'banking': 'Finance/Banking',
            'accounting': 'Finance/Banking',
            'cpa': 'Finance/Banking',
            'cfa': 'Finance/Banking',
            'audit': 'Finance/Banking',
            'investment': 'Finance/Banking',
            # Sales
            'sales': 'Sales',
            'account manager': 'Sales',
            'business development': 'Sales',
            'revenue': 'Sales',
            'quota': 'Sales',
            'territory': 'Sales',
            # Retail
            'retail': 'Retail/E-commerce',
            'e-commerce': 'Retail/E-commerce',
            'ecommerce': 'Retail/E-commerce',
            # Manufacturing
            'manufacturing': 'Manufacturing',
            'production': 'Manufacturing',
            'assembly': 'Manufacturing',
            # Education
            'education': 'Education',
            'teaching': 'Education',
            'teacher': 'Education',
            'professor': 'Education',
            # Government
            'government': 'Government/Public Sector',
            'public sector': 'Government/Public Sector',
            'federal': 'Government/Public Sector',
            'state': 'Government/Public Sector',
        }

        # Detect industry with priority (more specific matches first)
        detected_industry = None
        for keyword, industry in industry_keywords.items():
            if keyword in description:
                detected_industry = industry
                # Don't break - continue to find more specific matches
                # But prioritize certain industries
                if industry in ['Healthcare', 'Technology', 'Construction']:
                    break
        
        if detected_industry:
            job.industry_context = detected_industry
            
            # Auto-suggest industry template based on detected industry
            industry_to_template = {
                'Healthcare': 'healthcare',
                'Technology': 'technology',
                'Construction': 'construction',
                'Finance/Banking': 'finance',
                'Sales': 'sales',
            }
            
            suggested_template = industry_to_template.get(detected_industry)
            if suggested_template and not job.industry_template:
                # Store suggested template (can be applied later)
                job.industry_template = suggested_template
                logger.info(f"Auto-detected industry: {detected_industry}, suggested template: {suggested_template}")

    def apply_industry_template(self, template_name: str) -> None:
        """
        Apply an industry template to the current job details
        
        Args:
            template_name: Name of the industry template (e.g., 'healthcare', 'technology')
        """
        try:
            template = get_template_by_name(template_name)
            
            # Apply template weights
            self.job_details.scoring_profile = template.weights.copy()
            self.job_details.industry_template = template.name
            
            # Apply industry-specific skill synonyms if available
            if template.industry_specific_rules.get('skill_synonyms'):
                for skill, synonyms in template.industry_specific_rules['skill_synonyms'].items():
                    if skill not in self.job_details.skill_synonyms:
                        self.job_details.skill_synonyms[skill] = synonyms
                    else:
                        # Merge synonyms
                        existing = set(self.job_details.skill_synonyms[skill])
                        existing.update(synonyms)
                        self.job_details.skill_synonyms[skill] = list(existing)
            
            logger.info(f"Applied industry template '{template_name}' with weights: {template.weights}")
            logger.info(f"Template description: {template.description}")
            
        except ValueError as e:
            logger.warning(f"Failed to apply template '{template_name}': {e}")
            # Fall back to default weights
            self.job_details.scoring_profile = get_default_weights()
            self.job_details.industry_template = "general"

    def _research_equivalents(self):
        """Research equivalent titles, skills, and certifications"""
        # Use SkillsResearcher to find equivalents, passing experience level to filter seniority variations
        self.job_details.equivalent_titles = self.skills_researcher.find_equivalent_titles(
            self.job_details.job_title,
            experience_level=self.job_details.experience_level
        )

        # Find skill synonyms
        for skill in self.job_details.technical_stack:
            synonyms = self.skills_researcher.find_skill_synonyms(skill)
            if synonyms:
                self.job_details.skill_synonyms[skill] = synonyms

        logger.info(f"  Found {len(self.job_details.equivalent_titles)} equivalent titles")
        logger.info(f"  Mapped {len(self.job_details.skill_synonyms)} skill synonyms")

    async def _expand_certification_equivalents_async(self):
        """Expand certifications that mention 'or equivalent' using AI in parallel"""
        # AI certification researcher is always available (required)
        
        job_context = self.job_details.full_description
        
        # Find all certs that need research
        certs_to_research = [
            cert for cert in self.job_details.certifications
            if "equivalent" in cert.name.lower()
        ]
        
        if not certs_to_research:
            return
        
        async def research_cert_equivalent(cert):
            """Research equivalent for a single certification"""
            try:
                cert_name = cert.name
                # Run in thread pool since find_equivalents may be blocking
                loop = asyncio.get_event_loop()
                equivalents = await loop.run_in_executor(
                    None,
                    self.cert_researcher.find_equivalents,
                    cert_name,
                    job_context
                )
                return cert_name, equivalents
            except Exception as e:
                logger.error(f"  ERROR researching equivalents for {cert.name}: {e}", exc_info=True)
                return cert.name, []
        
        # Research all certs in parallel
        tasks = [research_cert_equivalent(cert) for cert in certs_to_research]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"  ERROR: Exception during cert research: {result}", exc_info=True)
                continue
            cert_name, equivalents = result
            if equivalents:
                logger.info(f"  Found {len(equivalents)} equivalent(s) for {cert_name}")
                # Store equivalents in job_details for matching
                self.job_details.certification_equivalents[cert_name] = equivalents
            else:
                logger.info(f"  No equivalents found for {cert_name}")
    
    def _expand_certification_equivalents(self):
        """Expand certifications that mention 'or equivalent' using AI (sync wrapper)"""
        # Run async version - handle existing event loop (e.g., Streamlit)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Event loop is already running (e.g., in Streamlit), use nest_asyncio
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self._expand_certification_equivalents_async())
            else:
                return loop.run_until_complete(self._expand_certification_equivalents_async())
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self._expand_certification_equivalents_async())

    async def _parse_resumes_async(self, resume_files: List[str], progress_callback=None) -> List[Dict[str, Any]]:
        """Parse all resume files in parallel with simple cache by file hash"""
        total = len(resume_files)
        if total == 0:
            return []
        
        async def parse_single_resume(resume_file, index):
            """Parse a single resume file"""
            try:
                logger.info(f"  Parsing resume {index}/{total}: {Path(resume_file).name}")
                if progress_callback:
                    # Progress from 20% to 40% (20% range for parsing)
                    progress = 0.20 + ((index - 1) / total * 0.20)
                    progress_callback("parsing", progress, index, total)
                
                # Compute hash of file contents to reuse parsed output
                file_hash = None
                try:
                    # Use asyncio to read file in thread pool (non-blocking)
                    loop = asyncio.get_event_loop()
                    def read_file():
                        with open(resume_file, "rb") as f:
                            return f.read()
                    file_bytes = await loop.run_in_executor(None, read_file)
                    file_hash = hashlib.sha256(file_bytes).hexdigest()
                except Exception as e:
                    logger.warning(f"    WARNING: Failed to read {resume_file}: {e}", exc_info=True)
                    file_hash = None
                
                # Check cache first
                cached_candidate = self.resume_cache.get(file_hash) if file_hash else None
                
                if cached_candidate:
                    logger.debug("    Using cached parse for this resume")
                    candidate_data = cached_candidate
                else:
                    try:
                        # Run parsing in thread pool since it's I/O bound
                        loop = asyncio.get_event_loop()
                        candidate_data = await loop.run_in_executor(
                            None, 
                            self.resume_parser.parse, 
                            resume_file
                        )
                        # Store in cache if hash available
                        if file_hash:
                            self.resume_cache[file_hash] = candidate_data
                    except Exception as e:
                        # Filter out errors related to deprecated _generate_deterministic_seed method
                        error_str = str(e)
                        if '_generate_deterministic_seed' not in error_str:
                            logger.warning(f"    WARNING: Failed to parse {resume_file}: {e}", exc_info=True)
                        return None
                
                if progress_callback:
                    # Update progress after each resume
                    progress = 0.20 + (index / total * 0.20)
                    progress_callback("parsing", progress, index, total)
                
                return candidate_data
            except Exception as e:
                # Filter out errors related to deprecated _generate_deterministic_seed method
                error_str = str(e)
                if '_generate_deterministic_seed' not in error_str:
                    logger.error(f"    ERROR parsing resume {index} ({Path(resume_file).name}): {e}", exc_info=True)
                return None
        
        # Create tasks for all resumes
        tasks = [
            parse_single_resume(resume_file, i)
            for i, resume_file in enumerate(resume_files, 1)
        ]
        
        # Execute all parsing tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        candidates = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"  ERROR: Exception during parsing resume {i+1}: {result}", exc_info=True)
                continue
            if result is not None:
                candidates.append(result)
        
        logger.info(f"  Successfully parsed {len(candidates)} resume(s)")
        return candidates

    def _deduplicate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate candidates based on name and email.
        If duplicates are found, keep the first occurrence (most complete data).
        
        Args:
            candidates: List of candidate dictionaries
            
        Returns:
            Deduplicated list of candidates
        """
        if not candidates:
            return candidates
        
        seen = {}  # (name_lower, email_lower) -> candidate
        deduplicated = []
        duplicates_found = []
        
        for candidate in candidates:
            name = candidate.get('name', '').strip().lower()
            email = candidate.get('email', '').strip().lower()
            
            # Create a unique key from name and email
            if name or email:
                key = (name, email)
            else:
                # If no name/email, use raw_text hash as fallback
                raw_text = candidate.get('raw_text', '')
                key = (hashlib.sha256(raw_text.encode()).hexdigest()[:16], '')
            
            if key in seen:
                # Duplicate found
                existing = seen[key]
                existing_name = existing.get('name', 'Unknown')
                candidate_name = candidate.get('name', 'Unknown')
                duplicates_found.append(f"{candidate_name} (duplicate of {existing_name})")
                logger.warning(f"  WARNING: Duplicate candidate detected: {candidate_name} (email: {email or 'N/A'}) - skipping duplicate")
                # Keep the first occurrence (usually has more complete data)
                continue
            else:
                seen[key] = candidate
                deduplicated.append(candidate)
        
        if duplicates_found:
            logger.info(f"  Removed {len(duplicates_found)} duplicate candidate(s)")
        
        return deduplicated
    
    def _parse_resumes(self, resume_files: List[str], progress_callback=None) -> List[Dict[str, Any]]:
        """Parse all resume files (sync wrapper for backward compatibility)"""
        # Run async version - handle existing event loop (e.g., Streamlit)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Event loop is already running (e.g., in Streamlit), use create_task
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self._parse_resumes_async(resume_files, progress_callback))
            else:
                return loop.run_until_complete(self._parse_resumes_async(resume_files, progress_callback))
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self._parse_resumes_async(resume_files, progress_callback))

    def _check_dealbreakers(self, candidate: Dict[str, Any], job_details: JobDetails) -> Tuple[bool, str]:
        """
        Check if candidate meets any dealbreaker criteria
        
        Args:
            candidate: Candidate data dictionary
            job_details: Job requirements
            
        Returns:
            Tuple of (is_disqualified, reason)
        """
        if not job_details.dealbreakers:
            return False, ""
        
        candidate_text = candidate.get('raw_text', '').lower()
        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        candidate_certs = [c.lower() for c in candidate.get('certifications', [])]
        candidate_titles = [t.lower() for t in candidate.get('job_titles', [])]
        
        for dealbreaker in job_details.dealbreakers:
            dealbreaker_lower = dealbreaker.lower()
            
            # Check if dealbreaker is mentioned in resume text
            if dealbreaker_lower in candidate_text:
                return True, f"Dealbreaker found in resume: {dealbreaker}"
            
            # Check if it's a skill-related dealbreaker
            if any(dealbreaker_lower in skill or skill in dealbreaker_lower for skill in candidate_skills):
                # This is a match, but we need to check if it's a negative dealbreaker
                # For now, if dealbreaker contains "missing" or "no", it's a negative check
                if "missing" in dealbreaker_lower or "no " in dealbreaker_lower or "lack" in dealbreaker_lower:
                    # This means candidate is missing something required
                    return True, f"Dealbreaker: {dealbreaker}"
            
            # Check if it's a certification-related dealbreaker
            if any(dealbreaker_lower in cert or cert in dealbreaker_lower for cert in candidate_certs):
                if "missing" in dealbreaker_lower or "no " in dealbreaker_lower or "lack" in dealbreaker_lower:
                    return True, f"Dealbreaker: {dealbreaker}"
            
            # Check for negative patterns (e.g., "Missing required license")
            if "missing" in dealbreaker_lower or "no " in dealbreaker_lower:
                # Extract what's missing
                missing_item = dealbreaker_lower.replace("missing", "").replace("no ", "").replace("lack of", "").strip()
                # Check if candidate has this item
                has_item = (
                    missing_item in candidate_text or
                    any(missing_item in skill for skill in candidate_skills) or
                    any(missing_item in cert for cert in candidate_certs)
                )
                if not has_item:
                    return True, f"Dealbreaker: {dealbreaker}"
        
        return False, ""

    async def _score_candidates_async(self, candidates: List[Dict[str, Any]], progress_callback=None):
        """Score all candidates in parallel using async"""
        total = len(candidates)
        self.candidate_scores = []
        
        if total == 0:
            return
        
        # Create semaphore to limit concurrent API calls (max 10)
        semaphore = asyncio.Semaphore(10)
        
        async def score_with_semaphore(candidate, index):
            """Score a single candidate with semaphore for rate limiting"""
            async with semaphore:
                try:
                    logger.info(f"  Scoring candidate {index}/{total}: {candidate.get('name', 'Unknown')}")
                    if progress_callback:
                        # Progress from 40% to 70% (30% range for scoring)
                        progress = 0.40 + ((index - 1) / total * 0.30)
                        progress_callback("scoring", progress, index, total)
                    
                    # Check dealbreakers first
                    is_disqualified, dealbreaker_reason = self._check_dealbreakers(candidate, self.job_details)
                    if is_disqualified:
                        logger.info(f"    Candidate disqualified due to dealbreaker: {dealbreaker_reason}")
                        # Create a low score for disqualified candidates
                        from models import CandidateScore
                        score_result = CandidateScore(
                            name=candidate.get('name', 'Unknown'),
                            phone=candidate.get('phone', ''),
                            email=candidate.get('email', ''),
                            certifications=candidate.get('certifications', []),
                            fit_score=0.0,  # Automatic disqualification
                            chain_of_thought=f"DEALBREAKER: {dealbreaker_reason}. Candidate automatically disqualified.",
                            rationale=f"This candidate has been automatically disqualified due to: {dealbreaker_reason}",
                            experience_match={'level_match': 0.0, 'titles': [], 'years': 0},
                            certification_match={'has_must_have': False, 'has_bonus': False, 'candidate_certs': []},
                            skills_match={'required_match_rate': 0.0, 'preferred_match_rate': 0.0, 'candidate_skills': []},
                            location_match=False,
                            component_scores={}
                        )
                    else:
                        score_result = await self.scoring_engine.score_candidate_async(
                            candidate=candidate,
                            job_details=self.job_details
                        )
                    
                    if progress_callback:
                        # Update progress after each candidate
                        progress = 0.40 + (index / total * 0.30)
                        progress_callback("scoring", progress, index, total)
                    
                    return score_result
                except Exception as e:
                    logger.error(f"  ERROR scoring candidate {index} ({candidate.get('name', 'Unknown')}): {e}", exc_info=True)
                    # Return a default low score for failed candidates
                    from models import CandidateScore
                    return CandidateScore(
                        name=candidate.get('name', 'Unknown'),
                        phone=candidate.get('phone', ''),
                        email=candidate.get('email', ''),
                        certifications=candidate.get('certifications', []),
                        fit_score=1.0,
                        chain_of_thought=f"Error during scoring: {str(e)}",
                        rationale=f"Scoring failed: {str(e)}",
                        experience_match={'level_match': 0.0, 'titles': [], 'years': 0},
                        certification_match={'has_must_have': False, 'has_bonus': False, 'candidate_certs': []},
                        skills_match={'required_match_rate': 0.0, 'preferred_match_rate': 0.0, 'candidate_skills': []},
                        location_match=False,
                        component_scores={}
                    )
        
        # Create tasks for all candidates
        tasks = [
            score_with_semaphore(candidate, i) 
            for i, candidate in enumerate(candidates, 1)
        ]
        
        # Execute all scoring tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"  ERROR: Exception during scoring candidate {i+1}: {result}", exc_info=True)
                # Create a default low score for exceptions
                from models import CandidateScore
                # Safely get candidate data - ensure it's a dictionary
                if i < len(candidates) and isinstance(candidates[i], dict):
                    candidate = candidates[i]
                    name = candidate.get('name', 'Unknown')
                    phone = candidate.get('phone', '')
                    email = candidate.get('email', '')
                    certifications = candidate.get('certifications', [])
                else:
                    # Fallback if candidate data is invalid
                    name = 'Unknown'
                    phone = ''
                    email = ''
                    certifications = []
                
                result = CandidateScore(
                    name=name,
                    phone=phone,
                    email=email,
                    certifications=certifications,
                    fit_score=1.0,
                    chain_of_thought=f"Exception during scoring: {str(result)}",
                    rationale=f"Scoring failed: {str(result)}",
                    experience_match={'level_match': 0.0, 'titles': [], 'years': 0},
                    certification_match={'has_must_have': False, 'has_bonus': False, 'candidate_certs': []},
                    skills_match={'required_match_rate': 0.0, 'preferred_match_rate': 0.0, 'candidate_skills': []},
                    location_match=False,
                    component_scores={}
                )
            self.candidate_scores.append(result)
        
        # Apply score calibration after all candidates are scored
        self._calibrate_scores()
    
    def _score_candidates(self, candidates: List[Dict[str, Any]], progress_callback=None):
        """Score all candidates (sync wrapper for backward compatibility)"""
        # Run async version - handle existing event loop (e.g., Streamlit)
        try:
            # Try to get the current event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Event loop is already running (e.g., in Streamlit), use nest_asyncio
                    import nest_asyncio
                    nest_asyncio.apply()
                    return loop.run_until_complete(self._score_candidates_async(candidates, progress_callback))
                else:
                    return loop.run_until_complete(self._score_candidates_async(candidates, progress_callback))
            except RuntimeError as e:
                # No event loop exists, create new one
                if "no current event loop" in str(e).lower():
                    return asyncio.run(self._score_candidates_async(candidates, progress_callback))
                else:
                    # Re-raise if it's a different RuntimeError
                    raise
        except Exception as e:
            # Catch any other exceptions and log them properly
            logger.error(f"Error in _score_candidates: {e}", exc_info=True)
            # Fallback: try to create a new event loop
            try:
                return asyncio.run(self._score_candidates_async(candidates, progress_callback))
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
                raise

    def _calibrate_scores(self):
        """
        Calibrate scores to ensure proper distribution
        
        Expected distribution:
        - Top candidates: 7.5-10.0
        - Good candidates: 6.0-7.4
        - Viable candidates: 5.0-5.9
        - Poor candidates: <5.0
        """
        if not self.candidate_scores:
            return
        
        # Calculate current score distribution
        scores = [cs.fit_score for cs in self.candidate_scores]
        mean_score = sum(scores) / len(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        
        # Determine if calibration is needed
        # Ideal mean should be around 6.0-6.5 (middle of viable range)
        calibration_factor = 1.0
        
        if mean_score > 7.0:
            # Scores are too high, need to reduce
            # Target mean of 6.25, so reduce by factor
            calibration_factor = 6.25 / mean_score if mean_score > 0 else 1.0
            logger.info(f"  Calibrating scores: Mean too high ({mean_score:.2f}), applying factor {calibration_factor:.3f}")
        elif mean_score < 5.0:
            # Scores are too low, but we'll be conservative and not inflate
            # Only calibrate if mean is very low (<4.0)
            if mean_score < 4.0:
                calibration_factor = 5.0 / mean_score if mean_score > 0 else 1.0
                logger.info(f"  Calibrating scores: Mean too low ({mean_score:.2f}), applying factor {calibration_factor:.3f}")
            else:
                logger.info(f"  Score distribution acceptable (mean: {mean_score:.2f})")
        else:
            logger.info(f"  Score distribution acceptable (mean: {mean_score:.2f})")
        
        # Apply calibration if needed
        if calibration_factor != 1.0:
            must_have_certs_required = any(c.category == 'must-have' for c in self.job_details.certifications)
            
            for candidate_score in self.candidate_scores:
                original_score = candidate_score.fit_score
                calibrated_score = original_score * calibration_factor
                # Ensure calibrated score stays in valid range
                calibrated_score = max(1.0, min(10.0, calibrated_score))
                
                # CRITICAL: Re-apply cap for candidates missing ALL must-have certs AFTER calibration
                # Calibration should not inflate scores for candidates missing critical requirements
                if must_have_certs_required:
                    has_must_have = candidate_score.certification_match.get('has_must_have', False)
                    if not has_must_have and calibrated_score > 5.0:
                        logger.info(f"    RE-CAPPING: {candidate_score.name} missing must-have certs, capping calibrated score at 5.0")
                        calibrated_score = min(calibrated_score, 5.0)
                
                # Update score and calibration metadata
                candidate_score.fit_score = calibrated_score
                candidate_score.calibration_applied = True
                candidate_score.calibration_factor = calibration_factor
                
                logger.debug(f"    {candidate_score.name}: {original_score:.2f} -> {calibrated_score:.2f}")

    def _check_score_consistency(self):
        """
        Check for score inconsistencies between similar candidates
        Flags candidates with very different scores but similar profiles
        """
        if len(self.candidate_scores) < 2:
            return
        
        # Compare each pair of candidates
        for i, candidate1 in enumerate(self.candidate_scores):
            for j, candidate2 in enumerate(self.candidate_scores[i+1:], start=i+1):
                score_diff = abs(candidate1.fit_score - candidate2.fit_score)
                
                # If scores differ by more than 2.0, check if profiles are similar
                if score_diff > 2.0:
                    similarity = self._calculate_profile_similarity(candidate1, candidate2)
                    
                    # If profiles are similar (>70% similarity) but scores differ significantly
                    if similarity > 0.7:
                        logger.warning(f"  WARNING: Similar candidates with very different scores:")
                        logger.warning(f"    {candidate1.name}: {candidate1.fit_score:.2f}")
                        logger.warning(f"    {candidate2.name}: {candidate2.fit_score:.2f}")
                        logger.warning(f"    Similarity: {similarity:.1%}, Score difference: {score_diff:.2f}")

    def _calculate_profile_similarity(self, candidate1: CandidateScore, candidate2: CandidateScore) -> float:
        """
        Calculate similarity between two candidate profiles based on:
        - Certifications overlap
        - Skills overlap
        - Experience level similarity
        - Job title similarity
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        similarity_scores = []
        
        # Certifications similarity
        certs1 = set(c.lower() for c in candidate1.certifications)
        certs2 = set(c.lower() for c in candidate2.certifications)
        if certs1 or certs2:
            cert_overlap = len(certs1 & certs2) / max(len(certs1 | certs2), 1)
            similarity_scores.append(cert_overlap)
        
        # Skills similarity
        skills1 = set(s.lower() for s in candidate1.skills_match.get('candidate_skills', []))
        skills2 = set(s.lower() for s in candidate2.skills_match.get('candidate_skills', []))
        if skills1 or skills2:
            skills_overlap = len(skills1 & skills2) / max(len(skills1 | skills2), 1)
            similarity_scores.append(skills_overlap)
        
        # Experience level similarity
        exp1 = candidate1.experience_match.get('years', 0)
        exp2 = candidate2.experience_match.get('years', 0)
        if exp1 > 0 or exp2 > 0:
            exp_diff = abs(exp1 - exp2) / max(max(exp1, exp2), 1)
            exp_similarity = 1.0 - min(exp_diff, 1.0)
            similarity_scores.append(exp_similarity)
        
        # Component scores similarity (if available)
        if candidate1.component_scores and candidate2.component_scores:
            component_diffs = []
            for key in candidate1.component_scores.keys():
                if key in candidate2.component_scores:
                    diff = abs(candidate1.component_scores[key] - candidate2.component_scores[key]) / 10.0
                    component_diffs.append(1.0 - diff)
            if component_diffs:
                avg_component_similarity = sum(component_diffs) / len(component_diffs)
                similarity_scores.append(avg_component_similarity)
        
        # Return average similarity
        return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0

    def _analyze_score_distribution(self, sorted_candidates: List[CandidateScore]):
        """
        Analyze score distribution to check for clustering or other issues
        """
        if not sorted_candidates:
            return
        
        scores = [cs.fit_score for cs in sorted_candidates]
        
        # Check for clustering (too many candidates at same score)
        score_counts = {}
        for score in scores:
            # Round to 0.5 for clustering detection
            rounded_score = round(score * 2) / 2
            score_counts[rounded_score] = score_counts.get(rounded_score, 0) + 1
        
        # Flag if more than 30% of candidates share the same rounded score
        max_cluster_size = max(score_counts.values()) if score_counts else 0
        cluster_threshold = len(sorted_candidates) * 0.3
        
        if max_cluster_size > cluster_threshold:
            clustered_score = max(score_counts.items(), key=lambda x: x[1])[0]
            logger.warning(f"  WARNING: Score clustering detected - {max_cluster_size} candidates at score {clustered_score:.1f}")
        
        # Verify ranking order makes sense
        # Check if score differences are reasonable
        for i in range(len(sorted_candidates) - 1):
            score_diff = sorted_candidates[i].fit_score - sorted_candidates[i+1].fit_score
            # If scores are very close (<0.1 difference), ranking might be arbitrary
            if 0 < score_diff < 0.1:
                logger.debug(f"  NOTE: Candidates {i+1} and {i+2} have very similar scores "
                      f"({sorted_candidates[i].fit_score:.2f} vs {sorted_candidates[i+1].fit_score:.2f})")

    def _rank_candidates(self) -> List[CandidateScore]:
        """
        Rank candidates and select top 4-10
        Also performs consistency checks to flag potential issues
        """
        # Perform consistency checks before ranking
        self._check_score_consistency()
        
        # Sort by fit score (descending) - ALWAYS sort
        sorted_candidates = sorted(
            self.candidate_scores,
            key=lambda x: x.fit_score,
            reverse=True
        )
        
        # Analyze score distribution
        self._analyze_score_distribution(sorted_candidates)

        # Select top candidates (4-10 based on viability)
        # Consider candidates with score >= 5.0 as viable
        viable_candidates = [c for c in sorted_candidates if c.fit_score >= 5.0]

        if len(viable_candidates) < 4:
            # If less than 4 viable, still only include viable candidates (not all)
            # This ensures we never include candidates below 5.0 threshold
            top_candidates = viable_candidates
            logger.info(f"  Only {len(viable_candidates)} viable candidate(s) found (score >= 5.0)")
            logger.info(f"  Note: {len(sorted_candidates) - len(viable_candidates)} candidate(s) excluded (score < 5.0)")
        else:
            # Take top 10 or all viable, whichever is smaller
            top_candidates = viable_candidates[:min(10, len(viable_candidates))]

        # Ensure candidates are sorted (highest to lowest)
        top_candidates = sorted(top_candidates, key=lambda x: x.fit_score, reverse=True)
        
        logger.info(f"  Selected {len(top_candidates)} top candidate(s) (all with score >= 5.0)")

        return top_candidates

    def _generate_report(self, top_candidates: List[CandidateScore]) -> str:
        """Generate PDF report and upload to S3"""
        from storage import save_bytes, USE_S3
        import tempfile
        import os as _os

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"Candidate_Ranking_Report_{timestamp}.pdf"

        # Generate PDF to temporary file first
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Generate PDF to temp file
            self.pdf_generator.generate(
                job_details=self.job_details,
                top_candidates=top_candidates,
                all_candidates_count=len(self.candidate_scores),
                output_path=tmp_path
            )

            # Read the generated PDF and save to S3/storage
            with open(tmp_path, 'rb') as f:
                pdf_content = f.read()

            # Use the storage module to save (will use S3 if configured)
            stored_path, _ = save_bytes(pdf_content, output_filename)
            logger.info(f"PDF report saved to: {stored_path}")

            return stored_path
        finally:
            # Clean up temp file
            if _os.path.exists(tmp_path):
                _os.remove(tmp_path)

    def _persist_run(self, user_id: str, pdf_path: str, job_source_asset_id: str,
                     resume_assets: List[Dict[str, Any]], top_candidates: List[CandidateScore]) -> None:
        """
        Persist run metadata: job description, resumes, report, and top candidates.
        """

        def _exec(conn, query, params):
            # Swap parameter style for psycopg2 if needed
            if conn.__class__.__module__.startswith("psycopg2"):
                query = query.replace("?", "%s")
            cur = conn.cursor()
            cur.execute(query, params)
            return cur

        now = utcnow_str()
        job_id = str(uuid.uuid4())
        report_id = str(uuid.uuid4())

        certifications_json = json.dumps([asdict(c) for c in self.job_details.certifications])
        required_skills_json = json.dumps(self.job_details.required_skills)
        preferred_skills_json = json.dumps(self.job_details.preferred_skills)

        with get_db() as conn:
            try:
                # Job description
                _exec(
                    conn,
                    """
                    INSERT INTO job_descriptions (
                        id, user_id, title, location, certifications_json,
                        required_skills_json, preferred_skills_json, full_description,
                        source_asset_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        user_id,
                        self.job_details.job_title,
                        self.job_details.location,
                        certifications_json,
                        required_skills_json,
                        preferred_skills_json,
                        self.job_details.full_description,
                        job_source_asset_id,
                        now,
                    ),
                )

                # Report
                _exec(
                    conn,
                    """
                    INSERT INTO reports (id, user_id, job_description_id, pdf_path, summary_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report_id,
                        user_id,
                        job_id,
                        pdf_path,
                        json.dumps({"all_candidates": len(self.candidate_scores), "top_candidates": len(top_candidates)}),
                        now,
                    ),
                )

                # Resumes (optional, if provided)
                # Only persist resumes that have a valid file_asset_id (saved to file_assets table)
                # Resumes without file_asset_id will be saved later in the auto-save section
                if resume_assets:
                    for asset in resume_assets:
                        # source_asset_id must be a valid file_assets.id (UUID), not a hash
                        # Skip resumes that don't have file_asset_id set yet (they'll be saved later)
                        source_asset_id = asset.get("file_asset_id")
                        if not source_asset_id:
                            # Skip this resume - it will be saved later when file_asset_id is available
                            continue
                        
                        resume_id = str(uuid.uuid4())
                        _exec(
                            conn,
                            """
                            INSERT INTO resumes (id, user_id, original_name, stored_path, parsed_metadata_json, source_asset_id, uploaded_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                resume_id,
                                user_id,
                                asset.get("original_name"),
                                asset.get("stored_path"),
                                None,
                                source_asset_id,  # Use actual file_assets.id
                                now,
                            ),
                        )

                # Candidate scores (top candidates snapshot)
                for cand in top_candidates:
                    score_id = str(uuid.uuid4())
                    _exec(
                        conn,
                        """
                        INSERT INTO candidate_scores (
                            id, report_id, candidate_name, email, phone, fit_score, rationale, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            score_id,
                            report_id,
                            cand.name,
                            cand.email,
                            cand.phone,
                            cand.fit_score,
                            cand.rationale,
                            json.dumps(asdict(cand)),
                        ),
                    )

                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to persist run: {e}", exc_info=True)
                raise


def main():
    """Example usage"""
    logger.info("\nRECRUITMENT CANDIDATE RANKER")
    logger.info("This application requires input via code or API.")
    logger.info("\nExample usage:")
    logger.info("""
    from candidate_ranker import CandidateRankerApp

    app = CandidateRankerApp()

    pdf_path = app.run(
        job_title="Data Scientist",
        certifications=[
            {"name": "AWS Certified Machine Learning", "category": "must-have"},
            {"name": "Google Cloud Professional Data Engineer", "category": "bonus"}
        ],
        location="New York, NY",
        job_description="Full job description here...",
        resume_files=["resume1.pdf", "resume2.pdf", "resume3.pdf"]
    )

    logger.info(f"Report generated: {pdf_path}")
    """)


if __name__ == "__main__":
    main()
