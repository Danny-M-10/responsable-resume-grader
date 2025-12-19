# Recruitment Candidate Ranker - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Application Overview](#application-overview)
5. [Using the Web Interface](#using-the-web-interface)
6. [Using the Python API](#using-the-python-api)
7. [Input Requirements](#input-requirements)
8. [Understanding the Output](#understanding-the-output)
9. [Scoring Methodology](#scoring-methodology)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Introduction

The Recruitment Candidate Ranker is an AI-powered system designed for high-level recruitment advisors to screen and rank job candidates efficiently and objectively.

### Key Features

- Automated job requirement analysis
- Resume parsing from multiple formats
- Chain-of-thought scoring with transparent reasoning
- Professional PDF reports with visualizations
- Skills synonym matching
- Equivalent job title recognition
- Web-based and programmatic interfaces

## System Requirements

- Python 3.8 or higher
- 500 MB free disk space
- Internet connection (for package installation)
- Operating Systems: Windows, macOS, Linux

## Installation

1. Download or clone the application files

2. Open a terminal/command prompt

3. Navigate to the application directory:
```bash
cd /path/to/candidate-ranker
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

Installation is complete when all packages install successfully.

## Application Overview

### Architecture

The system consists of several modules:

- **candidate_ranker.py**: Main application orchestration
- **resume_parser.py**: Extracts data from resume files
- **scoring_engine.py**: Evaluates candidates with reasoning
- **pdf_generator.py**: Creates professional reports
- **skills_researcher.py**: Finds equivalent terms
- **models.py**: Data structures
- **app.py**: Web interface (Streamlit)

### Workflow

1. **Job Analysis**: Parse and structure job requirements
2. **Research**: Find equivalent skills and titles
3. **Resume Parsing**: Extract candidate information
4. **Scoring**: Evaluate each candidate with reasoning
5. **Ranking**: Select top 4-10 candidates
6. **Report Generation**: Create downloadable PDF

## Using the Web Interface

### Launching the Interface

```bash
streamlit run app.py
```

A browser window will open automatically at `http://localhost:8501`

### Step-by-Step Guide

#### 1. Enter Job Details

**Job Title**
- Enter the exact position title
- Example: "Data Scientist", "Senior Software Engineer"

**Location**
- Enter the job location
- Example: "New York, NY", "Remote", "San Francisco, CA"

**Certifications**
- Set number of certifications
- For each certification:
  - Enter the full certification name
  - Select category:
    - **must-have**: Required (heavily weighted)
    - **bonus**: Preferred (additional points)

Example:
- AWS Certified Machine Learning - Specialty (must-have)
- Google Cloud Professional Data Engineer (bonus)

#### 2. Enter Job Description

Paste the complete job description including:
- Required qualifications
- Preferred qualifications
- Technical skills
- Experience requirements
- Responsibilities
- Industry context

The system automatically extracts:
- Required vs preferred skills
- Experience level (Junior/Mid/Senior)
- Technical stack
- Soft skills

#### 3. Upload Resumes

- Click "Browse files"
- Select one or more resume files
- Supported formats: PDF, DOCX, TXT
- Multiple files can be uploaded simultaneously

Note: PDF files must be text-based, not scanned images

#### 4. Process Candidates

- Click "Process Candidates"
- Wait for processing to complete
- View results on screen

#### 5. Download Report

- Review top candidates in the interface
- Click "Download PDF Report"
- Save the report to your computer

## Using the Python API

### Basic Usage

```python
from candidate_ranker import CandidateRankerApp

# Initialize
app = CandidateRankerApp()

# Configure job
job_title = "Data Scientist"

certifications = [
    {"name": "AWS Certified Machine Learning", "category": "must-have"},
    {"name": "Google Cloud Data Engineer", "category": "bonus"}
]

location = "New York, NY"

job_description = """
[Full job description text here...]
"""

resume_files = [
    "resumes/candidate1.pdf",
    "resumes/candidate2.pdf",
    "resumes/candidate3.docx"
]

# Process
pdf_path = app.run(
    job_title=job_title,
    certifications=certifications,
    location=location,
    job_description=job_description,
    resume_files=resume_files
)

print(f"Report: {pdf_path}")
```

### Advanced Usage

Access intermediate results:

```python
# After running app.run()

# Job details
print(app.job_details.required_skills)
print(app.job_details.equivalent_titles)

# All candidate scores
for candidate in app.candidate_scores:
    print(f"{candidate.name}: {candidate.fit_score}")
    print(f"Rationale: {candidate.rationale}")
```

## Input Requirements

### Job Title
- Required: Yes
- Format: Text string
- Example: "Data Scientist", "Product Manager"

### Certifications
- Required: No (can be empty list)
- Format: List of dictionaries
- Keys: "name" (string), "category" ("must-have" or "bonus")

### Location
- Required: Yes
- Format: Text string
- Example: "City, State" or "Remote"

### Job Description
- Required: Yes
- Format: Text string (can be multi-line)
- Recommendations:
  - Include "Required" and "Preferred" sections
  - List technical skills explicitly
  - Mention experience level
  - Include responsibilities and context

### Resume Files
- Required: Yes (at least one)
- Formats: PDF (.pdf), Word (.docx), Text (.txt)
- Quality: Text-based PDFs (not scanned images)

## Understanding the Output

### PDF Report Structure

#### Section 1: Job Summary

Contains:
- Position title
- Equivalent job titles identified
- Experience level (Junior/Mid/Senior)
- Must-have certifications
- Bonus certifications
- Required skills
- Preferred skills
- Location

This section shows how the system interpreted the job requirements.

#### Section 2: Candidate Rankings

For each top candidate:

**Header**
- Rank number
- Candidate name
- Fit score (X/10)

**Contact Information**
- Email address
- Phone number

**Certifications**
- List of held certifications
- Or "None listed" if none found

**Rationale**
Concise explanation including:
- Strengths (what matches well)
- Bonus qualifications (extra points)
- Gaps (what's missing)
- Overall assessment

#### Section 3: Ranking Visualization

Matrix chart showing:

**Columns (Criteria)**
1. Must-Have Certs
2. Bonus Certs
3. Required Skills
4. Preferred Skills
5. Experience
6. Job Title
7. Location
8. Score

**Rows**
- One row per candidate

**Symbols**
- ✓ (Green checkmark): Meets criteria
- ✗ (Red X): Does not meet criteria

**Score Colors**
- Dark Green: 8.0-10.0 (Excellent)
- Green: 6.5-7.9 (Good)
- Orange: 5.0-6.4 (Viable)
- Red: Below 5.0 (Limited fit)

#### Section 4: Overall Notes

Contains:
- Summary statistics (average, highest, lowest scores)
- Number of excluded candidates
- Trends and patterns (certification gaps, skill gaps)
- Recommendations for hiring team

### Candidate Selection

The system selects top candidates as follows:
- Candidates with scores ≥ 5.0 are considered viable
- Top 4-10 viable candidates are included
- If fewer than 4 viable candidates, all are included
- Candidates below 5.0 are excluded from top list

## Scoring Methodology

### Weighted Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Must-Have Certifications | 30% | Critical requirements |
| Bonus Certifications | 10% | Preferred certifications |
| Required Skills | 25% | Essential technical skills |
| Preferred Skills | 10% | Nice-to-have skills |
| Experience Level | 10% | Years and seniority match |
| Job Title Match | 10% | Relevant previous titles |
| Location | 5% | Geographic match |

### Scoring Process

For each criterion:

1. **Evaluate match** (0.0 to 1.0 scale)
   - 1.0 = Perfect match
   - 0.5 = Partial match
   - 0.0 = No match

2. **Apply weight**
   - Multiply match score by weight

3. **Scale to 10**
   - Convert to 1-10 scale

4. **Sum all components**
   - Total score = sum of weighted components

### Chain-of-Thought Reasoning

For each candidate, the system documents:

1. Evaluation of each criterion
2. Match identification (MATCH or MISSING)
3. Match rates (e.g., 3/5 skills = 0.60)
4. Weighted calculations
5. Final score

This provides transparency and explainability.

### Equivalent Matching

The system recognizes:

**Job Title Synonyms**
- Data Scientist ↔ ML Engineer ↔ AI Scientist
- Software Engineer ↔ Software Developer ↔ Programmer

**Skill Synonyms**
- JavaScript = JS = ECMAScript
- Machine Learning = ML
- AWS = Amazon Web Services

**Seniority Variations**
- Automatically generates Senior/Junior/Lead variations

## Best Practices

### Job Description Quality

1. **Structure clearly**
   - Use "Required" and "Preferred" sections
   - List skills explicitly
   - Mention experience expectations

2. **Be specific**
   - Name exact technologies (e.g., "Python 3", not just "programming")
   - Specify certification full names
   - Include seniority level

3. **Include context**
   - Industry information
   - Team structure
   - Key responsibilities

### Certification Management

1. **Use full names**
   - "AWS Certified Machine Learning - Specialty"
   - Not: "AWS ML Cert"

2. **Categorize accurately**
   - must-have: Truly required, heavily weighted
   - bonus: Nice to have, adds points

3. **Don't over-require**
   - Too many must-haves may exclude good candidates

### Resume File Quality

1. **Text-based PDFs**
   - Avoid scanned documents
   - Ensure text is selectable

2. **Standard formats**
   - Traditional resume structure
   - Clear section headers (Experience, Education, Skills)

3. **File naming**
   - Use candidate names for easy identification
   - Example: "john_doe_resume.pdf"

### Interpreting Results

1. **Use as a screening tool**
   - Not final hiring decision
   - Supplement with interviews

2. **Review rationales**
   - Understand why scores were assigned
   - Check for false positives/negatives

3. **Consider context**
   - Some good candidates may score lower
   - Manual review recommended for borderline cases

## Troubleshooting

### Installation Issues

**Problem**: pip install fails

**Solutions**:
- Ensure Python 3.8+ is installed
- Try: `pip install --upgrade pip`
- Use virtual environment: `python -m venv venv`

**Problem**: Package conflicts

**Solutions**:
- Use virtual environment
- Update setuptools: `pip install --upgrade setuptools`

### Web Interface Issues

**Problem**: Streamlit doesn't start

**Solutions**:
- Check if port 8501 is available
- Try different port: `streamlit run app.py --server.port 8502`
- Restart terminal and try again

**Problem**: Upload fails

**Solutions**:
- Check file size (very large files may timeout)
- Ensure file format is supported
- Try uploading files one at a time

### Resume Parsing Issues

**Problem**: Name/contact not extracted

**Solutions**:
- Ensure name is at top of resume
- Check that email/phone are formatted standardly
- Try different file format

**Problem**: Skills not detected

**Solutions**:
- Use standard skill names (e.g., "Python" not "Py")
- Include skills in a dedicated section
- Check that resume has clear structure

**Problem**: PDF parsing fails

**Solutions**:
- Verify PDF is text-based (not scanned image)
- Try converting to DOCX or TXT
- Use Adobe Acrobat to re-save PDF

### PDF Generation Issues

**Problem**: PDF creation fails

**Solutions**:
- Check write permissions in directory
- Ensure enough disk space
- Close any open PDF files with same name

**Problem**: Charts not appearing

**Solutions**:
- Ensure matplotlib is installed
- Check for matplotlib backend issues
- Try regenerating report

### Scoring Issues

**Problem**: All scores are low

**Solutions**:
- Review job description clarity
- Check if requirements are too specific
- Verify resume quality and formatting
- Review equivalent title/skill matching

**Problem**: Unexpected rankings

**Solutions**:
- Read chain-of-thought reasoning
- Check certification matching
- Review required vs preferred skills
- Verify experience level expectations

### General Issues

**Problem**: Process takes too long

**Solutions**:
- Check number of resumes (10+ may take longer)
- Verify resume file sizes
- Ensure stable system resources

**Problem**: Results don't match expectations

**Solutions**:
- Review job description interpretation in report
- Check extracted requirements
- Verify candidate data was parsed correctly
- Read chain-of-thought for each candidate

## Appendix

### File Structure

```
candidate-ranker/
├── app.py                    # Web interface
├── candidate_ranker.py       # Main application
├── resume_parser.py          # Resume parsing
├── scoring_engine.py         # Candidate scoring
├── pdf_generator.py          # Report generation
├── skills_researcher.py      # Synonym matching
├── models.py                 # Data structures
├── requirements.txt          # Dependencies
├── README.md                 # Documentation
├── QUICK_START.md           # Quick start guide
├── USER_MANUAL.md           # This file
└── example_usage.py         # Code examples
```

### Support Resources

- README.md: Technical documentation
- QUICK_START.md: Fast setup guide
- example_usage.py: Code examples
- Generated PDF reports: Example outputs

### Version Information

Application Version: 1.0
Last Updated: December 2024

---

For technical support, contact the development team.
