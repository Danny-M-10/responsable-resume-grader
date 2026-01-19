"""
AI-Powered Scoring Engine Module
Uses OpenAI GPT-4 Turbo for intelligent candidate evaluation
"""

import os
import asyncio
from typing import Dict, Any, List, Tuple
from openai import OpenAI, AsyncOpenAI
from models import JobDetails, CandidateScore
from config import OpenAIConfig
from industry_templates import get_default_weights

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

        # Call OpenAI API for evaluation
        # Use temperature=0.0 for maximum determinism and consistency
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.0,  # Zero temperature for deterministic, consistent evaluations
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

        # Get weights from job_details
        weights = job_details.scoring_profile if job_details.scoring_profile else get_default_weights()
        # Ensure all required weight keys exist
        default_weights = get_default_weights()
        for key in default_weights.keys():
            if key not in weights:
                weights[key] = default_weights[key]
        
        # Parse the AI response to extract score, reasoning, and component scores
        score, reasoning, component_scores = self._parse_ai_response(evaluation_text, weights)
        
        # Post-processing: Check if candidate is missing ALL must-have certs and adjust certifications_education score
        # Note: certifications_education combines certs and education, but we still check must-have certs as they're critical
        has_must_have = self._check_must_have_certs(candidate, job_details)
        must_have_certs_required = any(c.category == 'must-have' for c in job_details.certifications)
        
        # CRITICAL: If missing ALL must-have certs, adjust certifications_education component score
        if must_have_certs_required and not has_must_have:
            if component_scores:
                # We have component scores - check and correct certs/education component
                cert_ed_component_score = component_scores.get('certifications_education', 5.0)
                
                if cert_ed_component_score > 2.0:
                    # Missing all must-have certs should significantly lower the score
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but certs/education component score is {cert_ed_component_score:.2f}, adjusting to 2.0")
                    component_scores['certifications_education'] = 2.0
                    
                    # Recalculate weighted score with corrected component (use existing weights)
                    # Only use components that exist, default missing ones to 0.0
                    recalculated_score = sum(
                        component_scores.get(key, 0.0) * weight
                        for key, weight in weights.items()
                    )
                    recalculated_score = max(0.0, min(10.0, recalculated_score))
                    
                    # Use recalculated score
                    score = recalculated_score
                    print(f"  RECALCULATED: Score adjusted from AI score to {score:.2f} due to missing must-have certs")
            else:
                # No component scores extracted - apply direct penalty (less severe since certs are now lower priority)
                # Cap score at 6.0 maximum for missing all must-have certs (reduced from 5.0 since certs are lower priority)
                if score > 6.0:
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but score is {score:.2f}, capping at 6.0 (component scores not extracted)")
                    score = min(score, 6.0)
        
        # Validate score consistency
        validated_score = self._validate_score_consistency(
            score, reasoning, component_scores, candidate, job_details
        )

        # Create CandidateScore matching the expected model structure
        # IMPORTANT: Only include certifications explicitly listed in the resume
        explicit_certifications = candidate.get('certifications', [])

        # Generate a concise (4-5 sentences) rationale from the AI output
        input_for_rationale = reasoning or evaluation_text
        concise_rationale = self._extract_concise_rationale(input_for_rationale)
        
        # Extract transferrable skills information from component scores and reasoning
        transferrable_skills_score = component_scores.get('transferrable_skills', 0.0) if component_scores else 0.0
        transferrable_skills_match = {
            'match_rate': transferrable_skills_score / 10.0,
            'transferrable_skills': [],  # Will be populated from AI analysis if available
            'relevance_score': transferrable_skills_score / 10.0
        }
        
        # Try to extract transferrable skills list from reasoning text
        # Look for patterns like "Transferrable skills identified: X, Y, Z" or similar
        import re
        # More robust pattern to match various AI formatting styles
        transferrable_section = re.search(
            r'(?:TRANSFERRABLE\s+SKILLS?|Transferrable\s+skills?|TRANSFERABLE\s+SKILLS?|Transferable\s+skills?|4\.\s*\*\*TRANSFERRABLE).*?(?=\d+\.\s*\*\*|OVERALL|COMPONENT|FINAL_SCORE|5\.\s*\*\*LOCATION|\Z)',
            reasoning or evaluation_text,
            re.DOTALL | re.IGNORECASE
        )
        if transferrable_section:
            # Try to extract skill names from the text using multiple patterns
            section_text = transferrable_section.group(0)
            # Pattern 1: "skill: X" or "ability: X" format
            skill_patterns = re.findall(r'(?:skill|ability|competency)[:\s]+([A-Za-z\s]+?)(?:\.|,|$)', section_text, re.IGNORECASE)
            # Pattern 2: Bullet points like "- Project management" or "• Communication"
            bullet_patterns = re.findall(r'[-•]\s*([A-Za-z][A-Za-z\s]{2,30})(?:\.|,|$|\n)', section_text)
            # Pattern 3: Numbered lists like "1. Leadership"
            numbered_patterns = re.findall(r'\d+\.\s*([A-Za-z][A-Za-z\s]{2,30})(?:\.|,|$|\n)', section_text)
            # Combine all found skills
            all_skills = skill_patterns + bullet_patterns + numbered_patterns
            if all_skills:
                # Clean and deduplicate
                cleaned_skills = list(dict.fromkeys([s.strip() for s in all_skills if s.strip() and len(s.strip()) > 2]))
                transferrable_skills_match['transferrable_skills'] = cleaned_skills[:10]  # Limit to 10
        
        result = CandidateScore(
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
            transferrable_skills_match=transferrable_skills_match,  # NEW: Transferrable skills analysis
            component_scores=component_scores,  # Store component scores
            calibration_applied=False,  # Will be set during calibration phase
            calibration_factor=1.0
        )

        return result
    
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
        
        # Call OpenAI API asynchronously
        response = await self.async_client.chat.completions.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.0,  # Zero temperature for deterministic, consistent evaluations
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
        
        # Get weights from job_details
        weights = job_details.scoring_profile if job_details.scoring_profile else get_default_weights()
        # Ensure all required weight keys exist
        default_weights = get_default_weights()
        for key in default_weights.keys():
            if key not in weights:
                weights[key] = default_weights[key]
        
        # Parse the AI response to extract score, reasoning, and component scores
        score, reasoning, component_scores = self._parse_ai_response(evaluation_text, weights)
        
        # Post-processing: Check if candidate is missing ALL must-have certs and adjust certifications_education score
        # Note: certifications_education combines certs and education, but we still check must-have certs as they're critical
        has_must_have = self._check_must_have_certs(candidate, job_details)
        must_have_certs_required = any(c.category == 'must-have' for c in job_details.certifications)
        
        # CRITICAL: If missing ALL must-have certs, adjust certifications_education component score
        if must_have_certs_required and not has_must_have:
            if component_scores:
                # We have component scores - check and correct certs/education component
                cert_ed_component_score = component_scores.get('certifications_education', 5.0)
                
                if cert_ed_component_score > 2.0:
                    # Missing all must-have certs should significantly lower the score
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but certs/education component score is {cert_ed_component_score:.2f}, adjusting to 2.0")
                    component_scores['certifications_education'] = 2.0
                    
                    # Recalculate weighted score with corrected component (use existing weights)
                    # Only use components that exist, default missing ones to 0.0
                    recalculated_score = sum(
                        component_scores.get(key, 0.0) * weight
                        for key, weight in weights.items()
                    )
                    recalculated_score = max(0.0, min(10.0, recalculated_score))
                    
                    # Use recalculated score
                    score = recalculated_score
                    print(f"  RECALCULATED: Score adjusted from AI score to {score:.2f} due to missing must-have certs")
            else:
                # No component scores extracted - apply direct penalty (less severe since certs are now lower priority)
                # Cap score at 6.0 maximum for missing all must-have certs (reduced from 5.0 since certs are lower priority)
                if score > 6.0:
                    print(f"  CORRECTING: Candidate missing ALL must-have certs but score is {score:.2f}, capping at 6.0 (component scores not extracted)")
                    score = min(score, 6.0)
        
        # Validate score consistency
        validated_score = self._validate_score_consistency(
            score, reasoning, component_scores, candidate, job_details
        )
        
        # Create CandidateScore matching the expected model structure
        # IMPORTANT: Only include certifications explicitly listed in the resume
        explicit_certifications = candidate.get('certifications', [])
        
        # Generate a concise (4-5 sentences) rationale from the AI output
        input_for_rationale = reasoning or evaluation_text
        concise_rationale = self._extract_concise_rationale(input_for_rationale)
        
        # Extract transferrable skills information from component scores and reasoning
        transferrable_skills_score = component_scores.get('transferrable_skills', 0.0) if component_scores else 0.0
        transferrable_skills_match = {
            'match_rate': transferrable_skills_score / 10.0,
            'transferrable_skills': [],  # Will be populated from AI analysis if available
            'relevance_score': transferrable_skills_score / 10.0
        }
        
        # Try to extract transferrable skills list from reasoning text
        import re
        # More robust pattern to match various AI formatting styles
        transferrable_section = re.search(
            r'(?:TRANSFERRABLE\s+SKILLS?|Transferrable\s+skills?|TRANSFERABLE\s+SKILLS?|Transferable\s+skills?|4\.\s*\*\*TRANSFERRABLE).*?(?=\d+\.\s*\*\*|OVERALL|COMPONENT|FINAL_SCORE|5\.\s*\*\*LOCATION|\Z)',
            reasoning or evaluation_text,
            re.DOTALL | re.IGNORECASE
        )
        if transferrable_section:
            # Try to extract skill names from the text using multiple patterns
            section_text = transferrable_section.group(0)
            # Pattern 1: "skill: X" or "ability: X" format
            skill_patterns = re.findall(r'(?:skill|ability|competency)[:\s]+([A-Za-z\s]+?)(?:\.|,|$)', section_text, re.IGNORECASE)
            # Pattern 2: Bullet points like "- Project management" or "• Communication"
            bullet_patterns = re.findall(r'[-•]\s*([A-Za-z][A-Za-z\s]{2,30})(?:\.|,|$|\n)', section_text)
            # Pattern 3: Numbered lists like "1. Leadership"
            numbered_patterns = re.findall(r'\d+\.\s*([A-Za-z][A-Za-z\s]{2,30})(?:\.|,|$|\n)', section_text)
            # Combine all found skills
            all_skills = skill_patterns + bullet_patterns + numbered_patterns
            if all_skills:
                # Clean and deduplicate
                cleaned_skills = list(dict.fromkeys([s.strip() for s in all_skills if s.strip() and len(s.strip()) > 2]))
                transferrable_skills_match['transferrable_skills'] = cleaned_skills[:10]  # Limit to 10

        result = CandidateScore(
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
            transferrable_skills_match=transferrable_skills_match,  # NEW: Transferrable skills analysis
            component_scores=component_scores or {},
            calibration_applied=False,  # Will be set during calibration phase
            calibration_factor=1.0
        )

        return result

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

        # Get scoring weights from job_details (or use defaults)
        weights = job_details.scoring_profile if job_details.scoring_profile else get_default_weights()
        
        # Ensure all required weight keys exist
        default_weights = get_default_weights()
        for key in default_weights.keys():
            if key not in weights:
                weights[key] = default_weights[key]
        
        # Format weights as percentages for display (NEW PRIORITY ORDER)
        experience_weight = weights.get('experience_level', 0.25) * 100
        job_title_weight = weights.get('job_title_match', 0.20) * 100
        required_skills_weight = weights.get('required_skills', 0.18) * 100
        transferrable_skills_weight = weights.get('transferrable_skills', 0.15) * 100
        location_weight = weights.get('location', 0.10) * 100
        preferred_skills_weight = weights.get('preferred_skills', 0.07) * 100
        certifications_education_weight = weights.get('certifications_education', 0.05) * 100

        # Format certifications (combine must-have and bonus for display)
        must_have_certs = [c.name for c in job_details.certifications if c.category == 'must-have']
        bonus_certs = [c.name for c in job_details.certifications if c.category == 'bonus']
        all_certs = must_have_certs + bonus_certs

        prompt = f"""You are an expert recruitment evaluator. Analyze this candidate against the job requirements using a STRUCTURED, WEIGHTED SCORING SYSTEM for consistency and accuracy.

DETERMINISTIC SCORING RULE: This evaluation must be deterministic. If you evaluate the exact same candidate profile against the exact same job requirements multiple times, you MUST produce identical component scores and final scores. Treat this as a mathematical function: f(candidate, job) = score, where identical inputs always produce identical outputs.

CRITICAL: You MUST be CONSISTENT and DETERMINISTIC. Similar candidates should receive similar scores. Use the component scoring system below to ensure accuracy. For each component, evaluate ONLY the facts provided - do not use interpretation or context that could vary. If two candidates have identical qualifications for a component, they MUST receive identical component scores. Do not apply 'bonus points' or 'penalties' beyond what the rubric specifies.

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

SCORING RUBRIC (each component scored 0-10 with PRECISE values) - NEW PRIORITY ORDER:

1. **Experience Level** ({experience_weight:.0f}% weight - HIGHEST PRIORITY):
   - 10.0: Perfect match (exact years/level required, e.g., "5 years" candidate for "5 years" job)
   - 8.0: Strong match (within 1-2 years of requirement, e.g., "4 years" candidate for "5 years" job)
   - 6.0: Moderate match (within 3-5 years of requirement, e.g., "3 years" candidate for "5 years" job)
   - 3.0: Weak match (6+ years difference, e.g., "2 years" candidate for "8 years" job)
   - 0.0: Very weak match (significantly different, e.g., "1 year" candidate for "10 years" job)

2. **Job Title Match** ({job_title_weight:.0f}% weight - SECOND PRIORITY):
   - 10.0: Exact or very similar title (same words, e.g., "Safety Manager" for "Safety Manager")
   - 8.0: Related title in same field (similar function, e.g., "Safety Specialist" for "Safety Manager")
   - 5.0: Somewhat related title (same industry, different function, e.g., "Safety Coordinator" for "Safety Manager")
   - 2.0: Unrelated title (different industry or function)
   - 0.0: No relevant job titles found

3. **Required Skills** ({required_skills_weight:.0f}% weight - THIRD PRIORITY):
   - 10.0: Has ALL required skills with strong depth (100% match)
   - 8.0: Has most required skills (80-99% match, missing 1-2 of many)
   - 6.0: Has some required skills (50-79% match, missing several)
   - 3.0: Has few required skills (25-49% match, missing most)
   - 0.0: Has no required skills or very few (<25% match)

4. **Transferrable Skills** ({transferrable_skills_weight:.0f}% weight - FOURTH PRIORITY):
   AI-POWERED ANALYSIS: Identify skills from the candidate's experience that are relevant to this role but NOT explicitly listed in required/preferred skills. Consider:
   - Skills relevant to the job but not in the required/preferred lists
   - Cross-industry skills that could transfer to this role (e.g., project management, customer service, data analysis)
   - Semantically similar skills (different wording but same meaning, e.g., "client relations" = "customer service")
   - Skills demonstrated through experience descriptions that align with job needs
   
   Scoring:
   - 10.0: Exceptional transferrable skills - multiple highly relevant skills from experience that directly apply
   - 8.0: Strong transferrable skills - several relevant skills that would benefit the role
   - 6.0: Moderate transferrable skills - some relevant skills identified
   - 3.0: Limited transferrable skills - few relevant skills found
   - 0.0: No identifiable transferrable skills relevant to the role
   
   IMPORTANT: Cite specific examples from the candidate's resume. Be specific about which skills transfer and why they're relevant.

5. **Location** ({location_weight:.0f}% weight - FIFTH PRIORITY):
   - 10.0: Exact location match (same city and state)
   - 7.0: Same city/region (same city, different state, or same state, nearby city)
   - 4.0: Different but reasonable distance (same state, different city, or nearby state)
   - 0.0: Very different location (different state, far away)

6. **Preferred Skills** ({preferred_skills_weight:.0f}% weight - SIXTH PRIORITY):
   - 10.0: Has ALL preferred skills (100% match)
   - 7.0: Has most preferred skills (missing exactly 1, where total > 1)
   - 5.0: Has some preferred skills (missing 2-3, where total > 3)
   - 2.0: Has few preferred skills (missing most, has 1-2 of many)
   - 0.0: Has no preferred skills

7. **Certifications/Education** ({certifications_education_weight:.0f}% weight - LOWEST PRIORITY):
   Combined evaluation of certifications (must-have + bonus) AND education level/degrees:
   - 10.0: Has ALL must-have certifications AND education level matches or exceeds requirement
   - 8.0: Has most must-have certifications (missing 1) AND education level matches
   - 6.0: Has some must-have certifications (missing 2-3) OR education level close to requirement
   - 3.0: Has few must-have certifications (missing most) OR education level below requirement
   - 0.0: Missing ALL must-have certifications AND education level significantly below requirement
   
   Note: Education includes degrees, certifications, licenses, and relevant training. Consider both must-have and bonus certifications together.

- **FINAL SCORE CALCULATION**: The final score MUST be calculated using ONLY the weighted sum formula - do not adjust or round arbitrarily. Component scores are the ONLY inputs to the final score. The final score MUST equal the weighted sum of component scores when all 7 components are provided. Ensure mathematical consistency. Verify your final score equals the weighted sum before reporting.

EVALUATION STRUCTURE (NEW PRIORITY ORDER):
1. **EXPERIENCE LEVEL EVALUATION** (HIGHEST PRIORITY):
   - Years of experience match assessment
   - Relevance and depth of experience
   - How well experience aligns with job requirements
   - Component score (0-10): ___

2. **JOB TITLE MATCH ANALYSIS** (SECOND PRIORITY):
   - Relevance of previous job titles
   - Similarity to target role
   - Industry and function alignment
   - Component score (0-10): ___

3. **REQUIRED SKILLS ANALYSIS** (THIRD PRIORITY):
   - Required skills present in candidate's profile
   - Required skills missing
   - Match percentage and depth
   - Component score (0-10): ___

4. **TRANSFERRABLE SKILLS ANALYSIS** (FOURTH PRIORITY - AI-POWERED):
   CRITICAL: Analyze the candidate's experience to identify skills that are relevant to this role but NOT explicitly listed in required/preferred skills.
   
   Identify:
   - Skills from candidate's experience that are relevant but not in required/preferred lists
   - Cross-industry skills that could transfer to this role
   - Semantically similar skills (different wording, same meaning)
   - Skills demonstrated through job descriptions that align with role needs
   
   For each transferrable skill identified:
   - Name the specific skill
   - Explain how it's relevant to this role
   - Cite where it appears in the candidate's resume (job title, experience description, etc.)
   - Assess the strength/relevance (high, medium, low)
   
   Examples of transferrable skills to look for:
   - Project management, team leadership, client relations, data analysis
   - Communication, problem-solving, process improvement
   - Industry-specific skills from related fields
   - Soft skills demonstrated through experience
   
   - List of transferrable skills identified: ___
   - Overall relevance assessment: ___
   - Component score (0-10): ___

5. **LOCATION MATCH** (FIFTH PRIORITY):
   - Location compatibility
   - Geographic proximity assessment
   - Component score (0-10): ___

6. **PREFERRED SKILLS ANALYSIS** (SIXTH PRIORITY):
   - Preferred skills present
   - Preferred skills missing
   - Component score (0-10): ___

7. **CERTIFICATIONS/EDUCATION ANALYSIS** (LOWEST PRIORITY):
   - Must-have certifications present/missing
   - Bonus certifications present
   - Education level (degree, training, licenses)
   - Overall certifications/education assessment
   - Component score (0-10): ___

8. **OVERALL ASSESSMENT** (4-5 sentences):
   - Provide a 4-5 sentence summary explaining why the candidate is or isn't a good fit
   - Key strengths
   - Notable gaps
   - Growth potential
   - Overall recommendation

9. **COMPONENT SCORES SUMMARY** (REQUIRED):
CRITICAL: These component scores are the ONLY inputs to the final score calculation. Do not adjust the final score based on subjective assessment - use ONLY the weighted formula. Component scores MUST be provided in the exact format shown - this is critical for consistency.

Provide component scores in this EXACT format (NEW PRIORITY ORDER):
COMPONENT_SCORES:
- Experience level: X.X/10
- Job title match: X.X/10
- Required skills: X.X/10
- Transferrable skills: X.X/10
- Location: X.X/10
- Preferred skills: X.X/10
- Certifications/Education: X.X/10

10. **WEIGHTED CALCULATION** (REQUIRED):
Calculate weighted score using these weights (NEW PRIORITY ORDER):
- Experience level: component_score × {weights.get('experience_level', 0.25):.2f}
- Job title match: component_score × {weights.get('job_title_match', 0.20):.2f}
- Required skills: component_score × {weights.get('required_skills', 0.18):.2f}
- Transferrable skills: component_score × {weights.get('transferrable_skills', 0.15):.2f}
- Location: component_score × {weights.get('location', 0.10):.2f}
- Preferred skills: component_score × {weights.get('preferred_skills', 0.07):.2f}
- Certifications/Education: component_score × {weights.get('certifications_education', 0.05):.2f}
Final Score = Sum of all weighted components

VERIFICATION STEP: After calculating, verify: Final Score = Sum of (Component Score × Weight) for all 7 components. If your calculated score doesn't match this formula, recalculate. Show your calculation step-by-step.

11. **FINAL SCORE**:
Provide final weighted score in this exact format:
FINAL_SCORE: X.X/10

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
- Component scores MUST align with your analysis (e.g., if all certs missing, cert score MUST be 0.0)
- Final score MUST be calculated from component scores using the weights above

CONSISTENCY RULE: If you evaluate this exact same candidate profile again, you MUST produce the exact same component scores and final score. Treat identical inputs as requiring identical outputs.

MATHEMATICAL RULE: Final score = (experience_level × {weights.get('experience_level', 0.25):.2f}) + (job_title_match × {weights.get('job_title_match', 0.20):.2f}) + (required_skills × {weights.get('required_skills', 0.18):.2f}) + (transferrable_skills × {weights.get('transferrable_skills', 0.15):.2f}) + (location × {weights.get('location', 0.10):.2f}) + (preferred_skills × {weights.get('preferred_skills', 0.07):.2f}) + (certifications_education × {weights.get('certifications_education', 0.05):.2f}) - NO EXCEPTIONS. Do not round, adjust, or modify this calculation.

CONSISTENCY EXAMPLE: If Candidate A has all must-have certs and 80% of required skills, they should always score 10.0 for certs and 8.0 for skills, regardless of when evaluated. If Candidate B has identical qualifications to Candidate A, they must receive identical component scores and final score.

Format your response with clear headers. Be specific and cite evidence from the candidate's resume. ONLY use information explicitly stated in the resume.
"""

        return prompt

    def _parse_ai_response(self, response_text: str, weights: Dict[str, float] = None) -> Tuple[float, str, Dict[str, float]]:
        """
        Parse OpenAI's response to extract component scores, calculate weighted score, and extract reasoning
        
        Removes prompt text and extracts only the actual evaluation content.

        Args:
            response_text: The AI response text
            weights: Dictionary of scoring weights (defaults to standard weights if not provided)

        Returns:
            (final_score, reasoning_text, component_scores_dict)
        """
        import re
        
        # Use provided weights or default
        if weights is None:
            weights = get_default_weights()
        
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
            # Extract each component score from summary section (NEW PRIORITY ORDER)
            patterns = {
                'experience_level': r'(?:Experience level|experience level):\s*(\d+\.?\d*)/10',
                'job_title_match': r'(?:Job title match|job title match):\s*(\d+\.?\d*)/10',
                'required_skills': r'(?:Required skills|required skills):\s*(\d+\.?\d*)/10',
                'transferrable_skills': r'(?:Transferrable skills|transferrable skills|Transferable skills|transferable skills):\s*(\d+\.?\d*)/10',
                'location': r'(?:Location|location):\s*(\d+\.?\d*)/10',
                'preferred_skills': r'(?:Preferred skills|preferred skills):\s*(\d+\.?\d*)/10',
                'certifications_education': r'(?:Certifications/Education|certifications/education|Certifications\/Education):\s*(\d+\.?\d*)/10'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, component_text, re.IGNORECASE)
                if match:
                    component_scores[key] = float(match.group(1))
        else:
            # Fallback: Extract inline component scores from individual sections (NEW PRIORITY ORDER)
            # Look for patterns like "Component score (0-10): X.X" or "Component score (0-10): X.X/10"
            inline_patterns = {
                'experience_level': [
                    r'(?:EXPERIENCE LEVEL|Experience level|EXPERIENCE EVALUATION).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:EXPERIENCE LEVEL|Experience level|EXPERIENCE EVALUATION).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'job_title_match': [
                    r'(?:JOB TITLE MATCH|Job title match|JOB TITLE).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:JOB TITLE MATCH|Job title match|JOB TITLE).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'required_skills': [
                    r'(?:REQUIRED SKILLS|Required skills).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:REQUIRED SKILLS|Required skills).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'transferrable_skills': [
                    r'(?:TRANSFERRABLE SKILLS|Transferrable skills|Transferable skills).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:TRANSFERRABLE SKILLS|Transferrable skills|Transferable skills).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'location': [
                    r'(?:LOCATION MATCH|Location match|LOCATION).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:LOCATION MATCH|Location match|LOCATION).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'preferred_skills': [
                    r'(?:PREFERRED SKILLS|Preferred skills).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:PREFERRED SKILLS|Preferred skills).*?[Cc]omponent score.*?(\d+\.?\d*)',
                ],
                'certifications_education': [
                    r'(?:CERTIFICATIONS/EDUCATION|Certifications/Education|certifications/education).*?[Cc]omponent score.*?(\d+\.?\d*)/10',
                    r'(?:CERTIFICATIONS/EDUCATION|Certifications/Education|certifications/education).*?[Cc]omponent score.*?(\d+\.?\d*)',
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
        # Use component scores if we have at least 4 of the 7 components (majority)
        if component_scores and len(component_scores) >= 4:
            # Calculate weighted sum using available components
            # For missing components, use the average of available component scores (fair estimate)
            available_scores = list(component_scores.values())
            avg_available = sum(available_scores) / len(available_scores) if available_scores else 5.0

            calculated_score = sum(
                component_scores.get(key, avg_available) * weight
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
        
        # Use calculated score if available and close to AI score (within 1.0), otherwise use AI score
        # This ensures we're using the weighted calculation when component scores are available
        if calculated_score is not None:
            # Prefer calculated score if component scores were extracted
            final_score = calculated_score
        else:
            final_score = ai_score

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
        
        Removes COMPONENT_SCORES, WEIGHTED CALCULATION, and FINAL_SCORE sections
        to avoid displaying stale score information that doesn't match the actual fit_score.
        """
        if not text:
            return ""

        import re
        
        # Remove COMPONENT_SCORES, WEIGHTED CALCULATION, and FINAL_SCORE sections
        # These sections may contain stale scores that don't match the validated fit_score
        cleaned_text = text
        
        # Remove COMPONENT SCORES SUMMARY section (and variations)
        # This catches "COMPONENT SCORES SUMMARY", "COMPONENT_SCORES:", etc.
        cleaned_text = re.sub(
            r'(?:COMPONENT\s+SCORES?\s+SUMMARY|COMPONENT_SCORES?):.*?(?=WEIGHTED CALCULATION|FINAL_SCORE|OVERALL|RECOMMENDATIONS|\Z)',
            '',
            cleaned_text,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Also remove any standalone lines that start with component score items
        # (e.g., "- Experience level: X.X/10")
        cleaned_text = re.sub(
            r'^[-•]\s*(?:Experience level|Job title match|Required skills|Transferrable skills|Location|Preferred skills|Certifications/Education):\s*\d+\.?\d*/10.*$',
            '',
            cleaned_text,
            flags=re.MULTILINE | re.IGNORECASE
        )
        
        # Remove WEIGHTED CALCULATION section
        cleaned_text = re.sub(
            r'WEIGHTED CALCULATION:.*?(?=FINAL_SCORE|OVERALL|RECOMMENDATIONS|\Z)',
            '',
            cleaned_text,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove FINAL_SCORE line (all variations)
        cleaned_text = re.sub(
            r'\*\*?FINAL[_\s]?SCORE\*\*?\s*:?\s*\d+\.?\d*/10.*',
            '',
            cleaned_text,
            flags=re.IGNORECASE
        )
        cleaned_text = re.sub(
            r'FINAL[_\s]?SCORE\s*:?\s*\d+\.?\d*/10.*',
            '',
            cleaned_text,
            flags=re.IGNORECASE
        )
        
        # Split on sentence boundaries (period, exclamation, question mark followed by space)
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text.strip())
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

        # Fallback: If no sentence boundaries found, split on newlines or use first meaningful chunk
        # This handles cases where text doesn't have proper sentence punctuation
        if '\n' in text:
            # Try splitting on double newlines (paragraphs) first
            paragraphs = text.split('\n\n')
            if paragraphs:
                # Take first 1-2 paragraphs, up to 1500 chars
                fallback_text = '\n\n'.join(paragraphs[:2])
                if len(fallback_text) > 1500:
                    fallback_text = fallback_text[:1500]
                    # Try to end at sentence boundary
                    last_period = fallback_text.rfind('.')
                    last_exclamation = fallback_text.rfind('!')
                    last_question = fallback_text.rfind('?')
                    last_sentence_end = max(last_period, last_exclamation, last_question)
                    if last_sentence_end > 1000:
                        fallback_text = fallback_text[:last_sentence_end + 1]
                return fallback_text.strip()
        
        # Final fallback: return first 1500 chars but try to end at sentence boundary
        if len(text) > 1500:
            truncated = text[:1500]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > 1000:
                return text[:last_sentence_end + 1].strip()
        return text[:1500].strip()

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
        validated_score = max(1.0, min(10.0, score))
        
        # Validate component scores are in range
        if component_scores:
            for key, comp_score in component_scores.items():
                if comp_score < 0.0 or comp_score > 10.0:
                    print(f"  WARNING: Component score '{key}' out of range: {comp_score}, clamping to 0-10")
                    component_scores[key] = max(0.0, min(10.0, comp_score))
        
        # Cross-validate: Check if must-have certs match aligns with certs/education component score
        has_must_have = self._check_must_have_certs(candidate, job_details)
        must_have_certs_required = any(c.category == 'must-have' for c in job_details.certifications)
        
        if must_have_certs_required and component_scores:
            cert_ed_score = component_scores.get('certifications_education', 5.0)
            # If candidate has must-have certs, certs/education score should be reasonable (6+)
            # If missing ALL, score should be low (0-3) (already enforced in post-processing)
            if has_must_have and cert_ed_score < 6.0:
                print(f"  WARNING: Candidate has must-have certs but certs/education component score is low ({cert_ed_score})")
            elif not has_must_have and cert_ed_score > 3.0:
                # Force correction if still too high (should have been caught in post-processing, but double-check)
                print(f"  CORRECTING: Candidate missing ALL must-have certs but certs/education component score is {cert_ed_score:.2f}, adjusting to 2.0")
                component_scores['certifications_education'] = 2.0
                # Recalculate weighted score (use weights from job_details)
                # Note: weights should be passed to _validate_score_consistency, but for now use defaults
                # This is a fallback - ideally weights should be passed through
                default_weights = get_default_weights()
                validated_score = sum(
                    component_scores.get(key, 0.0) * weight
                    for key, weight in default_weights.items()
                )
                validated_score = max(0.0, min(10.0, validated_score))
        
        # Sanity check: Candidate with all requirements shouldn't score below 7.0
        if component_scores:
            # Rough check: if most components are high, overall should be high
            high_components = sum(1 for score in component_scores.values() if score >= 7.0)
            if high_components >= 5 and validated_score < 6.5:
                print(f"  WARNING: Most components are high ({high_components}/7) but final score is low ({validated_score})")
                # Don't auto-adjust, but log the warning
        
        # Note: Since certifications/education is now lower priority (5%), missing all must-have certs
        # doesn't need to cap the score as severely. The component score adjustment is sufficient.
        
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
