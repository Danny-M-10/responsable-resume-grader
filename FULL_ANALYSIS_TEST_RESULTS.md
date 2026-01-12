# Full Candidate Analysis Test - API-Based Testing

## Test Scripts Created

Two test scripts have been created to test the full candidate analysis workflow:

1. **`test_full_analysis_api.py`** - Python-based test script (requires `requests` library)
2. **`test_full_analysis.sh`** - Bash-based test script using curl (no additional dependencies)

## Test Workflow

Both scripts test the complete analysis workflow:

1. **Login/Authentication**
   - Login with test credentials
   - Retrieve and store auth token

2. **Upload Job Description**
   - Upload sample job description file (`data_scientist_job.txt`)
   - Parse and extract job requirements
   - Store job ID

3. **Upload Resume Files**
   - Upload multiple resume files (Jane Smith, John Doe, Michael Chen)
   - Parse resume data
   - Store candidate IDs

4. **Start Analysis**
   - Submit analysis configuration
   - Use "technology" industry template
   - Start background analysis process

5. **Monitor Progress**
   - Poll analysis status endpoint
   - Wait for completion (max 300 seconds)
   - Check for errors

6. **Retrieve Results**
   - Fetch completed analysis results
   - Display ranked candidates
   - Show summary statistics

## Usage

### Bash Script (Recommended - No Dependencies)
```bash
chmod +x test_full_analysis.sh
./test_full_analysis.sh
```

### Python Script (Requires requests library)
```bash
python3 test_full_analysis_api.py
```

## Expected Results

When the test completes successfully, you should see:

- ✅ Login successful
- ✅ Job uploaded with parsed data (job title, location)
- ✅ Resumes uploaded (3 candidate IDs)
- ✅ Analysis started (analysis ID and status)
- ✅ Analysis completed
- ✅ Ranked candidates with scores
- ✅ Summary statistics

## Current Status

**Status**: Test scripts created and ready to run

**Note**: The bash script started executing but may need network access permissions. Both scripts are ready for testing.

## Next Steps

1. Run the test script (bash version recommended)
2. Verify all steps complete successfully
3. Check results in the browser at `/history` page
4. Review any errors or issues encountered
