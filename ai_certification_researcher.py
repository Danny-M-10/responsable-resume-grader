"""
AI-Powered Certification Researcher
Uses LLM (Gemini or OpenAI) to research equivalent certifications when job description mentions "or equivalent"
"""

import os
import json
import re
import logging
from typing import List, Dict
from config import is_ai_configured
from llm_client import generate, LLMError

logger = logging.getLogger(__name__)


class AICertificationResearcher:
    """
    AI-powered certification researcher that identifies equivalent certifications.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize AI certification researcher.

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
        print(f"AI certification research enabled (using {provider} / {model})")

    def find_equivalents(self, certification: str, job_context: str = "") -> List[str]:
        """
        Find equivalent certifications using AI

        Args:
            certification: The certification name (e.g., "COSS", "OSHA 30")
            job_context: Optional job description context for better matching

        Returns:
            List of equivalent certification names
        """

        # Check if certification mentions "or equivalent"
        if "equivalent" not in certification.lower():
            return []

        # Extract the base certification name
        base_cert = certification.split("or equivalent")[0].strip()
        base_cert = base_cert.split("or")[0].strip() if "or" in base_cert else base_cert

        prompt = f"""You are a certification expert. Research equivalent certifications for the given certification.

CERTIFICATION: {base_cert}

JOB CONTEXT (if provided):
{job_context[:1000]}

Find and list equivalent certifications that would be acceptable substitutes for "{base_cert}".

CRITICAL RULES:
1. **Industry Knowledge**: Use your knowledge of certification equivalencies
2. **Same Level**: Equivalents should be at the same professional level
3. **Same Domain**: Equivalents should be in the same field/industry
4. **Common Equivalencies**:
   - Safety certifications: COSS ≈ CHST ≈ ASP ≈ CUSP (all safety professional certs)
   - OSHA certifications: OSHA 30 ≈ OSHA 10 (with experience) ≈ OSHA 500
   - Project management: PMP ≈ PRINCE2 ≈ CAPM (with experience)
   - Cloud: AWS Certified ≈ Azure Certified ≈ GCP Certified (same specialty)
5. **Be Specific**: Include full certification names, not just abbreviations
6. **Be Conservative**: Only include certifications that are truly equivalent

Return ONLY a JSON array of equivalent certification names:
["Equivalent Cert 1", "Equivalent Cert 2", ...]

If no clear equivalents exist, return an empty array: []

JSON:
"""

        try:
            response_text = generate(
                [{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.2,
            )
            if not response_text:
                return []

            response_text = response_text.strip()

            # Parse JSON
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                equivalents = json.loads(json_str)
                return [eq.strip() for eq in equivalents if eq.strip()]

        except json.JSONDecodeError as e:
            print(f"WARNING: Failed to parse AI response as JSON: {e}")
        except Exception as e:
            print(f"WARNING: AI certification research failed: {e}")

        return []

    def expand_certification_list(self, certifications: List[str], job_context: str = "") -> List[str]:
        """
        Expand a list of certifications to include equivalents

        Args:
            certifications: List of certification names (may include "or equivalent")
            job_context: Optional job description context

        Returns:
            Expanded list with equivalents added
        """
        expanded = []
        
        for cert in certifications:
            expanded.append(cert)
            
            # Check if this cert mentions "or equivalent"
            if "equivalent" in cert.lower():
                equivalents = self.find_equivalents(cert, job_context)
                expanded.extend(equivalents)
                if equivalents:
                    print(f"  Found {len(equivalents)} equivalent(s) for {cert}")

        return list(set(expanded))  # Remove duplicates

