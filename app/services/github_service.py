"""
GitHub Service — Comprehensive Codebase, Folder & SQL Architecture Analysis & RAG Ingestion.

Features:
  1. Inspects repository structure, analyzing every folder and file across the repo.
  2. Discovers and deeply parses all SQL files (*.sql) to extract table definitions,
     column types, primary keys, foreign keys, and ER relational mappings.
  3. Categorizes each folder's architectural role (UI, Routers, Services, Models, Migrations, Tests).
  4. Synthesizes an academic project profile (Title, Domain, Problem Statement, Tech Stack, Modules, DB).
  5. Ingests structured chapter-targeted documents into ChromaDB RAG and triggers diagram generation.
"""
from __future__ import annotations

import io
import json
import os
import re
import uuid
import zipfile
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


# ─────────────────────────────────────────────────────────────────────────────
# 1. GitHub URL Parser
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# 2. SQL DDL Parser — Deep Schema & Relational Entity Extraction
# ─────────────────────────────────────────────────────────────────────────────

def parse_sql_ddl(sql_text: str) -> Dict[str, Any]:
    """
    Parses SQL DDL statements (*.sql) to extract:
      - Table definitions with column names, SQL data types, constraints
      - Primary keys and Foreign keys
      - Relational entity-relationship links between tables
      - Markdown Data Dictionary tables ready for academic reports
    """
    if not sql_text:
        return {"tables": [], "relationships": [], "data_dictionary_md": ""}

    # Strip single-line and multi-line SQL comments
    cleaned = re.sub(r'--.*?$', '', sql_text, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    tables: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []

    # Match CREATE TABLE [IF NOT EXISTS] <table_name> ( <body> )
    table_pattern = re.compile(
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"\'\w\.]+)\s*\((.*?)\)\s*;',
        re.IGNORECASE | re.DOTALL
    )

    for match in table_pattern.finditer(cleaned):
        raw_name, body = match.group(1), match.group(2)
        table_name = raw_name.strip('`"\'').split('.')[-1]

        columns: List[Dict[str, Any]] = []
        primary_keys: List[str] = []
        foreign_keys: List[Dict[str, str]] = []

        # Split body by commas NOT enclosed within parentheses
        raw_lines: List[str] = []
        current: List[str] = []
        paren_depth = 0
        for ch in body:
            if ch == '(':
                paren_depth += 1
            elif ch == ')':
                paren_depth -= 1
            if ch == ',' and paren_depth == 0:
                raw_lines.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            raw_lines.append("".join(current).strip())

        for line in raw_lines:
            line_str = " ".join(line.split())
            if not line_str:
                continue

            # Check for Table-level Primary Key constraint
            pk_match = re.match(r'^(?:CONSTRAINT\s+\w+\s+)?PRIMARY\s+KEY\s*\((.*?)\)', line_str, re.IGNORECASE)
            if pk_match:
                cols = [c.strip('`"\' ') for c in pk_match.group(1).split(',')]
                primary_keys.extend(cols)
                continue

            # Check for Table-level Foreign Key constraint
            fk_match = re.match(
                r'^(?:CONSTRAINT\s+\w+\s+)?FOREIGN\s+KEY\s*\((.*?)\)\s*REFERENCES\s+([`"\'\w\.]+)\s*\((.*?)\)',
                line_str, re.IGNORECASE
            )
            if fk_match:
                fk_col = fk_match.group(1).strip('`"\' ')
                ref_table = fk_match.group(2).strip('`"\' ').split('.')[-1]
                ref_col = fk_match.group(3).strip('`"\' ')
                foreign_keys.append({"column": fk_col, "ref_table": ref_table, "ref_col": ref_col})
                relationships.append({
                    "from_table": table_name,
                    "from_column": fk_col,
                    "to_table": ref_table,
                    "to_column": ref_col
                })
                continue

            # Skip other table-level constraints (UNIQUE, CHECK)
            if re.match(r'^(?:CONSTRAINT\s+\w+\s+)?(?:UNIQUE|CHECK|KEY)\b', line_str, re.IGNORECASE):
                continue

            # Match column definition: <col_name> <col_type_with_optional_args> [modifiers...]
            col_match = re.match(r'^([`"\'\w]+)\s+([A-Za-z0-9_]+(?:\s*\([^)]*\))?)(?:\s+(.*))?$', line_str)
            if col_match:
                col_name = col_match.group(1).strip('`"\'')
                col_type = col_match.group(2).upper()
                modifiers = col_match.group(3) or ""

                is_pk = bool(re.search(r'\bPRIMARY\s+KEY\b', modifiers, re.IGNORECASE))
                is_fk = bool(re.search(r'\bREFERENCES\s+([`"\'\w\.]+)\s*\((.*?)\)', modifiers, re.IGNORECASE))
                is_nullable = not bool(re.search(r'\bNOT\s+NULL\b', modifiers, re.IGNORECASE))

                if is_pk:
                    primary_keys.append(col_name)

                ref_info = ""
                if is_fk:
                    fk_inline = re.search(r'\bREFERENCES\s+([`"\'\w\.]+)\s*\((.*?)\)', modifiers, re.IGNORECASE)
                    if fk_inline:
                        ref_tbl = fk_inline.group(1).strip('`"\'').split('.')[-1]
                        ref_c = fk_inline.group(2).strip('`"\'')
                        ref_info = f"References {ref_tbl}({ref_c})"
                        relationships.append({
                            "from_table": table_name,
                            "from_column": col_name,
                            "to_table": ref_tbl,
                            "to_column": ref_c
                        })

                columns.append({
                    "name": col_name,
                    "type": col_type,
                    "primary_key": is_pk,
                    "foreign_key": is_fk,
                    "nullable": is_nullable,
                    "details": ref_info or modifiers[:40]
                })

        # Synchronize column PK flags with table-level PKs
        for c in columns:
            if c["name"] in primary_keys:
                c["primary_key"] = True

        tables.append({
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys
        })

    # Build Markdown Data Dictionary representation
    dd_parts = ["## Database Data Dictionary & Relational Schema\n"]
    if tables:
        for t in tables:
            dd_parts.append(f"### Table: `{t['table_name']}`")
            dd_parts.append("| Column Name | Data Type | Key Type | Nullable | Constraints / Reference |")
            dd_parts.append("| :--- | :--- | :--- | :--- | :--- |")
            for c in t["columns"]:
                key_type = "PK" if c["primary_key"] else ("FK" if c["foreign_key"] else "-")
                nullable = "YES" if c["nullable"] else "NO"
                dd_parts.append(f"| `{c['name']}` | {c['type']} | **{key_type}** | {nullable} | {c['details'] or '-'} |")
            dd_parts.append("\n")

        if relationships:
            dd_parts.append("### Relational Entity Mappings (ER Links)")
            for r in relationships:
                dd_parts.append(f"- `{r['from_table']}.{r['from_column']}` ──> `{r['to_table']}.{r['to_column']}`")
            dd_parts.append("\n")

    return {
        "tables": tables,
        "relationships": relationships,
        "data_dictionary_md": "\n".join(dd_parts)
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Comprehensive Repository Fetcher (Exhaustive Folder & File Analysis)
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_github_repository_data(
    owner: str,
    repo: str,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetches the repository and analyzes every file and folder:
      1. Downloads repo archive zip to inspect 100% of files without API throttling.
      2. Discovers and extracts all .sql files and parses table DDL.
      3. Categorizes every folder in the codebase and extracts module code samples.
      4. Discovers dependencies, configs, test suites, and documentation.
      5. Gracefully falls back to Git Trees API + raw content if zip download is unavailable.
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
        "default_branch": branch or "main",
        "topics": [],
        "languages": [],
        "file_paths": [],
        "folders": {},              # folder_path -> list of filenames
        "folder_roles": {},        # folder_path -> architectural role
        "readme_content": "",
        "dependency_content": "",
        "dependency_file": "",
        "sql_files": {},           # file_path -> full SQL content
        "parsed_tables": [],       # parsed table schemas
        "relationships": [],       # foreign key relationships
        "data_dictionary_md": "",  # formatted Data Dictionary
        "sample_code_files": {},   # file_path -> code excerpt
        "test_files": [],          # list of test file paths
        "config_files": [],        # list of config file paths
    }

    async with httpx.AsyncClient(timeout=40.0, follow_redirects=True) as client:
        # Step A: Fetch Repository Metadata (default branch, description, topics)
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            resp = await client.get(api_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                repo_data["description"] = data.get("description") or ""
                repo_data["default_branch"] = branch or data.get("default_branch") or "main"
                repo_data["topics"] = data.get("topics") or []
        except Exception as e:
            logger.warning(f"Failed to fetch GitHub repo info: {e}")

        active_branch = branch or repo_data["default_branch"]

        # Step B: Attempt full zip archive download for exhaustive 100% file analysis
        zip_downloaded = False
        zip_urls = [
            f"https://github.com/{owner}/{repo}/archive/refs/heads/{active_branch}.zip",
            f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{active_branch}",
            f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
        ]

        for z_url in zip_urls:
            try:
                z_resp = await client.get(z_url)
                if z_resp.status_code == 200 and len(z_resp.content) > 1000:
                    _process_repository_zip(z_resp.content, repo_data)
                    zip_downloaded = True
                    logger.success(f"Successfully downloaded and analyzed full repository zip for {owner}/{repo}")
                    break
            except Exception as e:
                logger.debug(f"Zip download from {z_url} failed: {e}")

        # Step C: Fallback to Git Trees API if zip is unavailable
        if not zip_downloaded:
            logger.info("Falling back to Git Trees API for repository structure traversal")
            await _process_via_git_trees(client, headers, owner, repo, active_branch, repo_data)

    # Step D: Parse all discovered SQL files into Database Tables & Data Dictionary
    combined_sql = "\n\n".join(repo_data["sql_files"].values())
    if combined_sql:
        ddl_analysis = parse_sql_ddl(combined_sql)
        repo_data["parsed_tables"] = ddl_analysis["tables"]
        repo_data["relationships"] = ddl_analysis["relationships"]
        repo_data["data_dictionary_md"] = ddl_analysis["data_dictionary_md"]
        logger.success(f"Parsed {len(repo_data['parsed_tables'])} database tables from SQL files across repo.")

    return repo_data


def _process_repository_zip(zip_bytes: bytes, repo_data: Dict[str, Any]) -> None:
    """Extracts and analyzes every file and folder from the repository zip archive in memory."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        namelist = z.namelist()
        if not namelist:
            return

        # Strip root archive directory prefix (e.g. repo-main/)
        root_prefix = namelist[0].split("/")[0] + "/" if "/" in namelist[0] else ""

        # Ignored directory names (build artifacts, vendor dependencies)
        ignored_dirs = {
            "node_modules", ".git", ".github", "__pycache__", "venv", ".venv",
            "env", "dist", "build", ".next", ".nuxt", "target", "vendor", ".idea", ".vscode"
        }

        # Ignored binary extensions
        ignored_exts = {
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".zip", ".tar",
            ".gz", ".bin", ".exe", ".dll", ".so", ".jar", ".woff", ".woff2", ".ttf", ".pdf"
        }

        for item_name in namelist:
            # Strip root prefix
            rel_path = item_name[len(root_prefix):] if item_name.startswith(root_prefix) else item_name
            if not rel_path or rel_path.endswith("/"):
                continue

            parts = rel_path.split("/")
            if any(p in ignored_dirs for p in parts):
                continue

            ext = os.path.splitext(rel_path)[1].lower()
            if ext in ignored_exts:
                continue

            repo_data["file_paths"].append(rel_path)

            # Record Folder Organization
            folder = os.path.dirname(rel_path) or "root"
            if folder not in repo_data["folders"]:
                repo_data["folders"][folder] = []
                repo_data["folder_roles"][folder] = _classify_folder_role(folder)
            repo_data["folders"][folder].append(os.path.basename(rel_path))

            # 1. Check for SQL files (*.sql)
            if ext == ".sql":
                try:
                    content = z.read(item_name).decode("utf-8", errors="ignore")
                    repo_data["sql_files"][rel_path] = content
                except Exception:
                    pass

            # 2. Check for README
            if os.path.basename(rel_path).lower().startswith("readme") and not repo_data["readme_content"]:
                try:
                    repo_data["readme_content"] = z.read(item_name).decode("utf-8", errors="ignore")[:10000]
                except Exception:
                    pass

            # 3. Check for Dependency Manifests
            dep_names = {"requirements.txt", "package.json", "pyproject.toml", "pipfile", "go.mod", "pom.xml", "cargo.toml"}
            if os.path.basename(rel_path).lower() in dep_names and not repo_data["dependency_content"]:
                try:
                    repo_data["dependency_file"] = rel_path
                    repo_data["dependency_content"] = z.read(item_name).decode("utf-8", errors="ignore")[:4000]
                except Exception:
                    pass

            # 4. Check for Test & Config files
            if "test" in rel_path.lower():
                repo_data["test_files"].append(rel_path)
            if ext in {".env", ".example", ".yaml", ".yml", ".toml", ".json", ".dockerfile"} or "docker" in rel_path.lower():
                repo_data["config_files"].append(rel_path)

            # 5. Extract Code Samples from Every Folder (up to 3 files per folder)
            code_exts = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".php", ".rb", ".cs", ".sql", ".prisma"}
            if ext in code_exts:
                folder_samples = [p for p in repo_data["sample_code_files"] if os.path.dirname(p) == folder]
                if len(folder_samples) < 3:
                    try:
                        code_txt = z.read(item_name).decode("utf-8", errors="ignore")[:3500]
                        repo_data["sample_code_files"][rel_path] = code_txt
                    except Exception:
                        pass


async def _process_via_git_trees(
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    owner: str,
    repo: str,
    active_branch: str,
    repo_data: Dict[str, Any]
) -> None:
    """Fallback: Traverses the repository using GitHub REST API Git Trees and fetches key files via raw URLs."""
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{active_branch}?recursive=1"
    try:
        tree_resp = await client.get(tree_url, headers=headers)
        if tree_resp.status_code == 200:
            tree_items = tree_resp.json().get("tree", [])
            for item in tree_items:
                if item.get("type") == "blob":
                    p = item["path"]
                    repo_data["file_paths"].append(p)
                    folder = os.path.dirname(p) or "root"
                    if folder not in repo_data["folders"]:
                        repo_data["folders"][folder] = []
                        repo_data["folder_roles"][folder] = _classify_folder_role(folder)
                    repo_data["folders"][folder].append(os.path.basename(p))

                    if p.lower().endswith(".sql"):
                        repo_data["sql_files"][p] = ""
    except Exception as e:
        logger.warning(f"Git trees API failed: {e}")

    # Fetch README
    readme_candidates = ["README.md", "readme.md", "README.rst", "docs/README.md"]
    for rm_path in readme_candidates:
        if not repo_data["file_paths"] or any(p.lower() == rm_path.lower() for p in repo_data["file_paths"]):
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{active_branch}/{rm_path}"
            try:
                r = await client.get(raw_url)
                if r.status_code == 200 and len(r.text.strip()) > 20:
                    repo_data["readme_content"] = r.text[:8000]
                    break
            except Exception:
                pass

    # Fetch Dependencies
    for df in ["requirements.txt", "package.json", "pyproject.toml", "go.mod"]:
        match = next((p for p in repo_data["file_paths"] if p.endswith(df)), None)
        if match:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{active_branch}/{match}"
            try:
                r = await client.get(raw_url)
                if r.status_code == 200:
                    repo_data["dependency_file"] = match
                    repo_data["dependency_content"] = r.text[:4000]
                    break
            except Exception:
                pass

    # Fetch all SQL files discovered in the tree
    for sql_path in list(repo_data["sql_files"].keys())[:15]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{active_branch}/{sql_path}"
        try:
            r = await client.get(raw_url)
            if r.status_code == 200:
                repo_data["sql_files"][sql_path] = r.text[:10000]
        except Exception:
            pass


def _classify_folder_role(folder_path: str) -> str:
    """Classifies the architectural role of a directory for academic software modeling."""
    p_lower = folder_path.lower()
    if any(k in p_lower for k in ["ui", "frontend", "components", "pages", "views", "templates", "public"]):
        return "Presentation & User Interface Layer"
    elif any(k in p_lower for k in ["router", "controllers", "routes", "api", "endpoints"]):
        return "API Routing & Controller Layer"
    elif any(k in p_lower for k in ["service", "logic", "core", "domain", "usecase"]):
        return "Business Logic & Application Service Layer"
    elif any(k in p_lower for k in ["db", "database", "sql", "migration", "migrations", "model", "models", "entity", "entities", "prisma"]):
        return "Data Persistence, Schema & Storage Layer"
    elif any(k in p_lower for k in ["test", "tests", "spec", "cypress"]):
        return "Verification, Unit & Integration Testing Layer"
    elif any(k in p_lower for k in ["config", "deploy", "docker", "k8s", "scripts", "infra"]):
        return "Configuration, Containerization & Infrastructure Layer"
    else:
        return "Utility & Supporting Modules Layer"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Codebase Architecture & Academic Project Analysis
# ─────────────────────────────────────────────────────────────────────────────

async def analyze_github_codebase(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesizes the extracted folder structures, SQL schemas, and source code
    into a comprehensive academic project structure.
    """
    owner = repo_data["owner"]
    repo = repo_data["repo"]
    desc = repo_data.get("description", "")
    readme = repo_data.get("readme_content", "")[:3500]
    deps = repo_data.get("dependency_content", "")[:2000]
    file_list = repo_data.get("file_paths", [])[:120]
    schema_samples = "\n\n".join([f"--- File: {k} ---\n{v[:1500]}" for k, v in repo_data.get("sample_code_files", {}).items()])
    parsed_tables = repo_data.get("parsed_tables", [])

    # Try LLM-based analysis first
    llm_analysis = await _analyze_via_llm(owner, repo, desc, readme, deps, file_list, schema_samples, parsed_tables)
    if llm_analysis:
        llm_analysis["parsed_tables"] = parsed_tables
        return llm_analysis

    # Fallback heuristic analysis
    analysis = _heuristic_analysis(owner, repo, desc, readme, deps, file_list, schema_samples, parsed_tables)
    analysis["parsed_tables"] = parsed_tables
    return analysis


async def _analyze_via_llm(
    owner: str,
    repo: str,
    desc: str,
    readme: str,
    deps: str,
    file_list: List[str],
    schema_samples: str,
    parsed_tables: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Analyzes repository via LLM to generate formal academic project details."""
    from app.services.llm_service import _generate_via_openai_compatible, _resolve_provider_info

    table_names = [t.get("table_name") for t in parsed_tables] if parsed_tables else []
    tables_summary = f"DETECTED DATABASE TABLES FROM SQL: {', '.join(table_names)}" if table_names else ""

    prompt = f"""You are an expert academic technical writer and software architecture evaluator.
Analyze the following GitHub repository and produce a comprehensive academic report profile.

REPOSITORY: {owner}/{repo}
DESCRIPTION: {desc}
DIRECTORY PATHS SAMPLE: {', '.join(file_list[:80])}
{tables_summary}
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
  "database_used": "e.g. PostgreSQL, Supabase, MySQL, SQLite, MongoDB",
  "methodology": "Agile Iterative Development",
  "existing_system": "Limitations and bottlenecks of conventional manual or monolithic solutions.",
  "proposed_system": "Architectural design, data flow, and modern capabilities of the proposed system.",
  "unique_features": ["Feature 1", "Feature 2", "Feature 3"],
  "architecture_summary": "Summary of system architecture and component interactions."
}}
Ensure category is one of: "Application or System Development", "Internet Based", "Research Based", "Data Science & ML", "Embedded Systems / IoT"."""

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
    schema_samples: str,
    parsed_tables: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Robust rule-based heuristic extraction when LLM is offline."""
    formatted_title = repo.replace("-", " ").replace("_", " ").title()
    title = f"{formatted_title} Platform"

    # Tech Stack Detection
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

    # Database Detection
    database = "PostgreSQL"
    if parsed_tables:
        if "supabase" in combined_text:
            database = "Supabase PostgreSQL"
        elif "mysql" in combined_text:
            database = "MySQL"
        elif "sqlite" in combined_text:
            database = "SQLite"
        else:
            database = "PostgreSQL Relational Database"
    elif "supabase" in combined_text:
        database = "Supabase PostgreSQL"
        stack.add("Supabase")
    elif "mongo" in combined_text:
        database = "MongoDB"
    elif "mysql" in combined_text:
        database = "MySQL"
    elif "sqlite" in combined_text:
        database = "SQLite"

    domain = "Web Application"
    if any(k in combined_text for k in ["ml", "machine learning", "ai", "deep learning", "torch", "tensorflow"]):
        domain = "Artificial Intelligence & ML"
    elif any(k in combined_text for k in ["iot", "arduino", "raspberry", "sensor"]):
        domain = "Embedded Systems / IoT"

    category = "Application or System Development"
    problem_statement = (
        f"In contemporary computing environments, modern applications face challenges in delivering cohesive, "
        f"modular solutions that integrate responsive user interfaces with robust backend data pipelines. "
        f"Existing implementations often rely on ad-hoc scripting, leading to maintenance bottlenecks, data inconsistency, "
        f"and limited scalability.\n\n"
        f"The {title} addresses these academic and engineering challenges by implementing a decoupled, full-stack architecture "
        f"utilizing modern frameworks and reliable persistence ({database}). The system is engineered to provide high performance, "
        f"intuitive user interactions, and robust data integrity."
    )

    modules = [
        "User Management & Security Module",
        "Core Processing & Business Logic Service",
        "Database Persistence & Schema Management",
        "Interactive Client UI & Dashboard",
    ]

    return {
        "title": title,
        "domain": domain,
        "category": category,
        "problem_statement": problem_statement,
        "tech_stack": sorted(list(stack)) if stack else ["Python", "FastAPI", "React", "PostgreSQL"],
        "modules": modules,
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


# ─────────────────────────────────────────────────────────────────────────────
# 5. Ingestion of Code, SQL & Folders into ChromaDB Vector Store
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_github_to_rag(
    project_id: str,
    repo_data: Dict[str, Any],
    analysis: Dict[str, Any]
) -> int:
    """
    Creates and indexes 6 structured, chapter-targeted documents into ChromaDB:
      1. GitHub_SQL_Database_Schema_and_Data_Dictionary.md (Powers Chapters 3 & 5)
      2. GitHub_Repository_Folder_Structure_and_Modules.md (Powers Chapters 1 & 4)
      3. GitHub_Source_Code_Components_and_Endpoints.md (Powers Chapters 2 & 4)
      4. GitHub_Dependencies_and_Environment.md (Powers Chapters 2 & 4)
      5. GitHub_Tests_and_Quality_Assurance.md (Powers Chapter 4 testing section)
      6. GitHub_README_and_Documentation.md (Powers Chapters 1 & 6)
    """
    upload_dir = Path(settings.UPLOAD_DIR) / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    db = get_supabase()
    total_chunks = 0
    now = datetime.now(timezone.utc).isoformat()
    docs: List[Tuple[str, str]] = []

    # Document 1: SQL Database Schema & Data Dictionary (For Chapters 3 & 5)
    data_dict = repo_data.get("data_dictionary_md", "")
    sql_files = repo_data.get("sql_files", {})
    sql_doc_parts = [
        f"# Complete Database Design, SQL Schemas & Data Dictionary",
        f"Source: {repo_data.get('github_url')}",
        f"Database Engine: {analysis.get('database_used')}",
        "\n"
    ]
    if data_dict:
        sql_doc_parts.append(data_dict)
    if sql_files:
        sql_doc_parts.append("## SQL Source Files Across Repository\n")
        for path, code in sql_files.items():
            sql_doc_parts.append(f"### File: `{path}`\n```sql\n{code[:5000]}\n```\n")
    else:
        sql_doc_parts.append("## Relational Data Modeling\nStandard relational schema models utilized across the backend services.\n")
    docs.append(("GitHub_SQL_Database_Schema_and_Data_Dictionary.md", "\n".join(sql_doc_parts)))

    # Document 2: Exhaustive Folder Hierarchy & Module Roles (For Chapters 1 & 4)
    folders = repo_data.get("folders", {})
    folder_roles = repo_data.get("folder_roles", {})
    folder_doc_parts = [
        f"# Complete Repository Directory Structure & Architectural Folders",
        f"Project: {analysis.get('title')}",
        f"Total Files Analyzed: {len(repo_data.get('file_paths', []))}",
        "\n## Folder-by-Folder Architectural Breakdown\n"
    ]
    for f_path, files in folders.items():
        role = folder_roles.get(f_path, "Module Layer")
        file_preview = ", ".join(files[:15]) + ("..." if len(files) > 15 else "")
        folder_doc_parts.append(f"### Directory: `{f_path}/`\n- **Architectural Role**: {role}\n- **Files ({len(files)})**: {file_preview}\n")
    docs.append(("GitHub_Repository_Folder_Structure_and_Modules.md", "\n".join(folder_doc_parts)))

    # Document 3: Source Code Components, API Routes & Business Logic (For Chapters 2 & 4)
    code_samples = repo_data.get("sample_code_files", {})
    if code_samples:
        src_parts = ["# Extracted Source Code Components, API Endpoints & Logic\n"]
        for p, code in list(code_samples.items())[:20]:
            src_parts.append(f"## Module File: `{p}`\n```\n{code}\n```\n")
        docs.append(("GitHub_Source_Code_Components_and_Endpoints.md", "\n".join(src_parts)))

    # Document 4: Dependencies, Libraries & Environment (For Chapters 2 & 4)
    dep_content = repo_data.get("dependency_content", "")
    config_files = repo_data.get("config_files", [])
    dep_parts = [
        f"# Project Dependencies, Toolchain & Configuration",
        f"Detected Tech Stack: {', '.join(analysis.get('tech_stack', []))}\n",
        f"## Dependency Manifest (`{repo_data.get('dependency_file', 'Manifest')}`)\n```\n{dep_content}\n```\n",
        f"## Configuration & Infrastructure Files\n" + "\n".join([f"- `{c}`" for c in config_files[:25]])
    ]
    docs.append(("GitHub_Dependencies_and_Environment.md", "\n".join(dep_parts)))

    # Document 5: Tests & Quality Assurance (For Chapter 4)
    test_files = repo_data.get("test_files", [])
    if test_files:
        test_parts = [
            "# Testing Suite, Test Cases & Quality Assurance",
            "Discovered Test Suites in Repository:\n" + "\n".join([f"- `{t}`" for t in test_files[:30]])
        ]
        docs.append(("GitHub_Tests_and_Quality_Assurance.md", "\n".join(test_parts)))

    # Document 6: Technical README & Documentation (For Chapters 1 & 6)
    readme_content = repo_data.get("readme_content", "")
    if readme_content:
        docs.append(("GitHub_README_and_Documentation.md", f"# Technical Documentation & README\n\n{readme_content}"))

    # Chunk and embed each document into ChromaDB
    for filename, content in docs:
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}_{filename}"
        file_path.write_text(content, encoding="utf-8")

        chunks = chunk_text(content)
        if chunks:
            count = add_chunks(project_id, chunks, filename)
            total_chunks += count

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

    logger.success(f"Indexed {total_chunks} exhaustive code, folder & SQL chunks from GitHub repository '{repo_data.get('repo')}'")

    # Generate Chapter 3 Architecture Diagram and ER Diagram
    try:
        from app.services.diagram_service import generate_diagram_image
        diag_meta = {
            "title": analysis.get("title"),
            "tech_stack": analysis.get("tech_stack", []),
            "database_used": analysis.get("database_used"),
            "modules": analysis.get("modules", []),
            "tables": repo_data.get("parsed_tables", []),
        }
        await generate_diagram_image(
            project_id=project_id,
            diagram_type="ch3_architecture_diagram",
            prompt=f"System Architecture Diagram for {analysis.get('title')}",
            title=analysis.get("title", "System"),
            context_meta=diag_meta
        )
        await generate_diagram_image(
            project_id=project_id,
            diagram_type="ch3_er_diagram",
            prompt=f"Database ER Diagram for {analysis.get('title')}",
            title=analysis.get("title", "Database"),
            context_meta=diag_meta
        )
        logger.success("Pre-generated Chapter 3 Architecture Diagram and ER Diagram.")
    except Exception as exc:
        logger.warning(f"Initial diagram generation warning: {exc}")

    return total_chunks
