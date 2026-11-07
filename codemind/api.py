"""FastAPI application for CodeMind AI – Phase 6."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from codemind.engine import ReviewEngine
from codemind.engine.feedback import FeedbackProcessor
from codemind.memory import MemoryManager
from codemind.schemas import (
    ReviewRequest, ReviewResponse,
    FeedbackRequest, FeedbackResponse,
    ConventionAddRequest, HealthResponse,
)
from codemind.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App Lifespan – initializes shared singletons once at startup
# ---------------------------------------------------------------------------
_engine: ReviewEngine | None = None
_feedback_processor: FeedbackProcessor | None = None
_memory: MemoryManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine, _feedback_processor, _memory
    logger.info("🚀 Starting CodeMind AI…")
    _engine = ReviewEngine()
    _feedback_processor = FeedbackProcessor()
    _memory = MemoryManager()
    yield
    logger.info("👋 CodeMind AI shutting down.")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CodeMind AI",
    description="Adaptive Code Review Agent powered by Vectorize Hindsight memory.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Check service health and connectivity."""
    settings = get_settings()
    alive = await _memory.ping()
    return HealthResponse(
        status="ok" if alive else "degraded",
        hindsight_connected=alive,
        groq_model=settings.groq_model,
        bank_id=settings.hindsight_bank_id,
    )


@app.post("/api/review", response_model=ReviewResponse, tags=["Review"])
async def review_code(request: ReviewRequest):
    """Review Python source code using AST analysis + Hindsight memory + LLM."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")
    return await _engine.review(request)


@app.post("/api/review/upload", response_model=ReviewResponse, tags=["Review"])
async def review_upload(file: UploadFile = File(...)):
    """Upload a .py file and get a full code review."""
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are accepted.")
    content = await file.read()
    try:
        code = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 encoded Python.")
    request = ReviewRequest(code=code, filename=file.filename)
    return await _engine.review(request)


@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(feedback: FeedbackRequest):
    """Submit Accept/Reject decision for a review suggestion.

    Stores the decision in Hindsight memory to shape future reviews.
    """
    return await _feedback_processor.process(feedback)


@app.post("/api/conventions", tags=["Memory"])
async def add_convention(request: ConventionAddRequest):
    """Manually add a team coding convention to Hindsight memory."""
    if not request.rule.strip():
        raise HTTPException(status_code=400, detail="Rule text cannot be empty.")
    await _memory.retain_custom_rule(rule_text=request.rule, author=request.author)
    return {"status": "ok", "message": f"Convention stored: '{request.rule[:80]}…'"}


@app.get("/api/memories", tags=["Memory"])
async def get_memories():
    """Retrieve current learned team conventions and guardrails."""
    conventions = await _memory.recall_conventions(
        code_context="coding standards conventions rules",
        max_tokens=3000,
    )
    guardrails = await _memory.recall_guardrails(max_tokens=2000)
    team_profile = await _memory.reflect_team_profile()
    history = await _memory.recall_review_history()
    return {
        "team_profile": team_profile,
        "conventions": conventions,
        "guardrails": guardrails,
        "review_history": history,
    }


@app.get("/api/history", tags=["Memory"])
async def get_review_history():
    """Return past review sessions from Hindsight memory."""
    history = await _memory.recall_review_history()
    return {"history": history, "count": len(history)}


# ---------------------------------------------------------------------------
# Serve static web UI (Phase 7)
# ---------------------------------------------------------------------------
import os
_static_dir = os.path.join(os.path.dirname(__file__), "web", "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_ui():
        return FileResponse(os.path.join(_static_dir, "index.html"))
