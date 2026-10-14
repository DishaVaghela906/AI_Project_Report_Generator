"""
Chapters router.

Endpoints:
  POST   /chapters/generate          — Generate a chapter with AI
  GET    /chapters/{project_id}       — Get all chapters for a project
  GET    /chapters/{project_id}/{n}   — Get a specific chapter
  PATCH  /chapters/{project_id}/{n}   — Edit / save chapter content
  DELETE /chapters/{project_id}/{n}   — Reset / delete a chapter

Also provides:
  GET  /chapters/{project_id}/{n}/stream  — SSE streaming generation
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger

from app.core.database import get_supabase
from app.models.schemas import (
    ChapterGenerateRequest,
    ChapterResponse,
    ChapterStatus,
    ChapterUpdateRequest,
    DiagramGenerateRequest,
    DiagramGenerateResponse,
    MessageResponse,
)
from app.services.diagram_service import (
    ensure_chapter_diagrams,
    generate_diagram_image,
    get_diagram_path,
)
from app.services.llm_service import generate_chapter, stream_chapter
from app.services.prompt_builder import CHAPTER_METADATA, build_prompt, get_chapter_title
from app.services.vector_store import retrieve_context

router = APIRouter(prefix="/chapters", tags=["Chapters"])


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE (blocking)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def generate(payload: ChapterGenerateRequest):
    """
    Generate a chapter using AI.

    Flow:
    1. Fetch project details from Supabase.
    2. Retrieve relevant context from ChromaDB (RAG).
    3. Build a structured prompt.
    4. Call Ollama (Qwen3-8B) with the chapter-specific API key.
    5. Save the generated content to Supabase.
    """
    db = get_supabase()

    # ── Fetch project ─────────────────────────────────────────────────────────
    proj_res = db.table("projects").select("*").eq("id", payload.project_id).execute()
    if not proj_res.data:
        raise HTTPException(status_code=404, detail=f"Project '{payload.project_id}' not found")
    project = proj_res.data[0]

    # ── RAG: retrieve context ─────────────────────────────────────────────────
    chapter_title = get_chapter_title(payload.chapter_number)
    query = f"Chapter {payload.chapter_number} {chapter_title} {project['title']}"
    context_chunks = retrieve_context(payload.project_id, query, top_k=6)

    # ── Build prompt ──────────────────────────────────────────────────────────
    prompt = build_prompt(
        chapter_number=payload.chapter_number,
        project=project,
        context_chunks=context_chunks,
        extra_instructions=payload.extra_instructions,
    )

    # ── Mark as generating in DB ──────────────────────────────────────────────
    existing = _get_chapter_row(payload.project_id, payload.chapter_number)
    chap_id = existing["id"] if existing else str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    if existing:
        db.table("chapters").update({"status": ChapterStatus.GENERATING.value, "updated_at": now}) \
            .eq("id", chap_id).execute()
    else:
        db.table("chapters").insert({
            "id": chap_id,
            "project_id": payload.project_id,
            "chapter_number": payload.chapter_number,
            "chapter_title": chapter_title,
            "content": "",
            "status": ChapterStatus.GENERATING.value,
            "created_at": now,
            "updated_at": now,
        }).execute()

    # ── Generate ──────────────────────────────────────────────────────────────
    try:
        content = await generate_chapter(payload.chapter_number, prompt)
        # Generate & embed accurate diagrams (via Hugging Face or technical renderer)
        content = await ensure_chapter_diagrams(payload.project_id, payload.chapter_number, content, project)
        final_status = ChapterStatus.DONE.value
    except Exception as exc:
        logger.error(f"Chapter {payload.chapter_number} generation failed: {exc}")
        content = ""
        final_status = ChapterStatus.ERROR.value

    # ── Save result ───────────────────────────────────────────────────────────
    generated_at = datetime.now(timezone.utc).isoformat()
    db.table("chapters").update({
        "content": content,
        "status": final_status,
        "generated_at": generated_at,
        "updated_at": generated_at,
    }).eq("id", chap_id).execute()

    if final_status == ChapterStatus.ERROR.value:
        raise HTTPException(status_code=500, detail="Chapter generation failed. Check Ollama logs.")

    return ChapterResponse(
        id=chap_id,
        project_id=payload.project_id,
        chapter_number=payload.chapter_number,
        chapter_title=chapter_title,
        content=content,
        status=ChapterStatus.DONE,
        generated_at=generated_at,
        updated_at=generated_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# STREAM GENERATE (SSE)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/{chapter_number}/stream")
async def stream_generate(project_id: str, chapter_number: int):
    """
    Stream chapter generation via Server-Sent Events.
    Connect to this endpoint and receive tokens as they are generated.
    """
    db = get_supabase()

    proj_res = db.table("projects").select("*").eq("id", project_id).execute()
    if not proj_res.data:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    project = proj_res.data[0]

    chapter_title = get_chapter_title(chapter_number)
    query = f"Chapter {chapter_number} {chapter_title} {project['title']}"
    context_chunks = retrieve_context(project_id, query, top_k=6)
    prompt = build_prompt(
        chapter_number=chapter_number,
        project=project,
        context_chunks=context_chunks,
    )

    async def event_generator():
        full_text = []
        async for token in stream_chapter(chapter_number, prompt):
            full_text.append(token)
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

        # Persist after streaming completes
        content = "".join(full_text)
        try:
            content = await ensure_chapter_diagrams(project_id, chapter_number, content, project)
        except Exception as e:
            logger.warning(f"Error ensuring chapter diagrams during stream: {e}")

        now = datetime.now(timezone.utc).isoformat()
        existing = _get_chapter_row(project_id, chapter_number)
        if existing:
            db.table("chapters").update({
                "content": content,
                "status": ChapterStatus.DONE.value,
                "generated_at": now,
                "updated_at": now,
            }).eq("id", existing["id"]).execute()
        else:
            db.table("chapters").insert({
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "content": content,
                "status": ChapterStatus.DONE.value,
                "generated_at": now,
                "created_at": now,
                "updated_at": now,
            }).execute()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAMS GENERATION & RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{project_id}/generate-diagram", response_model=DiagramGenerateResponse)
async def generate_diagram_for_project(project_id: str, payload: DiagramGenerateRequest):
    """
    Generates a technical diagram (ER diagram, architecture diagram, flowchart, etc.)
    using Hugging Face Text-to-Image inference (with automatic technical fallback).
    Optionally embeds the diagram into the associated chapter markdown.
    """
    db = get_supabase()
    proj_res = db.table("projects").select("*").eq("id", project_id).execute()
    if not proj_res.data:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    project = proj_res.data[0]

    prompt = payload.prompt or f"{payload.diagram_type.replace('_', ' ').title()} for {project['title']}"
    url, _ = await generate_diagram_image(
        project_id=project_id,
        diagram_type=payload.diagram_type,
        prompt=prompt,
        title=project["title"],
        context_meta=project
    )

    # Optionally embed into chapter markdown if requested
    if payload.embed_in_chapter and payload.chapter_number:
        row = _get_chapter_row(project_id, payload.chapter_number)
        if row and row.get("content"):
            tag = f"\n\n![Figure {payload.chapter_number}: {payload.diagram_type.replace('_', ' ').title()}]({url})\n\n"
            if url not in row["content"]:
                new_content = row["content"] + tag
                now = datetime.now(timezone.utc).isoformat()
                db.table("chapters").update({"content": new_content, "updated_at": now}).eq("id", row["id"]).execute()

    return DiagramGenerateResponse(
        diagram_url=url,
        diagram_type=payload.diagram_type,
        message=f"Diagram '{payload.diagram_type}' generated successfully via Hugging Face/internal renderer."
    )


@router.get("/diagrams/{project_id}/{filename}")
async def serve_diagram_file(project_id: str, filename: str):
    """Serves generated technical diagram image."""
    path = get_diagram_path(project_id, filename)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Diagram image not found")
    return FileResponse(str(path), media_type="image/png")


# ─────────────────────────────────────────────────────────────────────────────
# LIST CHAPTERS FOR PROJECT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}", response_model=list[ChapterResponse])
async def list_chapters(project_id: str):
    """Get all generated chapters for a project."""
    db = get_supabase()
    result = (
        db.table("chapters")
        .select("*")
        .eq("project_id", project_id)
        .order("chapter_number")
        .execute()
    )
    return [_map_chapter(r) for r in result.data]


# ─────────────────────────────────────────────────────────────────────────────
# GET SINGLE CHAPTER
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/{chapter_number}", response_model=ChapterResponse)
async def get_chapter(project_id: str, chapter_number: int):
    """Get a specific chapter."""
    row = _get_chapter_row(project_id, chapter_number)
    if not row:
        raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} not yet generated")
    return _map_chapter(row)


# ─────────────────────────────────────────────────────────────────────────────
# EDIT CHAPTER
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/{project_id}/{chapter_number}", response_model=ChapterResponse)
async def update_chapter(project_id: str, chapter_number: int, payload: ChapterUpdateRequest):
    """Save manually edited chapter content."""
    db = get_supabase()
    row = _get_chapter_row(project_id, chapter_number)
    if not row:
        raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} not found")

    now = datetime.now(timezone.utc).isoformat()
    db.table("chapters").update({
        "content": payload.content,
        "status": ChapterStatus.DONE.value,
        "updated_at": now,
    }).eq("id", row["id"]).execute()

    row["content"] = payload.content
    row["updated_at"] = now
    return _map_chapter(row)


# ─────────────────────────────────────────────────────────────────────────────
# DELETE / RESET CHAPTER
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{project_id}/{chapter_number}", response_model=MessageResponse)
async def delete_chapter(project_id: str, chapter_number: int):
    """Delete/reset a chapter so it can be regenerated."""
    db = get_supabase()
    row = _get_chapter_row(project_id, chapter_number)
    if not row:
        raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} not found")

    db.table("chapters").delete().eq("id", row["id"]).execute()
    return MessageResponse(message=f"Chapter {chapter_number} deleted. Regenerate when ready.")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_chapter_row(project_id: str, chapter_number: int) -> dict | None:
    db = get_supabase()
    result = (
        db.table("chapters")
        .select("*")
        .eq("project_id", project_id)
        .eq("chapter_number", chapter_number)
        .execute()
    )
    return result.data[0] if result.data else None


def _map_chapter(row: dict) -> ChapterResponse:
    return ChapterResponse(
        id=row["id"],
        project_id=row["project_id"],
        chapter_number=row["chapter_number"],
        chapter_title=row["chapter_title"],
        content=row.get("content", ""),
        status=ChapterStatus(row["status"]),
        generated_at=row.get("generated_at"),
        updated_at=row.get("updated_at"),
    )
