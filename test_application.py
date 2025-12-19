"""
Test Script for Candidate Ranker Application
Runs a complete test with sample resumes
"""

from candidate_ranker import CandidateRankerApp
import os
import glob


def main():
    print("=" * 80)
    print("TESTING RECRUITMENT CANDIDATE RANKER APPLICATION")
    print("=" * 80)
    print()

    # Initialize the application
    app = CandidateRankerApp()

    # Define job details
    job_title = "Data Scientist"

    certifications = [
        {"name": "AWS Certified Machine Learning - Specialty", "category": "must-have"},
        {"name": "Google Cloud Professional Data Engineer", "category": "bonus"},
        {"name": "Microsoft Certified: Azure Data Scientist Associate", "category": "bonus"}
    ]

    location = "New York, NY"

    job_description = """
    DATA SCIENTIST - FINANCE SECTOR

    We are seeking an experienced Data Scientist to join our analytics team
    in our New York office. The ideal candidate will have strong machine learning
    skills and experience deploying models in production environments within
    the financial services industry.

    REQUIRED QUALIFICATIONS:
    - 5+ years of experience in data science or machine learning
    - Strong proficiency in Python and SQL
    - Experience with machine learning frameworks (TensorFlow, PyTorch, or scikit-learn)
    - Hands-on experience with AWS ML services (SageMaker, Lambda, etc.)
    - Bachelor's degree in Computer Science, Statistics, Mathematics, or related field
    - AWS Certified Machine Learning - Specialty certification
    - Experience in financial services or banking sector preferred
    - Proven track record of deploying ML models to production

    PREFERRED QUALIFICATIONS:
    - Master's degree or PhD in relevant field
    - Experience with big data technologies (Spark, Hadoop)
    - Knowledge of deep learning and neural networks
    - Google Cloud or Azure certifications
    - Experience with MLOps and model governance
    - Strong communication and presentation skills
    - Leadership and team management experience

    TECHNICAL SKILLS REQUIRED:
    - Programming: Python (required), R, SQL
    - ML/AI: TensorFlow, PyTorch, scikit-learn, XGBoost
    - Cloud: AWS (SageMaker, EC2, S3, Lambda) - required
    - Data: Pandas, NumPy, Spark, SQL databases
    - Tools: Git, Docker, MLflow, Jupyter
    - Visualization: Matplotlib, Seaborn, Tableau or Power BI

    RESPONSIBILITIES:
    - Design and implement machine learning models for financial risk assessment
    - Deploy and maintain models in production environments using AWS
    - Collaborate with engineering teams on ML infrastructure
    - Present findings to stakeholders and executives
    - Mentor junior data scientists
    - Ensure models comply with financial regulations

    SOFT SKILLS:
    - Excellent communication and presentation abilities
    - Strong analytical and problem-solving skills
    - Ability to work collaboratively in cross-functional teams
    - Self-motivated and detail-oriented
    - Experience managing stakeholder expectations

    This is a full-time position based in New York, NY.
    Competitive salary ($150K-$200K) and benefits package.
    Some remote work flexibility available.
    """

    # Get sample resume files
    resume_dir = "sample_resumes"
    resume_files = glob.glob(os.path.join(resume_dir, "*.txt"))

    if not resume_files:
        print("ERROR: No resume files found in sample_resumes directory")
        return

    print(f"Found {len(resume_files)} sample resumes:")
    for i, resume_file in enumerate(resume_files, 1):
        print(f"  {i}. {os.path.basename(resume_file)}")
    print()

    # Run the screening process
    print("Starting candidate screening process...")
    print()

    try:
        pdf_path = app.run(
            job_title=job_title,
            certifications=certifications,
            location=location,
            job_description=job_description,
            resume_files=resume_files
        )

        print()
        print("=" * 80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print(f"PDF Report generated at: {pdf_path}")
        print()

        # Display results summary
        print("RESULTS SUMMARY:")
        print("-" * 80)
        print(f"Total candidates evaluated: {len(app.candidate_scores)}")
        print()

        print("Top Candidates (sorted by fit score):")
        print()

        for i, candidate in enumerate(app.candidate_scores[:10], 1):
            print(f"{i}. {candidate.name}")
            print(f"   Score: {candidate.fit_score}/10")
            print(f"   Email: {candidate.email}")
            print(f"   Phone: {candidate.phone}")
            print(f"   Certifications: {', '.join(candidate.certifications) if candidate.certifications else 'None'}")
            print(f"   Rationale: {candidate.rationale}")
            print()

        # Statistics
        if app.candidate_scores:
            scores = [c.fit_score for c in app.candidate_scores]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)

            print("-" * 80)
            print("STATISTICS:")
            print(f"  Average Score: {avg_score:.2f}")
            print(f"  Highest Score: {max_score:.2f}")
            print(f"  Lowest Score: {min_score:.2f}")
            print(f"  Viable Candidates (score >= 5.0): {sum(1 for s in scores if s >= 5.0)}")
            print()

        print("=" * 80)
        print("Open the PDF report to see the complete analysis with visualizations.")
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print("TEST FAILED")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
