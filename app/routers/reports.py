"""
Report Export router.

Assembles all generated chapters into a final PDF or DOCX document.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from app.core.database import get_supabase
from app.models.schemas import ExportFormat, ReportExportRequest, ReportExportResponse
from app.services.report_exporter import export_to_docx, export_to_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/export", response_model=ReportExportResponse)
async def export_report(payload: ReportExportRequest):
    """
    Export the final project report in PDF or DOCX format.

    All chapters with status 'done' are included (or only those specified
    in include_chapters).
    """
    db = get_supabase()

    # ── Fetch project ─────────────────────────────────────────────────────────
    proj_res = db.table("projects").select("*").eq("id", payload.project_id).execute()
    if not proj_res.data:
        raise HTTPException(status_code=404, detail=f"Project '{payload.project_id}' not found")
    project = proj_res.data[0]

    # ── Fetch chapters ────────────────────────────────────────────────────────
    chap_res = (
        db.table("chapters")
        .select("*")
        .eq("project_id", payload.project_id)
        .eq("status", "done")
        .order("chapter_number")
        .execute()
    )

    if not chap_res.data:
        raise HTTPException(
            status_code=400,
            detail="No completed chapters found. Generate chapters before exporting.",
        )

    chapters = chap_res.data

    # ── Export ────────────────────────────────────────────────────────────────
    try:
        if payload.format == ExportFormat.PDF:
            out_path: Path = export_to_pdf(
                project=project,
                chapters=chapters,
                include_chapters=payload.include_chapters,
                cover_page=payload.cover_page,
            )
        else:
            out_path = export_to_docx(
                project=project,
                chapters=chapters,
                include_chapters=payload.include_chapters,
                cover_page=payload.cover_page,
            )
    except Exception as exc:
        logger.error(f"Export failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

    download_url = f"/reports/download/{out_path.name}"

    return ReportExportResponse(
        download_url=download_url,
        format=payload.format,
        filename=out_path.name,
        generated_at=datetime.now(timezone.utc),
    )


@router.post("/export/pdf", response_model=ReportExportResponse)
async def export_pdf_report(payload: dict):
    project_id = payload.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    req = ReportExportRequest(project_id=project_id, format=ExportFormat.PDF)
    return await export_report(req)


@router.post("/export/docx", response_model=ReportExportResponse)
async def export_docx_report(payload: dict):
    project_id = payload.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    req = ReportExportRequest(project_id=project_id, format=ExportFormat.DOCX)
    return await export_report(req)


@router.get("/download/{filename}")
async def download_report(filename: str):
    """Download a previously exported report file."""
    # Resolve path safely (prevent path traversal)
    from app.core.config import settings
    exports_dir = Path(settings.UPLOAD_DIR).parent / "exports"
    file_path = (exports_dir / filename).resolve()

    if not str(file_path).startswith(str(exports_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found. Please export again.")

    media_type = (
        "application/pdf" if filename.endswith(".pdf")
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
    )
