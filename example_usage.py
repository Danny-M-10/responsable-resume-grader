"""
Example Usage of Candidate Ranker Application

This script demonstrates how to use the recruitment candidate
screening and ranking system.
"""

from candidate_ranker import CandidateRankerApp


def main():
    """Example workflow"""

    print("RECRUITMENT CANDIDATE RANKER - EXAMPLE USAGE")
    print("=" * 80)
    print()

    # Initialize the application
    app = CandidateRankerApp()

    # Example: Data Scientist position
    print("Example: Screening candidates for Data Scientist position")
    print()

    # Job details
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
    skills and experience deploying models in production environments.

    REQUIRED QUALIFICATIONS:
    - 5+ years of experience in data science or machine learning
    - Strong proficiency in Python and SQL
    - Experience with machine learning frameworks (TensorFlow, PyTorch, or scikit-learn)
    - Hands-on experience with AWS ML services (SageMaker, etc.)
    - Bachelor's degree in Computer Science, Statistics, Mathematics, or related field
    - AWS Certified Machine Learning - Specialty certification

    PREFERRED QUALIFICATIONS:
    - Master's degree or PhD in relevant field
    - Experience with big data technologies (Spark, Hadoop)
    - Knowledge of deep learning and neural networks
    - Experience in financial services or banking sector
    - Google Cloud or Azure certifications
    - Strong communication and presentation skills

    TECHNICAL SKILLS:
    - Programming: Python, R, SQL
    - ML/AI: TensorFlow, PyTorch, scikit-learn, XGBoost
    - Cloud: AWS (SageMaker, EC2, S3), familiarity with GCP or Azure
    - Data: Pandas, NumPy, Spark, SQL databases, NoSQL
    - Tools: Git, Docker, Jupyter, MLflow
    - Visualization: Matplotlib, Seaborn, Tableau

    RESPONSIBILITIES:
    - Design and implement machine learning models for business problems
    - Deploy and maintain models in production environments
    - Collaborate with engineering teams on ML infrastructure
    - Present findings to stakeholders and executives
    - Mentor junior data scientists

    This is a full-time position based in New York, NY.
    Competitive salary and benefits package.
    """

    # Resume files to evaluate
    # NOTE: Replace these with actual resume file paths
    resume_files = [
        # "resumes/candidate1.pdf",
        # "resumes/candidate2.pdf",
        # "resumes/candidate3.docx",
        # Add more resume files here
    ]

    # Check if resume files are provided
    if not resume_files:
        print("=" * 80)
        print("NO RESUME FILES PROVIDED")
        print("=" * 80)
        print()
        print("To use this example:")
        print("1. Place resume files (PDF, DOCX, or TXT) in a 'resumes' folder")
        print("2. Update the resume_files list in this script with the file paths")
        print("3. Run the script again")
        print()
        print("Example:")
        print("  resume_files = [")
        print("      'resumes/john_doe.pdf',")
        print("      'resumes/jane_smith.docx',")
        print("      'resumes/alex_johnson.txt'")
        print("  ]")
        print()
        return

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
        print("SUCCESS!")
        print("=" * 80)
        print()
        print(f"Report generated at: {pdf_path}")
        print()
        print("The report includes:")
        print("  - Job summary with extracted requirements")
        print("  - Ranked list of top candidates")
        print("  - Detailed scoring rationale for each candidate")
        print("  - Visual ranking matrix")
        print("  - Overall analysis and recommendations")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print()
        print(f"An error occurred: {e}")
        print()
        print("Please check:")
        print("  - All resume files exist and are readable")
        print("  - File formats are supported (PDF, DOCX, TXT)")
        print("  - You have write permissions in the current directory")
        print()


def create_sample_resumes():
    """
    Helper function to create sample resume text files for testing
    Call this if you want to generate sample resumes
    """
    import os

    os.makedirs("resumes", exist_ok=True)

    # Sample Resume 1 - Strong match
    resume1 = """
JANE SMITH
New York, NY 10001
jane.smith@email.com | (555) 123-4567

CERTIFICATIONS
- AWS Certified Machine Learning - Specialty
- Google Cloud Professional Data Engineer

PROFESSIONAL EXPERIENCE

Senior Data Scientist | XYZ Financial Corp | 2019 - Present
- Design and deploy machine learning models for credit risk assessment
- Led team of 3 data scientists on fraud detection project
- Implemented MLOps pipeline using AWS SageMaker and MLflow
- Technologies: Python, TensorFlow, PyTorch, AWS, SQL

Data Scientist | ABC Analytics | 2017 - 2019
- Built predictive models for customer churn
- Developed recommendation systems using collaborative filtering
- Technologies: Python, scikit-learn, Spark, PostgreSQL

EDUCATION
Master of Science in Data Science | Columbia University | 2017
Bachelor of Science in Mathematics | NYU | 2015

TECHNICAL SKILLS
Programming: Python, R, SQL
ML/AI: TensorFlow, PyTorch, scikit-learn, XGBoost, Keras
Cloud: AWS (SageMaker, EC2, S3, Lambda), Google Cloud Platform
Data: Pandas, NumPy, Spark, PostgreSQL, MongoDB
Tools: Git, Docker, Jupyter, MLflow, Airflow
Visualization: Matplotlib, Seaborn, Tableau, Power BI
"""

    # Sample Resume 2 - Moderate match
    resume2 = """
JOHN DOE
Boston, MA 02101
john.doe@email.com | (555) 234-5678

PROFESSIONAL EXPERIENCE

Machine Learning Engineer | Tech Startup Inc | 2020 - Present
- Develop ML models for natural language processing
- Deploy models using Kubernetes and Docker
- Technologies: Python, TensorFlow, Kubernetes, GCP

Data Analyst | Retail Company | 2018 - 2020
- Performed statistical analysis on sales data
- Created dashboards using Tableau
- Technologies: Python, SQL, Tableau

EDUCATION
Bachelor of Science in Computer Science | MIT | 2018

TECHNICAL SKILLS
Python, TensorFlow, scikit-learn, SQL, Git, Docker, GCP, Tableau

CERTIFICATIONS
- Google Cloud Professional Machine Learning Engineer (in progress)
"""

    # Sample Resume 3 - Lower match
    resume3 = """
ALEX JOHNSON
San Francisco, CA 94102
alex.j@email.com | (555) 345-6789

PROFESSIONAL EXPERIENCE

Junior Data Scientist | StartupXYZ | 2022 - Present
- Assist in building predictive models
- Perform data cleaning and preprocessing
- Technologies: Python, pandas, scikit-learn

Data Intern | Company ABC | 2021 - 2022
- Created data visualizations
- Performed basic statistical analysis

EDUCATION
Bachelor of Science in Statistics | UC Berkeley | 2021

TECHNICAL SKILLS
Python, pandas, NumPy, scikit-learn, SQL, Excel, Tableau
"""

    # Write files
    with open("resumes/jane_smith.txt", "w") as f:
        f.write(resume1)

    with open("resumes/john_doe.txt", "w") as f:
        f.write(resume2)

    with open("resumes/alex_johnson.txt", "w") as f:
        f.write(resume3)

    print("Sample resumes created in 'resumes/' directory")
    print("  - jane_smith.txt")
    print("  - john_doe.txt")
    print("  - alex_johnson.txt")
    print()
    print("Update example_usage.py to use these files:")
    print("  resume_files = [")
    print("      'resumes/jane_smith.txt',")
    print("      'resumes/john_doe.txt',")
    print("      'resumes/alex_johnson.txt'")
    print("  ]")


if __name__ == "__main__":
    # Uncomment the following line to create sample resumes for testing
    # create_sample_resumes()

    main()
