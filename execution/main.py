"""
main.py — FastAPI application entry point for All-Seeing AI.

Responsibilities:
    - Create the FastAPI app instance
    - Configure CORS (allow frontend origin)
    - Mount all routes from routes.py
    - Provide root health check

Run the server:
    cd execution/
    uvicorn main:app --reload --port 8000

Docs are auto-generated at:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router

# ── App instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="All-Seeing AI API",
    description=(
        "Backend for All-Seeing AI — scrapes websites and provides "
        "AI-powered summaries, insights, and grounded Q&A."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allows the frontend (running from a file:// URL or localhost dev server)
# to call the API. Tighten allow_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(router)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check — confirms the server is running."""
    return {"status": "online", "service": "All-Seeing AI API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
