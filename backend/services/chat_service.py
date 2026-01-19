"""
AI Chat Service for Candidate Selection Rationale
Allows users to ask questions about candidate selection decisions
"""
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from sqlalchemy import text
from backend.database.connection import AsyncSessionLocal
from config import OpenAIConfig

logger = logging.getLogger(__name__)


class ChatService:
    """Service for generating AI chat responses about candidate selection"""

    def __init__(self, api_key: str = None):
        """Initialize chat service with OpenAI client"""
        self.api_key = api_key or OpenAIConfig.get_api_key()
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = OpenAI(api_key=self.api_key)
        self.model = OpenAIConfig.get_model()

    async def generate_chat_response(
        self, analysis_id: str, user_message: str, user_id: str
    ) -> str:
        """
        Generate AI response to user's question about candidate selection

        Args:
            analysis_id: Analysis ID
            user_message: User's question
            user_id: User ID for authorization

        Returns:
            AI response string
        """
        try:
            # Load analysis data
            analysis_data, job_data = await self._load_analysis_data(
                analysis_id, user_id
            )

            if not analysis_data:
                return "I couldn't find the analysis data. Please make sure the analysis is completed."

            # Build context from analysis
            context = self._build_analysis_context(analysis_data, job_data)

            # Build prompt with system instructions and user question
            system_prompt = self._build_system_prompt()
            user_prompt = f"{context}\n\nUser question: {user_message}"

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,  # Slightly higher for conversational responses
                max_tokens=1000,
            )

            if not response.choices or len(response.choices) == 0:
                return "I'm sorry, I couldn't generate a response. Please try again."

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating chat response: {e}", exc_info=True)
            return f"I encountered an error while processing your question: {str(e)}. Please try again."

    async def _load_analysis_data(
        self, analysis_id: str, user_id: str
    ) -> tuple:
        """Load analysis and job data from database"""
        async with AsyncSessionLocal() as db:
            # Get analysis
            analysis_result = await db.execute(
                text("""
                    SELECT id, job_id, status, results, config
                    FROM analyses
                    WHERE id = :analysis_id AND user_id = :user_id
                """),
                {"analysis_id": analysis_id, "user_id": user_id},
            )
            analysis_row = analysis_result.fetchone()

            if not analysis_row:
                return None, None

            # Parse results
            results_data = None
            if analysis_row[3]:  # results column
                try:
                    if isinstance(analysis_row[3], str):
                        results_data = json.loads(analysis_row[3])
                    else:
                        results_data = analysis_row[3]
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse analysis results: {e}")
                    return None, None

            # Parse config
            config_data = None
            if analysis_row[4]:  # config column
                try:
                    if isinstance(analysis_row[4], str):
                        config_data = json.loads(analysis_row[4])
                    else:
                        config_data = analysis_row[4]
                except (json.JSONDecodeError, TypeError):
                    config_data = {}

            # Get job data
            job_id = analysis_row[1]
            job_result = await db.execute(
                text("""
                    SELECT title, location, parsed_data
                    FROM jobs
                    WHERE id = :job_id AND user_id = :user_id
                """),
                {"job_id": job_id, "user_id": user_id},
            )
            job_row = job_result.fetchone()

            job_data = None
            if job_row:
                job_parsed_data = None
                if job_row[2]:  # parsed_data column
                    try:
                        if isinstance(job_row[2], str):
                            job_parsed_data = json.loads(job_row[2])
                        else:
                            job_parsed_data = job_row[2]
                    except (json.JSONDecodeError, TypeError):
                        job_parsed_data = {}

                job_data = {
                    "title": job_row[0],
                    "location": job_row[1],
                    "parsed_data": job_parsed_data or {},
                }

            return (
                {"results": results_data, "config": config_data, "status": analysis_row[2]},
                job_data,
            )

    def _build_analysis_context(
        self, analysis_data: Dict[str, Any], job_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build context string from analysis data"""
        context_parts = []

        # Job information
        if job_data:
            context_parts.append("=== JOB INFORMATION ===")
            context_parts.append(f"Title: {job_data.get('title', 'N/A')}")
            context_parts.append(f"Location: {job_data.get('location', 'N/A')}")

            parsed_data = job_data.get("parsed_data", {})
            if parsed_data:
                if parsed_data.get("required_skills"):
                    context_parts.append(
                        f"Required Skills: {', '.join(parsed_data.get('required_skills', []))}"
                    )
                if parsed_data.get("preferred_skills"):
                    context_parts.append(
                        f"Preferred Skills: {', '.join(parsed_data.get('preferred_skills', []))}"
                    )
                if parsed_data.get("required_certifications"):
                    context_parts.append(
                        f"Required Certifications: {', '.join(parsed_data.get('required_certifications', []))}"
                    )
                if parsed_data.get("preferred_certifications"):
                    context_parts.append(
                        f"Preferred Certifications: {', '.join(parsed_data.get('preferred_certifications', []))}"
                    )
                if parsed_data.get("experience_level"):
                    context_parts.append(
                        f"Experience Level: {parsed_data.get('experience_level')}"
                    )

        # Analysis configuration
        config = analysis_data.get("config", {})
        if config:
            context_parts.append("\n=== ANALYSIS CONFIGURATION ===")
            if config.get("industry_template"):
                context_parts.append(f"Industry Template: {config.get('industry_template')}")
            if config.get("custom_scoring_weights"):
                context_parts.append("Custom Scoring Weights:")
                for key, value in config.get("custom_scoring_weights", {}).items():
                    context_parts.append(f"  - {key}: {value}")

        # Candidates information
        results = analysis_data.get("results", {})
        candidates = results.get("candidates", []) if results else []

        if candidates:
            context_parts.append("\n=== CANDIDATES ===")
            context_parts.append(f"Total Candidates: {len(candidates)}")

            # Calculate average score
            if candidates:
                avg_score = sum(c.get("fit_score", c.get("score", 0)) for c in candidates) / len(candidates)
                context_parts.append(f"Average Score: {avg_score:.2f}")

            context_parts.append("\nRanked Candidates (highest to lowest score):")
            for idx, candidate in enumerate(candidates, 1):
                score = candidate.get("fit_score", candidate.get("score", 0))
                name = candidate.get("name", "Unknown")
                rationale = candidate.get("rationale", "No rationale provided")
                
                context_parts.append(f"\n#{idx}. {name} (Score: {score:.2f})")
                context_parts.append(f"   Rationale: {rationale}")
                
                # Add certifications if available
                certs = candidate.get("certifications", [])
                if certs:
                    cert_names = [c.get("name", c) if isinstance(c, dict) else c for c in certs]
                    context_parts.append(f"   Certifications: {', '.join(cert_names)}")
                
                # Add skills if available
                skills = candidate.get("skills", [])
                if skills:
                    skill_names = [s.get("name", s) if isinstance(s, dict) else s for s in skills]
                    context_parts.append(f"   Skills: {', '.join(skill_names[:10])}")  # Limit to first 10

        return "\n".join(context_parts)

    def _build_system_prompt(self) -> str:
        """Build system prompt for AI chat"""
        return """You are an AI assistant helping a recruiter understand candidate selection decisions. 
You have access to detailed information about:
- Job requirements (title, location, skills, certifications, experience level)
- All candidates with their scores, rankings, and detailed rationales
- Analysis configuration (scoring weights, industry template)

Your role is to answer questions about:
- Why specific candidates were ranked high or low
- Score differences between candidates
- Strengths and weaknesses of individual candidates
- How candidates match job requirements
- Comparisons between candidates
- Suggestions for candidate selection

Guidelines:
- Be concise but informative
- Reference specific candidates by name when relevant
- Explain scoring rationale in accessible, clear terms
- Compare candidates when asked
- Focus on actionable insights for the recruiter
- If asked about a candidate not in the data, politely say you don't have information about them

Answer the user's question based on the analysis data provided."""


# Singleton instance
_chat_service_instance: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create chat service instance"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
