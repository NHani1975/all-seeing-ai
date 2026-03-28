"""
routes.py — FastAPI route definitions for the All-Seeing AI API.

Routes:
    POST /api/analyze  — Scrape a URL + run AI analysis
    POST /api/chat     — Answer a question grounded in website content

Both routes:
    - Validate inputs (Pydantic models)
    - Return structured JSON on success
    - Return { "error": "..." } with appropriate HTTP status on failure
    - NEVER silently swallow errors
"""

import sys
import os

# Make sibling execution scripts importable
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator

from utils_scraper import fetch_page, clean_html, smart_truncate
from utils_ai import chat_completion, parse_json_response
from generate_analysis import SYSTEM_PROMPT as ANALYSIS_SYSTEM, build_user_prompt
from generate_chat_reply import SYSTEM_PROMPT as CHAT_SYSTEM

router = APIRouter()


# ══════════════════════════════════════════════════════════════
#  /api/analyze
# ══════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url cannot be empty")
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class AnalyzeResponse(BaseModel):
    url:           str
    summary:       str
    bullet_points: list[str]
    pros:          list[str]
    cons:          list[str]
    insights:      list[str]
    content:       str          # Raw cleaned text — stored by frontend for chat


@router.post("/api/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_website(body: AnalyzeRequest):
    """
    Scrape a website and return AI-generated analysis.

    Pipeline:
        1. Fetch raw HTML (utils_scraper.fetch_page)
        2. Clean HTML to plain text (utils_scraper.clean_html)
        3. Truncate using head+tail strategy (utils_scraper.smart_truncate)
        4. Send to OpenAI for structured analysis (generate_analysis prompt)
        5. Validate response shape and return
    """
    url = body.url

    # ── Step 1: Scrape ────────────────────────────────────────
    try:
        html = fetch_page(url)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=f"Scraping failed: {exc}")

    # ── Step 2: Clean ─────────────────────────────────────────
    try:
        text = clean_html(html)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Content extraction failed: {exc}")

    # ── Step 3: Truncate ──────────────────────────────────────
    content = smart_truncate(text, max_chars=12_000)

    # ── Step 4: AI Analysis ───────────────────────────────────
    try:
        raw = chat_completion(
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM},
                {"role": "user",   "content": build_user_prompt(content)},
            ],
            max_tokens=2000,
            temperature=0.2,
            response_format="json_object",
        )
        result = parse_json_response(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {exc}")

    # ── Step 5: Validate shape ────────────────────────────────
    required = {"summary", "bullet_points", "pros", "cons", "insights"}
    missing  = required - result.keys()
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"AI returned incomplete response — missing keys: {missing}",
        )

    return AnalyzeResponse(
        url=url,
        summary=result["summary"],
        bullet_points=result["bullet_points"],
        pros=result["pros"],
        cons=result["cons"],
        insights=result["insights"],
        content=content,   # Returned to frontend for subsequent chat calls
    )


# ══════════════════════════════════════════════════════════════
#  /api/chat
# ══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    question: str
    content:  str

    @field_validator("question", "content")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    answer: str


@router.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_content(body: ChatRequest):
    """
    Answer a user question grounded strictly in the provided website content.

    The AI is explicitly instructed NOT to use outside knowledge.
    If the answer isn't in the content, returns a clear not-found message.
    """
    content  = smart_truncate(body.content, max_chars=10_000)
    question = body.question

    user_message = f"""WEBSITE CONTENT:
---
{content}
---

QUESTION: {question}"""

    try:
        answer = chat_completion(
            messages=[
                {"role": "system", "content": CHAT_SYSTEM},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=600,
            temperature=0.1,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"AI chat failed: {exc}")

    return ChatResponse(answer=answer)
