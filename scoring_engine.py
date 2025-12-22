"""
Scoring Engine Module
Evaluates candidates with chain-of-thought reasoning and assigns fit scores
"""

from typing import Dict, Any, List
from models import JobDetails, CandidateScore, Certification


class ScoringEngine:
    """
    Evaluates candidates against job requirements
    Uses chain-of-thought reasoning to compute fit scores (1-10)
    """

    def __init__(self):
        # Scoring weights
        self.weights = {
            'must_have_certs': 0.30,      # 30% - Critical
            'bonus_certs': 0.10,           # 10%
            'required_skills': 0.25,       # 25% - Very important
            'preferred_skills': 0.10,      # 10%
            'experience_level': 0.10,      # 10%
            'job_title_match': 0.10,       # 10%
            'location': 0.05              # 5%
        }

    def score_candidate(self, candidate: Dict[str, Any],
                       job_details: JobDetails) -> CandidateScore:
        """
        Score a candidate with chain-of-thought reasoning

        Args:
            candidate: Parsed candidate data
            job_details: Structured job requirements

        Returns:
            CandidateScore with fit score and detailed reasoning
        """

        # Initialize chain-of-thought narrative
        cot_steps = []
        cot_steps.append("CHAIN-OF-THOUGHT EVALUATION:")
        cot_steps.append("")

        # Component scores
        scores = {}

        # 1. CERTIFICATION MATCH (Must-have)
        cot_steps.append("1. MUST-HAVE CERTIFICATIONS:")
        cert_match = self._evaluate_certifications(
            candidate, job_details, 'must-have', cot_steps
        )
        scores['must_have_certs'] = cert_match

        # 2. CERTIFICATION MATCH (Bonus)
        cot_steps.append("")
        cot_steps.append("2. BONUS CERTIFICATIONS:")
        bonus_cert_match = self._evaluate_certifications(
            candidate, job_details, 'bonus', cot_steps
        )
        scores['bonus_certs'] = bonus_cert_match

        # 3. REQUIRED SKILLS MATCH
        cot_steps.append("")
        cot_steps.append("3. REQUIRED SKILLS:")
        req_skills_match = self._evaluate_skills(
            candidate, job_details.required_skills,
            job_details.skill_synonyms, cot_steps
        )
        scores['required_skills'] = req_skills_match

        # 4. PREFERRED SKILLS MATCH
        cot_steps.append("")
        cot_steps.append("4. PREFERRED SKILLS:")
        pref_skills_match = self._evaluate_skills(
            candidate, job_details.preferred_skills,
            job_details.skill_synonyms, cot_steps
        )
        scores['preferred_skills'] = pref_skills_match

        # 5. EXPERIENCE LEVEL MATCH
        cot_steps.append("")
        cot_steps.append("5. EXPERIENCE LEVEL:")
        exp_match = self._evaluate_experience(
            candidate, job_details, cot_steps
        )
        scores['experience_level'] = exp_match

        # 6. JOB TITLE MATCH
        cot_steps.append("")
        cot_steps.append("6. JOB TITLE MATCH:")
        title_match = self._evaluate_job_title(
            candidate, job_details, cot_steps
        )
        scores['job_title_match'] = title_match

        # 7. LOCATION MATCH
        cot_steps.append("")
        cot_steps.append("7. LOCATION:")
        location_match = self._evaluate_location(
            candidate, job_details, cot_steps
        )
        scores['location'] = location_match

        # Calculate weighted score
        cot_steps.append("")
        cot_steps.append("WEIGHTED SCORE CALCULATION:")

        total_score = 0.0
        for component, weight in self.weights.items():
            component_score = scores[component]
            weighted = component_score * weight * 10  # Scale to 10
            total_score += weighted
            cot_steps.append(
                f"  {component}: {component_score:.2f} x {weight} x 10 = {weighted:.2f}"
            )

        cot_steps.append("")
        cot_steps.append(f"TOTAL SCORE: {total_score:.2f} / 10.0")

        # Generate concise rationale
        rationale = self._generate_rationale(
            candidate, job_details, scores, total_score
        )

        # Create detailed match dictionaries
        experience_match = {
            'years': candidate.get('years_of_experience', 0),
            'titles': candidate.get('job_titles', []),
            'level_match': scores['experience_level']
        }

        # Only include certifications explicitly listed in resume (no equivalents)
        candidate_certs_explicit = candidate.get('certifications', [])
        certification_match = {
            'has_must_have': scores['must_have_certs'] >= 0.8,
            'has_bonus': scores['bonus_certs'] > 0,
            'candidate_certs': candidate_certs_explicit  # Only explicit certifications
        }

        skills_match = {
            'required_match_rate': scores['required_skills'],
            'preferred_match_rate': scores['preferred_skills'],
            'candidate_skills': candidate.get('skills', [])
        }

        # Return CandidateScore - only include explicitly extracted certifications
        # Do NOT add equivalent certifications to the candidate's certification list
        explicit_certifications = candidate.get('certifications', [])
        
        return CandidateScore(
            name=candidate.get('name', 'Unknown'),
            phone=candidate.get('phone', 'Not Found'),
            email=candidate.get('email', 'Not Found'),
            certifications=explicit_certifications,  # Only what's explicitly in resume
            fit_score=round(total_score, 2),
            chain_of_thought="\n".join(cot_steps),
            rationale=rationale,
            experience_match=experience_match,
            certification_match=certification_match,
            skills_match=skills_match,
            location_match=(location_match >= 0.5)
        )

    def _evaluate_certifications(self, candidate: Dict[str, Any],
                                job_details: JobDetails, category: str,
                                cot_steps: List[str]) -> float:
        """Evaluate certification match"""
        required_certs = [
            c.name for c in job_details.certifications
            if c.category == category
        ]

        if not required_certs:
            cot_steps.append(f"  No {category} certifications required.")
            return 1.0  # Full score if none required

        candidate_certs = candidate.get('certifications', [])
        candidate_certs_lower = [c.lower() for c in candidate_certs]

        matched = 0
        for req_cert in required_certs:
            # Get equivalent certifications if available
            equivalents = job_details.certification_equivalents.get(req_cert, [])
            all_possible_certs = [req_cert] + equivalents
            all_possible_certs_lower = [c.lower() for c in all_possible_certs]
            
            # Check for exact or partial match (including equivalents)
            req_cert_lower = req_cert.lower()
            is_match = any(
                possible_cert.lower() in cand_cert or cand_cert in possible_cert.lower()
                for possible_cert in all_possible_certs
                for cand_cert in candidate_certs_lower
            )

            if is_match:
                matched += 1
                # Find which candidate cert matched (for reporting)
                matched_cert = next(
                    (cand_cert for cand_cert in candidate_certs_lower 
                     for possible_cert in all_possible_certs_lower
                     if possible_cert in cand_cert or cand_cert in possible_cert),
                    None
                )
                # Get the original case from candidate's cert list
                if matched_cert:
                    original_cert = next(
                        (c for c in candidate.get('certifications', []) 
                         if matched_cert in c.lower()),
                        None
                    )
                    if original_cert and original_cert.lower() != req_cert.lower():
                        # Only mention if it's an equivalent (not the exact cert)
                        cot_steps.append(f"  MATCH: {original_cert} (equivalent to {req_cert})")
                    else:
                        cot_steps.append(f"  MATCH: {req_cert}")
                else:
                cot_steps.append(f"  MATCH: {req_cert}")
            else:
                cot_steps.append(f"  MISSING: {req_cert}")

        match_rate = matched / len(required_certs) if required_certs else 1.0

        cot_steps.append(f"  Match rate: {matched}/{len(required_certs)} = {match_rate:.2f}")

        return match_rate

    def _evaluate_skills(self, candidate: Dict[str, Any],
                        required_skills: List[str],
                        skill_synonyms: Dict[str, List[str]],
                        cot_steps: List[str]) -> float:
        """Evaluate skill match with synonym support"""
        if not required_skills:
            cot_steps.append("  No specific skills required.")
            return 1.0

        candidate_skills = candidate.get('skills', [])
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        candidate_text_lower = candidate.get('raw_text', '').lower()

        matched = 0
        for skill in required_skills:
            skill_lower = skill.lower()

            # Check direct match
            is_match = skill_lower in ' '.join(candidate_skills_lower)

            # Check synonyms
            if not is_match and skill in skill_synonyms:
                for synonym in skill_synonyms[skill]:
                    if synonym.lower() in candidate_text_lower:
                        is_match = True
                        break

            if is_match:
                matched += 1
                cot_steps.append(f"  MATCH: {skill}")
            else:
                cot_steps.append(f"  MISSING: {skill}")

        match_rate = matched / len(required_skills) if required_skills else 1.0

        cot_steps.append(f"  Match rate: {matched}/{len(required_skills)} = {match_rate:.2f}")

        return match_rate

    def _evaluate_experience(self, candidate: Dict[str, Any],
                           job_details: JobDetails,
                           cot_steps: List[str]) -> float:
        """Evaluate experience level match"""
        candidate_years = candidate.get('years_of_experience', 0)

        # Expected years based on level
        level_ranges = {
            'Junior': (0, 3),
            'Mid-level': (3, 7),
            'Senior': (7, 100)
        }

        expected_min, expected_max = level_ranges.get(
            job_details.experience_level, (0, 100)
        )

        cot_steps.append(f"  Job requires: {job_details.experience_level}")
        cot_steps.append(f"  Candidate has: {candidate_years} years")

        if expected_min <= candidate_years <= expected_max:
            cot_steps.append(f"  MATCH: {candidate_years} years fits {job_details.experience_level} range")
            return 1.0
        elif candidate_years > expected_max:
            # Overqualified - still good but slightly penalized
            overage = min((candidate_years - expected_max) / 5, 0.2)
            score = max(0.8, 1.0 - overage)
            cot_steps.append(f"  OVERQUALIFIED: {candidate_years} years > {expected_max}, score: {score:.2f}")
            return score
        else:
            # Underqualified
            gap = expected_min - candidate_years
            penalty = min(gap / 5, 0.6)
            score = max(0.2, 1.0 - penalty)
            cot_steps.append(f"  UNDERQUALIFIED: {candidate_years} years < {expected_min}, score: {score:.2f}")
            return score

    def _evaluate_job_title(self, candidate: Dict[str, Any],
                          job_details: JobDetails,
                          cot_steps: List[str]) -> float:
        """Evaluate job title match"""
        candidate_titles = candidate.get('job_titles', [])
        candidate_titles_lower = [t.lower() for t in candidate_titles]

        job_title_lower = job_details.job_title.lower()
        equivalent_titles_lower = [t.lower() for t in job_details.equivalent_titles]

        all_target_titles = [job_title_lower] + equivalent_titles_lower

        # Check for exact or partial match
        for cand_title in candidate_titles_lower:
            for target_title in all_target_titles:
                # Partial match (e.g., "Senior Data Scientist" matches "Data Scientist")
                if target_title in cand_title or cand_title in target_title:
                    cot_steps.append(f"  MATCH: '{cand_title}' matches '{target_title}'")
                    return 1.0

        # No match found
        if candidate_titles:
            cot_steps.append(f"  Candidate titles: {', '.join(candidate_titles[:3])}")
            cot_steps.append(f"  No direct match to '{job_details.job_title}'")
            return 0.3  # Partial credit for having titles
        else:
            cot_steps.append("  No job titles found in resume")
            return 0.0

    def _evaluate_location(self, candidate: Dict[str, Any],
                         job_details: JobDetails,
                         cot_steps: List[str]) -> float:
        """Evaluate location match"""
        candidate_location = candidate.get('location', '').lower()
        job_location = job_details.location.lower()

        cot_steps.append(f"  Job location: {job_details.location}")
        cot_steps.append(f"  Candidate location: {candidate.get('location', 'Not specified')}")

        # Check for city match
        if candidate_location and job_location:
            # Extract city (before comma)
            job_city = job_location.split(',')[0].strip()
            cand_city = candidate_location.split(',')[0].strip()

            if job_city in candidate_location or cand_city in job_location:
                cot_steps.append("  MATCH: Same location")
                return 1.0

        # Check for remote-friendly keywords
        if 'remote' in job_location or 'anywhere' in job_location:
            cot_steps.append("  Job allows remote - location not critical")
            return 1.0

        # Partial match
        cot_steps.append("  Different location - may need relocation")
        return 0.5

    def _generate_rationale(self, candidate: Dict[str, Any],
                          job_details: JobDetails,
                          scores: Dict[str, float],
                          total_score: float) -> str:
        """Generate concise rationale for the candidate"""
        rationale_parts = []

        # Strengths
        strengths = []
        if scores['must_have_certs'] >= 0.8:
            strengths.append("has required certifications")
        if scores['required_skills'] >= 0.7:
            strengths.append("strong required skills match")
        if scores['experience_level'] >= 0.8:
            strengths.append("appropriate experience level")
        if scores['job_title_match'] >= 0.8:
            strengths.append("relevant job title")

        # Gaps
        gaps = []
        if scores['must_have_certs'] < 0.5:
            gaps.append("missing critical certifications")
        if scores['required_skills'] < 0.5:
            gaps.append("insufficient required skills")
        if scores['experience_level'] < 0.5:
            gaps.append("experience level mismatch")

        # Bonuses
        bonuses = []
        if scores['bonus_certs'] > 0:
            bonuses.append("bonus certifications")
        if scores['preferred_skills'] >= 0.7:
            bonuses.append("strong preferred skills")

        # Construct rationale
        if strengths:
            rationale_parts.append(f"Strengths: {', '.join(strengths)}.")

        if bonuses:
            rationale_parts.append(f"Bonus qualifications: {', '.join(bonuses)}.")

        if gaps:
            rationale_parts.append(f"Gaps: {', '.join(gaps)}.")

        # Overall assessment
        if total_score >= 8.0:
            assessment = "Excellent fit for the position"
        elif total_score >= 6.5:
            assessment = "Good fit with minor gaps"
        elif total_score >= 5.0:
            assessment = "Viable candidate with some limitations"
        else:
            assessment = "Limited fit for this position"

        rationale_parts.append(assessment + ".")

        return " ".join(rationale_parts)
