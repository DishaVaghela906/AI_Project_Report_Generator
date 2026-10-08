"""
Basic smoke tests for the API.

Run with:  pytest tests/ -v
Requires:  SUPABASE_URL and SUPABASE_KEY set in .env (or environment).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

def test_root():
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "llm" in data or "ollama" in data


# ─────────────────────────────────────────────────────────────────────────────
# Projects CRUD
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_PROJECT = {
    "title": "Test Project",
    "domain": "Web",
    "category": "Application or System Development",
    "problem_statement": "Students need help generating reports.",
    "objectives": ["Automate report writing", "Reduce documentation time"],
    "tech_stack": ["Python", "FastAPI", "Supabase"],
    "modules": ["User Auth", "Report Generator", "Export"],
    "methodology": "Agile",
    "sdlc_model": "Agile",
    "database_used": "Supabase PostgreSQL",
    "institution": "Test University",
    "department": "Computer Science",
    "academic_year": "2024-25",
}


@pytest.fixture
def created_project_id():
    """Create a project and return its ID. Clean up after test."""
    response = client.post("/api/v1/projects/", json=SAMPLE_PROJECT)
    assert response.status_code == 201
    project_id = response.json()["id"]
    yield project_id
    # Cleanup
    client.delete(f"/api/v1/projects/{project_id}")


def test_create_project():
    response = client.post("/api/v1/projects/", json=SAMPLE_PROJECT)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == SAMPLE_PROJECT["title"]
    assert "id" in data
    # Cleanup
    client.delete(f"/api/v1/projects/{data['id']}")


def test_list_projects():
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_project(created_project_id):
    response = client.get(f"/api/v1/projects/{created_project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == created_project_id


def test_get_project_not_found():
    response = client.get("/api/v1/projects/non-existent-id")
    assert response.status_code == 404


def test_update_project(created_project_id):
    response = client.patch(
        f"/api/v1/projects/{created_project_id}",
        json={"title": "Updated Test Project"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Test Project"


# ─────────────────────────────────────────────────────────────────────────────
# Chapters
# ─────────────────────────────────────────────────────────────────────────────

def test_list_chapters_empty(created_project_id):
    response = client.get(f"/api/v1/chapters/{created_project_id}")
    assert response.status_code == 200
    assert response.json() == []


def test_get_chapter_not_found(created_project_id):
    response = client.get(f"/api/v1/chapters/{created_project_id}/1")
    assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Builder (unit test)
# ─────────────────────────────────────────────────────────────────────────────

def test_prompt_builder():
    from app.services.prompt_builder import build_prompt

    project = {
        "title": "Test Project",
        "domain": "Web",
        "category": "Application or System Development",
        "problem_statement": "Students need help.",
        "objectives": ["Automate"],
        "tech_stack": ["Python"],
        "modules": ["Auth"],
        "methodology": "Agile",
        "sdlc_model": "Agile",
        "database_used": "PostgreSQL",
        "team_members": [],
        "guide_name": None,
        "institution": "Test U",
        "department": "CS",
        "academic_year": "2024",
        "existing_system": None,
        "proposed_system": None,
        "unique_features": [],
        "implementation_details": None,
        "testing_details": None,
        "results": None,
        "future_scope": None,
    }

    prompt = build_prompt(1, project, context_chunks=["Sample context chunk"])
    assert "Chapter 1" in prompt
    assert "Introduction" in prompt
    assert "Sample context chunk" in prompt
    assert "Test Project" in prompt
