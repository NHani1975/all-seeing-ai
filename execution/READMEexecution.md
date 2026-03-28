# Execution

This folder contains **deterministic Python scripts** — the reliable, testable workhorses of the system.

## Principles

- Each script does **one thing well** (single responsibility)
- Scripts are **self-contained**: they read from `.env` for secrets and accept CLI args or stdin for dynamic inputs
- Scripts **never guess** — they fail loudly with clear error messages
- Scripts are **well-commented** so the orchestration layer understands what they do

## Convention

| Prefix | Purpose |
|--------|---------|
| `scrape_` | Web scraping and data extraction |
| `enrich_` | Data enrichment via APIs |
| `export_` | Writing outputs (Google Sheets, files, etc.) |
| `generate_` | Generating content or reports |
| `utils_` | Shared helpers (auth, logging, etc.) |

## Environment

Secrets and config live in **`.env`** at the project root. Use `python-dotenv` to load them:

```python
from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY=("your_api_key_here")
