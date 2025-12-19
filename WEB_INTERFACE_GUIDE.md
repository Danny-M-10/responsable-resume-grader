# Web Interface - Quick Access Guide

## ✓ Application Running Successfully!

The Recruitment Candidate Ranker web interface is now live and accessible.

---

## 🌐 Access URLs

### Local Access (Recommended)
**Primary URL**: http://localhost:8501

### Network Access (Same Network)
**Network URL**: http://192.168.4.236:8501

### External Access (If Port Forwarding Enabled)
**External URL**: http://159.48.210.153:8501

---

## 📱 How to Access

### Option 1: Click URL (Easiest)
Simply click on the Local URL above: http://localhost:8501

Your default browser will open the application.

### Option 2: Manual Browser
1. Open your web browser (Chrome, Safari, Firefox, etc.)
2. Type in the address bar: `localhost:8501`
3. Press Enter

### Option 3: Copy-Paste
Copy this URL and paste into your browser:
```
http://localhost:8501
```

---

## 🎯 Using the Web Interface

### Step-by-Step Guide

#### 1. Enter Job Details
Fill in the form with:
- **Job Title**: e.g., "Data Scientist"
- **Location**: e.g., "New York, NY"
- **Number of Certifications**: Select how many
- **Certification Details**: For each certification:
  - Name (e.g., "AWS Certified Machine Learning")
  - Category: "must-have" or "bonus"

#### 2. Add Job Description
Paste the complete job description including:
- Required qualifications
- Preferred qualifications
- Technical skills
- Experience requirements
- Responsibilities

#### 3. Upload Resumes
Click "Browse files" and select resume files:
- Supported formats: PDF, DOCX, TXT
- Can upload multiple files at once
- You can use the sample resumes in `sample_resumes/` folder

#### 4. Process Candidates
Click the "🚀 Process Candidates" button

The application will:
- Analyze the job requirements
- Parse all resumes
- Score each candidate
- Generate rankings

#### 5. View Results
After processing:
- See top candidates on screen
- View scores and rationales
- Review contact information

#### 6. Download PDF Report
Click "📥 Download PDF Report" button
- Professional PDF with all details
- Visual ranking charts
- Ready to share with stakeholders

---

## 💡 Quick Test

Want to try it immediately? Use the sample data:

### 1. Job Details
```
Job Title: Data Scientist
Location: New York, NY
Certifications:
  1. AWS Certified Machine Learning - Specialty (must-have)
  2. Google Cloud Professional Data Engineer (bonus)
```

### 2. Job Description
Use the example from `test_application.py` or create your own.

### 3. Upload Sample Resumes
Navigate to the `sample_resumes/` folder and upload:
- jane_smith_resume.txt
- emily_rodriguez_resume.txt
- sarah_johnson_resume.txt
- michael_chen_resume.txt
- john_doe_resume.txt
- alex_kim_resume.txt

### 4. Process
Click "Process Candidates" and wait ~10 seconds

### 5. Expected Results
- Jane Smith: ~8.68/10 (Top candidate)
- Sarah Johnson: ~8.18/10
- Emily Rodriguez: ~8.02/10

---

## 🖥️ Interface Features

### Input Forms
- Clean, intuitive interface
- Dynamic certification fields
- Large text area for job descriptions
- Multi-file upload with drag-and-drop

### Results Display
- Summary metrics (Total candidates, Top candidates, Average score)
- Expandable candidate cards with details
- Color-coded scores
- Contact information readily visible

### PDF Download
- One-click download
- Professional formatting
- Includes all analysis and charts
- Ready for distribution

---

## 🔧 Troubleshooting

### Can't Access the URL?

**Issue**: Page won't load

**Solutions**:
1. Wait 10 seconds for full startup
2. Try refreshing the page (Cmd+R or F5)
3. Check the URL is exactly: `http://localhost:8501`
4. Ensure no other app is using port 8501

### Upload Not Working?

**Issue**: Can't upload files

**Solutions**:
1. Check file format (PDF, DOCX, or TXT only)
2. Ensure file size is reasonable (< 10MB)
3. Try uploading one file at a time first

### Processing Fails?

**Issue**: Error when clicking "Process Candidates"

**Solutions**:
1. Verify all required fields are filled
2. Check job description is not empty
3. Ensure at least one resume is uploaded
4. Review error message for specific issue

### Slow Processing?

**Issue**: Takes too long to process

**Expected Times**:
- 1-3 resumes: 5-10 seconds
- 4-6 resumes: 10-20 seconds
- 7-10 resumes: 20-40 seconds

If longer, check:
- File sizes (large PDFs take longer)
- System resources

---

## 🎨 Interface Preview

### Main Sections

**Header**
```
RECRUITMENT CANDIDATE RANKER
AI-Powered Candidate Screening and Ranking System
```

**Job Details Section**
- Job Title input
- Location input
- Certifications builder

**Job Description Section**
- Large text area with placeholder

**Resume Upload Section**
- File browser
- Upload status
- List of uploaded files

**Process Button**
- Large, prominent button
- Shows "🚀 Process Candidates"

**Results Section** (After Processing)
- Summary metrics
- Top candidates list
- Expandable details
- Download button

---

## 📊 Example Output

After processing, you'll see:

```
RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Candidates: 6
Top Candidates: 3
Average Score: 6.17

Top Candidates:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Jane Smith - Score: 8.68/10
   Email: jane.smith@email.com
   Phone: (555) 123-4567
   Certifications: AWS Certified ML, GCP Data Engineer
   Rationale: Excellent fit for position...

[More candidates...]

DOWNLOAD REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 Download PDF Report
```

---

## 🛑 Stopping the Application

To stop the web interface:

```bash
# Find the Streamlit process
ps aux | grep streamlit

# Kill it (replace PID with actual process ID)
kill [PID]
```

Or simply close the terminal window.

---

## 📁 Where Files Are Saved

Generated PDF reports are saved to:
```
/Users/danny/Desktop/Claude Code Test/
```

With filename format:
```
Candidate_Ranking_Report_YYYYMMDD_HHMMSS.pdf
```

---

## 🚀 Performance Tips

### For Best Experience

1. **Use Modern Browser**: Chrome, Safari, Firefox (latest versions)
2. **Stable Connection**: Even though it's local, browser needs resources
3. **Clear Cache**: If issues, try clearing browser cache
4. **One Tab**: Don't open multiple tabs with the app

### For Faster Processing

1. **Text-based PDFs**: Faster than scanned documents
2. **Smaller Files**: Compress large PDFs if possible
3. **Batch Size**: Process 5-10 resumes at a time
4. **Format**: DOCX and TXT process fastest

---

## 💡 Advanced Features

### Customization Options

The web interface can be customized by editing `app.py`:
- Change color scheme
- Modify layout
- Add custom fields
- Adjust scoring weights

### Data Export

All results can be:
- Downloaded as PDF (built-in)
- Saved to database (requires modification)
- Exported to CSV (requires modification)

---

## 📱 Mobile Access

The interface is responsive and works on mobile devices:

1. Access from phone/tablet using Network URL
2. Navigate to: `http://192.168.4.236:8501`
3. Use same workflow as desktop

**Note**: File upload may require "Share" functionality on mobile.

---

## ✅ Application Status

```
✓ Web Server Running
✓ Port 8501 Active
✓ Local Access Available
✓ Network Access Available
✓ All Features Functional
```

---

## 🎯 Next Steps

1. **Open Browser**: Navigate to http://localhost:8501
2. **Test with Samples**: Use the 6 sample resumes
3. **View Results**: See the ranking in real-time
4. **Download Report**: Get the professional PDF
5. **Use for Real**: Upload actual candidate resumes!

---

**Application is ready to use!**

Open your browser and visit: **http://localhost:8501**

Enjoy using the Recruitment Candidate Ranker! 🎉
