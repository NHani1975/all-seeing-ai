"""
scrape_website.py — CLI scraper: URL → clean plain text.

Single responsibility: accept a URL, scrape it, clean it, print the result.
This script is the sole entry point for all web scraping in the pipeline.

Usage (CLI):
    python scrape_website.py --url https://stripe.com

Output:
    Prints clean plain text to stdout.
    On success, exits with code 0.
    On failure, prints an error message to stderr and exits with code 1.

Pipe into analysis:
    python scrape_website.py --url https://stripe.com | python generate_analysis.py
"""

import argparse
import sys

# Add parent dir to path so sibling util modules resolve correctly
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils_scraper import fetch_page, clean_html, smart_truncate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a website and output clean plain text."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Full URL to scrape (must include http:// or https://)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=12_000,
        help="Maximum characters to output (default: 12000, uses head+tail strategy)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url  = args.url.strip()

    # Normalize: add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        print(f"[scrape_website] Fetching: {url}", file=sys.stderr)
        html = fetch_page(url)

        print("[scrape_website] Cleaning HTML ...", file=sys.stderr)
        text = clean_html(html)

        original_len = len(text)
        text = smart_truncate(text, max_chars=args.max_chars)

        if len(text) < original_len:
            print(
                f"[scrape_website] Content truncated: {original_len} → {len(text)} chars "
                f"(head+tail strategy)",
                file=sys.stderr,
            )

        print(f"[scrape_website] Done. {len(text)} chars extracted.", file=sys.stderr)

        # ── OUTPUT: clean text to stdout ──────────────────────────────
        print(text)

    except (ValueError, RuntimeError) as exc:
        print(f"[scrape_website] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
