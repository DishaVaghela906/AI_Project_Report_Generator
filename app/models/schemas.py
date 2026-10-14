"""
Pydantic models (schemas) for all API request / response payloads.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class ProjectCategory(str, Enum):
    APPLICATION = "Application or System Development"
    INTERNET_BASED = "Internet Based"
    RESEARCH = "Research Based"
    RESEARCH_PROJECT = "Research Project"
    DATA_SCIENCE_ML = "Data Science & ML"
    EMBEDDED_IOT = "Embedded Systems / IoT"
    INDUSTRY_AUTOMATION = "Industry Automation"
    NETWORK_ADMIN = "Network or System Administration"


class ChapterStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    DONE = "done"
    ERROR = "error"


class ExportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


class SDLCModel(str, Enum):
    WATERFALL = "Waterfall"
    AGILE = "Agile"
    SPIRAL = "Spiral"
    PROTOTYPE = "Prototype"
    INCREMENTAL = "Incremental"
    RAD = "RAD"


# ─────────────────────────────────────────────────────────────────────────────
# Project
# ─────────────────────────────────────────────────────────────────────────────

class TeamMember(BaseModel):
    name: str
    role: str
    enrollment_no: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    domain: str = Field(..., description="e.g. Web, ML, IoT, Networking")
    category: ProjectCategory
    problem_statement: str
    objectives: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list, description="Languages, frameworks, tools")
    modules: list[str] = Field(default_factory=list, description="Major modules of the project")
    methodology: str = Field(default="Agile Iterative Development", description="Approach taken, e.g. Agile, Waterfall")
    sdlc_model: SDLCModel = SDLCModel.AGILE
    database_used: Optional[str] = None
    team_members: list[TeamMember] = []
    guide_name: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    existing_system: Optional[str] = None
    proposed_system: Optional[str] = None
    unique_features: Optional[list[str]] = None
    implementation_details: Optional[str] = None
    testing_details: Optional[str] = None
    results: Optional[str] = None
    future_scope: Optional[str] = None
    github_url: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    domain: str
    category: ProjectCategory
    problem_statement: str
    objectives: list[str]
    tech_stack: list[str]
    modules: list[str]
    methodology: str
    sdlc_model: SDLCModel
    database_used: Optional[str]
    team_members: list[TeamMember]
    guide_name: Optional[str]
    institution: Optional[str]
    department: Optional[str]
    academic_year: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    github_url: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[ProjectCategory] = None
    problem_statement: Optional[str] = None
    objectives: Optional[list[str]] = None
    tech_stack: Optional[list[str]] = None
    modules: Optional[list[str]] = None
    methodology: Optional[str] = None
    sdlc_model: Optional[SDLCModel] = None
    database_used: Optional[str] = None
    team_members: Optional[list[TeamMember]] = None
    guide_name: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    existing_system: Optional[str] = None
    proposed_system: Optional[str] = None
    unique_features: Optional[list[str]] = None
    implementation_details: Optional[str] = None
    testing_details: Optional[str] = None
    results: Optional[str] = None
    future_scope: Optional[str] = None
    github_url: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Import & Analysis
# ─────────────────────────────────────────────────────────────────────────────

class GitHubAnalyzeRequest(BaseModel):
    url: Optional[str] = Field(None, description="GitHub repository or branch URL, e.g. https://github.com/owner/repo")
    github_url: Optional[str] = Field(None, description="Alternative alias for repository URL")
    branch: Optional[str] = Field(None, description="Optional branch name")

    @property
    def target_url(self) -> str:
        res = self.url or self.github_url
        if not res:
            raise ValueError("Either 'url' or 'github_url' must be provided")
        return res


class GitHubAnalyzeResponse(BaseModel):
    github_url: str
    owner: str
    repo: str
    title: str
    domain: str
    category: str
    problem_statement: str
    tech_stack: list[str]
    modules: list[str]
    database_used: Optional[str] = None
    methodology: str = "Agile Iterative Development"
    existing_system: Optional[str] = None
    proposed_system: Optional[str] = None
    unique_features: list[str] = []
    architecture_summary: Optional[str] = None


class GitHubImportToProjectRequest(BaseModel):
    github_url: str = Field(..., description="GitHub repository URL")
    branch: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# File Upload
# ─────────────────────────────────────────────────────────────────────────────

class UploadedFileResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_type: str
    file_size: int
    status: str   # "processing" | "ready" | "error"
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Chapter Generation
# ─────────────────────────────────────────────────────────────────────────────

class ChapterGenerateRequest(BaseModel):
    project_id: str
    chapter_number: int = Field(..., ge=1, le=6)
    extra_instructions: Optional[str] = Field(
        None,
        description="Any specific guidance for this chapter (e.g. 'focus on the ML pipeline')",
    )


class ChapterUpdateRequest(BaseModel):
    content: str = Field(..., description="Edited chapter content in markdown")


class ChapterResponse(BaseModel):
    id: str
    project_id: str
    chapter_number: int
    chapter_title: str
    content: str
    status: ChapterStatus
    generated_at: Optional[datetime]
    updated_at: Optional[datetime]


class DiagramGenerateRequest(BaseModel):
    diagram_type: str = Field("ch3_architecture_diagram", description="Type of diagram: ch3_architecture_diagram, ch3_er_diagram, flowchart, sdlc")
    prompt: Optional[str] = Field(None, description="Custom prompt description for diagram generation")
    chapter_number: Optional[int] = Field(3, description="Associated chapter number to embed into")
    embed_in_chapter: bool = Field(True, description="Whether to automatically embed diagram tag into chapter markdown")


class DiagramGenerateResponse(BaseModel):
    diagram_url: str
    diagram_type: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Report Export
# ─────────────────────────────────────────────────────────────────────────────

class ReportExportRequest(BaseModel):
    project_id: str
    format: ExportFormat = ExportFormat.PDF
    include_chapters: Optional[list[int]] = Field(
        None,
        description="Which chapters to include (1-6). None = all chapters.",
    )
    cover_page: bool = True


class ReportExportResponse(BaseModel):
    download_url: str
    format: ExportFormat
    filename: str
    generated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# User Authentication
# ─────────────────────────────────────────────────────────────────────────────

class UserSignupRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: str = Field(..., min_length=2, description="Full name of user")


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "user"
    created_at: Optional[datetime] = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─────────────────────────────────────────────────────────────────────────────
# Generic Responses
# ─────────────────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

