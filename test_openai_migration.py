"""
Comprehensive test suite for OpenAI migration
Tests all AI components to ensure they work correctly
"""

import os
import sys
from pathlib import Path

def test_config():
    """Test AI configuration (Gemini or OpenAI)"""
    print("\n" + "="*80)
    print("TEST 1: AI Configuration (Gemini or OpenAI)")
    print("="*80)
    
    try:
        from config import is_ai_configured, get_llm_provider, GeminiConfig, OpenAIConfig
        
        configured = is_ai_configured()
        provider = get_llm_provider()
        print(f"✓ Config imported successfully")
        print(f"  AI configured: {configured}")
        print(f"  Provider: {provider or 'none'}")
        
        if configured:
            if provider == "gemini":
                key = GeminiConfig.get_api_key()
                model = GeminiConfig.get_model()
            else:
                key = OpenAIConfig.get_api_key()
                model = OpenAIConfig.get_model()
            print(f"  API Key length: {len(key)} characters")
            print(f"  Model: {model}")
            print("✓ Configuration test PASSED")
            return True
        else:
            print("✗ Configuration test FAILED: No AI provider configured (set GEMINI_API_KEY or OPENAI_API_KEY)")
            return False
    except Exception as e:
        print(f"✗ Configuration test FAILED: {e}")
        return False


def test_ai_job_parser():
    """Test AI job parser"""
    print("\n" + "="*80)
    print("TEST 2: AI Job Parser")
    print("="*80)
    
    try:
        from ai_job_parser import AIJobParser
        
        parser = AIJobParser()
        print("✓ AIJobParser initialized successfully")
        
        # Create a test job description file
        test_job_content = """
        Job Title: Solar Safety Manager
        
        Location: Remote
        
        We are seeking an experienced Solar Safety Manager to oversee safety protocols 
        for our solar installation projects.
        
        Required Certifications:
        - OSHA 30 Hour certification (or equivalent)
        - CSP (Certified Safety Professional) or equivalent
        
        Preferred Certifications:
        - CHST (Construction Health and Safety Technician)
        
        Required Skills:
        - Safety management
        - Risk assessment
        - Training and development
        - Regulatory compliance
        
        Experience: Minimum 5 years in construction safety management.
        """
        
        test_file = Path("test_job_description.txt")
        test_file.write_text(test_job_content)
        
        print(f"  Created test job description file: {test_file}")
        
        # Parse the job description
        result = parser.parse(str(test_file))
        
        print(f"  Extracted job title: {result.get('job_title', 'NOT FOUND')}")
        print(f"  Extracted location: {result.get('location', 'NOT FOUND')}")
        print(f"  Extracted certifications: {len(result.get('certifications', []))}")
        print(f"  Extracted required skills: {len(result.get('required_skills', []))}")
        
        # Cleanup
        test_file.unlink()
        
        # Validate results
        if result.get('job_title') and 'solar' in result.get('job_title', '').lower():
            print("✓ AI Job Parser test PASSED")
            return True
        else:
            print(f"✗ AI Job Parser test FAILED: Job title not extracted correctly")
            print(f"  Got: {result.get('job_title')}")
            return False
            
    except Exception as e:
        print(f"✗ AI Job Parser test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_resume_parser():
    """Test AI resume parser"""
    print("\n" + "="*80)
    print("TEST 3: AI Resume Parser")
    print("="*80)
    
    try:
        from ai_resume_parser import AIResumeParser
        
        parser = AIResumeParser()
        print("✓ AIResumeParser initialized successfully")
        
        # Create a test resume file
        test_resume_content = """
        John Doe
        Email: john.doe@email.com
        Phone: (555) 123-4567
        Location: San Francisco, CA
        
        EXPERIENCE:
        Safety Manager | ABC Construction | 2018 - Present
        - Managed safety protocols for construction projects
        - Conducted safety training sessions
        - Ensured OSHA compliance
        
        SKILLS:
        - Safety Management
        - Risk Assessment
        - OSHA Compliance
        - Training Development
        
        CERTIFICATIONS:
        - OSHA 30 Hour Certification
        - CSP (Certified Safety Professional)
        
        EDUCATION:
        Bachelor of Science in Safety Engineering | State University | 2015
        """
        
        test_file = Path("test_resume.txt")
        test_file.write_text(test_resume_content)
        
        print(f"  Created test resume file: {test_file}")
        
        # Parse the resume
        result = parser.parse(str(test_file))
        
        print(f"  Extracted name: {result.get('name', 'NOT FOUND')}")
        print(f"  Extracted email: {result.get('email', 'NOT FOUND')}")
        print(f"  Extracted skills: {len(result.get('skills', []))}")
        print(f"  Extracted certifications: {len(result.get('certifications', []))}")
        
        # Cleanup
        test_file.unlink()
        
        # Validate results
        if result.get('name') and result.get('skills'):
            print("✓ AI Resume Parser test PASSED")
            return True
        else:
            print(f"✗ AI Resume Parser test FAILED: Missing required fields")
            return False
            
    except Exception as e:
        print(f"✗ AI Resume Parser test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_scoring_engine():
    """Test AI scoring engine"""
    print("\n" + "="*80)
    print("TEST 4: AI Scoring Engine")
    print("="*80)
    
    try:
        from ai_scoring_engine import AIScoringEngine, HybridScoringEngine
        from models import JobDetails, Certification
        
        # Test HybridScoringEngine initialization
        scoring_engine = HybridScoringEngine(use_ai=True)
        print("✓ HybridScoringEngine initialized successfully")
        
        # Create test job details
        job_details = JobDetails(
            job_title="Solar Safety Manager",
            certifications=[
                Certification(name="OSHA 30", category="must-have"),
                Certification(name="CSP", category="must-have")
            ],
            location="Remote",
            full_description="Seeking experienced safety manager for solar projects."
        )
        
        # Create test candidate
        candidate = {
            'name': 'John Doe',
            'email': 'john@email.com',
            'phone': '555-1234',
            'skills': ['Safety Management', 'OSHA Compliance', 'Risk Assessment'],
            'certifications': ['OSHA 30 Hour Certification', 'CSP'],
            'years_of_experience': 5,
            'job_titles': ['Safety Manager'],
            'location': 'San Francisco, CA'
        }
        
        print("  Created test job details and candidate")
        
        # Score the candidate
        score_result = scoring_engine.score_candidate(candidate, job_details)
        
        print(f"  Candidate name: {score_result.name}")
        print(f"  Fit score: {score_result.fit_score}/10")
        print(f"  Certifications match: {score_result.certification_match}")
        
        if score_result.fit_score > 0:
            print("✓ AI Scoring Engine test PASSED")
            return True
        else:
            print("✗ AI Scoring Engine test FAILED: Invalid score")
            return False
            
    except Exception as e:
        print(f"✗ AI Scoring Engine test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_certification_researcher():
    """Test AI certification researcher"""
    print("\n" + "="*80)
    print("TEST 5: AI Certification Researcher")
    print("="*80)
    
    try:
        from ai_certification_researcher import AICertificationResearcher
        
        researcher = AICertificationResearcher()
        print("✓ AICertificationResearcher initialized successfully")
        
        # Test finding equivalents
        cert = "OSHA 30 or equivalent"
        job_context = "Solar safety manager position requiring OSHA 30 certification"
        
        print(f"  Testing equivalent search for: {cert}")
        equivalents = researcher.find_equivalents(cert, job_context)
        
        print(f"  Found {len(equivalents)} equivalent(s)")
        if equivalents:
            for eq in equivalents:
                print(f"    - {eq}")
        
        # Test expand_certification_list
        certs = ["OSHA 30 or equivalent", "CSP"]
        expanded = researcher.expand_certification_list(certs, job_context)
        
        print(f"  Expanded certification list: {len(expanded)} total")
        
        print("✓ AI Certification Researcher test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ AI Certification Researcher test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_candidate_ranker_app():
    """Test the full CandidateRankerApp workflow"""
    print("\n" + "="*80)
    print("TEST 6: Candidate Ranker App (Full Workflow)")
    print("="*80)
    
    try:
        from candidate_ranker import CandidateRankerApp
        
        app = CandidateRankerApp()
        print("✓ CandidateRankerApp initialized successfully")
        
        # Create test files
        test_job_content = """
        Job Title: Solar Safety Manager
        Location: Remote
        
        We are seeking an experienced Solar Safety Manager.
        
        Required Certifications:
        - OSHA 30 Hour certification (or equivalent)
        - CSP (Certified Safety Professional) or equivalent
        """
        
        test_resume_content = """
        Jane Smith
        Email: jane.smith@email.com
        Phone: (555) 987-6543
        
        EXPERIENCE:
        Safety Manager | XYZ Solar | 2019 - Present
        - Managed safety for solar installation projects
        - OSHA 30 certified
        - CSP certified
        
        CERTIFICATIONS:
        - OSHA 30 Hour Certification
        - CSP (Certified Safety Professional)
        """
        
        job_file = Path("test_job_full.txt")
        resume_file = Path("test_resume_full.txt")
        
        job_file.write_text(test_job_content)
        resume_file.write_text(test_resume_content)
        
        print("  Created test files")
        
        # Run the workflow
        certifications = [
            {"name": "OSHA 30 or equivalent", "category": "must-have"},
            {"name": "CSP or equivalent", "category": "must-have"}
        ]
        
        print("  Running candidate ranking workflow...")
        pdf_path = app.run(
            job_title="Solar Safety Manager",
            certifications=certifications,
            location="Remote",
            job_description=test_job_content,
            resume_files=[str(resume_file)]
        )
        
        print(f"  Generated PDF report: {pdf_path}")
        
        # Cleanup
        job_file.unlink()
        resume_file.unlink()
        
        if Path(pdf_path).exists():
            print("✓ Candidate Ranker App test PASSED")
            return True
        else:
            print("✗ Candidate Ranker App test FAILED: PDF not generated")
            return False
            
    except Exception as e:
        print(f"✗ Candidate Ranker App test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("OPENAI MIGRATION TEST SUITE")
    print("="*80)
    print("\nTesting all components to verify AI (Gemini or OpenAI) configuration...")
    
    results = []
    
    # Run all tests
    results.append(("Configuration", test_config()))
    results.append(("AI Job Parser", test_ai_job_parser()))
    results.append(("AI Resume Parser", test_ai_resume_parser()))
    results.append(("AI Scoring Engine", test_ai_scoring_engine()))
    results.append(("AI Certification Researcher", test_ai_certification_researcher()))
    results.append(("Candidate Ranker App", test_candidate_ranker_app()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("\n" + "="*80)
    print(f"Total: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 All tests passed! Migration is successful.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

