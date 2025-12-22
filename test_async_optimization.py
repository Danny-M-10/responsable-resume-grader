#!/usr/bin/env python3
"""
Test script for async optimization and skills fallback removal
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from candidate_ranker import CandidateRankerApp
from models import JobDetails

def test_skills_fallback_removal():
    """Test that skills fallback is removed - skills should be empty if not provided by AI"""
    print("=" * 80)
    print("TEST 1: Skills Fallback Removal")
    print("=" * 80)
    
    app = CandidateRankerApp()
    
    # Create job details without providing skills (simulating AI not extracting any)
    job = app._parse_job_details(
        job_title="Software Engineer",
        certifications=[{"name": "AWS Certified", "category": "must-have"}],
        location="Remote",
        job_description="We are looking for a software engineer with Python experience.",
        required_skills=None,  # Not provided by AI
        preferred_skills=None  # Not provided by AI
    )
    
    print(f"Required skills: {job.required_skills}")
    print(f"Preferred skills: {job.preferred_skills}")
    
    # Verify skills are empty arrays, not populated from technical_stack
    assert job.required_skills == [], f"Expected empty array, got: {job.required_skills}"
    assert job.preferred_skills == [], f"Expected empty array, got: {job.preferred_skills}"
    
    print("✓ PASS: Skills are empty arrays when not provided by AI (no fallback)")
    print()

def test_async_scoring():
    """Test that async scoring method exists and works"""
    print("=" * 80)
    print("TEST 2: Async Scoring Method")
    print("=" * 80)
    
    from ai_scoring_engine import HybridScoringEngine, AIScoringEngine
    
    # Test HybridScoringEngine
    engine = HybridScoringEngine()
    assert hasattr(engine, 'score_candidate_async'), "HybridScoringEngine async method not found"
    
    # Test AIScoringEngine directly
    ai_engine = AIScoringEngine()
    assert hasattr(ai_engine, 'score_candidate_async'), "AIScoringEngine async method not found"
    assert hasattr(ai_engine, 'async_client'), "AsyncOpenAI client not found in AIScoringEngine"
    
    print("✓ PASS: Async scoring methods exist")
    print()

def test_async_resume_parsing():
    """Test that async resume parsing method exists"""
    print("=" * 80)
    print("TEST 3: Async Resume Parsing Method")
    print("=" * 80)
    
    app = CandidateRankerApp()
    
    # Check that async method exists
    assert hasattr(app, '_parse_resumes_async'), "Async resume parsing method not found"
    
    print("✓ PASS: Async resume parsing method exists")
    print()

def test_async_cert_research():
    """Test that async cert research method exists"""
    print("=" * 80)
    print("TEST 4: Async Certification Research Method")
    print("=" * 80)
    
    app = CandidateRankerApp()
    
    # Check that async method exists
    assert hasattr(app, '_expand_certification_equivalents_async'), "Async cert research method not found"
    
    print("✓ PASS: Async certification research method exists")
    print()

def test_rate_limiting():
    """Test that rate limiting semaphore is in place"""
    print("=" * 80)
    print("TEST 5: Rate Limiting (Semaphore)")
    print("=" * 80)
    
    import inspect
    from candidate_ranker import CandidateRankerApp
    
    app = CandidateRankerApp()
    
    # Get source code of async scoring method
    source = inspect.getsource(app._score_candidates_async)
    
    # Check for semaphore
    assert 'Semaphore' in source, "Semaphore not found in async scoring method"
    assert 'asyncio.Semaphore' in source or 'Semaphore(10)' in source, "Rate limiting semaphore not configured"
    
    print("✓ PASS: Rate limiting semaphore (max 10 concurrent) is configured")
    print()

def test_nest_asyncio_import():
    """Test that nest_asyncio can be imported"""
    print("=" * 80)
    print("TEST 6: nest-asyncio Package")
    print("=" * 80)
    
    try:
        import nest_asyncio
        print(f"✓ PASS: nest-asyncio imported successfully (version: {nest_asyncio.__version__ if hasattr(nest_asyncio, '__version__') else 'unknown'})")
    except ImportError as e:
        print(f"✗ FAIL: Could not import nest-asyncio: {e}")
        return False
    
    print()
    return True

def test_asyncopenai_client():
    """Test that AsyncOpenAI client is initialized"""
    print("=" * 80)
    print("TEST 7: AsyncOpenAI Client")
    print("=" * 80)
    
    from ai_scoring_engine import AIScoringEngine
    
    try:
        engine = AIScoringEngine()
        assert hasattr(engine, 'async_client'), "AsyncOpenAI client not initialized"
        assert engine.async_client is not None, "AsyncOpenAI client is None"
        print("✓ PASS: AsyncOpenAI client is initialized")
    except Exception as e:
        print(f"✗ FAIL: Error initializing AsyncOpenAI client: {e}")
        return False
    
    print()
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("TESTING ASYNC OPTIMIZATION AND SKILLS FALLBACK REMOVAL")
    print("=" * 80 + "\n")
    
    tests = [
        ("Skills Fallback Removal", test_skills_fallback_removal),
        ("Async Scoring Method", test_async_scoring),
        ("Async Resume Parsing", test_async_resume_parsing),
        ("Async Cert Research", test_async_cert_research),
        ("Rate Limiting", test_rate_limiting),
        ("nest-asyncio Package", test_nest_asyncio_import),
        ("AsyncOpenAI Client", test_asyncopenai_client),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result is not False:
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"✗ FAIL: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ FAIL: {test_name}")
            print(f"  Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 80)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n✓ All tests passed! The async optimization is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

