"""
FastAPI application factory.
"""
from __future__ import annotations

import os
# Force transformers / sentence-transformers to use PyTorch (avoids Keras 3 conflict on Windows)
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.routers import auth, chapters, projects, reports, uploads


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks and cleanup on shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Ensure storage directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.DIAGRAMS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    (Path(settings.UPLOAD_DIR).parent / "exports").mkdir(parents=True, exist_ok=True)

    # Check LLM availability at startup
    from app.services.llm_service import check_llm_health
    llm_health = await check_llm_health()
    if llm_health.get("ready"):
        logger.success(f"✓ LLM Provider '{llm_health['provider']}' is ready — model: {llm_health['model']}")
    else:
        logger.warning(
            f"⚠ LLM Provider '{llm_health.get('provider')}' not ready: "
            f"{llm_health.get('message')}"
        )

    yield  # Application is running

    logger.info("Shutting down...")


# ─────────────────────────────────────────────────────────────────────────────
# App instance
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-Powered Project Report Generator Backend. "
        "Supports Groq, Hugging Face, OpenRouter, and Ollama with RAG (ChromaDB) and Supabase storage."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_api_requests(request: Request, call_next):
    """Log all incoming frontend API requests and response status codes."""
    start_time = time.time()
    method = request.method
    path = request.url.path

    # Log incoming request
    if path.startswith("/api/"):
        logger.info(f"➡️  Incoming API: {method} {path}")

    response = await call_next(request)
    elapsed_ms = (time.time() - start_time) * 1000

    if path.startswith("/api/"):
        status = response.status_code
        if status >= 400:
            logger.error(f"❌ API {method} {path} → {status} ({elapsed_ms:.1f}ms)")
        else:
            logger.success(f"✓ API {method} {path} → {status} ({elapsed_ms:.1f}ms)")

    return response

# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(chapters.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


from fastapi.responses import FileResponse
from app.services.diagram_service import get_diagram_path

@app.get("/api/v1/diagrams/{project_id}/{filename}", tags=["Diagrams"])
async def get_diagram_file_main(project_id: str, filename: str):
    path = get_diagram_path(project_id, filename)
    if not path or not path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Diagram image not found")
    return FileResponse(str(path), media_type="image/png")


# ─────────────────────────────────────────────────────────────────────────────
# Health / Root
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/info", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    from app.services.llm_service import check_llm_health
    llm_health = await check_llm_health()
    return {
        "status": "healthy",
        "llm": llm_health,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Static Frontend Mount
# ─────────────────────────────────────────────────────────────────────────────

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
frontend_dir = Path(__file__).parent.parent / "frontend"

if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
elif frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
