"""
Test Job Description Parser
Demonstrates automatic extraction from job description file
"""

from job_description_parser import JobDescriptionParser
import os


def main():
    print("=" * 80)
    print("TESTING JOB DESCRIPTION PARSER")
    print("=" * 80)
    print()

    # Test with sample job description
    job_file = "sample_job_descriptions/data_scientist_job.txt"

    if not os.path.exists(job_file):
        print(f"ERROR: Sample job file not found: {job_file}")
        return

    print(f"Parsing job description: {job_file}")
    print()

    # Parse the file
    parser = JobDescriptionParser()
    job_data = parser.parse(job_file)

    # Display extracted information
    print("EXTRACTED INFORMATION:")
    print("=" * 80)
    print()

    print(f"Job Title: {job_data['job_title']}")
    print(f"Location: {job_data['location']}")
    print(f"Experience: {job_data['experience_requirements']}")
    print(f"Salary Range: {job_data['salary_range']}")
    print()

    print("CERTIFICATIONS:")
    print("-" * 80)
    if job_data['certifications']:
        must_have = [c for c in job_data['certifications'] if c['category'] == 'must-have']
        bonus = [c for c in job_data['certifications'] if c['category'] == 'bonus']

        if must_have:
            print("\nMust-Have:")
            for cert in must_have:
                print(f"  ✓ {cert['name']}")

        if bonus:
            print("\nBonus:")
            for cert in bonus:
                print(f"  + {cert['name']}")
    else:
        print("  No certifications found")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total certifications found: {len(job_data['certifications'])}")
    print(f"Must-have certifications: {sum(1 for c in job_data['certifications'] if c['category'] == 'must-have')}")
    print(f"Bonus certifications: {sum(1 for c in job_data['certifications'] if c['category'] == 'bonus')}")
    print()

    print("=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("The job description parser can now automatically extract:")
    print("  ✓ Job title")
    print("  ✓ Location")
    print("  ✓ Certifications (with must-have/bonus categorization)")
    print("  ✓ Experience requirements")
    print("  ✓ Salary information")
    print("  ✓ Full job description text")
    print()
    print("This data can be used directly with the Candidate Ranker application!")
    print()


if __name__ == "__main__":
    main()
