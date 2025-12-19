"""
Resume Parser Module
Extracts structured information from resume files (PDF, DOCX, TXT)
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List
import PyPDF2
import docx


class ResumeParser:
    """Parses resumes and extracts structured candidate information"""

    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a resume file and extract structured information

        Args:
            file_path: Path to resume file

        Returns:
            Dictionary with candidate information
        """
        # Read file content based on extension
        content = self._read_file(file_path)

        # Extract structured information
        candidate = {
            'name': self._extract_name(content, file_path),
            'email': self._extract_email(content),
            'phone': self._extract_phone(content),
            'skills': self._extract_skills(content),
            'certifications': self._extract_certifications(content),
            'experience': self._extract_experience(content),
            'education': self._extract_education(content),
            'job_titles': self._extract_job_titles(content),
            'location': self._extract_location(content),
            'years_of_experience': self._estimate_years_of_experience(content),
            'raw_text': content
        }

        return candidate

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

    def _extract_name(self, content: str, file_path: str = None) -> str:
        """Extract candidate name from content or filename"""
        lines = content.strip().split('\n')

        # Try first non-empty line
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50 and not '@' in line and not self.phone_pattern.search(line):
                # Check if it looks like a name (2-4 words, mostly letters)
                words = line.split()
                if 2 <= len(words) <= 4 and all(re.match(r'^[A-Za-z\-\.]+$', w) for w in words):
                    return line

        # Fallback: Try to extract name from filename
        if file_path:
            name_from_filename = self._extract_name_from_filename(file_path)
            if name_from_filename:
                return name_from_filename

        return "Name Not Found"

    def _extract_name_from_filename(self, file_path: str) -> str:
        """
        Extract candidate name from filename

        Examples:
            john_doe_resume.pdf -> John Doe
            Jane-Smith.docx -> Jane Smith
            alex_kim.txt -> Alex Kim
            michael_chen_resume_2024.pdf -> Michael Chen
            JohnDoe.pdf -> John Doe
        """
        # Get filename without extension
        filename = Path(file_path).stem

        # Remove common prefixes (temp files, etc.)
        filename = re.sub(r'^tmp[a-z0-9]+[-_\s]*', '', filename, flags=re.IGNORECASE)

        # Remove common resume-related words and years
        filename = re.sub(r'(?i)[-_\s]*(resume|cv|curriculum|vitae|application|candidate|\d{4})[-_\s]*', ' ', filename)

        # Handle camelCase (e.g., JohnDoe -> John Doe)
        # Insert space before capital letters (but not at the start)
        filename = re.sub(r'(?<!^)(?=[A-Z])', ' ', filename)

        # Replace underscores and hyphens with spaces
        filename = filename.replace('_', ' ').replace('-', ' ')

        # Clean up extra spaces
        filename = ' '.join(filename.split())

        # Split into words and filter to keep only alphabetic words
        words = [w for w in filename.split() if w.isalpha()]

        # Check if it looks like a name (2-4 words)
        if 2 <= len(words) <= 4:
            # Capitalize each word
            name = ' '.join(word.capitalize() for word in words)
            return name

        # If more than 4 words, try to find first name + last name pattern
        # (typically the first 2 alphabetic words)
        if len(words) > 4:
            name = ' '.join(word.capitalize() for word in words[:2])
            return name

        # If it's a single word that's at least 3 characters, might be a last name
        if len(words) == 1 and len(words[0]) >= 3:
            return words[0].capitalize()

        return None

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

        # Common technical skills
        skill_keywords = [
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c\\+\\+', 'c#', 'ruby',
            'go', 'rust', 'php', 'swift', 'kotlin', 'scala', 'r',

            # Frameworks/Libraries
            'react', 'angular', 'vue', 'node\\.js', 'django', 'flask', 'spring',
            '\\.net', 'express', 'fastapi', 'rails', 'laravel',

            # Cloud/DevOps
            'aws', 'azure', 'gcp', 'google cloud', 'kubernetes', 'docker',
            'jenkins', 'terraform', 'ansible', 'ci/cd', 'devops',

            # Databases
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'oracle',
            'redis', 'elasticsearch', 'cassandra', 'dynamodb',

            # Data/AI
            'machine learning', 'deep learning', 'data science', 'nlp',
            'computer vision', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'spark', 'hadoop',

            # Methodologies
            'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma',

            # Tools
            'git', 'jira', 'confluence', 'slack', 'tableau', 'power bi',

            # Soft skills
            'leadership', 'communication', 'teamwork', 'problem-solving',
            'project management', 'analytical', 'critical thinking'
        ]

        content_lower = content.lower()

        for skill in skill_keywords:
            if re.search(r'\b' + skill + r'\b', content_lower):
                # Capitalize properly
                skills.append(skill.replace('\\', '').upper() if len(skill) <= 5
                            else skill.replace('\\', '').title())

        return list(set(skills))  # Remove duplicates

    def _extract_certifications(self, content: str) -> List[str]:
        """Extract certifications"""
        certifications = []

        # Common certification patterns
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

        # Look for common experience section headers
        exp_section = re.search(
            r'(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE)(.*?)(?:EDUCATION|SKILLS|CERTIFICATIONS|$)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if exp_section:
            exp_text = exp_section.group(1)

            # Try to extract job entries
            # Pattern: Company name, job title, dates
            entries = re.split(r'\n\s*\n', exp_text)

            for entry in entries[:10]:  # Limit to 10 entries
                if len(entry.strip()) > 20:
                    experiences.append({
                        'raw_entry': entry.strip()
                    })

        return experiences

    def _extract_education(self, content: str) -> List[str]:
        """Extract education information"""
        education = []

        # Common degree patterns
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

        # Common job title keywords
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
        # Common location patterns
        location_pattern = r'(?:Location|Address|Based in):\s*([\w\s,]+(?:,\s*[A-Z]{2})?)'
        match = re.search(location_pattern, content, re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Try to find City, State pattern in first 500 chars
        header = content[:500]
        city_state = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', header)

        if city_state:
            return city_state.group(1)

        return "Location Not Specified"

    def _estimate_years_of_experience(self, content: str) -> int:
        """Estimate years of experience from dates in resume"""
        # Find year patterns (1990-2099)
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', content)

        if years:
            years_int = [int(y) for y in years]
            # Estimate: latest year - earliest year
            return max(years_int) - min(years_int)

        # Try to find explicit "X years of experience"
        exp_match = re.search(r'(\d+)\+?\s*years?\s+of\s+experience', content, re.IGNORECASE)
        if exp_match:
            return int(exp_match.group(1))

        return 0  # Unknown
