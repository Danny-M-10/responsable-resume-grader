"""
LLM client abstraction: single interface for Gemini or OpenAI.
Used by scoring, chat, job/resume parsing, and certification research.
"""

import asyncio
import logging
from typing import Any, Dict, List

from config import (
    GeminiConfig,
    OpenAIConfig,
    get_llm_provider,
)

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM provider returns an error or is misconfigured."""

    pass


def _gemini_generate(messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
    """Sync Gemini API call. Used by generate() and, via executor, by generate_async()."""
    import google.generativeai as genai

    api_key = GeminiConfig.get_api_key()
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not set. Set GEMINI_API_KEY or pass api_key.")
    genai.configure(api_key=api_key)
    model_name = GeminiConfig.get_model()
    # Strip "models/" prefix if present (GeminiConfig may return "gemini-1.5-pro")
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    system_instruction = None
    user_parts: List[str] = []
    for m in messages:
        role = (m.get("role") or "user").lower()
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            system_instruction = content
        else:
            user_parts.append(content)

    prompt = "\n\n".join(user_parts) if user_parts else ""
    if not prompt:
        raise LLMError("No user content in messages.")

    try:
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_instruction,
        )
        config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        response = model.generate_content(prompt, generation_config=config)
    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "resource_exhausted" in msg:
            raise LLMError("Gemini API quota exceeded. Please try again later.") from e
        if "safety" in msg or "blocked" in msg:
            raise LLMError("Gemini blocked the response due to safety filters.") from e
        raise LLMError(f"Gemini API error: {e}") from e

    if not response or not response.text:
        raise LLMError("Gemini returned an empty response.")
    return response.text.strip()


def _openai_generate(messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
    """Sync OpenAI API call."""
    from openai import OpenAI

    api_key = OpenAIConfig.get_api_key()
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set. Set OPENAI_API_KEY or pass api_key.")
    client = OpenAI(api_key=api_key)
    model = OpenAIConfig.get_model()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception as e:
        raise LLMError(f"OpenAI API error: {e}") from e
    if not response.choices or len(response.choices) == 0:
        raise LLMError("OpenAI returned an empty response.")
    return (response.choices[0].message.content or "").strip()


def generate(
    messages: List[Dict[str, Any]],
    max_tokens: int = 4000,
    temperature: float = 0.0,
) -> str:
    """
    Synchronous LLM generate. Uses Gemini or OpenAI based on config.

    Args:
        messages: List of {"role": "user"|"system", "content": str}
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 = deterministic)

    Returns:
        Generated text.

    Raises:
        LLMError: If no provider is configured or the API call fails.
    """
    provider = get_llm_provider()
    if not provider:
        raise LLMError(
            "No AI provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY (and optionally LLM_PROVIDER=gemini|openai)."
        )
    if provider == "gemini":
        return _gemini_generate(messages, max_tokens, temperature)
    return _openai_generate(messages, max_tokens, temperature)


async def generate_async(
    messages: List[Dict[str, Any]],
    max_tokens: int = 4000,
    temperature: float = 0.0,
) -> str:
    """
    Asynchronous LLM generate. Runs sync call in a thread so it does not block the event loop.

    Args:
        messages: List of {"role": "user"|"system", "content": str}
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        Generated text.

    Raises:
        LLMError: If no provider is configured or the API call fails.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: generate(messages, max_tokens=max_tokens, temperature=temperature),
    )
