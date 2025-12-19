"""
Enhanced Resume Parser with OCR Support
Handles text-based PDFs, scanned PDFs, and image files
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List
import PyPDF2
import docx

# OCR support (optional - will gracefully degrade if not available)
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF_TO_IMAGE_AVAILABLE = True
except ImportError:
    PDF_TO_IMAGE_AVAILABLE = False


class ResumeParserOCR:
    """
    Enhanced resume parser with OCR support for scanned documents
    """

    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.ocr_enabled = OCR_AVAILABLE

    def parse(self, file_path: str, use_ocr: bool = True) -> Dict[str, Any]:
        """
        Parse a resume file with OCR fallback support

        Args:
            file_path: Path to resume file
            use_ocr: Whether to use OCR for scanned documents/images

        Returns:
            Dictionary with candidate information
        """
        # Read file content based on extension
        content = self._read_file(file_path, use_ocr=use_ocr)

        # If content is empty and OCR is available, it might be a scanned document
        if not content.strip() and use_ocr and self.ocr_enabled:
            print(f"  WARNING: Empty content, attempting OCR for {Path(file_path).name}")
            content = self._read_with_ocr(file_path)

        # Extract structured information
        candidate = {
            'name': self._extract_name(content),
            'email': self._extract_email(content),
            'phone': self._extract_phone(content),
            'skills': self._extract_skills(content),
            'certifications': self._extract_certifications(content),
            'experience': self._extract_experience(content),
            'education': self._extract_education(content),
            'job_titles': self._extract_job_titles(content),
            'location': self._extract_location(content),
            'years_of_experience': self._estimate_years_of_experience(content),
            'raw_text': content,
            'parsed_with_ocr': False  # Will be set to True if OCR was used
        }

        return candidate

    def _read_file(self, file_path: str, use_ocr: bool = True) -> str:
        """Read content from file based on extension"""
        file_ext = Path(file_path).suffix.lower()

        # Image files - use OCR directly
        if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            if use_ocr and self.ocr_enabled:
                print(f"  Detected image file, using OCR: {Path(file_path).name}")
                return self._read_image_with_ocr(file_path)
            else:
                raise ValueError(f"OCR not available. Cannot read image file: {file_path}")

        # Standard file formats
        if file_ext == '.pdf':
            # Try standard PDF reading first
            text = self._read_pdf(file_path)

            # If no text extracted and OCR is available, try OCR
            if not text.strip() and use_ocr and PDF_TO_IMAGE_AVAILABLE and self.ocr_enabled:
                print(f"  PDF appears to be scanned, using OCR: {Path(file_path).name}")
                text = self._read_pdf_with_ocr(file_path)

            return text

        elif file_ext in ['.docx', '.doc']:
            return self._read_docx(file_path)

        elif file_ext == '.txt':
            return self._read_txt(file_path)

        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def _read_pdf(self, file_path: str) -> str:
        """Extract text from text-based PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")

        return text

    def _read_pdf_with_ocr(self, file_path: str) -> str:
        """Extract text from scanned PDF using OCR"""
        if not PDF_TO_IMAGE_AVAILABLE or not self.ocr_enabled:
            return ""

        try:
            # Convert PDF to images
            images = convert_from_path(file_path)

            # Extract text from each page
            text = ""
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n"
                text += page_text + "\n"

            return text

        except Exception as e:
            print(f"  WARNING: OCR failed for PDF: {e}")
            return ""

    def _read_image_with_ocr(self, file_path: str) -> str:
        """Extract text from image file using OCR"""
        if not self.ocr_enabled:
            return ""

        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"  WARNING: OCR failed for image: {e}")
            return ""

    def _read_with_ocr(self, file_path: str) -> str:
        """Attempt to read file with OCR"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf' and PDF_TO_IMAGE_AVAILABLE:
            return self._read_pdf_with_ocr(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self._read_image_with_ocr(file_path)
        else:
            return ""

    def _read_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {e}")

    def _read_txt(self, file_path: str) -> str:
        """Read text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading TXT: {e}")

    # All other methods remain the same as resume_parser.py
    def _extract_name(self, content: str) -> str:
        """Extract candidate name"""
        lines = content.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50 and not '@' in line and not self.phone_pattern.search(line):
                words = line.split()
                if 2 <= len(words) <= 4 and all(re.match(r'^[A-Za-z\-\.]+$', w) for w in words):
                    return line
        return "Name Not Found"

    def _extract_email(self, content: str) -> str:
        """Extract email address"""
        match = self.email_pattern.search(content)
        return match.group(0) if match else "Email Not Found"

    def _extract_phone(self, content: str) -> str:
        """Extract phone number"""
        match = self.phone_pattern.search(content)
        return match.group(0) if match else "Phone Not Found"

    def _extract_skills(self, content: str) -> List[str]:
        """Extract technical and professional skills"""
        skills = []
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'c\\+\\+', 'c#', 'ruby',
            'go', 'rust', 'php', 'swift', 'kotlin', 'scala', 'r',
            'react', 'angular', 'vue', 'node\\.js', 'django', 'flask', 'spring',
            '\\.net', 'express', 'fastapi', 'rails', 'laravel',
            'aws', 'azure', 'gcp', 'google cloud', 'kubernetes', 'docker',
            'jenkins', 'terraform', 'ansible', 'ci/cd', 'devops',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'oracle',
            'redis', 'elasticsearch', 'cassandra', 'dynamodb',
            'machine learning', 'deep learning', 'data science', 'nlp',
            'computer vision', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'spark', 'hadoop',
            'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma',
            'git', 'jira', 'confluence', 'slack', 'tableau', 'power bi',
            'leadership', 'communication', 'teamwork', 'problem-solving',
            'project management', 'analytical', 'critical thinking'
        ]

        content_lower = content.lower()
        for skill in skill_keywords:
            if re.search(r'\b' + skill + r'\b', content_lower):
                skills.append(skill.replace('\\', '').upper() if len(skill) <= 5
                            else skill.replace('\\', '').title())

        return list(set(skills))

    def _extract_certifications(self, content: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        cert_patterns = [
            r'AWS\s+Certified\s+[\w\s]+',
            r'Google\s+Cloud\s+[\w\s]+',
            r'Microsoft\s+Certified\s+[\w\s]+',
            r'Azure\s+[\w\s]+',
            r'Cisco\s+Certified\s+[\w\s]+',
            r'CompTIA\s+[\w\s]+',
            r'PMP',
            r'Project\s+Management\s+Professional',
            r'Certified\s+[\w\s]+',
            r'CISSP',
            r'CEH',
            r'CISA',
            r'CPA',
            r'Six\s+Sigma\s+[\w\s]+',
        ]

        for pattern in cert_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            certifications.extend([m.strip() for m in matches])

        return list(set(certifications))

    def _extract_experience(self, content: str) -> List[Dict[str, str]]:
        """Extract work experience entries"""
        experiences = []
        exp_section = re.search(
            r'(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE)(.*?)(?:EDUCATION|SKILLS|CERTIFICATIONS|$)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if exp_section:
            exp_text = exp_section.group(1)
            entries = re.split(r'\n\s*\n', exp_text)
            for entry in entries[:10]:
                if len(entry.strip()) > 20:
                    experiences.append({'raw_entry': entry.strip()})

        return experiences

    def _extract_education(self, content: str) -> List[str]:
        """Extract education information"""
        education = []
        degree_patterns = [
            r'Bachelor(?:\'s)?\s+(?:of\s+)?(?:Science|Arts|Engineering)\s+in\s+[\w\s]+',
            r'Master(?:\'s)?\s+(?:of\s+)?(?:Science|Arts|Engineering)\s+in\s+[\w\s]+',
            r'PhD\s+in\s+[\w\s]+',
            r'B\.S\.\s+in\s+[\w\s]+',
            r'M\.S\.\s+in\s+[\w\s]+',
            r'MBA',
        ]

        for pattern in degree_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            education.extend([m.strip() for m in matches])

        return list(set(education))

    def _extract_job_titles(self, content: str) -> List[str]:
        """Extract previous job titles"""
        job_titles = []
        title_patterns = [
            r'(?:Senior|Sr\.|Junior|Jr\.)?\s*(?:Software|Data|Machine Learning|ML|AI)\s+(?:Engineer|Scientist|Developer|Analyst)',
            r'(?:Lead|Principal|Staff)\s+(?:Engineer|Developer|Scientist)',
            r'(?:Engineering|Product|Project)\s+Manager',
            r'DevOps\s+Engineer',
            r'Full\s+Stack\s+Developer',
            r'Frontend\s+Developer',
            r'Backend\s+Developer',
            r'Data\s+Analyst',
            r'Business\s+Analyst',
            r'Consultant',
            r'Architect',
        ]

        for pattern in title_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            job_titles.extend([m.strip() for m in matches])

        return list(set(job_titles))

    def _extract_location(self, content: str) -> str:
        """Extract candidate location"""
        location_pattern = r'(?:Location|Address|Based in):\s*([\w\s,]+(?:,\s*[A-Z]{2})?)'
        match = re.search(location_pattern, content, re.IGNORECASE)

        if match:
            return match.group(1).strip()

        header = content[:500]
        city_state = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', header)

        if city_state:
            return city_state.group(1)

        return "Location Not Specified"

    def _estimate_years_of_experience(self, content: str) -> int:
        """Estimate years of experience from dates"""
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', content)

        if years:
            years_int = [int(y) for y in years]
            return max(years_int) - min(years_int)

        exp_match = re.search(r'(\d+)\+?\s*years?\s+of\s+experience', content, re.IGNORECASE)
        if exp_match:
            return int(exp_match.group(1))

        return 0


def check_ocr_dependencies():
    """Check if OCR dependencies are installed"""
    print("Checking OCR dependencies...")
    print()

    dependencies = {
        'PIL (Pillow)': OCR_AVAILABLE,
        'pytesseract': OCR_AVAILABLE,
        'pdf2image': PDF_TO_IMAGE_AVAILABLE
    }

    all_available = all(dependencies.values())

    for dep, available in dependencies.items():
        status = "✓ Installed" if available else "✗ Not installed"
        print(f"  {status}: {dep}")

    print()

    if not all_available:
        print("To enable OCR support, install:")
        print("  pip install Pillow pytesseract pdf2image")
        print()
        print("Also install Tesseract OCR engine:")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print()

    return all_available


if __name__ == "__main__":
    check_ocr_dependencies()
