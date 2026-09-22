import json
import re
from typing import Type, TypeVar, Optional
import httpx
from pydantic import BaseModel, ValidationError
from app.core.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMProviderError(Exception):
    """Exception raised when LLM generation or validation fails across configured providers."""
    pass


def clean_json_string(text: str) -> str:
    """Removes markdown code fences and strips trailing whitespace from JSON response."""
    text = text.strip()
    pattern = r"^```(?:json)?\s*(.*?)\s*```$"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def mask_secret(text: str) -> str:
    """Sanitizes text to ensure API tokens or secrets are not exposed in error logs."""
    if not text:
        return text
    sanitized = text
    for key in (settings.GROQ_API_KEY, settings.GEMINI_API_KEY, settings.JIRA_API_TOKEN, settings.SUPABASE_KEY):
        if key and len(key) > 4:
            sanitized = sanitized.replace(key, f"{key[:4]}***MASKED***")
    return sanitized


async def _call_groq_http(system_prompt: str, user_prompt: str) -> str:
    """Invokes Groq API via HTTP standard request."""
    if not settings.GROQ_API_KEY:
        raise LLMProviderError("Groq API key is not configured.")

    url = f"{settings.GROQ_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(url, json=payload, headers=headers)
        if res.status_code != 200:
            raise LLMProviderError(f"Groq API error HTTP {res.status_code}: {res.text}")
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        if not content:
            raise LLMProviderError("Groq returned an empty response.")
        return content


async def _call_gemini_http(system_prompt: str, user_prompt: str) -> str:
    """Invokes Gemini REST API via HTTP standard request."""
    if not settings.GEMINI_API_KEY:
        raise LLMProviderError("Gemini API key is not configured.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(url, json=payload, headers=headers)
        if res.status_code != 200:
            raise LLMProviderError(f"Gemini API error HTTP {res.status_code}: {res.text}")
        data = res.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise LLMProviderError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise LLMProviderError("Gemini returned empty parts.")
        return parts[0].get("text", "")


async def execute_llm_request(
    system_prompt: str,
    user_prompt: str,
    response_model: Type[T],
    operation_name: str = "LLM Request",
) -> T:
    """
    Executes an LLM request trying Groq first, falling back to Gemini on failure,
    and validating the response against target Pydantic schema.
    """
    groq_error: Optional[Exception] = None
    gemini_error: Optional[Exception] = None

    # 1. Attempt Primary Provider: Groq
    try:
        raw_text = await _call_groq_http(system_prompt, user_prompt)
        cleaned_json = clean_json_string(raw_text)
        return response_model.model_validate_json(cleaned_json)
    except Exception as exc:
        groq_error = exc

    # 2. Attempt Fallback Provider: Gemini
    try:
        raw_text = await _call_gemini_http(system_prompt, user_prompt)
        cleaned_json = clean_json_string(raw_text)
        return response_model.model_validate_json(cleaned_json)
    except Exception as exc:
        gemini_error = exc

    # 3. Both failed
    groq_msg = mask_secret(str(groq_error)) if groq_error else "Skipped"
    gemini_msg = mask_secret(str(gemini_error)) if gemini_error else "Skipped"

    raise LLMProviderError(
        f"Operation '{operation_name}' failed. Primary provider Groq error: [{groq_msg}], "
        f"Fallback provider Gemini error: [{gemini_msg}]."
    )
