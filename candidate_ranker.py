"""
Recruitment Candidate Screening and Ranking Application
High-level recruitment advisor with advanced candidate screening capabilities
"""

import json
import os
import re
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


class CandidateRankerApp:
    """Main application for candidate screening and ranking"""

    def __init__(self, logo_path: str = None, use_ai: bool = True):
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

    def run(self, job_title: str, certifications: List[Dict[str, str]],
            location: str, job_description: str, resume_files: List[str],
            required_skills: List[str] = None, preferred_skills: List[str] = None,
            progress_callback=None) -> str:
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

        # Step 3: Parse all resumes (20-40%)
        print(f"STEP 3: Parsing {len(resume_files)} resume(s)...")
        candidates = self._parse_resumes(resume_files, progress_callback)

        # Step 4: Score each candidate (40-70%)
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
        
        # Use AI-extracted skills if provided, otherwise extract from description
        if required_skills:
            job.required_skills = required_skills
        if preferred_skills:
            job.preferred_skills = preferred_skills

        # Extract structured information from description (for other fields)
        self._extract_job_requirements(job)

        return job

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

        # Extract required vs preferred skills
        # Look for sections with "required" or "preferred"
        required_section = re.search(
            r'(?:required|must have|essential)[\s\S]*?(?:preferred|nice to have|bonus|$)',
            description,
            re.IGNORECASE
        )

        preferred_section = re.search(
            r'(?:preferred|nice to have|bonus)[\s\S]*?$',
            description,
            re.IGNORECASE
        )

        if required_section:
            req_text = required_section.group(0)
            job.required_skills = [
                tech for tech in job.technical_stack
                if tech.lower() in req_text.lower()
            ]
        else:
            # Default: most mentioned skills are required
            job.required_skills = job.technical_stack[:len(job.technical_stack)//2]

        if preferred_section:
            pref_text = preferred_section.group(0)
            job.preferred_skills = [
                tech for tech in job.technical_stack
                if tech.lower() in pref_text.lower() and tech not in job.required_skills
            ]
        else:
            job.preferred_skills = [
                tech for tech in job.technical_stack
                if tech not in job.required_skills
            ]

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

    def _expand_certification_equivalents(self):
        """Expand certifications that mention 'or equivalent' using AI"""
        # AI certification researcher is always available (required)
        
        job_context = self.job_details.full_description
        
        for cert in self.job_details.certifications:
            cert_name = cert.name
            
            # Check if certification mentions "or equivalent"
            if "equivalent" in cert_name.lower():
                equivalents = self.cert_researcher.find_equivalents(cert_name, job_context)
                if equivalents:
                    print(f"  Found {len(equivalents)} equivalent(s) for {cert_name}")
                    # Store equivalents in job_details for matching
                    self.job_details.certification_equivalents[cert_name] = equivalents
                else:
                    print(f"  No equivalents found for {cert_name}")

    def _parse_resumes(self, resume_files: List[str], progress_callback=None) -> List[Dict[str, Any]]:
        """Parse all resume files"""
        candidates = []
        total = len(resume_files)

        for i, resume_file in enumerate(resume_files, 1):
            print(f"  Parsing resume {i}/{total}: {Path(resume_file).name}")
            if progress_callback:
                # Progress from 20% to 40% (20% range for parsing)
                progress = 0.20 + ((i - 1) / total * 0.20)
                progress_callback("parsing", progress, i, total)
            try:
                candidate_data = self.resume_parser.parse(resume_file)
                candidates.append(candidate_data)
            except Exception as e:
                print(f"    WARNING: Failed to parse {resume_file}: {e}")
                continue
            if progress_callback:
                # Update progress after each resume
                progress = 0.20 + (i / total * 0.20)
                progress_callback("parsing", progress, i, total)

        print(f"  Successfully parsed {len(candidates)} resume(s)")
        return candidates

    def _score_candidates(self, candidates: List[Dict[str, Any]], progress_callback=None):
        """Score each candidate with chain-of-thought reasoning"""
        self.candidate_scores = []
        total = len(candidates)

        for i, candidate in enumerate(candidates, 1):
            print(f"  Scoring candidate {i}/{total}: {candidate.get('name', 'Unknown')}")
            if progress_callback:
                # Progress from 40% to 70% (30% range for scoring)
                progress = 0.40 + ((i - 1) / total * 0.30)
                progress_callback("scoring", progress, i, total)

            score_result = self.scoring_engine.score_candidate(
                candidate=candidate,
                job_details=self.job_details
            )

            self.candidate_scores.append(score_result)
            if progress_callback:
                # Update progress after each candidate
                progress = 0.40 + (i / total * 0.30)
                progress_callback("scoring", progress, i, total)
        
        # Apply score calibration after all candidates are scored
        self._calibrate_scores()

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
