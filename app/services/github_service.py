"""
GitHub Service — Codebase Ingestion, Architectural Analysis & RAG Ingestion.

Allows users to import code from a GitHub repository URL:
  1. Inspects repository metadata, directory trees, dependencies, and database schemas.
  2. Synthesizes an academic project analysis (Title, Domain, Problem Statement, Tech Stack, Modules, DB).
  3. Ingests architectural summaries, schemas, and README into ChromaDB for chapter generation.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from loguru import logger

from app.core.config import settings
from app.core.database import get_supabase
from app.models.schemas import ProjectCategory
from app.services.document_processor import chunk_text
from app.services.vector_store import add_chunks


def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
    """
    Parses a GitHub URL into (owner, repo, branch).
    Supports:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - https://github.com/owner/repo/tree/branch_name
      - github.com/owner/repo
    """
    clean_url = url.strip().rstrip("/")
    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]

    pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?"
    match = re.search(pattern, clean_url, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid GitHub repository URL: '{url}'. Expected format: https://github.com/owner/repo")

    owner = match.group(1)
    repo = match.group(2)
    branch = match.group(3) if match.group(3) else None
    return owner, repo, branch


async def fetch_github_repository_data(
    owner: str,
    repo: str,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetches repository metadata, file tree, and key architectural files from GitHub.
    Gracefully falls back to raw.githubusercontent.com if GitHub REST API hits rate limits.
    """
    headers = {
        "User-Agent": "AI-Project-Report-Generator/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    repo_data: Dict[str, Any] = {
        "owner": owner,
        "repo": repo,
        "github_url": f"https://github.com/{owner}/{repo}",
        "description": "",
        "default_branch": "main",
        "topics": [],
        "languages": [],
        "file_paths": [],
        "readme_content": "",
        "dependency_content": "",
        "dependency_file": "",
        "schema_content": "",
        "schema_files": [],
        "sample_code_files": {},
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # 1. Fetch Repository Info
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            resp = await client.get(api_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                repo_data["description"] = data.get("description") or ""
                repo_data["default_branch"] = branch or data.get("default_branch") or "main"
                repo_data["topics"] = data.get("topics") or []
            else:
                logger.warning(f"GitHub repo info API returned status {resp.status_code}")
                repo_data["default_branch"] = branch or "main"
        except Exception as e:
            logger.warning(f"Failed to fetch GitHub repo info: {e}")
            repo_data["default_branch"] = branch or "main"

        active_branch = branch or repo_data["default_branch"]

        # 2. Fetch File Tree via Git Trees API
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{active_branch}?recursive=1"
        try:
            tree_resp = await client.get(tree_url, headers=headers)
            if tree_resp.status_code == 200:
                tree_json = tree_resp.json()
                tree_items = tree_json.get("tree", [])
                repo_data["file_paths"] = [item["path"] for item in tree_items if item.get("type") == "blob"]
        except Exception as e:
            logger.warning(f"Failed to fetch recursive file tree: {e}")

        # 3. Fetch README Content
        readme_candidates = ["README.md", "readme.md", "README.rst", "README.txt", "docs/README.md"]
        for rm_path in readme_candidates:
            if not repo_data["file_paths"] or rm_path in repo_data["file_paths"] or rm_path.lower() in [p.lower() for p in repo_data["file_paths"]]:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{active_branch}/{rm_path}"
                try:
                    rm_resp = await client.get(raw_url)
                    if rm_resp.status_code == 200 and len(rm_resp.text.strip()) > 20:
                        repo_data["readme_content"] = rm_resp.text[:8000]
                        break
                except Exception:
                    pass

        # 4. Detect & Fetch Dependencies
        dep_files = [
            "requirements.txt", "package.json", "pyproject.toml",
            "Pipfile", "go.mod", "pom.xml", "Cargo.toml", "composer.json"
        ]
        for df in dep_files:
            match = next((p for p in repo_data["file_paths"] if p.endswith(df)), None) or df
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{active_branch}/{match}"
            try:
                df_resp = await client.get(raw_url)
                if df_resp.status_code == 200:
                    repo_data["dependency_file"] = match
                    repo_data["dependency_content"] = df_resp.text[:4000]
                    break
            except Exception:
                pass

        # 5. Detect & Fetch Database Schemas & Models
        schema_keywords = [".sql", "schema", "models.py", "model.py", "schema.prisma", "entities", "migration"]
        for p in repo_data["file_paths"]:
            p_lower = p.lower()
            if any(kw in p_lower for kw in schema_keywords) and not p_lower.endswith((".png", ".jpg", ".md", ".json", ".lock")):
                repo_data["schema_files"].append(p)
                if len(repo_data["schema_files"]) <= 4:
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{active_branch}/{p}"
                    try:
                        sf_resp = await client.get(raw_url)
                        if sf_resp.status_code == 200:
                            repo_data["sample_code_files"][p] = sf_resp.text[:4000]
                    except Exception:
                        pass

    return repo_data


async def analyze_github_codebase(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesizes extracted repository clues into an academic project structure.
    Uses LLM when available, with an intelligent heuristic fallback.
    """
    owner = repo_data["owner"]
    repo = repo_data["repo"]
    desc = repo_data.get("description", "")
    readme = repo_data.get("readme_content", "")[:3500]
    deps = repo_data.get("dependency_content", "")[:2000]
    file_list = repo_data.get("file_paths", [])[:120]
    schema_samples = "\n\n".join([f"--- File: {k} ---\n{v[:1500]}" for k, v in repo_data.get("sample_code_files", {}).items()])

    # Try LLM-based analysis first
    llm_analysis = await _analyze_via_llm(owner, repo, desc, readme, deps, file_list, schema_samples)
    if llm_analysis:
        return llm_analysis

    # Fallback heuristic analysis
    return _heuristic_analysis(owner, repo, desc, readme, deps, file_list, schema_samples)


async def _analyze_via_llm(
    owner: str,
    repo: str,
    desc: str,
    readme: str,
    deps: str,
    file_list: List[str],
    schema_samples: str
) -> Optional[Dict[str, Any]]:
    """Analyzes repository via LLM to generate academic project details."""
    from app.services.llm_service import _generate_via_openai_compatible, _resolve_provider_info

    prompt = f"""You are an expert academic project evaluator. Analyze the following GitHub repository and produce a comprehensive academic report profile.

REPOSITORY: {owner}/{repo}
DESCRIPTION: {desc}
DIRECTORY PATHS SAMPLE: {', '.join(file_list[:80])}
DEPENDENCY MANIFEST: {deps[:1200]}
README EXCERPT:
{readme[:2000]}
SCHEMA / CODE SAMPLES:
{schema_samples[:1500]}

Respond ONLY with a valid JSON object matching this exact schema:
{{
  "title": "Clean, Formal Academic Project Title",
  "domain": "e.g. Web Application / Machine Learning / IoT / Distributed Systems",
  "category": "Application or System Development",
  "problem_statement": "Detailed academic problem statement (2 paragraphs highlighting real-world challenges, motivation, and objectives).",
  "tech_stack": ["list", "of", "languages", "frameworks", "tools"],
  "modules": ["Module 1: User & Auth", "Module 2: Core Processing", "Module 3: Database & Storage", "Module 4: UI/Client Dashboard"],
  "database_used": "e.g. PostgreSQL, Supabase, MongoDB, SQLite",
  "methodology": "Agile Iterative Development",
  "existing_system": "Limitations and bottlenecks of conventional manual or monolithic solutions.",
  "proposed_system": "Architectural design, data flow, and modern capabilities of the proposed system.",
  "unique_features": ["Feature 1", "Feature 2", "Feature 3"],
  "architecture_summary": "Summary of system architecture and component interactions."
}}
Do not include markdown code fence formatting outside the JSON if possible. Ensure category is one of: "Application or System Development", "Internet Based", "Research Based", "Data Science & ML", "Embedded Systems / IoT"."""

    try:
        provider, api_key, model = _resolve_provider_info(1)
        if provider == "groq" and api_key:
            url = "https://api.groq.com/openai/v1/chat/completions"
        elif provider in ("huggingface", "hf") and api_key:
            url = "https://router.huggingface.co/hf-inference/v1/chat/completions"
        elif provider == "openrouter" and api_key:
            url = "https://openrouter.ai/api/v1/chat/completions"
        else:
            return None

        raw_response = await _generate_via_openai_compatible(
            url=url,
            api_key=api_key,
            model=model,
            prompt=prompt,
            chapter_number=1,
        )

        # Parse JSON from response
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```[a-zA-Z]*\n?", "", clean_json)
            clean_json = re.sub(r"\n?```$", "", clean_json)

        parsed = json.loads(clean_json)
        parsed["github_url"] = f"https://github.com/{owner}/{repo}"
        parsed["owner"] = owner
        parsed["repo"] = repo
        return parsed
    except Exception as e:
        logger.warning(f"LLM analysis failed, falling back to heuristics: {e}")
        return None


def _heuristic_analysis(
    owner: str,
    repo: str,
    desc: str,
    readme: str,
    deps: str,
    file_list: List[str],
    schema_samples: str
) -> Dict[str, Any]:
    """Robust rule-based heuristic extraction when LLM is unavailable."""
    # 1. Title
    formatted_title = repo.replace("-", " ").replace("_", " ").title()
    title = f"{formatted_title} Platform"

    # 2. Tech Stack Detection
    stack = set()
    file_str = " ".join(file_list).lower()
    combined_text = (deps + " " + readme + " " + file_str).lower()

    if "python" in combined_text or ".py" in file_str: stack.add("Python")
    if "fastapi" in combined_text: stack.add("FastAPI")
    if "django" in combined_text: stack.add("Django")
    if "flask" in combined_text: stack.add("Flask")
    if "react" in combined_text or ".jsx" in file_str or ".tsx" in file_str: stack.add("React")
    if "vue" in combined_text: stack.add("Vue.js")
    if "next" in combined_text: stack.add("Next.js")
    if "typescript" in combined_text or ".ts" in file_str: stack.add("TypeScript")
    if "javascript" in combined_text or ".js" in file_str: stack.add("JavaScript")
    if "node" in combined_text or "express" in combined_text: stack.add("Node.js")
    if "docker" in combined_text or "dockerfile" in file_str: stack.add("Docker")
    if "chroma" in combined_text: stack.add("ChromaDB")

    # 3. Database
    database = "PostgreSQL"
    if "supabase" in combined_text:
        database = "Supabase PostgreSQL"
        stack.add("Supabase")
    elif "mongo" in combined_text:
        database = "MongoDB"
        stack.add("MongoDB")
    elif "sqlite" in combined_text:
        database = "SQLite"
    elif "mysql" in combined_text:
        database = "MySQL"

    # 4. Domain & Category
    domain = "Web Application"
    category = ProjectCategory.APPLICATION.value
    if "ml" in combined_text or "machine learning" in combined_text or "torch" in combined_text or "tensorflow" in combined_text:
        domain = "Machine Learning & AI"
        category = ProjectCategory.DATA_SCIENCE_ML.value
    elif "iot" in combined_text or "arduino" in combined_text or "raspberry" in combined_text:
        domain = "Embedded Systems & IoT"
        category = ProjectCategory.EMBEDDED_IOT.value

    # 5. Problem Statement
    problem_statement = (
        f"In contemporary software engineering environments, {formatted_title} addresses critical bottlenecks "
        f"in existing workflows by providing automated, high-efficiency system modules. Traditional approaches "
        f"often suffer from manual latency, fragmented architecture, and limited maintainability.\n\n"
        f"This project implements a robust architecture utilizing modern frameworks to solve these challenges, "
        f"ensuring modular separation of concerns, high throughput, and seamless user interaction."
    )
    if desc:
        problem_statement = f"{desc}\n\n" + problem_statement

    return {
        "title": title,
        "domain": domain,
        "category": category,
        "problem_statement": problem_statement,
        "tech_stack": sorted(list(stack)) if stack else ["Python", "FastAPI", "React", "PostgreSQL"],
        "modules": [
            "User Management & Security Module",
            "Core Processing & Business Logic",
            "Database Persistence & Schema Management",
            "Interactive Client UI & Dashboard",
        ],
        "database_used": database,
        "methodology": "Agile Iterative Development",
        "existing_system": "Manual processes with disparate tools, lack of unified data modeling, and performance overhead.",
        "proposed_system": f"A full-stack, modular architecture designed with clean separation of concerns, utilizing {database} and modern APIs.",
        "unique_features": [
            "Automated architecture synthesis from code repository",
            "High-performance modular architecture",
            "Strict academic compliance and comprehensive data modeling"
        ],
        "architecture_summary": f"Modular client-server system organized across frontend components, backend routers, and {database} storage.",
        "github_url": f"https://github.com/{owner}/{repo}",
        "owner": owner,
        "repo": repo,
    }


async def ingest_github_to_rag(
    project_id: str,
    repo_data: Dict[str, Any],
    analysis: Dict[str, Any]
) -> int:
    """
    Ingests repository architecture, schema files, and technical README into ChromaDB
    and registers them in Supabase uploaded_files for the given project.
    Returns total chunks stored.
    """
    upload_dir = Path(settings.UPLOAD_DIR) / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    db = get_supabase()
    total_chunks = 0
    now = datetime.now(timezone.utc).isoformat()

    # Documents to create and embed
    docs = []

    # 1. Architecture & Directory Overview
    file_tree_snippet = "\n".join(repo_data.get("file_paths", [])[:150])
    arch_doc = f"""# System Architecture & Repository Structure
Source: {repo_data.get('github_url')}
Project Title: {analysis.get('title')}
Domain: {analysis.get('domain')}
Tech Stack: {', '.join(analysis.get('tech_stack', []))}
Database: {analysis.get('database_used')}

## Architecture Summary
{analysis.get('architecture_summary')}

## Modules
{chr(10).join(['- ' + m for m in analysis.get('modules', [])])}

## Repository Directory Tree
```
{file_tree_snippet}
```
"""
    docs.append(("GitHub_Architecture_Overview.md", arch_doc))

    # 2. Database Schema & Data Models
    schema_samples = repo_data.get("sample_code_files", {})
    if schema_samples:
        schema_text_parts = ["# Database Schemas and Entity Models\n"]
        for path, code in schema_samples.items():
            schema_text_parts.append(f"## File: {path}\n```\n{code}\n```\n")
        docs.append(("GitHub_Database_Schemas.md", "\n".join(schema_text_parts)))

    # 3. Technical README
    readme_content = repo_data.get("readme_content", "")
    if readme_content:
        docs.append(("GitHub_Repository_README.md", readme_content))

    # Process and index each document
    for filename, content in docs:
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}_{filename}"
        file_path.write_text(content, encoding="utf-8")

        chunks = chunk_text(content)
        if chunks:
            count = add_chunks(project_id, chunks, filename)
            total_chunks += count

            # Register in Supabase uploaded_files
            try:
                row = {
                    "id": file_id,
                    "project_id": project_id,
                    "filename": f"[GitHub] {filename}",
                    "file_type": "md",
                    "file_size": len(content.encode("utf-8")),
                    "saved_path": str(file_path),
                    "chunks_count": count,
                    "status": "ready",
                    "created_at": now,
                }
                db.table("uploaded_files").insert(row).execute()
            except Exception as e:
                logger.warning(f"Failed to record GitHub file in Supabase: {e}")

    logger.success(f"Indexed {total_chunks} code & architecture chunks from GitHub repo '{repo_data.get('repo')}'")
    return total_chunks
