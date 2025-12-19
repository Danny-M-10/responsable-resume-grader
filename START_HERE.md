# Welcome to the Recruitment Candidate Ranker

## What is This?

An AI-powered application that screens job candidates and ranks them intelligently, providing:
- Automated resume analysis
- Chain-of-thought scoring (transparent reasoning)
- Professional PDF reports with visualizations
- Top 4-10 candidate rankings

## Quick Start (3 Steps)

### Step 1: Install

**Option A - Automatic (Recommended)**

On macOS/Linux:
```bash
./setup.sh
```

On Windows:
```cmd
setup.bat
```

**Option B - Manual**
```bash
pip install -r requirements.txt
pip install -r requirements_ai.txt
```

### Step 1b: Configure OpenAI API Key (Required)

The application uses OpenAI GPT-4 Turbo for AI-powered analysis. You must set up an API key:

```bash
# Add to .env file (recommended)
echo "OPENAI_API_KEY=your-api-key-here" >> .env

# Or export as environment variable
export OPENAI_API_KEY='your-api-key-here'
```

See `OPENAI_API_SETUP.md` for detailed setup instructions.

### Step 2: Run

**Web Interface (Easiest)**
```bash
streamlit run app_enhanced.py
```
Then use your browser to upload a job description file (PDF, DOCX, or TXT) and candidate resumes. The system will automatically extract all requirements!

**Python Code**
```bash
python example_usage.py
```
Edit the file first to specify your resume files.

### Step 3: Get Results

Download the generated PDF report containing:
- Job analysis
- Ranked candidates with scores
- Detailed rationales
- Visual ranking chart

## What You Need

### Inputs Required
1. Job title (e.g., "Data Scientist")
2. Certifications with categories:
   - must-have (required)
   - bonus (preferred)
3. Location (e.g., "New York, NY")
4. Full job description
5. Candidate resume files (PDF, DOCX, or TXT)

### The Process
1. Analyzes job requirements
2. Parses resume files
3. Scores candidates (1-10) with reasoning
4. Ranks and selects top candidates
5. Generates professional PDF report

### The Output
A downloadable PDF with:
- Job summary and interpretation
- Top 4-10 ranked candidates
- Contact info and certifications
- Detailed rationales for each
- Visual ranking matrix
- Overall recommendations

## Documentation

Choose based on your needs:

**I want to start immediately**
→ Read: QUICK_START.md (3 min read)

**I want to understand everything**
→ Read: USER_MANUAL.md (15 min read)

**I'm a developer**
→ Read: README.md (10 min read)

**I want project overview**
→ Read: PROJECT_SUMMARY.md (5 min read)

## Example Usage

### Web Interface
1. Run: `streamlit run app.py`
2. Fill in job details in browser
3. Upload resume files
4. Click "Process Candidates"
5. Download PDF report

### Python API
```python
from candidate_ranker import CandidateRankerApp

app = CandidateRankerApp()

pdf_path = app.run(
    job_title="Data Scientist",
    certifications=[
        {"name": "AWS Certified ML", "category": "must-have"},
        {"name": "GCP Data Engineer", "category": "bonus"}
    ],
    location="New York, NY",
    job_description="[Full description here]",
    resume_files=["resume1.pdf", "resume2.pdf"]
)

print(f"Report: {pdf_path}")
```

## Key Features

1. **No Questions Asked**
   - Processes inputs directly
   - No clarification needed

2. **Transparent Scoring**
   - Shows step-by-step reasoning
   - Explains every decision

3. **Smart Matching**
   - Recognizes equivalent skills
   - Matches synonyms
   - Finds transferable experience

4. **Professional Reports**
   - Publication-ready PDFs
   - Charts and visualizations
   - Detailed analysis

## Scoring Criteria

Candidates scored on weighted criteria:
- Must-have certifications: 30%
- Required skills: 25%
- Bonus certifications: 10%
- Preferred skills: 10%
- Experience level: 10%
- Job title match: 10%
- Location: 5%

Final scores: 1-10
- 8.0-10.0: Excellent fit
- 6.5-7.9: Good fit
- 5.0-6.4: Viable candidate
- Below 5.0: Limited fit

## Files Overview

**Core Application**
- candidate_ranker.py - Main application
- resume_parser.py - Resume parsing
- scoring_engine.py - Candidate scoring
- pdf_generator.py - PDF generation
- skills_researcher.py - Synonym matching
- models.py - Data structures

**User Interfaces**
- app.py - Web interface
- example_usage.py - Python examples

**Documentation**
- START_HERE.md - This file
- QUICK_START.md - Fast setup
- USER_MANUAL.md - Comprehensive guide
- README.md - Technical docs
- PROJECT_SUMMARY.md - Overview

**Setup**
- requirements.txt - Dependencies
- setup.sh - Unix installer
- setup.bat - Windows installer

## Troubleshooting

**Installation fails**
- Ensure Python 3.8+ installed
- Try: `pip install --upgrade pip`

**Web interface won't start**
- Check if port 8501 is available
- Try: `streamlit run app.py --server.port 8502`

**Resume parsing issues**
- Use text-based PDFs (not scanned)
- Try DOCX or TXT format

**Low scores for all candidates**
- Review job description clarity
- Check if requirements too specific

For more help, see USER_MANUAL.md troubleshooting section.

## System Requirements

- Python 3.8 or higher
- 500 MB disk space
- Windows, macOS, or Linux

## Support

All documentation is included:
- Technical details: README.md
- User guide: USER_MANUAL.md
- Quick start: QUICK_START.md
- Code examples: example_usage.py

## Ready to Start?

1. Run setup: `./setup.sh` (or `setup.bat` on Windows)
2. Configure OpenAI API key: See `OPENAI_API_SETUP.md`
3. Launch app: `streamlit run app_enhanced.py`
4. Start screening candidates!

---

**Version 1.0 | December 2024**

For ResponsAble Safety Staffing
