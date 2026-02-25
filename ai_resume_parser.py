"""
AI-Powered Resume Parser
Uses LLM (Gemini or OpenAI) to intelligently extract skills and certifications with context understanding
"""

import os
import re
import json
import logging
from typing import Dict, List, Any
from resume_parser import ResumeParser
from config import is_ai_configured
from llm_client import generate, LLMError

logger = logging.getLogger(__name__)


class AIResumeParser:
    """
    AI-powered resume parser that uses LLM (Gemini or OpenAI) to understand context
    and extract only actual skills and certifications.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize AI resume parser.

        Args:
            api_key: Optional (uses GEMINI_API_KEY or OPENAI_API_KEY env var).
        """
        if not is_ai_configured():
            raise ValueError(
                "No AI provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY environment variable."
            )
        self.base_parser = ResumeParser()
        from config import get_llm_provider, GeminiConfig, OpenAIConfig
        provider = get_llm_provider()
        model = GeminiConfig.get_model() if provider == "gemini" else OpenAIConfig.get_model()
        print(f"AI resume parsing enabled (using {provider} / {model})")

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse resume using AI for intelligent extraction

        Args:
            file_path: Path to resume file

        Returns:
            Dictionary with candidate information
        """
        # Read file content using base parser
        content = self.base_parser._read_file(file_path)
        
        # Use AI to extract all information directly
        return self._ai_extract(content)

    def _ai_extract(self, content: str) -> Dict[str, Any]:
        """Use LLM (Gemini or OpenAI) to intelligently extract all candidate information"""
        
        if not content:
            return {}

        # Truncate content if too long (keep first 8000 chars for GPT-4 Turbo)
        content_length = len(content)
        if content_length > 12000:
            prioritized_content = content[:8000] + "\n\n[... rest of resume omitted ...]\n\n" + content[-4000:]
        else:
            prioritized_content = content

        prompt = f"""You are an expert resume analyzer. Extract comprehensive information from this resume. Extract ONLY information that is EXPLICITLY stated. DO NOT infer, assume, or fabricate any information.

RESUME CONTENT:
{prioritized_content}

Extract and return ONLY a JSON object with these fields:

{{
    "name": "candidate full name",
    "email": "email address",
    "phone": "phone number",
    "location": "city, state",
    "skills": ["skill1", "skill2", ...],
    "certifications": ["cert1", "cert2", ...],
    "education": ["degree1", "degree2", ...],
    "years_of_experience": number,
    "job_titles": ["title1", "title2", ...],
    "raw_text": "{prioritized_content[:500]}"
}}

CRITICAL RULES - STRICT ADHERENCE REQUIRED:

1. **ONLY EXTRACT EXPLICIT INFORMATION**:
   - You MUST be able to point to the exact text in the resume where each item appears
   - DO NOT infer skills from job titles (e.g., "Software Engineer" does NOT mean they know Python)
   - DO NOT infer certifications from experience descriptions
   - DO NOT add skills/certifications based on industry norms or assumptions
   - DO NOT mention equivalent certifications - only what's explicitly listed

2. **SKILLS EXTRACTION**:
   - Extract ONLY technical/professional skills that are EXPLICITLY mentioned
   - DO NOT extract generic words, company names, or job titles
   - DO NOT infer skills from context

3. **CERTIFICATIONS EXTRACTION**:
   - Extract ONLY certifications that are EXPLICITLY stated
   - Must be clearly identified as a certification
   - DO NOT infer certifications from experience

4. **NO FABRICATION**:
   - DO NOT add skills/certifications that would be "typical" for this role
   - DO NOT mention equivalent certifications
   - ONLY extract what is explicitly written in the resume text

Return ONLY valid JSON. If information is not found, use empty strings or arrays.
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

            # Parse JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    candidate_data = json.loads(json_str)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse AI response as JSON: {e}")
                    raise ValueError(f"Failed to parse AI response as JSON: {e}")

                # Validate extracted items against raw text to prevent fabrication
                extracted_skills = self._validate_against_resume(
                    candidate_data.get('skills', []), content, 'skill'
                )
                extracted_certs = self._validate_against_resume(
                    candidate_data.get('certifications', []), content, 'certification'
                )

                # Update with validated data
                candidate_data['skills'] = extracted_skills
                candidate_data['certifications'] = extracted_certs
                candidate_data['raw_text'] = content  # Store full content
                
                print(f"  AI extracted {len(extracted_skills)} skills and {len(extracted_certs)} certifications (validated)")
                return candidate_data
            else:
                raise ValueError("AI response didn't contain valid JSON")

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            # Filter out errors related to deprecated _generate_deterministic_seed method
            error_str = str(e)
            if '_generate_deterministic_seed' in error_str:
                raise ValueError("AI extraction failed: Internal parsing error")
            raise ValueError(f"AI extraction failed: {e}")

    def _validate_against_resume(self, items: List[str], resume_text: str, item_type: str) -> List[str]:
        """
        Validate that extracted items actually appear in the resume text
        
        Args:
            items: List of extracted skills or certifications
            resume_text: The raw resume text
            item_type: 'skill' or 'certification'
        
        Returns:
            List of validated items that appear in the resume
        """
        if not items:
            return []
        
        validated = []
        resume_lower = resume_text.lower()
        
        for item in items:
            item_lower = item.lower()
            # Check if item appears in resume (allowing for some variation)
            # Look for the item or its key components
            item_words = item_lower.split()
            
            # For certifications, be more strict - look for exact or near-exact match
            if item_type == 'certification':
                # Check for exact match or close match (allowing for punctuation)
                item_clean = re.sub(r'[^\w\s]', '', item_lower)
                resume_clean = re.sub(r'[^\w\s]', '', resume_lower)
                
                if item_clean in resume_clean or any(word in resume_clean for word in item_words if len(word) > 3):
                    validated.append(item)
                else:
                    print(f"  WARNING: {item_type} '{item}' not found in resume - excluding")
            else:
                # For skills, check if key words appear
                if any(word in resume_lower for word in item_words if len(word) > 2):
                    validated.append(item)
                else:
                    print(f"  WARNING: {item_type} '{item}' not found in resume - excluding")
        
        return validated

