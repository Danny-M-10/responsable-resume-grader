"""
Test AI job description extraction
"""

from config import load_env_file
load_env_file()

from ai_job_parser import AIJobParser
import tempfile
import os

# Sample job description similar to what user might upload
sample_job_description = """
SAFETY SPECIALIST

Location: Houston, TX

ResponsAble Safety Staffing is seeking a Certified Occupational Safety Specialist
for our Houston operations.

REQUIREMENTS:
- OSHA 30 Hour certification (required)
- First Aid/CPR certification (preferred)
- 5+ years experience in industrial safety
- Strong knowledge of OSHA regulations
- Excellent communication skills

RESPONSIBILITIES:
- Conduct safety inspections
- Develop safety programs
- Train employees on safety procedures

If you meet these qualifications, please apply today!
"""

print("=" * 70)
print("TESTING AI JOB DESCRIPTION EXTRACTION")
print("=" * 70)
print()

# Initialize parser
parser = AIJobParser()
print(f"AI Available: {parser.ai_available}")
print()

if not parser.ai_available:
    print("ERROR: AI parsing is not available. Check API key.")
    exit(1)

# Create temp file
temp_dir = tempfile.mkdtemp()
temp_path = os.path.join(temp_dir, "test_job.txt")

with open(temp_path, 'w') as f:
    f.write(sample_job_description)

print("Testing extraction on sample job description...")
print("-" * 70)

try:
    result = parser.parse(temp_path)

    print()
    print("EXTRACTION RESULTS:")
    print("=" * 70)
    print(f"Job Title: {result.get('job_title', 'NOT EXTRACTED')}")
    print(f"Location: {result.get('location', 'NOT EXTRACTED')}")
    print(f"Certifications: {len(result.get('certifications', []))} found")

    for cert in result.get('certifications', []):
        print(f"  - {cert.get('name')} ({cert.get('category')})")

    print(f"Required Skills: {result.get('required_skills', [])}")
    print(f"Preferred Skills: {result.get('preferred_skills', [])}")
    print(f"Experience Level: {result.get('experience_level', 'NOT EXTRACTED')}")
    print()

    # Validation
    if result.get('job_title') and result.get('job_title') != 'Not found':
        print("✅ Job title extracted successfully")
    else:
        print("❌ FAILED: Job title not extracted")

    if result.get('location') and result.get('location') != 'Not found':
        print("✅ Location extracted successfully")
    else:
        print("❌ FAILED: Location not extracted")

    if len(result.get('certifications', [])) > 0:
        print("✅ Certifications extracted successfully")
    else:
        print("⚠️  WARNING: No certifications extracted")

    print()
    print("=" * 70)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
os.remove(temp_path)
os.rmdir(temp_dir)
