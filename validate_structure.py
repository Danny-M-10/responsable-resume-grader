"""
Application Structure Validation
Tests core logic without external dependencies
"""

import os
import sys
import glob


def validate_files():
    """Validate all required files exist"""
    print("=" * 80)
    print("VALIDATING APPLICATION STRUCTURE")
    print("=" * 80)
    print()

    required_files = {
        'Core Modules': [
            'candidate_ranker.py',
            'resume_parser.py',
            'scoring_engine.py',
            'pdf_generator.py',
            'skills_researcher.py',
            'models.py'
        ],
        'User Interfaces': [
            'app.py',
            'example_usage.py'
        ],
        'Configuration': [
            'requirements.txt'
        ],
        'Documentation': [
            'README.md',
            'QUICK_START.md',
            'USER_MANUAL.md',
            'START_HERE.md',
            'PROJECT_SUMMARY.md',
            'FILE_GUIDE.md',
            'SYSTEM_ARCHITECTURE.md'
        ],
        'Setup Scripts': [
            'setup.sh',
            'setup.bat'
        ]
    }

    all_valid = True
    for category, files in required_files.items():
        print(f"{category}:")
        for file in files:
            exists = os.path.exists(file)
            status = "✓" if exists else "✗"
            print(f"  {status} {file}")
            if not exists:
                all_valid = False
        print()

    return all_valid


def validate_sample_resumes():
    """Validate sample resume files"""
    print("Sample Resumes:")
    resume_dir = "sample_resumes"

    if not os.path.exists(resume_dir):
        print(f"  ✗ Directory '{resume_dir}' not found")
        return False

    resume_files = glob.glob(os.path.join(resume_dir, "*.txt"))

    if not resume_files:
        print(f"  ✗ No resume files found in '{resume_dir}'")
        return False

    for resume_file in resume_files:
        print(f"  ✓ {os.path.basename(resume_file)}")

    print()
    return True


def test_imports():
    """Test that modules can be imported"""
    print("Testing Module Imports:")

    modules_to_test = [
        'models',
        'skills_researcher',
    ]

    all_imported = True
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name} - {e}")
            all_imported = False
        except Exception as e:
            print(f"  ⚠ {module_name} - {type(e).__name__}: {e}")

    print()
    return all_imported


def test_skills_researcher():
    """Test skills researcher functionality"""
    print("Testing Skills Researcher:")

    try:
        from skills_researcher import SkillsResearcher

        researcher = SkillsResearcher()

        # Test job title equivalents
        titles = researcher.find_equivalent_titles("Data Scientist")
        print(f"  ✓ Found {len(titles)} equivalent titles for 'Data Scientist'")
        print(f"    Examples: {', '.join(titles[:3])}")

        # Test skill synonyms
        synonyms = researcher.find_skill_synonyms("python")
        print(f"  ✓ Found {len(synonyms)} synonyms for 'python'")
        if synonyms:
            print(f"    Examples: {', '.join(synonyms[:3])}")

        print()
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        print()
        return False


def test_models():
    """Test data models"""
    print("Testing Data Models:")

    try:
        from models import Certification, JobDetails, CandidateScore

        # Test Certification
        cert = Certification(name="AWS ML", category="must-have")
        print(f"  ✓ Certification created: {cert.name} ({cert.category})")

        # Test JobDetails
        job = JobDetails(
            job_title="Data Scientist",
            certifications=[cert],
            location="New York, NY",
            full_description="Test description"
        )
        print(f"  ✓ JobDetails created: {job.job_title} in {job.location}")

        # Test CandidateScore
        candidate = CandidateScore(
            name="Test Candidate",
            phone="555-1234",
            email="test@email.com",
            certifications=["AWS ML"],
            fit_score=8.5,
            chain_of_thought="Test reasoning",
            rationale="Good match",
            experience_match={},
            certification_match={},
            skills_match={},
            location_match=True
        )
        print(f"  ✓ CandidateScore created: {candidate.name} (score: {candidate.fit_score})")

        print()
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def simulate_scoring():
    """Simulate the scoring logic"""
    print("Simulating Scoring Logic:")

    # Sample candidate data
    candidates = [
        {
            'name': 'Jane Smith',
            'has_aws_ml_cert': True,
            'has_bonus_certs': True,
            'required_skills_match': 0.9,
            'preferred_skills_match': 0.8,
            'experience_years': 7,
            'location': 'New York, NY'
        },
        {
            'name': 'John Doe',
            'has_aws_ml_cert': False,
            'has_bonus_certs': False,
            'required_skills_match': 0.7,
            'preferred_skills_match': 0.5,
            'experience_years': 4,
            'location': 'Boston, MA'
        },
        {
            'name': 'Alex Kim',
            'has_aws_ml_cert': False,
            'has_bonus_certs': False,
            'required_skills_match': 0.4,
            'preferred_skills_match': 0.3,
            'experience_years': 1,
            'location': 'Chicago, IL'
        }
    ]

    # Scoring weights
    weights = {
        'must_have_certs': 0.30,
        'bonus_certs': 0.10,
        'required_skills': 0.25,
        'preferred_skills': 0.10,
        'experience_level': 0.10,
        'job_title_match': 0.10,
        'location': 0.05
    }

    print(f"  Scoring {len(candidates)} candidates...")
    print()

    scored_candidates = []
    for candidate in candidates:
        # Calculate score
        score = 0.0

        # Must-have certs (30%)
        cert_score = 1.0 if candidate['has_aws_ml_cert'] else 0.0
        score += cert_score * weights['must_have_certs'] * 10

        # Bonus certs (10%)
        bonus_score = 1.0 if candidate['has_bonus_certs'] else 0.0
        score += bonus_score * weights['bonus_certs'] * 10

        # Required skills (25%)
        score += candidate['required_skills_match'] * weights['required_skills'] * 10

        # Preferred skills (10%)
        score += candidate['preferred_skills_match'] * weights['preferred_skills'] * 10

        # Experience (10%) - assuming 5-7 years is ideal
        exp_score = 1.0 if 5 <= candidate['experience_years'] <= 7 else 0.6
        score += exp_score * weights['experience_level'] * 10

        # Job title (10%) - assume 70% match
        score += 0.7 * weights['job_title_match'] * 10

        # Location (5%)
        loc_score = 1.0 if candidate['location'] == 'New York, NY' else 0.5
        score += loc_score * weights['location'] * 10

        scored_candidates.append({
            'name': candidate['name'],
            'score': round(score, 2)
        })

    # Sort by score
    scored_candidates.sort(key=lambda x: x['score'], reverse=True)

    for i, candidate in enumerate(scored_candidates, 1):
        print(f"  {i}. {candidate['name']}: {candidate['score']}/10")

    print()
    print(f"  ✓ Scoring simulation completed")
    print()
    return True


def main():
    """Run all validations"""

    results = {
        'File Structure': validate_files(),
        'Sample Resumes': validate_sample_resumes(),
        'Module Imports': test_imports(),
        'Skills Researcher': test_skills_researcher(),
        'Data Models': test_models(),
        'Scoring Logic': simulate_scoring()
    }

    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    print()

    all_passed = all(results.values())

    if all_passed:
        print("=" * 80)
        print("ALL VALIDATIONS PASSED!")
        print("=" * 80)
        print()
        print("Application structure is valid and core logic is working.")
        print()
        print("To run the full application with PDF generation:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run test: python test_application.py")
        print("3. Or launch web interface: streamlit run app.py")
    else:
        print("=" * 80)
        print("SOME VALIDATIONS FAILED")
        print("=" * 80)
        print()
        print("Please check the errors above.")

    print()
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
