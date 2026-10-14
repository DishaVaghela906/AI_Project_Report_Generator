"""
Diagram Service — Hugging Face Text-to-Image & Technical Diagram Generation.

Generates technical diagrams (System Architecture, ER Diagrams, Flowcharts, DFDs)
for academic report chapters:
1. Calls Hugging Face's Text-to-Image Inference API (e.g. FLUX.1, Stable Diffusion XL)
   using HF_API_KEY from environment/settings.
2. If Hugging Face API is unavailable/unauthorized, automatically falls back to a high-resolution,
   crisp PIL-rendered academic schematic diagram.
3. Automatically embeds the generated diagrams into Chapter 3 (System Design) and other chapters.
"""
from __future__ import annotations

import base64
import io
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# Hugging Face Models and Endpoints
# ─────────────────────────────────────────────────────────────────────────────

HF_IMAGE_MODELS = [
    settings.HF_IMAGE_MODEL or "Maelstrome/mermaid-gemmma-7b",
    "Maelstrome/mermaid-gemmma-7b",
    "Maelstrome/mermaid-gemma-7b",
]


_hf_token_valid: Dict[str, bool] = {}


async def generate_diagram_image(
    project_id: str,
    diagram_type: str,
    prompt: str,
    title: str = "System Diagram",
    context_meta: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Path]:
    """
    Generates a technical diagram image using Hugging Face Text-to-Image API.
    Falls back to a crisp PIL-rendered vector-style diagram if the HF API is unavailable.

    Returns:
        (image_url, local_file_path)
    """
    context_meta = context_meta or {}
    out_dir = Path(settings.DIAGRAMS_DIR) / project_id
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_name = re.sub(r"[^\w\-]", "_", diagram_type).lower()
    file_name = f"{clean_name}.png"
    out_path = out_dir / file_name
    relative_url = f"/api/v1/diagrams/{project_id}/{file_name}"

    # 1. Try Hugging Face Inference API (if token has not previously failed auth)
    hf_token = settings.HF_API_KEY or os.environ.get("HF_API_KEY") or os.environ.get("HUGGINGFACE_API_KEY")
    token_str = hf_token.strip() if hf_token else ""
    if token_str and _hf_token_valid.get(token_str) is not False:
        img_bytes = await _generate_via_huggingface(token_str, prompt)
        if img_bytes:
            try:
                out_path.write_bytes(img_bytes)
                logger.success(f"Generated diagram via Hugging Face API: {out_path}")
                return relative_url, out_path
            except Exception as e:
                logger.debug(f"Failed to write Hugging Face image to disk: {e}")

    # 2. Crisp Technical Diagram Renderer
    logger.info(f"Rendering technical diagram via internal renderer for '{diagram_type}'")
    _render_technical_diagram(out_path, diagram_type, title, context_meta)
    return relative_url, out_path


async def _render_mermaid_to_png(mermaid_code: str) -> Optional[bytes]:
    """Renders Mermaid code into a high-resolution PNG image via mermaid.ink service."""
    try:
        clean_code = mermaid_code.strip()
        if "```mermaid" in clean_code:
            match = re.search(r"```mermaid\s*(.*?)\s*```", clean_code, re.DOTALL)
            if match:
                clean_code = match.group(1).strip()
        elif "```" in clean_code:
            match = re.search(r"```\s*(.*?)\s*```", clean_code, re.DOTALL)
            if match:
                clean_code = match.group(1).strip()

        # Focus on Mermaid block start if preamble exists
        for kw in ["erDiagram", "graph TD", "graph LR", "flowchart TD", "classDiagram", "sequenceDiagram"]:
            if kw in clean_code:
                clean_code = clean_code[clean_code.find(kw):]
                break

        b64 = base64.b64encode(clean_code.encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/img/{b64}"
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 200:
                return resp.content
    except Exception as e:
        logger.debug(f"Mermaid rendering via external service skipped: {e}")
    return None


async def _generate_via_huggingface(api_key: str, prompt: str) -> Optional[bytes]:
    """
    Calls Hugging Face inference endpoints.
    Supports Mermaid code generation models (like Maelstrome/mermaid-gemmma-7b).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "AI-Project-Report-Generator/1.0",
    }
    
    technical_prompt = (
        f"Generate clean Mermaid.js diagram code for an academic engineering project report: {prompt}. "
        "Output valid Mermaid syntax for architecture flowchart or erDiagram."
    )

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for model in HF_IMAGE_MODELS:
            url = f"https://router.huggingface.co/hf-inference/models/{model}"
            try:
                resp = await client.post(url, headers=headers, json={"inputs": technical_prompt})
                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "")
                    if "image" in content_type:
                        return resp.content

                    try:
                        data = resp.json()
                        gen_text = ""
                        if isinstance(data, list) and len(data) > 0:
                            gen_text = data[0].get("generated_text", "")
                        elif isinstance(data, dict):
                            gen_text = data.get("generated_text", "")
                        if gen_text:
                            img_bytes = await _render_mermaid_to_png(gen_text)
                            if img_bytes:
                                logger.success(f"Rendered Mermaid diagram image from model '{model}'")
                                return img_bytes
                    except Exception:
                        if len(resp.content) > 1000:
                            return resp.content

                elif resp.status_code in (401, 403):
                    # Mark token as unauthorized for inference to prevent repeated network calls and warnings
                    _hf_token_valid[api_key] = False
                    logger.debug(f"HF model '{model}' returned {resp.status_code}. Using built-in renderer.")
                    break
                elif resp.status_code == 503:
                    logger.debug(f"Hugging Face model '{model}' is currently loading (503).")
                    break
                else:
                    logger.debug(f"HF model '{model}' returned status {resp.status_code}")
            except Exception as e:
                logger.debug(f"HF request to {url} failed: {e}")
                continue

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Technical Schematic Generator (High-Resolution PIL Fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _render_technical_diagram(
    out_path: Path,
    diagram_type: str,
    title: str,
    meta: Dict[str, Any]
) -> None:
    """Renders clean, vector-style engineering diagrams using PIL."""
    d_type = diagram_type.lower()
    if "er" in d_type or "database" in d_type or "schema" in d_type:
        _render_er_diagram(out_path, title, meta)
    elif "flowchart" in d_type or "dfd" in d_type or "process" in d_type:
        _render_flowchart_diagram(out_path, title, meta)
    else:
        _render_architecture_diagram(out_path, title, meta)


def _render_architecture_diagram(out_path: Path, title: str, meta: Dict[str, Any]) -> None:
    """Renders a 3-tier System Architecture Diagram."""
    width, height = 1200, 720
    img = Image.new("RGB", (width, height), color="#F9F6F0")
    draw = ImageDraw.Draw(img)

    # Header Bar
    draw.rectangle([(0, 0), (width, 65)], fill="#1F1C18")
    draw.text((35, 22), f"SYSTEM ARCHITECTURE DIAGRAM — {title.upper()}", fill="#F9F6F0")

    tech_stack = meta.get("tech_stack", ["React", "FastAPI", "Supabase", "ChromaDB"])
    if isinstance(tech_stack, str):
        tech_stack = [t.strip() for t in tech_stack.split(",") if t.strip()]

    database_name = meta.get("database_used", "PostgreSQL / Supabase")
    modules = meta.get("modules", ["User Authentication", "Core Processing Engine", "Database Storage", "Reporting Dashboard"])

    # 3 Architecture Tiers: Presentation Tier, Application Tier, Data Persistence Tier
    tiers = [
        {
            "name": "PRESENTATION TIER (CLIENT)",
            "sub": "Responsive Web Interface & State Management",
            "items": [t for t in tech_stack if any(k in t.lower() for k in ["react", "vue", "next", "html", "css", "js", "ui"])] or ["Interactive Web UI", "Client State Manager", "REST API Client"],
            "color": "#EFE9DE",
            "border": "#8C7355"
        },
        {
            "name": "APPLICATION & BUSINESS LOGIC TIER",
            "sub": "RESTful Routers, AI Orchestration & Controllers",
            "items": modules[:4] if modules else ["Authentication Controller", "Core Business Logic", "Vector Search Pipeline", "Export Engine"],
            "color": "#FFFFFF",
            "border": "#1F1C18"
        },
        {
            "name": "DATA PERSISTENCE & STORAGE TIER",
            "sub": "Relational Tables, Vector Store & File Storage",
            "items": [database_name, "ChromaDB Vector Embeddings", "Local Document Store", "Relational Schema Tables"],
            "color": "#EFE9DE",
            "border": "#8C7355"
        }
    ]

    tier_w = 330
    tier_h = 460
    y_start = 120
    x_positions = [60, 435, 810]

    for idx, tier in enumerate(tiers):
        x0 = x_positions[idx]
        y0 = y_start
        x1 = x0 + tier_w
        y1 = y0 + tier_h

        # Shadow & Box
        draw.rectangle([(x0+5, y0+5), (x1+5, y1+5)], fill="#DFD8CC")
        draw.rectangle([(x0, y0), (x1, y1)], fill=tier["color"], outline=tier["border"], width=2)

        # Tier Header
        draw.rectangle([(x0, y0), (x1, y0+55)], fill="#2C2621")
        draw.text((x0+14, y0+12), tier["name"][:30], fill="#FFFFFF")
        draw.text((x0+14, y0+34), tier["sub"][:38], fill="#D3C9B8")

        # Tier Component Cards
        card_y = y0 + 75
        for item in tier["items"][:5]:
            draw.rectangle([(x0+16, card_y), (x1-16, card_y+54)], fill="#FAF8F5", outline="#B5A995", width=1)
            draw.text((x0+28, card_y+16), f"• {str(item)[:32]}", fill="#1F1C18")
            card_y += 72

    # Draw Directional Connector Arrows between Tiers
    arrow_color = "#8C7355"
    # Tier 1 -> Tier 2
    draw.line([(390, 320), (435, 320)], fill=arrow_color, width=4)
    draw.polygon([(435, 320), (423, 314), (423, 326)], fill=arrow_color)
    draw.line([(435, 360), (390, 360)], fill=arrow_color, width=4)
    draw.polygon([(390, 360), (402, 354), (402, 366)], fill=arrow_color)
    draw.text((392, 298), "HTTP / JSON", fill="#666666")

    # Tier 2 -> Tier 3
    draw.line([(765, 320), (810, 320)], fill=arrow_color, width=4)
    draw.polygon([(810, 320), (798, 314), (798, 326)], fill=arrow_color)
    draw.line([(810, 360), (765, 360)], fill=arrow_color, width=4)
    draw.polygon([(765, 360), (777, 354), (777, 366)], fill=arrow_color)
    draw.text((770, 298), "SQL / CRUD", fill="#666666")

    # Footer Caption
    draw.rectangle([(0, height-45), (width, height)], fill="#EFE9DE")
    draw.text((35, height-32), f"Figure 3.1: Architecture Diagram for {title} — 3-Tier Enterprise Structure", fill="#444444")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def _render_er_diagram(out_path: Path, title: str, meta: Dict[str, Any]) -> None:
    """Renders a clean Entity-Relationship (ER) Database Schema Diagram."""
    width, height = 1200, 750
    img = Image.new("RGB", (width, height), color="#FAF8F5")
    draw = ImageDraw.Draw(img)

    # Header Bar
    draw.rectangle([(0, 0), (width, 65)], fill="#1F1C18")
    draw.text((35, 22), f"DATABASE ENTITY-RELATIONSHIP (ER) DIAGRAM — {title.upper()}", fill="#F9F6F0")

    tables = meta.get("tables", [])
    if not tables:
        # Fallback sample tables based on project
        tables = [
            {
                "table_name": "users",
                "columns": [
                    {"name": "id", "type": "SERIAL", "primary_key": True},
                    {"name": "email", "type": "VARCHAR(255)", "primary_key": False},
                    {"name": "full_name", "type": "VARCHAR(120)", "primary_key": False},
                    {"name": "role", "type": "VARCHAR(50)", "primary_key": False},
                    {"name": "created_at", "type": "TIMESTAMP", "primary_key": False},
                ]
            },
            {
                "table_name": "projects",
                "columns": [
                    {"name": "id", "type": "UUID", "primary_key": True},
                    {"name": "user_id", "type": "INT", "foreign_key": True},
                    {"name": "title", "type": "VARCHAR(255)", "primary_key": False},
                    {"name": "tech_stack", "type": "JSONB", "primary_key": False},
                    {"name": "github_url", "type": "TEXT", "primary_key": False},
                    {"name": "created_at", "type": "TIMESTAMP", "primary_key": False},
                ]
            },
            {
                "table_name": "chapters",
                "columns": [
                    {"name": "id", "type": "UUID", "primary_key": True},
                    {"name": "project_id", "type": "UUID", "foreign_key": True},
                    {"name": "chapter_number", "type": "INT", "primary_key": False},
                    {"name": "chapter_title", "type": "VARCHAR(200)", "primary_key": False},
                    {"name": "content", "type": "TEXT", "primary_key": False},
                    {"name": "status", "type": "VARCHAR(50)", "primary_key": False},
                ]
            }
        ]

    box_w = 330
    x_positions = [60, 435, 810]
    y_start = 120

    for idx, table in enumerate(tables[:3]):
        x0 = x_positions[idx]
        y0 = y_start
        t_name = table.get("table_name", f"table_{idx+1}")
        columns = table.get("columns", [])[:8]
        box_h = 60 + len(columns) * 32

        x1 = x0 + box_w
        y1 = y0 + box_h

        # Box shadow & border
        draw.rectangle([(x0+4, y0+4), (x1+4, y1+4)], fill="#E2DDD5")
        draw.rectangle([(x0, y0), (x1, y1)], fill="#FFFFFF", outline="#8C7355", width=2)

        # Table Header
        draw.rectangle([(x0, y0), (x1, y0+42)], fill="#2C2621")
        draw.text((x0+14, y0+14), f"TABLE: {t_name.upper()}", fill="#FFFFFF")

        # Column Entries
        cy = y0 + 52
        for col in columns:
            c_name = col.get("name", "field")
            c_type = col.get("type", "TEXT")
            is_pk = col.get("primary_key", False)
            is_fk = col.get("foreign_key", False)

            tag = "[PK] " if is_pk else ("[FK] " if is_fk else "     ")
            tag_color = "#8C7355" if is_pk else ("#4A6B82" if is_fk else "#1F1C18")
            draw.text((x0+14, cy), f"{tag}{c_name[:18]}", fill=tag_color)
            draw.text((x0+210, cy), f"{c_type[:13]}", fill="#666666")
            cy += 32

    # Draw ER Relationship lines (Table 1 -< Table 2 -< Table 3)
    arrow_color = "#8C7355"
    # Table 1 (users) -> Table 2 (projects)
    draw.line([(390, 240), (435, 240)], fill=arrow_color, width=3)
    draw.polygon([(435, 240), (423, 234), (423, 246)], fill=arrow_color)
    draw.text((395, 220), "1:N", fill="#555555")

    # Table 2 (projects) -> Table 3 (chapters)
    draw.line([(765, 240), (810, 240)], fill=arrow_color, width=3)
    draw.polygon([(810, 240), (798, 234), (798, 246)], fill=arrow_color)
    draw.text((770, 220), "1:N", fill="#555555")

    # Legend at bottom
    draw.rectangle([(60, height-130), (width-60, height-60)], fill="#EFE9DE", outline="#D3C9B8", width=1)
    draw.text((80, height-115), "ER DIAGRAM NOTATION LEGEND:", fill="#1F1C18")
    draw.text((80, height-90), "[PK] Primary Key (Unique Identifier)    |    [FK] Foreign Key (Relational Constraint)    |    ──> 1-to-Many Relationship", fill="#555555")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def _render_flowchart_diagram(out_path: Path, title: str, meta: Dict[str, Any]) -> None:
    """Renders a Data Flow & Process Flowchart Diagram."""
    width, height = 1100, 680
    img = Image.new("RGB", (width, height), color="#FAF8F5")
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (width, 60)], fill="#1F1C18")
    draw.text((35, 20), f"PROCESS FLOW & SYSTEM ARCHITECTURE FLOWCHART — {title.upper()}", fill="#F9F6F0")

    steps = [
        "1. Client User Input / Request",
        "2. API Authentication & Validation",
        "3. Core Business Logic Processing",
        "4. Database Persistence & ChromaDB RAG",
        "5. Output Synthesis & Document Rendering"
    ]

    box_w, box_h = 550, 64
    y = 110
    cx = width // 2

    for idx, step in enumerate(steps):
        x0, y0 = cx - (box_w // 2), y
        x1, y1 = x0 + box_w, y0 + box_h

        draw.rectangle([(x0+4, y0+4), (x1+4, y1+4)], fill="#DFD8CC")
        draw.rectangle([(x0, y0), (x1, y1)], fill="#FFFFFF", outline="#8C7355", width=2)
        draw.text((x0+24, y0+22), step, fill="#1F1C18")

        if idx < len(steps) - 1:
            arrow_y = y1
            draw.line([(cx, arrow_y), (cx, arrow_y + 36)], fill="#8C7355", width=3)
            draw.polygon([(cx, arrow_y + 36), (cx - 6, arrow_y + 26), (cx + 6, arrow_y + 26)], fill="#8C7355")
            y = arrow_y + 42
        else:
            y = y1 + 30

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


# ─────────────────────────────────────────────────────────────────────────────
# Automatic Chapter Diagram Injection
# ─────────────────────────────────────────────────────────────────────────────

async def ensure_chapter_diagrams(
    project_id: str,
    chapter_number: int,
    chapter_content: str,
    project_data: Dict[str, Any],
) -> str:
    """
    Inspects chapter content, generates required diagram images via Hugging Face/internal
    renderer, and injects clean markdown image tags into the content.
    """
    title = project_data.get("title", "Software System")
    tables_meta = project_data.get("parsed_tables") or []
    meta = {
        "title": title,
        "tech_stack": project_data.get("tech_stack", []),
        "database_used": project_data.get("database_used", "PostgreSQL"),
        "modules": project_data.get("modules", []),
        "tables": tables_meta,
    }

    updated_content = chapter_content

    try:
        if chapter_number == 3:
            # Chapter 3: System Design — Requires Architecture Diagram & ER Diagram
            # 1. System Architecture Diagram
            arch_tag = f"/api/v1/diagrams/{project_id}/ch3_architecture_diagram.png"
            if arch_tag not in updated_content:
                prompt = (
                    f"Software system architecture diagram for {title}, showing Presentation Layer, "
                    f"Application Router Layer, and Database Layer ({meta['database_used']})"
                )
                arch_url, _ = await generate_diagram_image(
                    project_id, "ch3_architecture_diagram", prompt, title=title, context_meta=meta
                )
                img_markdown = f"\n\n![Figure 3.1: System Architecture Diagram]({arch_url})\n\n"

                # Inject under 3.3 System Design or 3.1
                if "3.3" in updated_content:
                    updated_content = re.sub(
                        r"(3\.3[^\n]*\n)",
                        r"\1" + img_markdown,
                        updated_content,
                        count=1
                    )
                else:
                    updated_content += f"\n\n### 3.3 System Architecture\n{img_markdown}"

            # 2. Database ER Diagram
            er_tag = f"/api/v1/diagrams/{project_id}/ch3_er_diagram.png"
            if er_tag not in updated_content:
                prompt = (
                    f"Entity Relationship database ER diagram for {title}, displaying relational tables, "
                    f"attributes, primary keys and foreign keys for database {meta['database_used']}"
                )
                er_url, _ = await generate_diagram_image(
                    project_id, "ch3_er_diagram", prompt, title=title, context_meta=meta
                )
                er_markdown = f"\n\n![Figure 3.2: Database Entity-Relationship (ER) Diagram]({er_url})\n\n"

                # Inject under 3.5.1 ER Diagrams or 3.5 Database Design
                if "3.5.1" in updated_content:
                    updated_content = re.sub(
                        r"(3\.5\.1[^\n]*\n)",
                        r"\1" + er_markdown,
                        updated_content,
                        count=1
                    )
                elif "3.5" in updated_content:
                    updated_content = re.sub(
                        r"(3\.5[^\n]*\n)",
                        r"\1" + er_markdown,
                        updated_content,
                        count=1
                    )
                else:
                    updated_content += f"\n\n### 3.5.1 Database ER Diagram\n{er_markdown}"

        elif chapter_number == 2:
            # Chapter 2: SDLC / Requirement Flow (only if schedule/SDLC exists)
            sdlc_tag = f"/api/v1/diagrams/{project_id}/ch2_sdlc_diagram.png"
            if "2.5" in updated_content and sdlc_tag not in updated_content:
                prompt = f"Software development life cycle (SDLC) Agile iterative process diagram for {title}"
                sdlc_url, _ = await generate_diagram_image(
                    project_id, "ch2_sdlc_diagram", prompt, title=title, context_meta=meta
                )
                img_markdown = f"\n\n![Figure 2.1: SDLC Iterative Development Workflow]({sdlc_url})\n\n"
                updated_content = re.sub(r"(2\.5[^\n]*\n)", r"\1" + img_markdown, updated_content, count=1)

        elif chapter_number == 4:
            # Chapter 4: Implementation Process Flowchart
            flow_tag = f"/api/v1/diagrams/{project_id}/ch4_process_flowchart.png"
            if ("4.3" in updated_content or "4.4" in updated_content) and flow_tag not in updated_content:
                prompt = f"Engineering implementation workflow and testing pipeline flowchart for {title}"
                flow_url, _ = await generate_diagram_image(
                    project_id, "ch4_process_flowchart", prompt, title=title, context_meta=meta
                )
                img_markdown = f"\n\n![Figure 4.1: Implementation & Execution Flowchart]({flow_url})\n\n"
                target_sec = "4.3" if "4.3" in updated_content else "4.4"
                updated_content = re.sub(rf"({target_sec}[^\n]*\n)", r"\1" + img_markdown, updated_content, count=1)

    except Exception as exc:
        logger.warning(f"Error auto-generating diagrams for Chapter {chapter_number}: {exc}")

    return updated_content


def get_diagram_path(project_id: str, filename: str) -> Optional[Path]:
    """Returns local path for a diagram file if it exists."""
    safe_name = os.path.basename(filename)
    path = Path(settings.DIAGRAMS_DIR) / project_id / safe_name
    return path if path.exists() else None
