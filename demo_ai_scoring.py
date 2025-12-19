"""
Demo: Compare Rule-Based vs AI-Powered Candidate Scoring
"""

import os
import sys
from job_description_parser import JobDescriptionParser
from resume_parser import ResumeParser
from scoring_engine import ScoringEngine
from models import JobDetails

def main():
    print("="*70)
    print("CANDIDATE SCORING COMPARISON: Rule-Based vs AI-Powered")
    print("="*70)
    print()

    # Check if API key is set
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set - AI scoring unavailable")
        print()
        print("To enable AI scoring:")
        print("  export ANTHROPIC_API_KEY='sk-ant-your-key-here'")
        print()
        print("Get your API key at: https://console.anthropic.com/")
        print()
        print("Falling back to rule-based scoring only...")
        print()
        use_ai = False
    else:
        print("✓ API key found - AI scoring available")
        print()
        use_ai = True

    # Parse job description
    job_parser = JobDescriptionParser()
    print("Loading job description...")
    job_data = job_parser.parse('sample_job_descriptions/safety_lineman_job.txt')
    print(f"  Job Title: {job_data['job_title']}")
    print(f"  Certifications Required: {len(job_data['certifications'])}")
    print()

    # Parse resume
    resume_parser = ResumeParser()
    print("Loading candidate resume...")
    candidate = resume_parser.parse('sample_resumes/jane_smith_resume.txt')
    print(f"  Candidate: {candidate['name']}")
    print(f"  Experience: {candidate['years_of_experience']} years")
    print()

    # Convert to JobDetails model
    from models import Certification
    job_details = JobDetails(
        job_title=job_data['job_title'],
        location=job_data['location'],
        certifications=[Certification(**cert) for cert in job_data['certifications']],
        required_skills=[],
        preferred_skills=[],
        full_description=job_data['full_description'],
        skill_synonyms={}
    )

    print("="*70)
    print("RULE-BASED SCORING")
    print("="*70)
    print()

    # Score with rule-based engine
    rule_engine = ScoringEngine()
    print("Evaluating candidate with rule-based engine...")
    rule_score = rule_engine.score_candidate(candidate, job_details)

    print(f"\n{'Score:':<20} {rule_score.fit_score:.2f}/10")
    print(f"\nReasoning (first 500 chars):")
    print("-" * 70)
    print(rule_score.chain_of_thought[:500] + "...")
    print()

    if use_ai:
        print("="*70)
        print("AI-POWERED SCORING (Using Claude API)")
        print("="*70)
        print()

        try:
            from ai_scoring_engine import AIScoringEngine

            ai_engine = AIScoringEngine()
            print("Calling Claude API for intelligent evaluation...")
            print("(This may take 3-5 seconds...)")
            print()

            ai_score = ai_engine.score_candidate(candidate, job_details)

            print(f"\n{'Score:':<20} {ai_score.fit_score:.2f}/10")
            print(f"\nAI Reasoning:")
            print("-" * 70)
            print(ai_score.chain_of_thought)
            print()

            print("="*70)
            print("COMPARISON")
            print("="*70)
            print()
            print(f"Rule-Based Score:  {rule_score.fit_score:.2f}/10")
            print(f"AI-Powered Score:  {ai_score.fit_score:.2f}/10")
            print(f"Difference:        {abs(ai_score.fit_score - rule_score.fit_score):.2f} points")
            print()
            print("Key Differences:")
            print("  • Rule-based: Pattern matching, hardcoded weights")
            print("  • AI-powered: Context understanding, nuanced reasoning")
            print()

        except Exception as e:
            print(f"❌ AI scoring failed: {e}")
            print()
            print("Make sure you have:")
            print("  1. Installed anthropic: pip install anthropic")
            print("  2. Set API key: export ANTHROPIC_API_KEY='sk-ant-...'")
            print()

    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Get API key: https://console.anthropic.com/")
    print("  2. Read AI_INTEGRATION_GUIDE.md for full documentation")
    print("  3. Try with your own job descriptions and resumes!")
    print()

if __name__ == "__main__":
    main()
