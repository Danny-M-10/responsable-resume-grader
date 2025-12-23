"""
AI-Powered Scoring Engine Module
Uses OpenAI GPT-4 Turbo for intelligent candidate evaluation
"""

import os
import asyncio
import hashlib
from typing import Dict, Any, List, Tuple
from openai import OpenAI, AsyncOpenAI
from models import JobDetails, CandidateScore
from config import OpenAIConfig

class AIScoringEngine:
    """
    AI-powered candidate evaluation using OpenAI GPT-4 Turbo
    Provides intelligent, context-aware scoring with genuine chain-of-thought reasoning
    """

    def __init__(self, api_key: str = None):
        """
        Initialize AI scoring engine

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.api_key = api_key or OpenAIConfig.get_api_key()
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        self.model = OpenAIConfig.get_model()
    
    def _generate_deterministic_seed(self, candidate: Dict[str, Any], job_details: JobDetails) -> int:
        """
        Generate a deterministic seed from job and candidate data.
        Same candidate + same job = same seed = same AI response.
        
        Args:
            candidate: Parsed candidate data
            job_details: Structured job requirements
            
        Returns:
            Integer seed value (0-2^31-1)
        """
        # Create a deterministic string from key identifying information
        seed_string = (
            f"{job_details.job_title}|"
            f"{job_details.location}|"
            f"{candidate.get('email', '')}|"
            f"{candidate.get('name', '')}|"
            f"{','.join(sorted(job_details.required_skills))}|"
            f"{','.join(sorted([c.name for c in job_details.certifications]))}"
        )
        
        # Generate hash and convert to integer seed
        seed_hash = hashlib.sha256(seed_string.encode('utf-8')).hexdigest()
        # Use first 8 hex digits to create a 32-bit integer seed
        seed_int = int(seed_hash[:8], 16) % (2**31 - 1)
        
        return seed_int

    def score_candidate(self, candidate: Dict[str, Any],
                       job_details: JobDetails) -> CandidateScore:
        """
        Score a candidate using AI with genuine chain-of-thought reasoning

        Args:
            candidate: Parsed candidate data
            job_details: Structured job requirements

        Returns:
            CandidateScore with AI-generated fit score and detailed reasoning
        """

        # Build the evaluation prompt
        prompt = self._build_evaluation_prompt(candidate, job_details)

        # Generate deterministic seed for true determinism
        seed = self._generate_deterministic_seed(candidate, job_details)

        # Call OpenAI API for evaluation
        # Use temperature=0.0 and seed for maximum determinism and consistency
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.0,  # Zero temperature for deterministic, consistent evaluations
            seed=seed,  # Deterministic seed ensures same candidate + same job = same response
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract response
        if not response.choices or len(response.choices) == 0:
            raise ValueError("OpenAI response was empty")
        evaluation_text = response.choices[0].message.content

        # Parse the AI response to extract score, reasoning, and component scores
        score, reasoning, component_scores = self._parse_ai_response(evaluation_text)
        
        # Post-processing: Check if candidate is missing ALL must-have certs and adjust
        has_must_have = self._check_must_have_certs(candidate, job_details)
        must_have_certs_required = any(c.category == 'must-have' for c in job_details.certifications)
        
        # CRITICAL: If missing ALL must-have certs, enforce penalty even if component scores weren't extracted
        if must_have_certs_required and not has_must_have:
            if component_scores:
                # We have component scores - check and correct cert component
                cert_component_score = component_scores.get('must_have_certs', 5.0)
                
                if cert_component_score > 1.0:
                    # Force cert component to 0-1 range (use 0.5 as default)
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but cert component score is {cert_component_score:.2f}, forcing to 0.5")
                    component_scores['must_have_certs'] = 0.5
                    
                    # Recalculate weighted score with corrected component
                    weights = {
                        'must_have_certs': 0.30,
                        'bonus_certs': 0.10,
                        'required_skills': 0.25,
                        'preferred_skills': 0.10,
                        'experience_level': 0.10,
                        'job_title_match': 0.10,
                        'location': 0.05
                    }
                    
                    recalculated_score = sum(
                        component_scores.get(key, 5.0) * weight
                        for key, weight in weights.items()
                    )
                    recalculated_score = max(0.0, min(10.0, recalculated_score))
                    
                    # Use recalculated score
                    score = recalculated_score
                    print(f"  RECALCULATED: Score adjusted from AI score to {score:.2f} due to missing must-have certs")
            else:
                # No component scores extracted - apply direct penalty
                # Cap score at 5.0 maximum for missing all must-have certs
                if score > 5.0:
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but score is {score:.2f}, capping at 5.0 (component scores not extracted)")
                    score = min(score, 5.0)
        
        # Validate score consistency
        validated_score = self._validate_score_consistency(
            score, reasoning, component_scores, candidate, job_details
        )

        # Create CandidateScore matching the expected model structure
        # IMPORTANT: Only include certifications explicitly listed in the resume
        explicit_certifications = candidate.get('certifications', [])

        # Generate a concise (4-5 sentences) rationale from the AI output
        concise_rationale = self._extract_concise_rationale(reasoning or evaluation_text)
        
        return CandidateScore(
            name=candidate.get('name', 'Unknown'),
            phone=candidate.get('phone', ''),
            email=candidate.get('email', ''),
            certifications=explicit_certifications,  # Only explicit certifications from resume
            fit_score=round(validated_score, 2),
            chain_of_thought=evaluation_text,
            rationale=concise_rationale,
            experience_match={
                'level_match': (component_scores.get('experience_level', 8.0) / 10.0) if component_scores else 0.8,
                'titles': candidate.get('job_titles', []),
                'years': candidate.get('years_of_experience', 0)
            },
            certification_match={
                'has_must_have': self._check_must_have_certs(candidate, job_details),
                'has_bonus': len(explicit_certifications) > 0,
                'candidate_certs': explicit_certifications  # Only explicit certifications
            },
            skills_match={
                'required_match_rate': (component_scores.get('required_skills', 7.5) / 10.0) if component_scores else 0.75,
                'preferred_match_rate': (component_scores.get('preferred_skills', 6.0) / 10.0) if component_scores else 0.6,
                'candidate_skills': candidate.get('skills', [])  # Only explicit skills
            },
            location_match=self._check_location_match(candidate, job_details),
            component_scores=component_scores,  # Store component scores
            calibration_applied=False,  # Will be set during calibration phase
            calibration_factor=1.0
        )
    
    async def score_candidate_async(self, candidate: Dict[str, Any],
                                   job_details: JobDetails) -> CandidateScore:
        """
        Async version of score_candidate for parallel processing
        
        Args:
            candidate: Parsed candidate data
            job_details: Structured job requirements
            
        Returns:
            CandidateScore with AI-generated fit score and detailed reasoning
        """
        # Build the evaluation prompt (same as sync version)
        prompt = self._build_evaluation_prompt(candidate, job_details)
        
        # Generate deterministic seed for true determinism
        seed = self._generate_deterministic_seed(candidate, job_details)
        
        # Call OpenAI API asynchronously
        response = await self.async_client.chat.completions.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.0,  # Zero temperature for deterministic, consistent evaluations
            seed=seed,  # Deterministic seed ensures same candidate + same job = same response
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract response
        if not response.choices or len(response.choices) == 0:
            raise ValueError("OpenAI response was empty")
        evaluation_text = response.choices[0].message.content
        
        # Parse the AI response to extract score, reasoning, and component scores
        score, reasoning, component_scores = self._parse_ai_response(evaluation_text)
        
        # Post-processing: Check if candidate is missing ALL must-have certs and adjust
        has_must_have = self._check_must_have_certs(candidate, job_details)
        must_have_certs_required = any(c.category == 'must-have' for c in job_details.certifications)
        
        # CRITICAL: If missing ALL must-have certs, enforce penalty even if component scores weren't extracted
        if must_have_certs_required and not has_must_have:
            if component_scores:
                # We have component scores - check and correct cert component
                cert_component_score = component_scores.get('must_have_certs', 5.0)
                
                if cert_component_score > 1.0:
                    # Force cert component to 0-1 range (use 0.5 as default)
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but cert component score is {cert_component_score:.2f}, forcing to 0.5")
                    component_scores['must_have_certs'] = 0.5
                    
                    # Recalculate weighted score with corrected component
                    weights = {
                        'must_have_certs': 0.30,
                        'bonus_certs': 0.10,
                        'required_skills': 0.25,
                        'preferred_skills': 0.10,
                        'experience_level': 0.10,
                        'job_title_match': 0.10,
                        'location': 0.05
                    }
                    
                    recalculated_score = sum(
                        component_scores.get(key, 5.0) * weight
                        for key, weight in weights.items()
                    )
                    recalculated_score = max(0.0, min(10.0, recalculated_score))
                    
                    # Use recalculated score
                    score = recalculated_score
                    print(f"  RECALCULATED: Score adjusted from AI score to {score:.2f} due to missing must-have certs")
            else:
                # No component scores extracted - apply direct penalty
                # Cap score at 5.0 maximum for missing all must-have certs
                if score > 5.0:
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but score is {score:.2f}, capping at 5.0 (component scores not extracted)")
                    score = min(score, 5.0)
        
        # Validate score consistency
        validated_score = self._validate_score_consistency(
            score, reasoning, component_scores, candidate, job_details
        )
        
        # Create CandidateScore matching the expected model structure
        # IMPORTANT: Only include certifications explicitly listed in the resume
        explicit_certifications = candidate.get('certifications', [])
        
        # Generate a concise (4-5 sentences) rationale from the AI output
        concise_rationale = self._extract_concise_rationale(reasoning or evaluation_text)
        
        return CandidateScore(
            name=candidate.get('name', 'Unknown'),
            phone=candidate.get('phone', ''),
            email=candidate.get('email', ''),
            certifications=explicit_certifications,  # Only explicit certifications from resume
            fit_score=round(validated_score, 2),
            chain_of_thought=evaluation_text,
            rationale=concise_rationale,
            experience_match={
                'level_match': (component_scores.get('experience_level', 8.0) / 10.0) if component_scores else 0.8,
                'titles': candidate.get('job_titles', []),
                'years': candidate.get('years_of_experience', 0)
            },
            certification_match={
                'has_must_have': self._check_must_have_certs(candidate, job_details),
                'has_bonus': len(explicit_certifications) > 0,
                'candidate_certs': explicit_certifications  # Only explicit certifications
            },
            skills_match={
                'required_match_rate': (component_scores.get('required_skills', 7.5) / 10.0) if component_scores else 0.75,
                'preferred_match_rate': (component_scores.get('preferred_skills', 6.0) / 10.0) if component_scores else 0.6,
                'candidate_skills': candidate.get('skills', [])  # Only explicit skills
            },
            location_match=self._check_location_match(candidate, job_details),
            component_scores=component_scores or {}
        )

    def _check_must_have_certs(self, candidate: Dict[str, Any], job_details: JobDetails) -> bool:
        """Check if candidate has must-have certifications (including equivalents)"""
        must_have = [c.name.lower() for c in job_details.certifications if c.category == 'must-have']
        candidate_certs = [c.lower() for c in candidate.get('certifications', [])]

        if not must_have:
            return True

        # Check direct matches
        direct_match = any(req in cert or cert in req for req in must_have for cert in candidate_certs)
        if direct_match:
            return True

        # Check equivalent certifications
        for req_cert in must_have:
            equivalents = job_details.certification_equivalents.get(req_cert, [])
            all_possible = [req_cert] + [eq.lower() for eq in equivalents]
            if any(possible in cert or cert in possible for possible in all_possible for cert in candidate_certs):
                return True

        return False

    def _check_location_match(self, candidate: Dict[str, Any], job_details: JobDetails) -> bool:
        """Check if locations match"""
        candidate_loc = candidate.get('location', '').lower()
        job_loc = job_details.location.lower()

        if not candidate_loc or not job_loc:
            return False

        # Simple check - can be enhanced
        return any(word in job_loc for word in candidate_loc.split() if len(word) > 2)

    def _build_evaluation_prompt(self, candidate: Dict[str, Any],
                                 job_details: JobDetails) -> str:
        """Build a comprehensive prompt with weighted scoring system"""

        # Format certifications
        must_have_certs = [c.name for c in job_details.certifications if c.category == 'must-have']
        bonus_certs = [c.name for c in job_details.certifications if c.category == 'bonus']

        prompt = f"""You are an expert recruitment evaluator. Analyze this candidate against the job requirements using a STRUCTURED, WEIGHTED SCORING SYSTEM for consistency and accuracy.

CRITICAL: You MUST be CONSISTENT and DETERMINISTIC. Similar candidates should receive similar scores. Use the component scoring system below to ensure accuracy.

JOB REQUIREMENTS:
-----------------
Title: {job_details.job_title}
Location: {job_details.location}

Must-Have Certifications: {', '.join(must_have_certs) if must_have_certs else 'None specified'}
Bonus Certifications: {', '.join(bonus_certs) if bonus_certs else 'None specified'}

Required Skills: {', '.join(job_details.required_skills) if job_details.required_skills else 'None specified'}
Preferred Skills: {', '.join(job_details.preferred_skills) if job_details.preferred_skills else 'None specified'}

Full Job Description:
{job_details.full_description[:1000]}

CANDIDATE PROFILE:
------------------
Name: {candidate.get('name', 'Unknown')}
Email: {candidate.get('email', 'Not provided')}
Location: {candidate.get('location', 'Not specified')}
Years of Experience: {candidate.get('years_of_experience', 0)}

Certifications: {', '.join(candidate.get('certifications', [])) if candidate.get('certifications') else 'None listed'}
Skills: {', '.join(candidate.get('skills', [])[:20]) if candidate.get('skills') else 'None listed'}
Job Titles: {', '.join(candidate.get('job_titles', [])) if candidate.get('job_titles') else 'None listed'}

Education: {', '.join(candidate.get('education', [])) if candidate.get('education') else 'None listed'}

Resume Excerpt (first 500 chars):
{candidate.get('raw_text', '')[:500] if candidate.get('raw_text') else 'Not available'}

EVALUATION TASK - STRUCTURED COMPONENT SCORING:
-----------------------------------------------
You MUST provide component scores for EACH criterion below, then calculate the weighted final score.

SCORING RUBRIC (each component scored 0-10):
1. **Must-Have Certifications** (30% weight - CRITICAL):
   - 10: Has ALL required certifications
   - 7-9: Has most required certifications (1 missing)
   - 4-6: Has some required certifications (2-3 missing)
   - 1-2: Has few required certifications (4-5 missing)
   - **0: Missing ALL required certifications (CRITICAL - must be 0)**
   - **IMPORTANT: If candidate is missing ALL must-have certifications, component score MUST be 0-1, NOT 2-3. Must-have certifications are CRITICAL - missing all should severely penalize the candidate.**

2. **Bonus Certifications** (10% weight):
   - 10: Has all bonus certifications
   - 7-9: Has most bonus certifications
   - 4-6: Has some bonus certifications
   - 0-3: Has few or no bonus certifications

3. **Required Skills** (25% weight - VERY IMPORTANT):
   - 10: Has all required skills with strong depth
   - 7-9: Has most required skills (80%+ match)
   - 4-6: Has some required skills (50-79% match)
   - 0-3: Has few required skills (<50% match)

4. **Preferred Skills** (10% weight):
   - 10: Has all preferred skills
   - 7-9: Has most preferred skills
   - 4-6: Has some preferred skills
   - 0-3: Has few preferred skills

5. **Experience Level** (10% weight):
   - 10: Perfect match (exact years/level required)
   - 7-9: Strong match (close to requirements)
   - 4-6: Moderate match (somewhat close)
   - 0-3: Weak match (significantly different)

6. **Job Title Match** (10% weight):
   - 10: Exact or very similar title
   - 7-9: Related title in same field
   - 4-6: Somewhat related title
   - 0-3: Unrelated title

7. **Location** (5% weight):
   - 10: Exact location match
   - 7-9: Same city/region
   - 4-6: Different but reasonable distance
   - 0-3: Very different location

CRITICAL CONSISTENCY AND DETERMINISM REQUIREMENTS:
- **ABSOLUTE DETERMINISM**: Re-evaluating the EXACT same candidate against the EXACT same job requirements MUST produce IDENTICAL component scores and final score. Use the same scoring logic every time.
- **COMPONENT SCORE CONSISTENCY**: For identical candidate qualifications, assign the EXACT same component scores. Do not vary scores based on interpretation - use objective, repeatable criteria.
- **CROSS-VALIDATION**: Component scores must align with each other and with the final weighted score. If all components are high, final score must be high. If critical components are low, final score must reflect this.
- **EVIDENCE-BASED**: Base scores ONLY on explicitly stated information in the resume. Do not infer or assume qualifications not explicitly mentioned.
- **REPEATABILITY**: When you see the same candidate data and job requirements, apply the same scoring algorithm. Same inputs = same outputs.
- **COMPONENT SCORE ALIGNMENT**: If candidate has all must-have certs, that component MUST be 8-10. If missing ALL must-have certs, that component MUST be 0-1.
- **FINAL SCORE CALCULATION**: The final score MUST equal the weighted sum of component scores when all 7 components are provided. Ensure mathematical consistency.

EVALUATION STRUCTURE:
1. **MUST-HAVE CERTIFICATIONS ANALYSIS**:
   - Which required certifications does the candidate have?
   - Which are missing?
   - Component score (0-10): ___

2. **BONUS CERTIFICATIONS ANALYSIS**:
   - Which bonus certifications does the candidate have?
   - Component score (0-10): ___

3. **REQUIRED SKILLS ANALYSIS**:
   - Required skills present
   - Required skills missing
   - Match percentage
   - Component score (0-10): ___

4. **PREFERRED SKILLS ANALYSIS**:
   - Preferred skills present
   - Component score (0-10): ___

5. **EXPERIENCE EVALUATION**:
   - Relevance of experience
   - Years match assessment
   - Component score (0-10): ___

6. **JOB TITLE MATCH**:
   - Relevance of previous titles
   - Component score (0-10): ___

7. **LOCATION MATCH**:
   - Location compatibility
   - Component score (0-10): ___

8. **OVERALL ASSESSMENT** (4-5 sentences):
   - Provide a 4-5 sentence summary explaining why the candidate is or isn't a good fit
   - Key strengths
   - Notable gaps
   - Growth potential
   - Overall recommendation

9. **COMPONENT SCORES SUMMARY** (REQUIRED):
Provide component scores in this EXACT format:
COMPONENT_SCORES:
- Must-have certifications: X.X/10
- Bonus certifications: X.X/10
- Required skills: X.X/10
- Preferred skills: X.X/10
- Experience level: X.X/10
- Job title match: X.X/10
- Location: X.X/10

10. **WEIGHTED CALCULATION** (REQUIRED):
Calculate weighted score using these weights:
- Must-have certifications: component_score × 0.30
- Bonus certifications: component_score × 0.10
- Required skills: component_score × 0.25
- Preferred skills: component_score × 0.10
- Experience level: component_score × 0.10
- Job title match: component_score × 0.10
- Location: component_score × 0.05
Final Score = Sum of all weighted components

11. **FINAL SCORE**:
Provide final weighted score in this exact format:
FINAL_SCORE: X.X/10

**CRITICAL REMINDER - DETERMINISM AND CONSISTENCY**:
- Re-evaluating the EXACT same candidate against the EXACT same job requirements MUST produce IDENTICAL component scores and final score
- Use the same scoring criteria every time - do not vary based on interpretation
- Ensure component scores mathematically align with the final weighted score
- Same inputs (candidate data + job requirements) = same outputs (component scores + final score)

12. **RECOMMENDATIONS**:
   - Should this candidate be interviewed?
   - What questions to focus on?
   - Any red flags or concerns?

CRITICAL CONSTRAINTS:
- ONLY reference information that is EXPLICITLY stated in the candidate's resume
- DO NOT mention equivalent certifications - only what the candidate explicitly lists
- DO NOT infer skills or certifications from job titles or experience descriptions
- DO NOT fabricate or assume any information about the candidate
- Be factual and evidence-based - cite exact information from the resume
- Component scores MUST align with your analysis (e.g., if all certs missing, cert score MUST be low)
- Final score MUST be calculated from component scores using the weights above

Format your response with clear headers. Be specific and cite evidence from the candidate's resume. ONLY use information explicitly stated in the resume.
"""

        return prompt

    def _parse_ai_response(self, response_text: str) -> Tuple[float, str, Dict[str, float]]:
        """
        Parse OpenAI's response to extract component scores, calculate weighted score, and extract reasoning
        
        Removes prompt text and extracts only the actual evaluation content.

        Returns:
            (final_score, reasoning_text, component_scores_dict)
        """
        import re
        
        # Define scoring weights (must match prompt)
        weights = {
            'must_have_certs': 0.30,
            'bonus_certs': 0.10,
            'required_skills': 0.25,
            'preferred_skills': 0.10,
            'experience_level': 0.10,
            'job_title_match': 0.10,
            'location': 0.05
        }
        
        # Extract component scores
        component_scores = {}
        
        # First, try to find COMPONENT_SCORES section (preferred format)
        component_section = re.search(
            r'COMPONENT_SCORES:.*?(?=WEIGHTED CALCULATION|FINAL_SCORE|\Z)',
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        
        if component_section:
            component_text = component_section.group(0)
            # Extract each component score from summary section with enhanced patterns
            patterns = {
                'must_have_certs': [
                    r'(?:Must-have certifications|must-have certifications|must have certifications):\s*(\d+\.?\d*)/10',
                    r'(?:Must-have certifications|must-have certifications|must have certifications):\s*(\d+\.?\d*)',
                    r'must[- ]?have.*?cert.*?:\s*(\d+\.?\d*)/10',
                ],
                'bonus_certs': [
                    r'(?:Bonus certifications|bonus certifications):\s*(\d+\.?\d*)/10',
                    r'(?:Bonus certifications|bonus certifications):\s*(\d+\.?\d*)',
                    r'bonus.*?cert.*?:\s*(\d+\.?\d*)/10',
                ],
                'required_skills': [
                    r'(?:Required skills|required skills):\s*(\d+\.?\d*)/10',
                    r'(?:Required skills|required skills):\s*(\d+\.?\d*)',
                    r'required.*?skill.*?:\s*(\d+\.?\d*)/10',
                ],
                'preferred_skills': [
                    r'(?:Preferred skills|preferred skills):\s*(\d+\.?\d*)/10',
                    r'(?:Preferred skills|preferred skills):\s*(\d+\.?\d*)',
                    r'preferred.*?skill.*?:\s*(\d+\.?\d*)/10',
                ],
                'experience_level': [
                    r'(?:Experience level|experience level|experience):\s*(\d+\.?\d*)/10',
                    r'(?:Experience level|experience level|experience):\s*(\d+\.?\d*)',
                    r'experience.*?level.*?:\s*(\d+\.?\d*)/10',
                ],
                'job_title_match': [
                    r'(?:Job title match|job title match|job title):\s*(\d+\.?\d*)/10',
                    r'(?:Job title match|job title match|job title):\s*(\d+\.?\d*)',
                    r'job.*?title.*?match.*?:\s*(\d+\.?\d*)/10',
                ],
                'location': [
                    r'(?:Location|location):\s*(\d+\.?\d*)/10',
                    r'(?:Location|location):\s*(\d+\.?\d*)',
                    r'location.*?:\s*(\d+\.?\d*)/10',
                ]
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, component_text, re.IGNORECASE)
                    if match:
                        try:
                            score_val = float(match.group(1))
                            # Validate score is in valid range
                            if 0.0 <= score_val <= 10.0:
                                component_scores[key] = score_val
                                break  # Found valid score, move to next component
                        except (ValueError, IndexError):
                            continue
        else:
            # Fallback: Extract inline component scores from individual sections
            # Look for patterns like "Component score (0-10): X.X" or "Component score (0-10): X.X/10"
            inline_patterns = {
                'must_have_certs': [
                    r'(?:MUST-HAVE CERTIFICATIONS|Must-have certifications).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:MUST-HAVE CERTIFICATIONS|Must-have certifications).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'bonus_certs': [
                    r'(?:BONUS CERTIFICATIONS|Bonus certifications).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:BONUS CERTIFICATIONS|Bonus certifications).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'required_skills': [
                    r'(?:REQUIRED SKILLS|Required skills).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:REQUIRED SKILLS|Required skills).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'preferred_skills': [
                    r'(?:PREFERRED SKILLS|Preferred skills).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:PREFERRED SKILLS|Preferred skills).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'experience_level': [
                    r'(?:EXPERIENCE|Experience).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:EXPERIENCE|Experience).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'job_title_match': [
                    r'(?:JOB TITLE|Job title).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:JOB TITLE|Job title).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'location': [
                    r'(?:LOCATION|Location).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:LOCATION|Location).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
            }
            
            for key, patterns_list in inline_patterns.items():
                for pattern in patterns_list:
                    match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        try:
                            score_val = float(match.group(1))
                            component_scores[key] = score_val
                            break  # Found a match, move to next component
                        except (ValueError, IndexError):
                            continue
        
        # Calculate weighted score programmatically if we have component scores
        if component_scores and len(component_scores) == len(weights):
            calculated_score = sum(
                component_scores.get(key, 5.0) * weight
                for key, weight in weights.items()
            )
            # Ensure score is in valid range
            calculated_score = max(0.0, min(10.0, calculated_score))
        else:
            calculated_score = None
        
        # Extract final score from AI response
        score_match = re.search(r'FINAL_SCORE:\s*(\d+\.?\d*)/10', response_text, re.IGNORECASE)

        if score_match:
            ai_score = float(score_match.group(1))
        else:
            # If no explicit score found, use calculated score or default
            ai_score = calculated_score if calculated_score is not None else 5.0
        
        # ALWAYS prefer calculated_score when all component scores are available
        # This ensures consistency - same component scores = same final score
        if calculated_score is not None:
            # All component scores extracted - use calculated score as source of truth
            final_score = calculated_score
            
            # Validate calculated_score matches ai_score within tolerance (0.5 points)
            if abs(calculated_score - ai_score) > 0.5:
                print(f"  WARNING: Calculated score ({calculated_score:.2f}) differs from AI score ({ai_score:.2f}) by >0.5")
                print(f"  Using calculated_score as source of truth for consistency")
        else:
            # Component extraction failed - use AI score but log warning
            final_score = ai_score
            print(f"  WARNING: Component score extraction incomplete, using AI score: {ai_score:.2f}")

        # Extract only the evaluation content, removing any prompt text that might have been repeated
        # Look for the start of actual evaluation (after any prompt-like headers)
        reasoning = response_text

        # Remove common prompt-like patterns that might appear in the response
        # Remove lines that look like prompt instructions
        lines = reasoning.split('\n')
        cleaned_lines = []
        skip_until_content = True
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip lines that look like prompt instructions
            if skip_until_content:
                # Look for the start of actual content (evaluation sections)
                if (line_stripped.startswith('1.') or 
                    line_stripped.startswith('**') or
                    'MUST-HAVE CERTIFICATIONS' in line_stripped.upper() or
                    'SKILLS MATCH' in line_stripped.upper() or
                    'EXPERIENCE' in line_stripped.upper() or
                    'OVERALL FIT' in line_stripped.upper() or
                    'RECOMMENDATIONS' in line_stripped.upper()):
                    skip_until_content = False
                    cleaned_lines.append(line)
                # Skip prompt-like lines
                elif (line_stripped.startswith('You are') or
                      line_stripped.startswith('JOB REQUIREMENTS') or
                      line_stripped.startswith('CANDIDATE PROFILE') or
                      line_stripped.startswith('EVALUATION TASK') or
                      line_stripped.startswith('CRITICAL CONSTRAINTS') or
                      line_stripped.startswith('Format your response') or
                      line_stripped.startswith('At the end') or
                      '-----------------' in line_stripped or
                      line_stripped == ''):
                    continue
                else:
                    # If we see content that doesn't look like a prompt, start including it
                    if len(line_stripped) > 10 and not line_stripped.startswith('Title:') and not line_stripped.startswith('Location:'):
                        skip_until_content = False
                        cleaned_lines.append(line)
            else:
                # Once we're past prompt text, include everything except the FINAL_SCORE line
                if not re.match(r'FINAL_SCORE:\s*\d+\.?\d*/10', line_stripped, re.IGNORECASE):
                    cleaned_lines.append(line)
        
        reasoning = '\n'.join(cleaned_lines).strip()
        
        # If we removed everything, fall back to original (but remove FINAL_SCORE line)
        if not reasoning:
            reasoning = re.sub(r'FINAL_SCORE:\s*\d+\.?\d*/10.*', '', response_text, flags=re.IGNORECASE).strip()
        
        # Remove markdown headers (###, ##, #) from rationale
        # Remove lines that are only markdown headers
        reasoning_lines = reasoning.split('\n')
        cleaned_reasoning_lines = []
        for line in reasoning_lines:
            line_stripped = line.strip()
            # Skip lines that are only markdown headers (e.g., "### MUST-HAVE CERTIFICATIONS ANALYSIS:")
            if re.match(r'^#{1,6}\s+.*$', line_stripped):
                # Check if it's a header followed by content on the same line
                header_match = re.match(r'^#{1,6}\s+(.+)$', line_stripped)
                if header_match:
                    # If there's content after the header, keep just the content
                    content = header_match.group(1).strip()
                    if content:
                        cleaned_reasoning_lines.append(content)
                # Otherwise skip the header-only line
                continue
            # Remove markdown headers from the beginning of lines but keep the content
            line_cleaned = re.sub(r'^#{1,6}\s+', '', line)
            if line_cleaned.strip():
                cleaned_reasoning_lines.append(line_cleaned)
        
        reasoning = '\n'.join(cleaned_reasoning_lines).strip()
        
        return final_score, reasoning, component_scores

    def _extract_concise_rationale(self, text: str) -> str:
        """
        Produce a concise, 4-5 sentence rationale from the AI output.
        Falls back to a trimmed snippet if not enough structure is available.
        Ensures sentences are complete and don't cut off mid-sentence.
        """
        if not text:
            return ""

        import re
        # Split on sentence boundaries (period, exclamation, question mark followed by space)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        concise = []
        for s in sentences:
            if s and s.strip():
                concise.append(s.strip())
            # Extract 4-5 sentences (prefer 5 if available)
            if len(concise) >= 5:
                break

        if concise:
            # Join sentences and ensure we have at least 4 if available
            if len(concise) < 4 and len(sentences) > len(concise):
                # Try to get one more sentence if we have less than 4
                for s in sentences[len(concise):]:
                    if s and s.strip():
                        concise.append(s.strip())
                        if len(concise) >= 4:
                            break
            
            candidate_summary = " ".join(concise)
            # Allow up to 1500 characters for 4-5 sentences
            if len(candidate_summary) > 1500:
                # Truncate at the last complete sentence within limit
                truncated = candidate_summary[:1500]
                # Find the last complete sentence
                last_period = truncated.rfind('.')
                last_exclamation = truncated.rfind('!')
                last_question = truncated.rfind('?')
                last_sentence_end = max(last_period, last_exclamation, last_question)
                if last_sentence_end > 1000:  # Only truncate if we have a reasonable amount
                    candidate_summary = truncated[:last_sentence_end + 1]
            return candidate_summary

        # Fallback: return first 1500 chars but try to end at sentence boundary
        if len(text) > 1500:
            truncated = text[:1500]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > 1000:
                return text[:last_sentence_end + 1]
        return text[:1500]

    def _validate_score_consistency(self, score: float, reasoning: str, 
                                   component_scores: Dict[str, float],
                                   candidate: Dict[str, Any], 
                                   job_details: JobDetails) -> float:
        """
        Validate that score is consistent with evaluation content
        
        Args:
            score: Proposed final score
            reasoning: Evaluation reasoning text
            component_scores: Component scores dictionary
            candidate: Candidate data
            job_details: Job requirements
            
        Returns:
            Validated (and potentially adjusted) score
        """
        # Ensure score is in valid range
        validated_score = max(0.0, min(10.0, score))
        
        # Validate component scores are in range and consistent
        if component_scores:
            # Validate each component score is in valid range
            for key, comp_score in component_scores.items():
                if comp_score < 0.0 or comp_score > 10.0:
                    print(f"  WARNING: Component score '{key}' out of range: {comp_score}, clamping to 0-10")
                    component_scores[key] = max(0.0, min(10.0, comp_score))
            
            # Cross-validate: Recalculate score from components if all are present
            weights = {
                'must_have_certs': 0.30,
                'bonus_certs': 0.10,
                'required_skills': 0.25,
                'preferred_skills': 0.10,
                'experience_level': 0.10,
                'job_title_match': 0.10,
                'location': 0.05
            }
            
            if len(component_scores) == len(weights):
                # All components present - recalculate to ensure consistency
                recalculated = sum(
                    component_scores.get(key, 5.0) * weight
                    for key, weight in weights.items()
                )
                recalculated = max(0.0, min(10.0, recalculated))
                
                # If recalculated differs significantly from validated_score, use recalculated
                if abs(recalculated - validated_score) > 0.1:
                    print(f"  CORRECTING: Score inconsistency detected. Original: {validated_score:.2f}, Recalculated from components: {recalculated:.2f}")
                    validated_score = recalculated
        
        # Cross-validate: Check if must-have certs match aligns with cert component score
        has_must_have = self._check_must_have_certs(candidate, job_details)
        must_have_certs_required = any(c.category == 'must-have' for c in job_details.certifications)
        
        if must_have_certs_required and component_scores:
            cert_score = component_scores.get('must_have_certs', 5.0)
            # If candidate has must-have certs, score should be high (7+)
            # If missing ALL, score should be 0-1 (already enforced in post-processing)
            if has_must_have and cert_score < 7.0:
                print(f"  WARNING: Candidate has must-have certs but cert component score is low ({cert_score})")
            elif not has_must_have and cert_score > 1.0:
                # Force correction if still too high (should have been caught in post-processing, but double-check)
                print(f"  CORRECTING: Candidate missing ALL must-have certs but cert component score is {cert_score:.2f}, forcing to 0.5")
                component_scores['must_have_certs'] = 0.5
                # Recalculate weighted score
                weights = {
                    'must_have_certs': 0.30,
                    'bonus_certs': 0.10,
                    'required_skills': 0.25,
                    'preferred_skills': 0.10,
                    'experience_level': 0.10,
                    'job_title_match': 0.10,
                    'location': 0.05
                }
                validated_score = sum(
                    component_scores.get(key, 5.0) * weight
                    for key, weight in weights.items()
                )
                validated_score = max(0.0, min(10.0, validated_score))
        
        # Sanity check: Candidate with all requirements shouldn't score below 7.0
        if component_scores:
            # Rough check: if most components are high, overall should be high
            high_components = sum(1 for score in component_scores.values() if score >= 7.0)
            if high_components >= 5 and validated_score < 6.5:
                print(f"  WARNING: Most components are high ({high_components}/7) but final score is low ({validated_score})")
                # Don't auto-adjust, but log the warning
        
        # STRICT ENFORCEMENT: Candidate missing ALL must-have certs should be capped at 5.0
        if must_have_certs_required and not has_must_have:
            # Missing ALL critical certs should severely limit score
            # Even with perfect other components, max score is ~5.0
            if validated_score > 5.0:
                print(f"  CORRECTING: Candidate missing ALL must-have certs but score is {validated_score:.2f}, capping at 5.0")
                validated_score = min(validated_score, 5.0)
        
        return validated_score

    def _extract_recommendations(self, response_text: str) -> List[str]:
        """Extract key recommendations from AI response"""
        recommendations = []

        # Look for recommendations section
        import re
        rec_section = re.search(
            r'(?:RECOMMENDATIONS|6\.\s*\*\*RECOMMENDATIONS\*\*):(.+?)(?:\n\n|\Z)',
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if rec_section:
            rec_text = rec_section.group(1)
            # Extract bullet points or lines
            lines = [line.strip() for line in rec_text.split('\n') if line.strip()]
            recommendations = [line.lstrip('-•* ') for line in lines if line]

        return recommendations[:5]  # Top 5 recommendations


# AI-only scoring engine (no fallback)
class HybridScoringEngine:
    """
    AI-only scoring engine using OpenAI GPT-4 Turbo
    Note: This class name is kept for backward compatibility but it's now AI-only
    """

    def __init__(self, use_ai: bool = True, api_key: str = None):
        """
        Initialize AI scoring engine

        Args:
            use_ai: Must be True (AI is now required)
            api_key: OpenAI API key (optional, uses env var if not provided)
        """
        if not use_ai:
            raise ValueError("AI is now required for scoring. 'use_ai' must be True.")

        try:
            self.ai_engine = AIScoringEngine(api_key=api_key)
            print(f"AI-powered scoring enabled (using OpenAI {self.ai_engine.model})")
        except Exception as e:
            raise RuntimeError(f"AI scoring is required but unavailable: {e}. Please configure OpenAI API key.")

    def score_candidate(self, candidate: Dict[str, Any],
                       job_details: JobDetails) -> CandidateScore:
        """Score candidate using AI"""
        if not self.ai_engine:
            raise RuntimeError("AI scoring engine is not initialized.")
        return self.ai_engine.score_candidate(candidate, job_details)
    
    async def score_candidate_async(self, candidate: Dict[str, Any],
                                   job_details: JobDetails) -> CandidateScore:
        """Async version of score_candidate for parallel processing"""
        if not self.ai_engine:
            raise RuntimeError("AI scoring engine is not initialized.")
        return await self.ai_engine.score_candidate_async(candidate, job_details)
