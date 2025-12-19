"""
Job Description Parser Module
Automatically extracts job requirements from job description files
"""

import re
from typing import Dict, List, Tuple, Any
from pathlib import Path
import PyPDF2
import docx


class JobDescriptionParser:
    """
    Automatically extracts structured job information from job description files
    Supports PDF, DOCX, and TXT formats
    """

    def __init__(self):
        self.certification_keywords = {
            'must-have': [
                'required', 'must have', 'must-have', 'mandatory', 'essential',
                'critical', 'necessary', 'needs', 'minimum requirement'
            ],
            'bonus': [
                'preferred', 'bonus', 'nice to have', 'nice-to-have', 'plus',
                'desirable', 'optional', 'would be great', 'advantageous'
            ]
        }

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse job description file and extract all requirements

        Args:
            file_path: Path to job description file (PDF, DOCX, or TXT)

        Returns:
            Dictionary with structured job information
        """
        # Read file content
        content = self._read_file(file_path)

        # Extract all components
        job_data = {
            'job_title': self._extract_job_title(content),
            'location': self._extract_location(content),
            'certifications': self._extract_certifications(content),
            'full_description': content,
            'raw_requirements': self._extract_requirements_sections(content),
            'experience_requirements': self._extract_experience(content),
            'salary_range': self._extract_salary(content)
        }

        return job_data

    def _read_file(self, file_path: str) -> str:
        """Read content from file based on extension"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            return self._read_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self._read_docx(file_path)
        elif file_ext == '.txt':
            return self._read_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def _read_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")
        return text

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

    def _extract_job_title(self, content: str) -> str:
        """Extract job title from content with improved contextual detection"""
        lines = content.strip().split('\n')

        # Step 1: Try explicit title markers
        explicit_patterns = [
            r'(?:Job Title|Position|Role|Title):\s*([^\n]+)',
            r'(?:Job Title|Position|Role|Title)\s*[:\-]\s*([^\n]+)',
        ]

        for pattern in explicit_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if len(title) < 100 and not self._is_marketing_text(title):
                    return title

        # Step 2: Look for contextual job title mentions
        contextual_patterns = [
            # "experience as a [Job Title]"
            r'(?:experience as|position for|role as|join (?:us )?as)\s+(?:a|an)?\s*([A-Z][^.,!?\n]{5,80}?)(?:\s+(?:who|with|to|or|,)|\.|!)',
            # "are you an experienced [Job Title]"
            r'(?:are you an?|we want to hear from you if you are)\s+(?:experienced)?\s*([A-Z][^.,!?\n]{10,80}?)(?:\s+(?:professional|with|who|,))',
            # "looking for [Job Title]" or "seeking [Job Title]"
            r'(?:looking for|seeking|hiring)\s+(?:a|an)?\s*(?:experienced)?\s*([A-Z][^.,!?\n]{5,80}?)(?:\s+(?:who|with|to|or|,)|\.|!)',
            # "[Job Title] with X years experience" or "[Job Title] minimum"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+with\s+(?:a\s+)?minimum',
        ]

        for pattern in contextual_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                # Clean up and validate
                if self._is_valid_job_title(potential_title):
                    return potential_title

        # Step 3: Enhanced job title patterns (all industries)
        job_title_pattern = (
            r'\b((?:Senior|Sr\.|Junior|Jr\.|Lead|Principal|Staff|Chief|Assistant|Associate)\s+)?'
            r'(?:'
            # Tech roles
            r'(?:Software|Data|Machine Learning|ML|AI|Product|Project|Program|DevOps|Full Stack|Frontend|Backend|Quality Assurance|QA|Cloud|Security|Systems)'
            r'\s+(?:Engineer|Scientist|Developer|Analyst|Manager|Architect|Director|Specialist|Consultant|Administrator)|'
            # Safety/Construction roles
            r'(?:Safety|Construction|Electrical|Utility|Distribution|Power|Field|Site|Project)'
            r'\s+(?:Specialist|Manager|Engineer|Technician|Coordinator|Supervisor|Director|Professional|Inspector)|'
            # Healthcare roles
            r'(?:Registered|Licensed|Certified)?\s*(?:Nurse|Nursing|Medical|Clinical|Healthcare)'
            r'\s*(?:Professional|Specialist|Manager|Director|Coordinator)?|'
            # Finance roles
            r'(?:Financial|Accounting|Investment|Tax)\s+(?:Analyst|Manager|Director|Specialist|Consultant)|'
            # Generic professional roles
            r'(?:Business|Operations|Human Resources|HR|Marketing|Sales)\s+(?:Analyst|Manager|Director|Specialist|Coordinator)'
            r')\b'
        )

        # Step 4: Try first 20 lines for job title patterns
        for line in lines[:20]:
            if self._is_marketing_text(line):
                continue
            match = re.search(job_title_pattern, line, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        # Step 5: Try all-caps titles in first few lines (with better filtering)
        for line in lines[:10]:
            line = line.strip()
            if re.match(r'^[A-Z][A-Z\s\-&/]+$', line) and 5 < len(line) < 100:
                if not self._is_marketing_text(line) and not any(word in line.upper() for word in ['INC', 'LLC', 'CORP', 'LTD', 'COMPANY']):
                    return line

        return "Job Title Not Found"

    def _is_marketing_text(self, text: str) -> bool:
        """Check if text appears to be marketing copy rather than a job title"""
        if not text:
            return False

        text_lower = text.lower()

        # Marketing phrases that indicate this isn't a job title
        marketing_indicators = [
            'take your career',
            'join our team',
            'we are looking',
            'we are seeking',
            'we want to hear',
            'come work',
            'build your career',
            'grow with',
            'exciting opportunity',
            'are you an experienced',
            'do you have',
            'with a passion for',
            'ResponsAble', 'Staffing',  # Company name
        ]

        for indicator in marketing_indicators:
            if indicator.lower() in text_lower:
                return True

        # If text is too long, it's probably not a job title
        if len(text) > 100:
            return True

        return False

    def _is_valid_job_title(self, text: str) -> bool:
        """Validate if extracted text looks like a valid job title"""
        if not text or len(text) < 5 or len(text) > 100:
            return False

        # Skip if it's marketing text
        if self._is_marketing_text(text):
            return False

        # Should contain at least one job-related keyword
        job_keywords = [
            # General roles
            'manager', 'specialist', 'engineer', 'director', 'coordinator',
            'analyst', 'developer', 'scientist', 'technician', 'consultant',
            'supervisor', 'administrator', 'professional', 'inspector', 'designer',
            'architect', 'lead', 'senior', 'junior', 'principal', 'staff',
            # Safety & Construction
            'safety', 'construction', 'electrical', 'utility', 'distribution',
            'lineman', 'electrician', 'foreman', 'tradesman', 'mechanic',
            # Healthcare
            'nurse', 'medical', 'clinical', 'physician', 'therapist', 'practitioner',
            # Finance & Accounting
            'financial', 'accountant', 'auditor', 'controller', 'treasurer',
            # IT & Tech
            'programmer', 'administrator', 'architect', 'devops', 'sysadmin',
            # Other
            'officer', 'assistant', 'associate', 'representative', 'agent'
        ]

        text_lower = text.lower()
        has_job_keyword = any(keyword in text_lower for keyword in job_keywords)

        return has_job_keyword

    def _extract_location(self, content: str) -> str:
        """Extract job location"""
        # First, try explicit location markers
        location_marker_pattern = r'(?:Location|Office Location|Work Location|Based in|City):\s*([^\n]+)'
        marker_match = re.search(location_marker_pattern, content, re.IGNORECASE)

        if marker_match:
            potential_location = marker_match.group(1).strip()
            # Validate if it's actually a location
            if self._is_valid_location(potential_location):
                return potential_location

        # Try to find City, State format anywhere
        city_state_patterns = [
            # City, State (e.g., New York, NY)
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})\b',
            # City, State, Country
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2},\s*[A-Z][a-z]+)\b'
        ]

        for pattern in city_state_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if self._is_valid_location(match):
                    return match

        # Check for remote work indicators
        remote_patterns = [
            r'\b(Remote|Work from Home|WFH|Fully Remote|Remote-First|Remote Work)\b',
            r'\b(100% Remote|Remote Position|Remote Location)\b'
        ]

        for pattern in remote_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return "Remote"

        return "Location Not Specified"

    def _is_valid_location(self, text: str) -> bool:
        """
        Validate if text looks like a real location

        Args:
            text: Potential location string

        Returns:
            True if it looks like a valid location
        """
        if not text or len(text) < 2:
            return False

        # Too long to be a location
        if len(text) > 100:
            return False

        # Contains common non-location words/phrases
        non_location_indicators = [
            'we are', 'we\'re', 'looking for', 'seeking', 'hiring',
            'company', 'team', 'department', 'join', 'career',
            'opportunity', 'position', 'role', 'job', 'work with',
            'staffing', 'recruitment', 'at ', 'the ', 'our '
        ]

        text_lower = text.lower()
        for indicator in non_location_indicators:
            if indicator in text_lower:
                return False

        # Valid location patterns
        valid_patterns = [
            # City, State (New York, NY)
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}$',
            # Just state abbreviation
            r'^[A-Z]{2}$',
            # Remote
            r'^Remote$',
            # City name (at least 2 words or one capitalized word)
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',
            # Multiple cities
            r'[A-Z][a-z]+,\s*[A-Z]{2}(?:\s+(?:or|and)\s+[A-Z][a-z]+,\s*[A-Z]{2})'
        ]

        for pattern in valid_patterns:
            if re.match(pattern, text.strip()):
                return True

        return False

    def _is_valid_certification(self, text: str) -> bool:
        """
        Validate if text looks like an actual certification, not a benefit or other detail

        Args:
            text: Potential certification string

        Returns:
            True if it looks like a valid certification
        """
        if not text or len(text) < 2:
            return False

        text_lower = text.lower()

        # Filter out obvious non-certifications (benefits, compensation, work details)
        non_cert_indicators = [
            # Compensation and benefits
            'compensation', 'salary', 'pay', 'hour', 'hourly', 'weekly', 'annual',
            'offer', 'benefit', 'insurance', 'health', '401k', 'pto', 'vacation',
            'per hour', 'per week', 'per year', 'an hour', 'a week', 'a year',
            # Work schedule
            'hours', 'schedule', 'shift', 'week', 'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday',
            # Benefits
            'lodging', 'housing', 'food', 'meal', 'travel', 'mileage', 'per diem',
            'reimbursement', 'allowance', 'bonus', 'relocation',
            # Work details
            'mobilization', 'demo', 'demobilization', 'paid', 'unpaid',
            # Common phrases in job descriptions that aren't certs
            'what we offer', 'we offer', 'includes', 'provide', 'receive',
        ]

        for indicator in non_cert_indicators:
            if indicator in text_lower:
                return False

        # Check if it contains numbers that look like compensation (e.g., "42 to 47.50")
        if re.search(r'\d+\s+to\s+\d+|\$\d+|\d+\.\d+', text):
            return False

        # Must have at least one indicator that it's a certification
        cert_indicators = [
            # Has common cert acronyms (2-5 capital letters)
            r'\b[A-Z]{2,5}\b',
            # Has cert-related keywords
            r'certified|certification|license|licensed',
            # Has OSHA followed by number
            r'OSHA\s*\d+',
            # Professional designations
            r'professional|specialist|technician|engineer',
        ]

        has_cert_indicator = any(re.search(pattern, text, re.IGNORECASE) for pattern in cert_indicators)

        return has_cert_indicator

    def _extract_certifications(self, content: str) -> List[Dict[str, str]]:
        """
        Extract certifications and categorize as must-have or bonus

        Returns:
            List of dicts with 'name' and 'category' keys
        """
        certifications = []

        # First, look for explicit "Certifications:" section
        cert_section_pattern = r'(?:Certifications?|Required Certifications?|Certification Requirements?):\s*([^\n]+(?:\n(?!\n)[^\n]+)*)'
        cert_section_match = re.search(cert_section_pattern, content, re.IGNORECASE | re.MULTILINE)

        if cert_section_match:
            cert_text = cert_section_match.group(1)

            # Stop at the next section header (What We Offer, Benefits, Additional Requirements, etc.)
            next_section_pattern = r'(?:What We Offer|Benefits|Compensation|Additional Requirements|Requirements|Qualifications|Responsibilities|Duties):'
            next_section_match = re.search(next_section_pattern, cert_text, re.IGNORECASE)
            if next_section_match:
                # Only take text before the next section
                cert_text = cert_text[:next_section_match.start()]

            # Extract individual certifications from the section
            # Look for comma-separated or "or" separated items
            cert_items = re.split(r',|\bor\b', cert_text)
            for item in cert_items:
                item = item.strip()
                # Remove common prefixes/suffixes
                item = re.sub(r'(?:equivalent|certifications?|based on.*|minimum of|at least)\s*', '', item, flags=re.IGNORECASE)
                item = item.strip('.,;: ')

                if item and len(item) > 1 and len(item) < 100:
                    # Validate it's actually a certification, not a benefit or other text
                    if self._is_valid_certification(item):
                        category = self._categorize_certification(item, content)
                        certifications.append({
                            'name': item,
                            'category': category
                        })

        # Common certification patterns (tech and general)
        cert_patterns = [
            # Tech certifications
            r'AWS\s+Certified\s+[\w\s\-]+',
            r'Google\s+Cloud\s+(?:Professional\s+)?[\w\s\-]+(?:Engineer|Architect)',
            r'Microsoft\s+Certified[\w\s:\-]+',
            r'Azure\s+[\w\s\-]+(?:Associate|Expert)',
            r'Cisco\s+Certified\s+[\w\s\-]+',
            r'CompTIA\s+[\w\s\+]+',
            r'PMP',
            r'Project\s+Management\s+Professional',
            r'Certified\s+[\w\s\-]+(?:Engineer|Architect|Professional|Specialist)',
            r'CISSP',
            r'CEH',
            r'CISA',
            r'CISM',
            r'Six\s+Sigma\s+[\w\s]+',
            r'Scrum\s+Master',
            r'Professional\s+Scrum\s+Master',
            r'SAFe\s+[\w\s]+',
            r'Databricks\s+Certified\s+[\w\s]+',
            r'Salesforce\s+Certified\s+[\w\s]+',
            r'Oracle\s+Certified\s+[\w\s]+',

            # OSHA certifications
            r'OSHA\s+\d+',
            r'OSHA[\s\-]?(?:10|30|500|501|510|511)',

            # Safety certifications (common acronyms)
            r'\bCOSS\b',
            r'\bCHST\b',
            r'\bASP\b',
            r'\bCSP\b',
            r'\bCUSP\b',
            r'\bOHST\b',
            r'\bCIH\b',
            r'\bCET\b',
            r'\bCEAS\b',

            # Construction/Safety full names
            r'Certified\s+(?:Occupational\s+)?Safety\s+(?:Professional|Specialist|Technician)',
            r'Construction\s+Health\s+and\s+Safety\s+Technician',
            r'Associate\s+Safety\s+Professional',
            r'Certified\s+Utility\s+Safety\s+(?:Professional|Administrator)',
            r'Certified\s+Industrial\s+Hygienist',

            # Medical/Healthcare
            r'\bRN\b',
            r'\bLPN\b',
            r'\bCNA\b',
            r'\bBLS\b',
            r'\bACLS\b',
            r'\bPALS\b',
            r'Registered\s+Nurse',
            r'Licensed\s+Practical\s+Nurse',

            # Other professional certifications
            r'\bCPA\b',
            r'Certified\s+Public\s+Accountant',
            r'\bPE\b(?:\s+License)?',
            r'Professional\s+Engineer',
            r'\bCFA\b',
            r'Chartered\s+Financial\s+Analyst'
        ]

        # Find all certifications
        found_certs = set()
        for pattern in cert_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Clean up
                cert_name = re.sub(r'\s+', ' ', match.strip())
                # Don't add if already found in section parsing
                if cert_name.upper() not in [c['name'].upper() for c in certifications]:
                    found_certs.add(cert_name)

        # Categorize each certification
        for cert_name in found_certs:
            category = self._categorize_certification(cert_name, content)
            certifications.append({
                'name': cert_name,
                'category': category
            })

        return certifications

    def _categorize_certification(self, cert_name: str, content: str) -> str:
        """
        Determine if certification is must-have or bonus based on context

        Args:
            cert_name: The certification name
            content: Full job description content

        Returns:
            'must-have' or 'bonus'
        """
        # Find the certification in context
        # Look for surrounding text (200 chars before and after)
        cert_pattern = re.escape(cert_name)
        matches = list(re.finditer(cert_pattern, content, re.IGNORECASE))

        if not matches:
            return 'must-have'  # Default to must-have if can't find (be conservative)

        for match in matches:
            start = max(0, match.start() - 300)
            end = min(len(content), match.end() + 300)
            context = content[start:end].lower()

            # Check for must-have indicators
            for keyword in self.certification_keywords['must-have']:
                if keyword in context:
                    return 'must-have'

            # Check if it's in a "Certifications:" section (usually required)
            if 'certification' in context and 'required' not in context and 'preferred' not in context:
                # If in cert section but no explicit preferred, assume must-have
                if re.search(r'certifications?:', context):
                    return 'must-have'

        # Check entire sections
        # If cert appears in "Required" section, it's must-have
        required_section = self._extract_section(content, ['required', 'must have', 'essential', 'what we\'re looking for'])
        if required_section and cert_name.lower() in required_section.lower():
            return 'must-have'

        # Check if in preferred/bonus section
        preferred_section = self._extract_section(content, ['preferred', 'nice to have', 'bonus', 'plus'])
        if preferred_section and cert_name.lower() in preferred_section.lower():
            return 'bonus'

        # If found in "Certifications:" section specifically, default to must-have
        cert_section = re.search(r'Certifications?:\s*[^\n]*' + cert_pattern, content, re.IGNORECASE)
        if cert_section:
            return 'must-have'

        # Default to must-have (conservative approach)
        return 'must-have'

    def _extract_requirements_sections(self, content: str) -> Dict[str, str]:
        """Extract requirements and preferred sections"""
        sections = {}

        # Required section
        required_section = self._extract_section(
            content,
            ['required qualifications', 'required skills', 'requirements',
             'must have', 'essential qualifications', 'minimum qualifications']
        )
        if required_section:
            sections['required'] = required_section

        # Preferred section
        preferred_section = self._extract_section(
            content,
            ['preferred qualifications', 'preferred skills', 'nice to have',
             'bonus', 'preferred', 'plus', 'desired qualifications']
        )
        if preferred_section:
            sections['preferred'] = preferred_section

        # Responsibilities section
        responsibilities = self._extract_section(
            content,
            ['responsibilities', 'duties', 'what you\'ll do', 'role responsibilities',
             'key responsibilities']
        )
        if responsibilities:
            sections['responsibilities'] = responsibilities

        return sections

    def _extract_section(self, content: str, headers: List[str]) -> str:
        """Extract content under specific section headers"""
        for header in headers:
            # Pattern to match section header and capture content until next section
            pattern = rf'(?:^|\n)[\s\*\-]*{re.escape(header)}[\s\*\-:]*\n(.*?)(?=\n[\s\*\-]*(?:[A-Z][A-Za-z\s]+:|\n\n)|$)'

            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                if len(section_content) > 20:  # Meaningful content
                    return section_content

        return ""

    def _extract_experience(self, content: str) -> str:
        """Extract experience requirements"""
        # Patterns for experience
        exp_patterns = [
            r'(\d+\+?)\s*(?:\-\s*\d+)?\s*years?\s+(?:of\s+)?(?:experience|exp)',
            r'(?:minimum|at least|minimum of)\s+(\d+)\s+years?',
            r'(\d+\+?)\s*yrs?\s+(?:experience|exp)',
        ]

        for pattern in exp_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)

        # Check for experience level keywords
        if re.search(r'\b(?:senior|sr\.|experienced)\b', content, re.IGNORECASE):
            return "Senior level (5+ years)"
        elif re.search(r'\b(?:junior|jr\.|entry|entry-level)\b', content, re.IGNORECASE):
            return "Junior level (0-2 years)"
        else:
            return "Mid level (2-5 years)"

    def _extract_salary(self, content: str) -> str:
        """Extract salary information if present"""
        # Salary patterns
        salary_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\s*-\s*\$?\s*\d{1,3}(?:,\d{3})*)?(?:\s*(?:per year|annually|/year|/yr))?',
            r'\d{1,3}[kK]\s*-\s*\d{1,3}[kK]',
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)

        return "Not specified"


def parse_job_description_file(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a job description file

    Args:
        file_path: Path to job description file

    Returns:
        Structured job data dictionary
    """
    parser = JobDescriptionParser()
    return parser.parse(file_path)


if __name__ == "__main__":
    # Test the parser
    print("Job Description Parser - Test Mode")
    print()
    print("This module automatically extracts job requirements from files.")
    print("Supported formats: PDF, DOCX, TXT")
    print()
    print("Usage:")
    print("  from job_description_parser import parse_job_description_file")
    print("  job_data = parse_job_description_file('job_description.pdf')")
    print()
