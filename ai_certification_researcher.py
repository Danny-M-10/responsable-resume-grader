"""
AI-Powered Certification Researcher
Uses OpenAI GPT-4 Turbo to research equivalent certifications when job description mentions "or equivalent"
"""

import os
import json
import re
from typing import List, Dict
from openai import OpenAI
from config import OpenAIConfig


class AICertificationResearcher:
    """
    AI-powered certification researcher that identifies equivalent certifications
    """

    def __init__(self, api_key: str = None):
        """
        Initialize AI certification researcher

        Args:
            api_key: OpenAI API key (optional, uses env var if not provided)
        """
        self.api_key = api_key or OpenAIConfig.get_api_key()
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            self.model = OpenAIConfig.get_model()
            print(f"AI certification research enabled (using {self.model})")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")

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
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            if not response.choices or len(response.choices) == 0:
                return []

            response_text = response.choices[0].message.content.strip()

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

