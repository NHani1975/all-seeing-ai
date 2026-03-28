# All-Seeing AI 👁️

> **Understand any website instantly — powered by AI.**

All-Seeing AI is a full-stack AI application that lets you paste any website URL and immediately receive a deep, structured analysis. It scrapes the site, processes the content through a large language model, and returns a rich intelligence report — all in seconds.

---

## What It Does

| Feature | Description |
|---|---|
| 🔍 **Instant Scraping** | Fetches and cleans any public website's content |
| 📄 **Structured Summary** | 5-sentence overview, key bullet points, pros & cons |
| 💡 **AI Insights** | Business ideas, improvement suggestions, strategic takeaways |
| 💬 **Intel Chat** | Ask follow-up questions — answers grounded strictly in the page content |

---

## Tech Stack

**Frontend:** Vanilla HTML / CSS / JavaScript — cyber-intelligence terminal aesthetic with glassmorphism, animated neural canvas, and real-time loading steps.

**Backend:** Python + FastAPI — modular execution scripts following single-responsibility principles.

**AI:** [Groq](https://console.groq.com) (free tier) running **Llama 3.3 70B** — 14,400 requests/day at no cost.

---

## Architecture

Built on a strict **3-layer agent architecture**:

```
Layer 1 — Directives   directives/        Natural-language SOPs (what to do)
Layer 2 — Orchestration  (FastAPI + LLM)  Decision-making and routing
Layer 3 — Execution    execution/         Deterministic Python scripts (how to do it)
```

```
All-Seeing/
├── frontend/               # UI (index.html, style.css, app.js)
├── execution/
│   ├── main.py             # FastAPI app entry point
│   ├── routes.py           # API routes: /api/analyze, /api/chat
│   ├── utils_ai.py         # Groq/LLM wrapper
│   ├── utils_scraper.py    # Web scraping + text cleaning
│   ├── scrape_website.py   # CLI scraper
│   ├── generate_analysis.py# CLI analyzer
│   ├── generate_chat_reply.py # CLI chat
│   └── requirements.txt
├── directives/             # SOPs
├── .env                    # API keys (gitignored)
└── .tmp/                   # Intermediate files (gitignored)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r execution/requirements.txt

# 2. Add your Groq API key to .env
# Get a free key at: https://console.groq.com
GROQ_API_KEY=your_key_here

# 3. Start the backend
cd execution
python -m uvicorn main:app --reload --port 8000

# 4. Open the frontend
# Double-click frontend/index.html in your browser
```

API docs available at **http://127.0.0.1:8000/docs**

---

## Key Design Principles

- **Single responsibility** — each script does exactly one thing
- **Loud failures** — errors are explicit, never silently swallowed
- **Grounded AI** — chat answers are strictly limited to scraped content (no hallucination)
- **Head + tail truncation** — long pages preserve opening context AND closing content
