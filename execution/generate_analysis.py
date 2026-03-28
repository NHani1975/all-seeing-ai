"""
generate_analysis.py — Website content → structured AI analysis.

Single responsibility: take cleaned website text and produce a
structured JSON analysis via OpenAI.

Output JSON schema:
{
    "summary":       string  (max 5 sentences — factual overview),
    "bullet_points": list[str]  (exactly 5 key points),
    "pros":          list[str]  (3–5 strengths),
    "cons":          list[str]  (3–5 weaknesses),
    "insights":      list[str]  (3 advanced/strategic observations)
}

Usage (CLI):
    # From stdin (pipe from scraper):
    python scrape_website.py --url https://stripe.com | python generate_analysis.py

    # From argument:
    python generate_analysis.py --content "Website text here..."

    # From file:
    python generate_analysis.py --content-file page.txt
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils_ai import chat_completion, parse_json_response
from utils_scraper import smart_truncate


# ── Prompt ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert business and UX analyst. 
You analyze website content and return a precise, structured JSON report.
Be concise, factual, and data-driven. Do NOT invent information not present in the content."""

def build_user_prompt(content: str) -> str:
    return f"""Analyze the following website content and return a JSON object with EXACTLY these keys:

{{
  "summary": "A factual overview in no more than 5 sentences. Cover: what the site is, who it's for, and its core value proposition.",
  "bullet_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
  "pros": ["Strength 1", "Strength 2", "Strength 3"],
  "cons": ["Weakness 1", "Weakness 2", "Weakness 3"],
  "insights": [
    "Advanced strategic observation 1",
    "Advanced strategic observation 2", 
    "Advanced strategic observation 3"
  ]
}}

Rules:
- bullet_points: exactly 5 items, each a single concise sentence
- pros / cons: 3–5 items each, short phrases
- insights: 3 items — go beyond surface observations (business model, positioning, monetization, growth signals)
- Return ONLY valid JSON. No markdown. No explanation outside the JSON.

WEBSITE CONTENT:
---
{content}
---"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze website content and output structured JSON."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--content", help="Website text to analyze (as a string)")
    group.add_argument("--content-file", help="Path to a text file containing website content")
    return parser.parse_args()


def load_content(args: argparse.Namespace) -> str:
    """Load content from CLI arg, file, or stdin."""
    if args.content:
        return args.content.strip()

    if args.content_file:
        try:
            with open(args.content_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError as exc:
            print(f"[generate_analysis] ERROR reading file: {exc}", file=sys.stderr)
            sys.exit(1)

    # Fall back to stdin
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    print(
        "[generate_analysis] ERROR: No content provided. "
        "Use --content, --content-file, or pipe from scrape_website.py",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    args    = parse_args()
    content = load_content(args)

    if not content:
        print("[generate_analysis] ERROR: Content is empty.", file=sys.stderr)
        sys.exit(1)

    # Apply head+tail truncation before sending to AI
    content = smart_truncate(content, max_chars=12_000)

    print(
        f"[generate_analysis] Sending {len(content)} chars to OpenAI ...",
        file=sys.stderr,
    )

    try:
        raw = chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(content)},
            ],
            max_tokens=2000,
            temperature=0.2,
            response_format="json_object",
        )

        result = parse_json_response(raw)

        # Validate required keys exist
        required_keys = {"summary", "bullet_points", "pros", "cons", "insights"}
        missing = required_keys - result.keys()
        if missing:
            raise RuntimeError(
                f"AI response missing required keys: {missing}. "
                f"Got: {list(result.keys())}"
            )

        print("[generate_analysis] Done.", file=sys.stderr)

        # ── OUTPUT: JSON to stdout ────────────────────────────────────
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except RuntimeError as exc:
        print(f"[generate_analysis] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
