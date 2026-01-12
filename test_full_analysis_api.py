#!/usr/bin/env python3
"""
API-based test script to complete a full candidate analysis workflow.

This script tests the complete analysis workflow:
1. Login/Authentication
2. Upload job description
3. Upload resume files
4. Start analysis
5. Monitor progress
6. Retrieve and display results

Usage:
    python test_full_analysis_api.py
"""

import requests
import json
import time
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Configuration
BASE_URL = "https://recruiting.crossroadcoach.com"
TEST_EMAIL = "testuser2026@example.com"
TEST_PASSWORD = "TestPassword123!"

# Sample files
SAMPLE_JOB_FILE = "sample_job_descriptions/data_scientist_job.txt"
SAMPLE_RESUME_FILES = [
    "sample_resumes/jane_smith_resume.txt",
    "sample_resumes/john_doe_resume.txt",
    "sample_resumes/michael_chen_resume.txt",
]


class AnalysisTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.job_id: Optional[str] = None
        self.candidate_ids: List[str] = []
        self.analysis_id: Optional[str] = None

    def login(self, email: str, password: str) -> bool:
        """Login and store authentication token."""
        print("🔐 Logging in...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"email": email, "password": password},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: No token in response")
                return False
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def upload_job(self, job_file_path: str) -> bool:
        """Upload job description file."""
        print(f"\n📄 Uploading job description: {job_file_path}")
        try:
            job_path = Path(job_file_path)
            if not job_path.exists():
                print(f"❌ Job file not found: {job_file_path}")
                return False

            with open(job_path, 'rb') as f:
                files = {'file': (job_path.name, f, 'text/plain')}
                response = self.session.post(
                    f"{self.base_url}/api/jobs/upload",
                    files=files,
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                self.job_id = data.get("id")
                print(f"✅ Job uploaded successfully")
                print(f"   Job ID: {self.job_id}")
                if data.get("parsed_data"):
                    parsed = data["parsed_data"]
                    print(f"   Job Title: {parsed.get('job_title', 'N/A')}")
                    print(f"   Location: {parsed.get('location', 'N/A')}")
                return True
        except Exception as e:
            print(f"❌ Job upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text[:200]}")
            return False

    def upload_resumes(self, resume_file_paths: List[str]) -> bool:
        """Upload multiple resume files."""
        print(f"\n📄 Uploading {len(resume_file_paths)} resume files...")
        try:
            files = []
            for resume_path in resume_file_paths:
                path = Path(resume_path)
                if not path.exists():
                    print(f"⚠️  Resume file not found: {resume_path}")
                    continue
                files.append(('files', (path.name, open(path, 'rb'), 'text/plain')))

            if not files:
                print("❌ No valid resume files found")
                return False

            response = self.session.post(
                f"{self.base_url}/api/resumes/upload",
                files=files,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            self.candidate_ids = data.get("candidate_ids", [])
            print(f"✅ Resumes uploaded successfully")
            print(f"   Candidate IDs: {len(self.candidate_ids)}")
            for i, candidate_id in enumerate(self.candidate_ids, 1):
                print(f"   {i}. {candidate_id}")
            return True
        except Exception as e:
            print(f"❌ Resume upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text[:200]}")
            return False
        finally:
            # Close file handles
            for _, file_tuple in files:
                if len(file_tuple) > 1:
                    file_tuple[1].close()

    def start_analysis(self, industry_template: str = "general") -> bool:
        """Start candidate analysis."""
        if not self.job_id:
            print("❌ No job ID available. Upload job first.")
            return False
        if not self.candidate_ids:
            print("❌ No candidate IDs available. Upload resumes first.")
            return False

        print(f"\n🚀 Starting analysis...")
        print(f"   Job ID: {self.job_id}")
        print(f"   Candidates: {len(self.candidate_ids)}")
        print(f"   Industry Template: {industry_template}")

        try:
            config = {
                "job_id": self.job_id,
                "candidate_ids": self.candidate_ids,
                "industry_template": industry_template,
                "bias_reduction_enabled": False
            }

            response = self.session.post(
                f"{self.base_url}/api/analysis/start",
                json=config,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            self.analysis_id = data.get("id")
            status = data.get("status")
            print(f"✅ Analysis started successfully")
            print(f"   Analysis ID: {self.analysis_id}")
            print(f"   Status: {status}")
            return True
        except Exception as e:
            print(f"❌ Analysis start failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text[:200]}")
            return False

    def get_analysis_status(self) -> Optional[Dict[str, Any]]:
        """Get current analysis status."""
        if not self.analysis_id:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/api/analysis/{self.analysis_id}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Failed to get analysis status: {e}")
            return None

    def wait_for_analysis_completion(self, max_wait: int = 300, check_interval: int = 5) -> bool:
        """Wait for analysis to complete."""
        if not self.analysis_id:
            print("❌ No analysis ID available")
            return False

        print(f"\n⏳ Waiting for analysis to complete (max {max_wait}s)...")
        start_time = time.time()
        last_status = None

        while time.time() - start_time < max_wait:
            status_data = self.get_analysis_status()
            if not status_data:
                time.sleep(check_interval)
                continue

            status = status_data.get("status")
            if status != last_status:
                print(f"   Status: {status}")
                last_status = status

            if status == "completed":
                print(f"✅ Analysis completed!")
                return True
            elif status == "failed":
                print(f"❌ Analysis failed")
                return False

            time.sleep(check_interval)

        print(f"⏱️  Analysis did not complete within {max_wait}s")
        return False

    def get_results(self) -> Optional[Dict[str, Any]]:
        """Retrieve analysis results."""
        if not self.analysis_id:
            return None

        print(f"\n📊 Retrieving analysis results...")
        status_data = self.get_analysis_status()
        if status_data and status_data.get("status") == "completed":
            results = status_data.get("results")
            if results:
                print(f"✅ Results retrieved successfully")
                return results
            else:
                print(f"⚠️  Analysis completed but no results found")
                return None
        else:
            print(f"⚠️  Analysis not completed yet")
            return None

    def display_results_summary(self, results: Dict[str, Any]) -> None:
        """Display a summary of analysis results."""
        print(f"\n{'='*60}")
        print(f"ANALYSIS RESULTS SUMMARY")
        print(f"{'='*60}")

        if not results:
            print("No results to display")
            return

        # Display ranked candidates
        ranked_candidates = results.get("ranked_candidates", [])
        if ranked_candidates:
            print(f"\n📋 Ranked Candidates ({len(ranked_candidates)}):")
            print(f"{'-'*60}")
            for i, candidate in enumerate(ranked_candidates, 1):
                name = candidate.get("name", "Unknown")
                score = candidate.get("total_score", 0)
                print(f"{i}. {name}: {score:.2f}%")
                if candidate.get("summary"):
                    summary = candidate["summary"][:100]
                    print(f"   {summary}...")

        # Display summary statistics
        summary = results.get("summary", {})
        if summary:
            print(f"\n📈 Summary Statistics:")
            print(f"{'-'*60}")
            total_candidates = summary.get("total_candidates", 0)
            qualified = summary.get("qualified_count", 0)
            print(f"Total Candidates: {total_candidates}")
            print(f"Qualified: {qualified}")

        print(f"{'='*60}\n")

    def run_full_test(self, job_file: str, resume_files: List[str]) -> bool:
        """Run the complete analysis workflow."""
        print("="*60)
        print("FULL CANDIDATE ANALYSIS TEST")
        print("="*60)

        # Step 1: Login
        if not self.login(TEST_EMAIL, TEST_PASSWORD):
            return False

        # Step 2: Upload job
        if not self.upload_job(job_file):
            return False

        # Step 3: Upload resumes
        if not self.upload_resumes(resume_files):
            return False

        # Step 4: Start analysis
        if not self.start_analysis(industry_template="technology"):
            return False

        # Step 5: Wait for completion
        if not self.wait_for_analysis_completion():
            return False

        # Step 6: Get results
        results = self.get_results()
        if results:
            self.display_results_summary(results)
            return True
        else:
            print("❌ Failed to retrieve results")
            return False


def main():
    """Main test function."""
    tester = AnalysisTester(BASE_URL)

    # Check if sample files exist
    job_file = Path(SAMPLE_JOB_FILE)
    resume_files = [Path(f) for f in SAMPLE_RESUME_FILES]

    missing_files = []
    if not job_file.exists():
        missing_files.append(str(job_file))
    for rf in resume_files:
        if not rf.exists():
            missing_files.append(str(rf))

    if missing_files:
        print("❌ Missing sample files:")
        for f in missing_files:
            print(f"   - {f}")
        return 1

    # Run test
    success = tester.run_full_test(
        job_file=str(job_file),
        resume_files=[str(rf) for rf in resume_files]
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
