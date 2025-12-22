# Recruitment Candidate Screening and Ranking Application

A comprehensive AI-powered recruitment tool that analyzes job requirements and candidate resumes to provide intelligent ranking with detailed reasoning.

## Features

- Automated resume parsing from PDF, DOCX, and TXT formats
- Intelligent job requirement extraction from descriptions
- Chain-of-thought scoring with transparent reasoning
- Weighted evaluation across multiple criteria
- Professional PDF reports with visualizations
- Skills and job title synonym matching
- Certification requirement validation

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from candidate_ranker import CandidateRankerApp

# Initialize the application
app = CandidateRankerApp()

# Run the screening process
pdf_path = app.run(
    job_title="Data Scientist",
    certifications=[
        {"name": "AWS Certified Machine Learning", "category": "must-have"},
        {"name": "Google Cloud Professional Data Engineer", "category": "bonus"}
    ],
    location="New York, NY",
    job_description="""
    We are seeking a Data Scientist with strong machine learning skills...

    Required Skills:
    - Python, SQL, Machine Learning
    - 5+ years experience in data science
    - AWS ML services

    Preferred Skills:
    - TensorFlow, PyTorch
    - Big data technologies
    """,
    resume_files=[
        "path/to/resume1.pdf",
        "path/to/resume2.pdf",
        "path/to/resume3.docx"
    ]
)

print(f"Report generated: {pdf_path}")
```

### Command Line Example

See `example_usage.py` for a complete working example.

## How It Works

### 1. Job Analysis

The system analyzes the job description to extract:
- Required and preferred skills
- Experience level expectations
- Technical stack requirements
- Soft skills
- Industry context

### 2. Research Phase

Automatically researches:
- Equivalent job titles
- Skill synonyms and alternatives
- Current terminology

### 3. Resume Parsing

Extracts structured data from resumes:
- Contact information
- Skills and technologies
- Certifications
- Work experience
- Education
- Job titles

### 4. Scoring Algorithm

Each candidate receives a score from 1-10 based on weighted criteria:

- Must-have certifications: 30%
- Bonus certifications: 10%
- Required skills: 25%
- Preferred skills: 10%
- Experience level: 10%
- Job title match: 10%
- Location: 5%

### 5. Chain-of-Thought Reasoning

For each candidate, the system provides:
- Step-by-step evaluation process
- Match analysis for each criterion
- Identification of strengths and gaps
- Transparent scoring calculation

### 6. PDF Report

Generated report includes:
- Job summary with interpreted criteria
- Top 4-10 ranked candidates
- Contact information and certifications
- Detailed rationales
- Visual ranking matrix with checkmarks/X marks
- Overall analysis and recommendations

## Report Structure

### Job Summary Section
- Position title and equivalent titles
- Experience level requirements
- Must-have and bonus certifications
- Required and preferred skills
- Location requirements

### Candidate Rankings Section
- Ranked list of top candidates
- Fit scores (1-10 scale)
- Contact information
- Held certifications
- Detailed rationale for each candidate

### Ranking Visualization
- Matrix chart showing criteria matches
- Green checkmarks for met criteria
- Red X marks for unmet criteria
- Color-coded scores

### Overall Notes
- Summary statistics
- Trends in candidate pool
- Recommendations for hiring team

## Scoring Interpretation

- 8.0-10.0: Excellent fit, highly recommended
- 6.5-7.9: Good fit with minor gaps
- 5.0-6.4: Viable candidate with limitations
- Below 5.0: Limited fit for position

## File Formats

### Supported Resume Formats
- PDF (.pdf)
- Microsoft Word (.docx)
- Plain Text (.txt)

### Certification Categories
- `must-have`: Critical certifications (heavily weighted)
- `bonus`: Preferred certifications (additional points)

## Advanced Features

### Synonym Matching

The system recognizes equivalent terms:
- JavaScript = JS = ECMAScript
- Machine Learning = ML = Predictive Modeling
- AWS = Amazon Web Services

### Transferable Skills

Identifies relevant experience even with different titles:
- Data Scientist ↔ Machine Learning Engineer
- Software Engineer ↔ Software Developer

### Location Flexibility

Handles various location scenarios:
- Exact city match
- Remote-friendly positions
- Relocation consideration

## Output

The application generates a timestamped PDF file:

```
Candidate_Ranking_Report_20231217_143022.pdf
```

## Limitations

- Resume parsing accuracy depends on document formatting
- Skills extraction works best with clearly structured resumes
- Synonym matching is based on common industry terms
- Manual review recommended for final hiring decisions

## Best Practices

1. Provide detailed job descriptions with clear requirement sections
2. Use consistent certification names
3. Specify "must-have" vs "bonus" certifications clearly
4. Include both required and preferred skills
5. Ensure resume files are readable (not scanned images)

## Troubleshooting

### PDF Generation Errors
- Ensure all dependencies are installed
- Check write permissions in output directory

### Resume Parsing Issues
- Verify file format is supported
- Check that PDFs are text-based, not scanned images
- Ensure DOCX files are valid Word documents

### Low Match Scores
- Review job description clarity
- Check for overly specific requirements
- Consider broadening skill synonyms

## License

Proprietary - ResponsAble Safety Staffing

## Support

For issues or questions, contact the development team.
