"""
Quick test script to verify AI integration is working
"""

from config import load_env_file
load_env_file()

from candidate_ranker import CandidateRankerApp
import os

print("=" * 70)
print("TESTING AI INTEGRATION")
print("=" * 70)
print()

# Check if API key is configured
from config import AnthropicConfig
print(f"API Key configured: {AnthropicConfig.is_configured()}")

if not AnthropicConfig.is_configured():
    print("ERROR: Anthropic API key not found!")
    print("Please add it to the .env file")
    exit(1)

print("API Key found!")
print()

# Initialize app with AI enabled
print("Initializing Candidate Ranker with AI enabled...")
app = CandidateRankerApp(use_ai=True)
print()

# Check which scoring engine is being used
if hasattr(app.scoring_engine, 'ai_engine') and app.scoring_engine.ai_engine:
    print("✓ AI scoring engine is ACTIVE")
    print(f"  Model: {app.scoring_engine.ai_engine.model}")
else:
    print("✗ Using rule-based scoring (AI not available)")
print()

# Get sample resume files
import glob
sample_resumes = glob.glob("sample_resumes/*.txt")

if not sample_resumes:
    print("ERROR: No sample resumes found in sample_resumes/")
    exit(1)

print(f"Found {len(sample_resumes)} sample resumes")
print()

# Run a quick test with ONE resume
print("Running test with 1 resume (to save API costs)...")
print("=" * 70)

try:
    pdf_path = app.run(
        job_title="Software Engineer",
        certifications=[
            {"name": "AWS Certified Solutions Architect", "category": "must-have"}
        ],
        location="Remote",
        job_description="""
        We are looking for an experienced Software Engineer with strong Python skills.
        Must have experience with cloud platforms, preferably AWS.
        Required skills: Python, REST APIs, Git, Docker
        Preferred skills: Kubernetes, CI/CD, React
        """,
        resume_files=[sample_resumes[0]]  # Just test with first resume
    )

    print()
    print("=" * 70)
    print("✓ SUCCESS! AI integration is working!")
    print(f"Generated PDF: {pdf_path}")
    print()

    # Check the candidate score
    if app.candidate_scores:
        candidate = app.candidate_scores[0]
        print(f"Candidate: {candidate.name}")
        print(f"Score: {candidate.fit_score}/10")
        print(f"Rationale: {candidate.rationale[:200]}...")
        print()
        print("AI-powered candidate evaluation is ACTIVE! 🎉")

except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("AI integration test failed. Check the error above.")

print()
print("=" * 70)
