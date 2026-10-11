"""
Projects router — CRUD for project information.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.auth import get_current_user_optional
from app.core.database import get_supabase
from app.models.schemas import (
    MessageResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.vector_store import delete_project_vectors

router = APIRouter(prefix="/projects", tags=["Projects"])


# ─────────────────────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateRequest,
    current_user: dict | None = Depends(get_current_user_optional)
):
    """Create a new project with all its details."""
    db = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    user_id = current_user.get("sub") if current_user else None

    row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": payload.title,
        "domain": payload.domain,
        "category": payload.category.value,
        "problem_statement": payload.problem_statement,
        "objectives": payload.objectives,
        "tech_stack": payload.tech_stack,
        "modules": payload.modules,
        "methodology": payload.methodology,
        "sdlc_model": payload.sdlc_model.value,
        "database_used": payload.database_used,
        "team_members": [m.model_dump() for m in payload.team_members],
        "guide_name": payload.guide_name,
        "institution": payload.institution,
        "department": payload.department,
        "academic_year": payload.academic_year,
        "existing_system": payload.existing_system,
        "proposed_system": payload.proposed_system,
        "unique_features": payload.unique_features,
        "implementation_details": payload.implementation_details,
        "testing_details": payload.testing_details,
        "results": payload.results,
        "future_scope": payload.future_scope,
        "created_at": now,
        "updated_at": now,
    }

    result = db.table("projects").insert(row).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create project in database")

    logger.info(f"Project created: {row['id']} — '{payload.title}'")
    return _map_project(result.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# READ ALL
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(current_user: dict | None = Depends(get_current_user_optional)):
    """List all projects (ordered by most recent)."""
    db = get_supabase()
    query = db.table("projects").select("*")
    if current_user and current_user.get("sub"):
        query = query.eq("user_id", current_user["sub"])
    result = query.order("created_at", desc=True).execute()
    return [_map_project(r) for r in result.data]


# ─────────────────────────────────────────────────────────────────────────────
# READ ONE
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a single project by ID."""
    project = _fetch_project_or_404(project_id)
    return _map_project(project)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, payload: ProjectUpdateRequest):
    """Partially update project fields."""
    _fetch_project_or_404(project_id)   # verify exists

    db = get_supabase()
    updates = payload.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    # Serialise enums
    if "category" in updates:
        updates["category"] = updates["category"].value
    if "sdlc_model" in updates:
        updates["sdlc_model"] = updates["sdlc_model"].value
    if "team_members" in updates:
        updates["team_members"] = [m.model_dump() for m in payload.team_members]

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = db.table("projects").update(updates).eq("id", project_id).execute()
    return _map_project(result.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(project_id: str):
    """Delete a project and its associated vectors."""
    _fetch_project_or_404(project_id)

    db = get_supabase()
    db.table("projects").delete().eq("id", project_id).execute()

    # Clean up vector store
    delete_project_vectors(project_id)

    logger.info(f"Project deleted: {project_id}")
    return MessageResponse(message=f"Project '{project_id}' deleted successfully")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_project_or_404(project_id: str) -> dict:
    db = get_supabase()
    try:
        result = db.table("projects").select("*").eq("id", project_id).execute()
    except Exception:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return result.data[0]


def _map_project(row: dict) -> ProjectResponse:
    return ProjectResponse(
        id=row["id"],
        title=row["title"],
        domain=row["domain"],
        category=row["category"],
        problem_statement=row["problem_statement"],
        objectives=row.get("objectives") or [],
        tech_stack=row.get("tech_stack") or [],
        modules=row.get("modules") or [],
        methodology=row["methodology"],
        sdlc_model=row["sdlc_model"],
        database_used=row.get("database_used"),
        team_members=row.get("team_members") or [],
        guide_name=row.get("guide_name"),
        institution=row.get("institution"),
        department=row.get("department"),
        academic_year=row.get("academic_year"),
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
    )
