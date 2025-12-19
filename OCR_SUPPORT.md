# OCR Support for Scanned Resumes and Images

## Overview

The application now includes optional OCR (Optical Character Recognition) support to handle:
- **Scanned PDF documents** (image-based PDFs)
- **Image files** (JPG, PNG, TIFF, BMP)
- **Photos of resumes**

## Supported File Types

### Without OCR (Base Installation)
- Text-based PDF (.pdf)
- Word documents (.docx)
- Plain text (.txt)

### With OCR (Enhanced Installation)
All of the above, plus:
- Scanned PDF documents
- JPEG images (.jpg, .jpeg)
- PNG images (.png)
- TIFF images (.tiff)
- BMP images (.bmp)

## Installation

### Step 1: Install Python Packages

```bash
pip install -r requirements_ocr.txt
```

Or install OCR packages separately:

```bash
pip install Pillow pytesseract pdf2image
```

### Step 2: Install Tesseract OCR Engine

Tesseract is an external OCR engine required for text extraction.

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to your PATH

**Verify Installation:**
```bash
tesseract --version
```

You should see version information if installed correctly.

## Usage

### Using the Enhanced Parser

To use OCR support, import the OCR-enabled parser:

```python
from resume_parser_ocr import ResumeParserOCR

# Create parser instance
parser = ResumeParserOCR()

# Parse any supported file type
candidate_data = parser.parse("scanned_resume.pdf")
```

### Updating Existing Application

To enable OCR in the main application, modify `candidate_ranker.py`:

```python
# Change this line:
from resume_parser import ResumeParser

# To this:
from resume_parser_ocr import ResumeParserOCR as ResumeParser
```

## How It Works

### Automatic Detection

The parser automatically detects file types and applies appropriate handling:

1. **Image files (.jpg, .png, etc.)**
   - Directly applies OCR

2. **PDF files**
   - First attempts text extraction (fast)
   - If no text found, assumes scanned document
   - Converts to images and applies OCR

3. **Text-based files (.docx, .txt)**
   - Uses standard text extraction (no OCR needed)

### Graceful Degradation

If OCR dependencies are not installed:
- Text-based PDFs, DOCX, and TXT still work normally
- Image files will show an error message
- Scanned PDFs will extract empty text (with warning)

## Performance Considerations

### Processing Times

| File Type | Size | Processing Time |
|-----------|------|----------------|
| Text PDF | 1 page | < 1 second |
| Scanned PDF | 1 page | 3-5 seconds |
| Image (JPG) | Standard quality | 2-4 seconds |
| Multi-page scanned PDF | 5 pages | 15-25 seconds |

### Quality Factors

OCR accuracy depends on:
- **Image quality** - Higher resolution = better results
- **Text clarity** - Clear, printed text works best
- **Layout** - Standard resume layouts perform better
- **Language** - English text has highest accuracy

## Best Practices

### For Best OCR Results

1. **Image Quality**
   - Use 300 DPI or higher
   - Ensure good lighting (if photographing)
   - Avoid skewed or rotated images

2. **File Format**
   - PDF preferred over images
   - PNG better than JPG for text
   - Avoid heavily compressed images

3. **Document Quality**
   - Clean, printed resumes work best
   - Avoid handwritten notes
   - Remove background patterns

### Recommendations

1. **First Choice**: Request text-based PDFs or DOCX
2. **Second Choice**: High-quality scanned PDFs
3. **Last Resort**: Phone photos (ensure good lighting and focus)

## Troubleshooting

### OCR Not Working

**Problem**: Error "OCR not available"

**Solutions**:
- Verify Tesseract is installed: `tesseract --version`
- Install Python packages: `pip install Pillow pytesseract pdf2image`
- On macOS, ensure Tesseract is in PATH

**Problem**: "pytesseract.TesseractNotFoundError"

**Solutions**:
- Install Tesseract OCR engine (see installation above)
- Add Tesseract to system PATH
- On Windows, specify path manually:
  ```python
  import pytesseract
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### Poor OCR Quality

**Problem**: Extracted text is garbled or incomplete

**Solutions**:
- Check image quality (increase resolution)
- Ensure proper lighting and focus
- Remove backgrounds or watermarks
- Pre-process image (contrast, brightness)
- Request original document instead

### Slow Performance

**Problem**: OCR takes too long

**Solutions**:
- Reduce image resolution (balance with quality)
- Process fewer pages at once
- Use text-based PDFs when possible
- Consider cloud OCR services for large batches

## Advanced Configuration

### Custom Tesseract Path

```python
from resume_parser_ocr import ResumeParserOCR
import pytesseract

# Set custom Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

parser = ResumeParserOCR()
```

### OCR Language Configuration

```python
import pytesseract

# Configure for multiple languages
# Example: English + Spanish
custom_config = r'--oem 3 --psm 6 -l eng+spa'

# This would require modifications to resume_parser_ocr.py
# to pass custom config to pytesseract
```

### Disable OCR

To force text-only parsing (skip OCR even if available):

```python
parser = ResumeParserOCR()
candidate_data = parser.parse("resume.pdf", use_ocr=False)
```

## Checking OCR Status

Run the parser module directly to check OCR availability:

```bash
python resume_parser_ocr.py
```

Output will show:
```
Checking OCR dependencies...

  ✓ Installed: PIL (Pillow)
  ✓ Installed: pytesseract
  ✓ Installed: pdf2image
```

Or if missing:
```
Checking OCR dependencies...

  ✗ Not installed: PIL (Pillow)
  ✗ Not installed: pytesseract
  ✗ Not installed: pdf2image

To enable OCR support, install:
  pip install Pillow pytesseract pdf2image
...
```

## Cost-Benefit Analysis

### When to Use OCR

**Benefits:**
- Accept wider range of file formats
- Process scanned documents
- Handle phone photos of resumes
- More flexible for users

**Costs:**
- Slower processing (3-5x longer)
- Additional dependencies
- Lower accuracy than text-based
- Requires system OCR engine

### When to Skip OCR

For production systems with:
- High volume processing
- Strict accuracy requirements
- Performance constraints
- Controlled file submission

Consider requiring text-based files only.

## Production Deployment

### Docker Configuration

When deploying with Docker, include Tesseract:

```dockerfile
FROM python:3.9

# Install Tesseract
RUN apt-get update && \
    apt-get install -y tesseract-ocr && \
    apt-get clean

# Install Python packages
COPY requirements_ocr.txt .
RUN pip install -r requirements_ocr.txt

# Copy application
COPY . /app
WORKDIR /app
```

### Cloud Alternatives

For large-scale OCR, consider:
- AWS Textract
- Google Cloud Vision API
- Azure Computer Vision
- Adobe PDF Services API

These offer:
- Better accuracy
- Higher performance
- Scalability
- No local dependencies

## Summary

OCR support is **optional** and enhances the application to handle:
- Scanned PDF documents
- Image files (JPG, PNG, etc.)
- Photos of resumes

**Without OCR**: Text-based PDFs, DOCX, and TXT work perfectly

**With OCR**: All file types supported, with automatic detection and fallback

Choose based on your use case and accuracy vs. flexibility needs.

---

**Recommendation**: Start with basic text-based support. Add OCR only if users frequently submit scanned documents or images.
