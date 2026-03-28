"""
utils_ai.py — Central AI wrapper using Groq (OpenAI-compatible API).

Groq provides a free tier with 14,400 requests/day and very fast
inference via their LPU hardware.

Single responsibility: make chat completion calls via Groq.
All other scripts import from here.

Usage:
    from utils_ai import chat_completion, parse_json_response
    response = chat_completion(messages=[{"role": "user", "content": "Hello"}])
"""

import os
import json

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# ── Load .env from project root (two levels up from execution/) ──────────────
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Constants ────────────────────────────────────────────────────────────────
DEFAULT_MODEL      = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2000"))
GROQ_BASE_URL      = "https://api.groq.com/openai/v1"


def _get_client() -> OpenAI:
    """
    Build and return an OpenAI client pointed at Groq's API.
    Raises RuntimeError with a clear message if the API key is missing.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file at the project root. "
            "Get a free key at https://console.groq.com"
        )
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


def chat_completion(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.3,
    response_format: str | None = None,
) -> str:
    """
    Send a chat completion request to Groq and return the response text.

    Args:
        messages:        List of {"role": ..., "content": ...} dicts.
        model:           Groq model (default: llama-3.3-70b-versatile).
        max_tokens:      Maximum tokens in the response.
        temperature:     Sampling temperature (0 = most deterministic).
        response_format: Set to "json_object" to force JSON output.

    Returns:
        The assistant's message content as a string.

    Raises:
        RuntimeError: If the API key is missing or the API call fails.
    """
    client = _get_client()

    kwargs = dict(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content.strip()

    except OpenAIError as exc:
        raise RuntimeError(f"Groq API error: {exc}") from exc


def parse_json_response(raw: str) -> dict:
    """
    Parse a JSON string returned by the AI.
    Strips markdown code fences if present before parsing.

    Raises:
        RuntimeError: If the response cannot be parsed as JSON.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"AI returned invalid JSON. Raw response:\n{raw[:500]}\n\nError: {exc}"
        ) from exc
