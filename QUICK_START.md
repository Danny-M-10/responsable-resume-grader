# Quick Start Guide

Get started with the Recruitment Candidate Ranker in 3 easy steps.

## Option 1: Web Interface (Recommended)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_ai.txt
```

### Step 2: Configure OpenAI API Key

The application requires an OpenAI API key. Set it up:

```bash
# Add to .env file (recommended)
echo "OPENAI_API_KEY=your-api-key-here" >> .env

# Or export as environment variable
export OPENAI_API_KEY='your-api-key-here'
```

See `OPENAI_API_SETUP.md` for detailed instructions.

### Step 3: Launch the Web App

```bash
streamlit run app_enhanced.py
```

**Note:** Use `app_enhanced.py` for automatic job description extraction from uploaded files.

This will open a web browser with the application interface.

### Step 3: Use the Application

1. Enter job details (title, location, certifications)
2. Paste the full job description
3. Upload candidate resume files (PDF, DOCX, or TXT)
4. Click "Process Candidates"
5. Download the generated PDF report

## Option 2: Python Script

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_ai.txt
```

### Step 2: Configure OpenAI API Key

```bash
# Add to .env file
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

See `OPENAI_API_SETUP.md` for detailed instructions.

### Step 2: Create Sample Resumes (Optional)

Edit `example_usage.py` and uncomment:

```python
create_sample_resumes()
```

Run once to generate sample resumes:

```bash
python example_usage.py
```

### Step 3: Update and Run

Edit `example_usage.py` to specify your resume files:

```python
resume_files = [
    "resumes/candidate1.pdf",
    "resumes/candidate2.pdf",
    "resumes/candidate3.docx"
]
```

Run the script:

```bash
python example_usage.py
```

### Step 4: View Report

The PDF report will be generated in the current directory:
```
Candidate_Ranking_Report_YYYYMMDD_HHMMSS.pdf
```

## Understanding the Output

### PDF Report Sections

1. **Job Summary**
   - Analyzed requirements
   - Equivalent titles
   - Required and preferred skills

2. **Candidate Rankings**
   - Top 4-10 candidates
   - Fit scores (1-10)
   - Contact information
   - Certifications
   - Detailed rationales

3. **Ranking Visualization**
   - Matrix chart
   - Green checkmarks: Meets criteria
   - Red X marks: Does not meet criteria
   - Color-coded scores

4. **Overall Notes**
   - Summary statistics
   - Trends and patterns
   - Recommendations

### Score Interpretation

- **8.0-10.0**: Excellent fit, highly recommended for interview
- **6.5-7.9**: Good fit with minor gaps, recommended
- **5.0-6.4**: Viable candidate with limitations, consider
- **Below 5.0**: Limited fit for position, deprioritize

## Tips for Best Results

1. **Job Description**: Include clear sections for required vs preferred qualifications
2. **Certifications**: Specify "must-have" vs "bonus" accurately
3. **Resumes**: Use text-based PDFs (not scanned images)
4. **Skills**: The system recognizes synonyms (e.g., JavaScript = JS)

## Troubleshooting

### Web interface not loading
```bash
streamlit run app.py --server.port 8501
```

### PDF generation errors
Ensure write permissions in current directory

### Resume parsing issues
- Check file format (PDF, DOCX, TXT only)
- Ensure PDFs are text-based, not scanned images

## Next Steps

- See `README.md` for detailed documentation
- Review `example_usage.py` for code examples
- Check generated PDF report for full candidate analysis

## Support

For issues, refer to the main README or contact the development team.
