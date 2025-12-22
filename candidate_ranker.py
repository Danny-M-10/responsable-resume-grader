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
            job_source_asset_id: str = None) -> str:
        """
        Main workflow execution

        Args:
            job_title: The job title
            certifications: List of dicts with 'name' and 'category' ('must-have' or 'bonus')
            location: Job location
            job_description: Full job description
            resume_files: List of paths to resume files (PDF, DOCX, TXT)
            required_skills: Optional list of required skills from AI extraction
            preferred_skills: Optional list of preferred skills from AI extraction
            progress_callback: Optional callback function(step_name, progress, current, total) for progress updates

        Returns:
            Path to generated PDF report
        """
        print("=" * 80)
        print("RECRUITMENT CANDIDATE SCREENING AND RANKING SYSTEM")
        print("=" * 80)
        print()

        # Step 1: Parse and structure job details (0-10%)
        if progress_callback:
            progress_callback("analyzing", 0.05, 0, 0)
        print("STEP 1: Analyzing job requirements...")
        self.job_details = self._parse_job_details(
            job_title, certifications, location, job_description,
            required_skills=required_skills, preferred_skills=preferred_skills
        )
        if progress_callback:
            progress_callback("analyzing", 0.10, 0, 0)

        # Step 2: Research equivalent terms, skills, and certifications (10-20%)
        if progress_callback:
            progress_callback("researching", 0.15, 0, 0)
        print("STEP 2: Researching equivalent titles, skills, and certifications...")
        self._research_equivalents()
        
        # Step 2b: Expand certifications with AI if "or equivalent" mentioned
        print("STEP 2b: Researching equivalent certifications...")
        self._expand_certification_equivalents()
        if progress_callback:
            progress_callback("researching", 0.20, 0, 0)

        # Step 3: Parse all resumes (20-40%) - now parallelized
        print(f"STEP 3: Parsing {len(resume_files)} resume(s)...")
        # Merge external cache if provided (e.g., Streamlit session)
        if resume_cache is not None:
            # Use provided cache as backing store
            self.resume_cache = resume_cache

        candidates = self._parse_resumes(resume_files, progress_callback)

        # Step 4: Score each candidate (40-70%) - now parallelized
        print(f"STEP 4: Scoring {len(candidates)} candidate(s)...")
        self._score_candidates(candidates, progress_callback)

        # Step 5: Rank and select top candidates (70-80%)
        if progress_callback:
            progress_callback("ranking", 0.75, 0, 0)
        print("STEP 5: Ranking candidates...")
        top_candidates = self._rank_candidates()
        if progress_callback:
            progress_callback("ranking", 0.80, 0, 0)

        # Step 6: Generate PDF report (80-100%)
        if progress_callback:
            progress_callback("generating", 0.85, 0, 0)
        print("STEP 6: Generating PDF report...")
        pdf_path = self._generate_report(top_candidates)
        if progress_callback:
            progress_callback("generating", 1.0, 0, 0)

        print()
        print("=" * 80)
        print(f"REPORT GENERATED: {pdf_path}")
        print("=" * 80)

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
                print(f"WARNING: Failed to persist run metadata: {e}")

        return pdf_path

    def _parse_job_details(self, job_title: str, certifications: List[Dict[str, str]],
                          location: str, job_description: str, required_skills: List[str] = None,
                          preferred_skills: List[str] = None) -> JobDetails:
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
            full_description=job_description
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

        # Extract industry context
        industry_keywords = {
            'finance': 'Finance/Banking',
            'healthcare': 'Healthcare',
            'retail': 'Retail/E-commerce',
            'manufacturing': 'Manufacturing',
            'technology': 'Technology',
            'education': 'Education',
            'government': 'Government/Public Sector'
        }

        for keyword, industry in industry_keywords.items():
            if keyword in description:
                job.industry_context = industry
                break

    def _research_equivalents(self):
        """Research equivalent titles, skills, and certifications"""
        # Use SkillsResearcher to find equivalents
        self.job_details.equivalent_titles = self.skills_researcher.find_equivalent_titles(
            self.job_details.job_title
        )

        # Find skill synonyms
        for skill in self.job_details.technical_stack:
            synonyms = self.skills_researcher.find_skill_synonyms(skill)
            if synonyms:
                self.job_details.skill_synonyms[skill] = synonyms

        print(f"  Found {len(self.job_details.equivalent_titles)} equivalent titles")
        print(f"  Mapped {len(self.job_details.skill_synonyms)} skill synonyms")

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
                print(f"  ERROR researching equivalents for {cert.name}: {e}")
                return cert.name, []
        
        # Research all certs in parallel
        tasks = [research_cert_equivalent(cert) for cert in certs_to_research]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                print(f"  ERROR: Exception during cert research: {result}")
                continue
            cert_name, equivalents = result
            if equivalents:
                print(f"  Found {len(equivalents)} equivalent(s) for {cert_name}")
                # Store equivalents in job_details for matching
                self.job_details.certification_equivalents[cert_name] = equivalents
            else:
                print(f"  No equivalents found for {cert_name}")
    
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
                print(f"  Parsing resume {index}/{total}: {Path(resume_file).name}")
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
                    print(f"    WARNING: Failed to read {resume_file}: {e}")
                    file_hash = None
                
                # Check cache first
                cached_candidate = self.resume_cache.get(file_hash) if file_hash else None
                
                if cached_candidate:
                    print("    Using cached parse for this resume")
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
                        print(f"    WARNING: Failed to parse {resume_file}: {e}")
                        return None
                
                if progress_callback:
                    # Update progress after each resume
                    progress = 0.20 + (index / total * 0.20)
                    progress_callback("parsing", progress, index, total)
                
                return candidate_data
            except Exception as e:
                print(f"    ERROR parsing resume {index} ({Path(resume_file).name}): {e}")
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
                print(f"  ERROR: Exception during parsing resume {i+1}: {result}")
                continue
            if result is not None:
                candidates.append(result)
        
        print(f"  Successfully parsed {len(candidates)} resume(s)")
        return candidates
    
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
                    print(f"  Scoring candidate {index}/{total}: {candidate.get('name', 'Unknown')}")
                    if progress_callback:
                        # Progress from 40% to 70% (30% range for scoring)
                        progress = 0.40 + ((index - 1) / total * 0.30)
                        progress_callback("scoring", progress, index, total)
                    
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
                    print(f"  ERROR scoring candidate {index} ({candidate.get('name', 'Unknown')}): {e}")
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
                print(f"  ERROR: Exception during scoring candidate {i+1}: {result}")
                # Create a default low score for exceptions
                from models import CandidateScore
                candidate = candidates[i]
                result = CandidateScore(
                    name=candidate.get('name', 'Unknown'),
                    phone=candidate.get('phone', ''),
                    email=candidate.get('email', ''),
                    certifications=candidate.get('certifications', []),
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
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Event loop is already running (e.g., in Streamlit), use nest_asyncio
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self._score_candidates_async(candidates, progress_callback))
            else:
                return loop.run_until_complete(self._score_candidates_async(candidates, progress_callback))
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self._score_candidates_async(candidates, progress_callback))

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
            print(f"  Calibrating scores: Mean too high ({mean_score:.2f}), applying factor {calibration_factor:.3f}")
        elif mean_score < 5.0:
            # Scores are too low, but we'll be conservative and not inflate
            # Only calibrate if mean is very low (<4.0)
            if mean_score < 4.0:
                calibration_factor = 5.0 / mean_score if mean_score > 0 else 1.0
                print(f"  Calibrating scores: Mean too low ({mean_score:.2f}), applying factor {calibration_factor:.3f}")
            else:
                print(f"  Score distribution acceptable (mean: {mean_score:.2f})")
        else:
            print(f"  Score distribution acceptable (mean: {mean_score:.2f})")
        
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
                        print(f"    RE-CAPPING: {candidate_score.name} missing must-have certs, capping calibrated score at 5.0")
                        calibrated_score = min(calibrated_score, 5.0)
                
                # Update score and calibration metadata
                candidate_score.fit_score = calibrated_score
                candidate_score.calibration_applied = True
                candidate_score.calibration_factor = calibration_factor
                
                print(f"    {candidate_score.name}: {original_score:.2f} -> {calibrated_score:.2f}")

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
                        print(f"  WARNING: Similar candidates with very different scores:")
                        print(f"    {candidate1.name}: {candidate1.fit_score:.2f}")
                        print(f"    {candidate2.name}: {candidate2.fit_score:.2f}")
                        print(f"    Similarity: {similarity:.1%}, Score difference: {score_diff:.2f}")

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
            print(f"  WARNING: Score clustering detected - {max_cluster_size} candidates at score {clustered_score:.1f}")
        
        # Verify ranking order makes sense
        # Check if score differences are reasonable
        for i in range(len(sorted_candidates) - 1):
            score_diff = sorted_candidates[i].fit_score - sorted_candidates[i+1].fit_score
            # If scores are very close (<0.1 difference), ranking might be arbitrary
            if 0 < score_diff < 0.1:
                print(f"  NOTE: Candidates {i+1} and {i+2} have very similar scores "
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
            print(f"  Only {len(viable_candidates)} viable candidate(s) found (score >= 5.0)")
            print(f"  Note: {len(sorted_candidates) - len(viable_candidates)} candidate(s) excluded (score < 5.0)")
        else:
            # Take top 10 or all viable, whichever is smaller
            top_candidates = viable_candidates[:min(10, len(viable_candidates))]

        # Ensure candidates are sorted (highest to lowest)
        top_candidates = sorted(top_candidates, key=lambda x: x.fit_score, reverse=True)
        
        print(f"  Selected {len(top_candidates)} top candidate(s) (all with score >= 5.0)")

        return top_candidates

    def _generate_report(self, top_candidates: List[CandidateScore]) -> str:
        """Generate PDF report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"Candidate_Ranking_Report_{timestamp}.pdf"
        output_path = os.path.join(os.getcwd(), output_filename)

        # Generate PDF
        self.pdf_generator.generate(
            job_details=self.job_details,
            top_candidates=top_candidates,
            all_candidates_count=len(self.candidate_scores),
            output_path=output_path
        )

        return output_path

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
            if resume_assets:
                for asset in resume_assets:
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
                            asset.get("file_hash"),  # storing hash in source_asset_id for traceability
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


def main():
    """Example usage"""
    print("\nRECRUITMENT CANDIDATE RANKER")
    print("This application requires input via code or API.")
    print("\nExample usage:")
    print("""
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

    print(f"Report generated: {pdf_path}")
    """)


if __name__ == "__main__":
    main()
