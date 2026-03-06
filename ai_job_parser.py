"""
AI-Enhanced Job Description Parser
Uses LLM (Gemini or OpenAI) for intelligent extraction of job details
"""

import os
import json
import re
import logging
from typing import Dict, List, Any
from pathlib import Path
import PyPDF2
import docx
from config import is_ai_configured
from llm_client import generate, LLMError

logger = logging.getLogger(__name__)


def _extract_json_object(response_text: str) -> Dict[str, Any]:
    """
    Extract the first valid JSON object from a model response.

    Gemini sometimes wraps JSON in markdown fences or adds surrounding text, so
    this helper first tries the full response, then scans for balanced JSON
    objects and returns the first one that parses successfully.
    """
    cleaned = response_text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    start = None
    depth = 0
    for idx, char in enumerate(cleaned):
        if char == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif char == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidate = cleaned[start:idx + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict):
                            return parsed
                    except (json.JSONDecodeError, TypeError):
                        continue

    raise ValueError("AI response didn't contain valid JSON")


class AIJobParser:
    """
    AI-powered job description parser using LLM (Gemini or OpenAI).
    AI is required - no fallbacks.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize AI job parser.

        Args:
            api_key: Optional (uses GEMINI_API_KEY or OPENAI_API_KEY env var).
        """
        if not is_ai_configured():
            raise ValueError(
                "No AI provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY environment variable."
            )
        from config import get_llm_provider, GeminiConfig, OpenAIConfig
        provider = get_llm_provider()
        model = GeminiConfig.get_model() if provider == "gemini" else OpenAIConfig.get_model()
        print(f"AI job parsing enabled (using {provider} / {model})")

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse job description file using AI

        Args:
            file_path: Path to job description file

        Returns:
            Dictionary with extracted job information
        """
        # Read file content
        content = self._read_file(file_path)

        # Extract filename for context (sometimes filename contains job title)
        filename = Path(file_path).stem  # Get filename without extension
        
        # Use AI to extract all information
        return self._ai_extract(content, filename)

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
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    # Check if PDF is encrypted
                    if pdf_reader.is_encrypted:
                        raise ValueError("PDF file is encrypted/password-protected. Please provide an unencrypted version.")
                    
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                    
                    # Debug: Check if we got meaningful content
                    if len(text.strip()) < 50:
                        print(f"WARNING: PDF extraction resulted in very short text ({len(text)} chars)")
                        print(f"First 200 chars: {text[:200]}")
                        print("This may be a scanned/image-based PDF that requires OCR.")
                except PyPDF2.errors.PdfReadError as e:
                    raise ValueError(f"PDF file appears to be corrupted or invalid: {e}")
        except FileNotFoundError:
            raise ValueError(f"PDF file not found: {file_path}")
        except PermissionError:
            raise ValueError(f"Permission denied reading PDF file: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {e}")
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

    def _ai_extract(self, content: str, filename: str = "") -> Dict[str, Any]:
        """Use LLM (Gemini or OpenAI) to extract job information"""
        
        # Debug: Print first 500 chars to see what we're working with
        print(f"DEBUG: Content length: {len(content)}")
        print(f"DEBUG: First 500 chars: {content[:500]}")
        if filename:
            print(f"DEBUG: Filename: {filename}")
        
        # Use full content - GPT-4 Turbo can handle longer documents
        # For very long documents, prioritize beginning (where title usually is) but include more context
        content_length = len(content)
        if content_length > 12000:
            # Take first 8000 chars (likely to contain title and key requirements) + last 4000 chars
            prioritized_content = content[:8000] + "\n\n[... middle content omitted ...]\n\n" + content[-4000:]
        else:
            prioritized_content = content

        # Include filename in prompt if available (often contains job title)
        filename_context = f"\n\nFILENAME CONTEXT: The document filename is '{filename}'. This may contain clues about the job title (e.g., 'Solar-Safety-Manager.pdf' suggests the title is 'Solar Safety Manager')." if filename else ""

        prompt = f"""You are an expert recruitment AI analyzing a job description. Your PRIMARY task is to extract the EXACT job title that is being hired for. Read the entire document carefully and identify the main position being advertised.

JOB DESCRIPTION:
{prioritized_content}{filename_context}

Extract and return ONLY a JSON object with these fields:

{{
    "job_title": "the EXACT main job position title being hired for",
    "location": "city, state or Remote",
    "certifications": [
        {{"name": "cert name", "category": "must-have or bonus"}}
    ],
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1", "skill2"],
    "experience_level": "Junior/Mid/Senior",
    "industry_context": "brief description of the industry or field (optional)",
    "soft_skills": ["communication", "teamwork", "leadership"],
    "technical_stack": ["specific technologies", "tools", "software"]
}}

CRITICAL RULES FOR JOB TITLE EXTRACTION - READ CAREFULLY:

1. **Job Title is MANDATORY and CRITICAL** - You MUST extract the EXACT job title. This is the most important field.

2. **How to Find the Job Title** (check in this exact order):
   
   STEP 1: Look for explicit labels in the FIRST 20 lines:
   - "Job Title:", "Position:", "Role:", "Title:", "Job:", "Opening for:"
   - "We are hiring a", "Seeking a", "Looking for a", "Position Available:"
   - "Join our team as a", "Become our"
   
   STEP 2: Look for standalone capitalized lines in the FIRST 10 lines:
   - Lines that are ALL CAPS or Title Case
   - Examples: "SOLAR SAFETY MANAGER", "Safety Manager", "Solar Safety Manager"
   - These are often the job title displayed prominently
   
   STEP 3: Look for contextual phrases throughout the document:
   - "looking for [Job Title]" → extract "[Job Title]"
   - "seeking [Job Title]" → extract "[Job Title]"
   - "hiring [Job Title]" → extract "[Job Title]"
   - "[Job Title] position" → extract "[Job Title]"
   - "Position: [Job Title]" → extract "[Job Title]"
   - "[Job Title] with X years experience" → extract "[Job Title]"
   - "experience as a [Job Title]" → extract "[Job Title]"
   
   STEP 4: Look for compound titles and extract the PRIMARY one:
   - "Solar Safety Manager" → "Solar Safety Manager" (extract the FULL title)
   - "Safety Manager or Solar Safety Manager" → "Safety Manager" (first/main one)
   - If you see multiple titles, pick the one that appears FIRST and MOST FREQUENTLY
   
   STEP 5: Check document filename - sometimes the filename contains the job title
   - If filename is "Solar-Safety-Manager.pdf" → job title is likely "Solar Safety Manager"

3. **What Job Titles Look Like**:
   - Usually 2-5 words
   - Contains job function words: Manager, Specialist, Engineer, Coordinator, Supervisor, Director, Technician, etc.
   - May include industry/domain: Solar, Safety, Electrical, Medical, etc.
   - Examples: "Solar Safety Manager", "Safety Specialist", "Power Distribution Safety Manager", "Electrical Lineman"
   
4. **What NOT to Extract**:
   - Single words like "medical", "solar", "safety" - these are NOT job titles
   - Company names (e.g., "Telyon")
   - Department names
   - Generic phrases like "team member", "professional", "candidate"
   - Industry names alone (e.g., "medical" is an industry, not a job title)
   - If you see "medical" but the actual title is "Solar Safety Manager", extract "Solar Safety Manager"

5. **Validation Rules**:
   - Job title MUST be 2+ words (single words are almost never job titles)
   - Job title MUST contain a job function word (Manager, Specialist, Engineer, etc.)
   - If you extract a single word, you've made an error - look harder
   - The job title should make sense as a position someone would be hired for

6. **Examples of CORRECT extractions**:
   - Document says "Solar Safety Manager" → Extract: "Solar Safety Manager"
   - Document says "We are seeking a Solar Safety Manager" → Extract: "Solar Safety Manager"
   - Document filename is "Solar-Safety-Manager.pdf" and mentions "Solar Safety Manager" → Extract: "Solar Safety Manager"
   - Document mentions "medical field" and "Solar Safety Manager" → Extract: "Solar Safety Manager" (NOT "medical")
   
7. **Examples of INCORRECT extractions**:
   - Extracting "medical" when the title is "Solar Safety Manager" → WRONG
   - Extracting "solar" when the title is "Solar Safety Manager" → WRONG
   - Extracting a single word → WRONG

8. **Location**: Look for city, state, or "Remote"

9. **Certifications**: Extract certification names only (e.g., "OSHA 30", "CDL")

10. **Skills** - CRITICAL EXTRACTION RULES (MANDATORY):
   - Extract ONLY professional/technical skills EXPLICITLY mentioned as requirements
   - Skills are typically found in "Requirements", "Qualifications", "Skills Required" sections
   - DO NOT infer, guess, or extract skills that are not explicitly stated
   - DO NOT extract:
     * Single letters or very short words (e.g., "ai", "go", "aws" are NOT skills unless clearly stated as requirements)
     * Generic words from the job description
     * Industry names (e.g., "medical", "solar", "safety" alone are NOT skills)
     * Random words from sentences
     * Skills inferred from context - ONLY extract what is explicitly listed
   - Valid skills examples:
     * Technical: "Python programming", "Project Management", "Data Analysis", "Welding"
     * Professional: "Safety Management", "Risk Assessment", "Team Leadership"
     * Certifications as skills: "OSHA Compliance", "First Aid", "Forklift Operation"
   - **CRITICAL**: If NO specific skills are mentioned in requirements, you MUST return empty array []
   - **CRITICAL**: DO NOT create fallback skills - if not explicitly stated, return []
   - Separate into required vs preferred based on section headings
   - If a section says "not specified" or has no skills listed, return [] for that section

11. **Experience**: Look for years or level (Junior/Mid/Senior)

12. **Industry Context** (optional): Extract a brief description of the industry, sector, or field (e.g., "Utility/Solar Energy", "Healthcare", "Construction"). This helps understand the business context. If not clear, leave as null.

13. **Soft Skills** (optional): Extract interpersonal and communication skills explicitly mentioned (e.g., "communication", "teamwork", "leadership", "problem-solving"). Only extract if explicitly stated in requirements. If not mentioned, return empty array [].

14. **Technical Stack** (optional): Extract specific technologies, tools, software, or systems explicitly mentioned (e.g., "Python", "AWS", "SQL", "Salesforce"). Only extract technologies explicitly required. If not mentioned, return empty array [].

MOST IMPORTANT RULE:
- The job_title field MUST be a proper job title (2+ words, contains job function)
- If you're unsure between multiple options, choose the one that:
  a) Appears first in the document
  b) Is most specific and complete
  c) Contains both industry/domain AND job function
  d) Makes sense as a position someone would be hired for

Return ONLY valid JSON, no explanation or markdown formatting.
JSON:
"""

        try:
            response_text = generate(
                [{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.1,
            )
            if not response_text:
                raise ValueError("LLM response was empty")
            response_text = response_text.strip()

            # Try to parse JSON
            # Note: json and re are already imported at module level, no need to import locally

            # Debug: Print AI response
            print(f"DEBUG: AI response (first 500 chars): {response_text[:500]}")

            try:
                job_data = _extract_json_object(response_text)
            except ValueError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise ValueError(str(e))

            # Validate and fix job title - ensure it's a proper job title
            extracted_title = job_data.get('job_title', '').strip() if job_data.get('job_title') else ''

            # Check if title is invalid (single word, generic, etc.)
            title_words = extracted_title.split() if extracted_title else []
            title_lower = extracted_title.lower().strip()
            is_invalid = (
                not extracted_title or
                title_lower in ['not found', 'none', 'n/a', ''] or
                len(title_words) < 2 or  # Single word is not a valid job title
                title_lower in ['medical', 'solar', 'safety', 'manager', 'engineer', 'specialist']  # Common single-word mistakes
            )

            if is_invalid:
                print(f"WARNING: AI extracted invalid job title: '{extracted_title}' - setting to 'Not Specified'")
                job_data['job_title'] = 'Job Title Not Specified'
            else:
                print(f"DEBUG: Using AI-extracted title: '{extracted_title}'")

            # Ensure location is not empty
            extracted_location = job_data.get('location', '').strip() if job_data.get('location') else ''
            if not extracted_location or extracted_location.lower() in ['not found', 'none', 'n/a', '']:
                job_data['location'] = 'Location Not Specified'

            # Ensure all optional fields are present with defaults
            if 'industry_context' not in job_data:
                job_data['industry_context'] = None
            if 'soft_skills' not in job_data:
                job_data['soft_skills'] = []
            if 'technical_stack' not in job_data:
                job_data['technical_stack'] = []

            # Always attach the original description in Python rather than asking the model
            # to emit the full raw text inside JSON.
            job_data['full_description'] = content

            # Ensure skills are not empty or invalid - filter out single-word garbage
            # Strict filtering: reject abbreviations, single letters, and invalid short words
            invalid_abbreviations = ['ai', 'go', 'aws', 'it', 'hr', 'pr', 'ml', 'nlp', 'api', 'ui', 'ux', 'qa', 'pm']

            def is_valid_skill(skill: str) -> bool:
                """Validate that a skill is meaningful and not an invalid abbreviation"""
                if not skill or not isinstance(skill, str):
                    return False

                skill = skill.strip()
                if not skill:
                    return False

                skill_lower = skill.lower()

                # Reject if it's in the blacklist of invalid abbreviations
                if skill_lower in invalid_abbreviations:
                    return False

                # Reject single words <= 3 characters (too short to be meaningful)
                if len(skill) <= 3 and ' ' not in skill:
                    return False

                # Reject single letters
                if len(skill) == 1:
                    return False

                # Accept multi-word skills (they're usually meaningful)
                if ' ' in skill:
                    return True

                # Accept single words > 3 characters that aren't blacklisted
                if len(skill) > 3:
                    return True

                # Reject everything else
                return False

            if 'required_skills' in job_data:
                job_data['required_skills'] = [
                    skill.strip() for skill in job_data['required_skills']
                    if is_valid_skill(skill)
                ]
            if 'preferred_skills' in job_data:
                job_data['preferred_skills'] = [
                    skill.strip() for skill in job_data['preferred_skills']
                    if is_valid_skill(skill)
                ]

            # Filter soft_skills and technical_stack similarly
            if 'soft_skills' in job_data:
                job_data['soft_skills'] = [
                    skill.strip() for skill in job_data['soft_skills']
                    if is_valid_skill(skill)
                ]
            if 'technical_stack' in job_data:
                job_data['technical_stack'] = [
                    skill.strip() for skill in job_data['technical_stack']
                    if is_valid_skill(skill)
                ]

            return job_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}. Response: {response_text[:500]}")
        except Exception as e:
            raise ValueError(f"AI extraction failed: {e}")
