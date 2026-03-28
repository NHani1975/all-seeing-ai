"""
generate_chat_reply.py — Grounded Q&A: answer questions from website content only.

Single responsibility: given a user question and website content, produce
a factual answer grounded strictly in the provided content.

Hallucination prevention:
    The system prompt explicitly instructs the model to ONLY use the provided
    content. If the answer cannot be found, the model must respond with a
    specific not-found message instead of guessing.

Usage (CLI):
    python generate_chat_reply.py --question "Who is this for?" --content "..."
    python generate_chat_reply.py --question "What is pricing?" --content-file page.txt

Output:
    Prints plain-text answer to stdout.
    On failure, prints error to stderr and exits with code 1.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils_ai import chat_completion
from utils_scraper import smart_truncate


# ── Hallucination-prevention prompt ──────────────────────────────────────────
SYSTEM_PROMPT = """You are a precise research assistant. Your job is to answer questions
based ONLY on the website content provided by the user.

STRICT RULES:
1. Use ONLY information that is explicitly present in the provided content.
2. Do NOT guess, infer, or use outside knowledge.
3. If the answer cannot be found in the content, respond EXACTLY with:
   "I cannot find this information in the provided content."
4. Keep answers concise (2–5 sentences max unless a list is clearly better).
5. Be direct and factual. Do not add caveats or speculation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Answer a question grounded strictly in provided website content."
    )
    parser.add_argument(
        "--question",
        required=True,
        help="The question to answer.",
    )

    content_group = parser.add_mutually_exclusive_group()
    content_group.add_argument(
        "--content",
        help="Website text content (as a string).",
    )
    content_group.add_argument(
        "--content-file",
        help="Path to a file containing website content.",
    )
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
            print(f"[generate_chat_reply] ERROR reading file: {exc}", file=sys.stderr)
            sys.exit(1)

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    print(
        "[generate_chat_reply] ERROR: No content provided. "
        "Use --content, --content-file, or pipe content via stdin.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    args     = parse_args()
    question = args.question.strip()

    if not question:
        print("[generate_chat_reply] ERROR: --question cannot be empty.", file=sys.stderr)
        sys.exit(1)

    content = load_content(args)

    if not content:
        print("[generate_chat_reply] ERROR: Content is empty.", file=sys.stderr)
        sys.exit(1)

    # Truncate content — preserve head + tail to stay within token limits
    content = smart_truncate(content, max_chars=10_000)

    user_message = f"""WEBSITE CONTENT:
---
{content}
---

QUESTION: {question}"""

    print(
        f"[generate_chat_reply] Sending question to OpenAI ({len(content)} chars context) ...",
        file=sys.stderr,
    )

    try:
        answer = chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=600,
            temperature=0.1,   # Very low temperature for factual grounding
        )

        print("[generate_chat_reply] Done.", file=sys.stderr)

        # ── OUTPUT: answer to stdout ──────────────────────────────────
        print(answer)

    except RuntimeError as exc:
        print(f"[generate_chat_reply] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
