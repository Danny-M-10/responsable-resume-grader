# Company Logo Setup Guide

## Overview

Your Candidate Ranking Application now supports adding your company logo to all generated PDF reports. The logo appears in the header of every PDF document.

## Quick Start

### Option 1: Using the Web Interface (Streamlit)

1. Launch the application:
   ```bash
   source venv/bin/activate
   streamlit run app.py
   ```

2. In the web interface, you'll see a new section: **"Company Logo (Optional)"**

3. Click **"Upload Company Logo"**

4. Select your logo file (PNG, JPG, or JPEG)

5. You'll see a preview of your logo

6. Continue with the rest of the form and process candidates

7. Your PDF report will include the logo in the header!

### Option 2: Using Python Code

```python
from candidate_ranker import CandidateRankerApp

# Initialize with logo path
app = CandidateRankerApp(logo_path="path/to/your/logo.png")

# Run processing as usual
pdf_path = app.run(
    job_title="Data Scientist",
    certifications=[{"name": "AWS Certified", "category": "must-have"}],
    location="New York, NY",
    job_description="...",
    resume_files=["resume1.pdf", "resume2.pdf"]
)
```

## Logo Requirements

### Supported Formats
- PNG (recommended - supports transparency)
- JPG/JPEG
- Other formats supported by ReportLab

### Recommended Specifications

**Size:**
- Maximum width: 2.5 inches (in PDF)
- Maximum height: 1 inch (in PDF)
- Aspect ratio is automatically preserved

**Resolution:**
- Minimum: 150 DPI
- Recommended: 300 DPI for best quality
- File size: Under 1 MB (smaller is better)

**Dimensions (pixels):**
- Horizontal logo: 750 x 300 pixels
- Square logo: 300 x 300 pixels
- Vertical logo: 300 x 450 pixels

**Background:**
- Transparent background (PNG) works best
- White background is second best
- Avoid complex backgrounds

### Design Tips

1. **Keep it simple**: Logos with clean lines look best in PDFs
2. **High contrast**: Dark logo on light background (or vice versa)
3. **No tiny text**: Small text may not be readable at reduced size
4. **Test it**: Generate a sample PDF to see how it looks

## Where to Put Your Logo File

### Recommended Locations

1. **Project root directory:**
   ```
   /Users/danny/Documents/Cursor/Projects/crossroads_Candidate_Ranking_Application/
   └── company_logo.png
   ```

2. **Dedicated logos folder:**
   ```
   /Users/danny/Documents/Cursor/Projects/crossroads_Candidate_Ranking_Application/
   └── sample_logos/
       └── your_company_logo.png
   ```

3. **User home directory:**
   ```
   ~/Documents/company_logo.png
   ```

## Examples

### Example 1: Default Logo Setup

Create a logo file in the project root:
```bash
# Place your logo here:
cp /path/to/your/logo.png company_logo.png
```

Then use it in code:
```python
app = CandidateRankerApp(logo_path="company_logo.png")
```

### Example 2: Multiple Companies

If you work with multiple companies, organize logos by company:
```
sample_logos/
├── company_a_logo.png
├── company_b_logo.png
└── company_c_logo.png
```

Then specify which one to use:
```python
app = CandidateRankerApp(logo_path="sample_logos/company_a_logo.png")
```

### Example 3: Environment-Based Logo

Set logo path based on environment:
```python
import os

# Production uses real logo
if os.getenv('ENV') == 'production':
    logo_path = "logos/production_logo.png"
else:
    logo_path = None  # No logo in development

app = CandidateRankerApp(logo_path=logo_path)
```

## What Happens Without a Logo?

If no logo is provided:
- PDF still generates successfully
- Header shows **"ResponsAble Safety Staffing"** as text
- Everything else works normally

This is the **default behavior** if:
- No logo file is uploaded (web interface)
- `logo_path` is `None` (Python code)
- Logo file path doesn't exist
- Logo file is corrupted/unreadable

## Troubleshooting

### Logo Not Appearing

**Check 1: File exists**
```python
import os
print(os.path.exists("path/to/logo.png"))  # Should print True
```

**Check 2: File is readable**
```python
from PIL import Image
img = Image.open("path/to/logo.png")
print(f"Logo size: {img.size}")  # Should print dimensions
```

**Check 3: Path is correct**
- Use absolute paths for reliability: `/full/path/to/logo.png`
- Or relative to working directory: `./logo.png`

### Logo Looks Distorted

**Problem**: Logo is stretched or squished
**Solution**: Check aspect ratio. The PDF maintains aspect ratio, so your source image should have the right proportions.

**Problem**: Logo is blurry
**Solution**: Use a higher resolution image (300 DPI recommended)

### Logo is Too Large/Small

The logo is constrained to:
- Max width: 2.5 inches
- Max height: 1 inch

If your logo needs different sizing, edit `pdf_generator.py` line 174:
```python
logo = Image(self.logo_path, width=3*inch, height=1.5*inch)  # Custom size
```

### File Format Not Supported

If you get an error about unsupported format:
1. Convert your logo to PNG using an online converter
2. Or use this Python script:

```python
from PIL import Image

# Convert any image to PNG
img = Image.open("logo.jpg")
img.save("logo.png", "PNG")
```

## Advanced: Customizing Logo Placement

To change logo position or style, edit [pdf_generator.py](pdf_generator.py):

### Center the Logo
```python
# Line 175
logo.hAlign = 'CENTER'  # Instead of 'LEFT'
```

### Right-Align the Logo
```python
# Line 175
logo.hAlign = 'RIGHT'
```

### Resize the Logo
```python
# Line 174
logo = Image(self.logo_path, width=3*inch, height=1.2*inch)
```

### Add Border Around Logo
```python
# After line 178, add:
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

table = Table([[logo]], colWidths=[3*inch])
table.setStyle(TableStyle([
    ('BOX', (0,0), (-1,-1), 1, colors.black),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
]))
return table
```

## Example Logo Sources

If you need a logo created:
- **Canva**: [canva.com](https://canva.com) - Free logo maker
- **LogoMakr**: [logomakr.com](https://logomakr.com) - Simple online tool
- **Looka**: [looka.com](https://looka.com) - AI-powered logo generator
- **Hire a designer**: Fiverr, Upwork, 99designs

## Testing Your Logo

Generate a test PDF to see how your logo looks:

```bash
source venv/bin/activate
python example_usage.py
```

Check the generated PDF in your project directory. The logo should appear in the header of every page.

## Files Modified for Logo Support

The following files were updated to support logos:
- [pdf_generator.py](pdf_generator.py) - Logo rendering in PDF header
- [candidate_ranker.py](candidate_ranker.py) - Pass logo path to PDF generator
- [app.py](app.py) - Web interface for logo upload

## Summary

✅ Upload logos via web interface
✅ Pass logo path in Python code
✅ Automatic aspect ratio preservation
✅ Fallback to text if no logo provided
✅ Supports PNG, JPG, JPEG formats
✅ Easy customization options

---

**Your logo will now appear on every PDF report you generate!**
