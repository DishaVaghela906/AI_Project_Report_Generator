"""
File Upload router.

Handles upload → text extraction → chunking → embedding storage pipeline.
Supports: PDF, DOCX, PPTX, source code, images.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from loguru import logger

from app.core.config import settings
from app.core.database import get_supabase
from app.models.schemas import MessageResponse, UploadedFileResponse
from app.services.document_processor import SUPPORTED_EXTENSIONS, process_file
from app.services.vector_store import add_chunks

router = APIRouter(prefix="/uploads", tags=["File Uploads"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD FILE
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{project_id}",
    response_model=UploadedFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(project_id: str, file: UploadFile = File(...)):
    """
    Upload a document / source-code file for a project.

    Pipeline:
    1. Validate file type and size.
    2. Save raw file to disk.
    3. Extract → clean → chunk text.
    4. Store chunks in ChromaDB (vector store).
    5. Record upload metadata in Supabase.
    """
    # ── Validate project exists ───────────────────────────────────────────────
    db = get_supabase()
    proj_result = db.table("projects").select("id").eq("id", project_id).execute()
    if not proj_result.data:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    # ── Validate file extension ───────────────────────────────────────────────
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. "
                   f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # ── Read & validate size ──────────────────────────────────────────────────
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB",
        )

    # ── Save to disk ──────────────────────────────────────────────────────────
    file_id = str(uuid.uuid4())
    project_dir = UPLOAD_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    saved_path = project_dir / f"{file_id}{ext}"
    saved_path.write_bytes(content)
    logger.info(f"Saved upload: {saved_path}")

    # ── Process & embed ───────────────────────────────────────────────────────
    db_status = "processing"
    chunks_stored = 0
    try:
        chunks = process_file(saved_path, content)
        chunks_stored = add_chunks(project_id, chunks, file.filename or saved_path.name)
        db_status = "ready"
    except Exception as exc:
        logger.error(f"Processing failed for {file.filename}: {exc}")
        db_status = "error"

    # ── Record in Supabase ────────────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": file_id,
        "project_id": project_id,
        "filename": file.filename,
        "file_type": ext.lstrip("."),
        "file_size": len(content),
        "saved_path": str(saved_path),
        "chunks_count": chunks_stored,
        "status": db_status,
        "created_at": now,
    }
    db.table("uploaded_files").insert(row).execute()

    logger.info(
        f"Upload recorded: '{file.filename}' → project '{project_id}' "
        f"[{chunks_stored} chunks, status={db_status}]"
    )
    return UploadedFileResponse(
        id=file_id,
        project_id=project_id,
        filename=file.filename or "",
        file_type=ext.lstrip("."),
        file_size=len(content),
        status=db_status,
        created_at=now,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LIST FILES
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}", response_model=list[UploadedFileResponse])
async def list_uploads(project_id: str):
    """List all uploaded files for a project."""
    db = get_supabase()
    result = (
        db.table("uploaded_files")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [
        UploadedFileResponse(
            id=r["id"],
            project_id=r["project_id"],
            filename=r["filename"],
            file_type=r["file_type"],
            file_size=r["file_size"],
            status=r["status"],
            created_at=r["created_at"],
        )
        for r in result.data
    ]


# ─────────────────────────────────────────────────────────────────────────────
# DELETE FILE
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{project_id}/{file_id}", response_model=MessageResponse)
async def delete_upload(project_id: str, file_id: str):
    """Delete an uploaded file record (does not remove its vectors — re-upload to refresh)."""
    db = get_supabase()
    result = (
        db.table("uploaded_files")
        .select("*")
        .eq("id", file_id)
        .eq("project_id", project_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="File not found")

    row = result.data[0]
    # Remove from disk
    saved = Path(row.get("saved_path", ""))
    if saved.exists():
        saved.unlink()

    db.table("uploaded_files").delete().eq("id", file_id).execute()
    return MessageResponse(message=f"File '{row['filename']}' deleted")
