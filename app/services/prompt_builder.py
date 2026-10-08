"""
Prompt Builder Service.

Constructs precise, context-rich prompts for each of the 6 report chapters.
Each chapter has its own structured template. Retrieved RAG context is injected
into the prompt before the chapter-specific instructions.
"""
from __future__ import annotations

from app.models.schemas import ProjectCreateRequest


# ─── Chapter metadata ─────────────────────────────────────────────────────────

CHAPTER_METADATA: dict[int, dict] = {
    1: {
        "title": "Introduction",
        "sections": [
            "1.1 Introduction to Project",
            "1.2 Project Category",
            "1.3 Objectives",
            "1.4 Problem Formulation",
            "1.5 Identification/Recognition of Need",
            "1.6 Existing System",
            "1.7 Proposed System",
            "1.8 Unique Features of the System",
        ],
    },
    2: {
        "title": "Requirement Analysis and System Specification",
        "sections": [
            "2.1 Feasibility Study (Technical, Economical, Operational)",
            "2.2 Software Requirement Specification (Data Requirement, Functional Requirement, "
            "Performance Requirement, Dependability Requirement, Maintainability, Security, Look and Feel)",
            "2.3 Validation",
            "2.4 Expected Hurdles",
            "2.5 SDLC Model to be Used",
        ],
    },
    3: {
        "title": "System Design",
        "sections": [
            "3.1 Design Approach (Function oriented or Object oriented)",
            "3.2 Detail Design",
            "3.3 System Design using DFDs, Data Dictionary, Structured Charts, Flowcharts or UML",
            "3.4 User Interface Design",
            "3.5 Database Design",
            "3.5.1 ER Diagrams",
            "3.5.2 Normalization",
            "3.5.3 Database Manipulation",
            "3.5.4 Database Connection Controls and Strings",
            "3.6 Methodology",
        ],
    },
    4: {
        "title": "Implementation, Testing, and Maintenance",
        "sections": [
            "4.1 Introduction to Languages, IDEs, Tools and Technologies Used",
            "4.2 Coding Standards of Language Used",
            "4.3 Project Scheduling (PERT, GANTT charts)",
            "4.4 Testing Techniques and Test Plans",
        ],
    },
    5: {
        "title": "Results and Discussions",
        "sections": [
            "5.1 User Interface Representation",
            "5.1.1 Brief Description of Various Modules",
            "5.2 Snapshots of System with Brief Details",
            "5.3 Back-End Representation",
            "5.3.1 Snapshots of Database Tables with Brief Description",
        ],
    },
    6: {
        "title": "Conclusion and Future Scope",
        "sections": [
            "6.1 Conclusion",
            "6.2 Future Scope",
            "References / Bibliography",
        ],
    },
}


def build_prompt(
    chapter_number: int,
    project: dict,
    context_chunks: list[str],
    extra_instructions: str | None = None,
) -> str:
    """
    Builds the full LLM prompt for a given chapter.

    Parameters
    ----------
    chapter_number   : 1 – 6
    project          : project data dict (from Supabase row)
    context_chunks   : retrieved RAG chunks from uploaded documents
    extra_instructions : optional student guidance

    Returns
    -------
    A fully-formatted prompt string.
    """
    meta = CHAPTER_METADATA[chapter_number]
    sections_text = "\n".join(f"  - {s}" for s in meta["sections"])

    # ── RAG context block ─────────────────────────────────────────────────────
    if context_chunks:
        rag_block = "\n\n".join(context_chunks)
        context_section = f"""
## Uploaded Project Documents (use this context to make the report accurate):
---
{rag_block}
---
"""
    else:
        context_section = "## No documents were uploaded for this project.\n"

    # ── Project info block ────────────────────────────────────────────────────
    objectives = "\n".join(f"  - {o}" for o in (project.get("objectives") or []))
    tech_stack = ", ".join(project.get("tech_stack") or [])
    modules = ", ".join(project.get("modules") or [])
    team = "; ".join(
        f"{m.get('name')} ({m.get('role')})" for m in (project.get("team_members") or [])
    )

    project_info = f"""
## Project Information:
- **Title**: {project.get("title", "N/A")}
- **Domain**: {project.get("domain", "N/A")}
- **Category**: {project.get("category", "N/A")}
- **Problem Statement**: {project.get("problem_statement", "N/A")}
- **Objectives**:
{objectives if objectives else "  - Not specified"}
- **Technology Stack**: {tech_stack or "Not specified"}
- **Major Modules**: {modules or "Not specified"}
- **Methodology**: {project.get("methodology", "N/A")}
- **SDLC Model**: {project.get("sdlc_model", "N/A")}
- **Database Used**: {project.get("database_used", "Not specified")}
- **Team Members**: {team or "Not specified"}
- **Institution**: {project.get("institution", "N/A")}
- **Department**: {project.get("department", "N/A")}
- **Academic Year**: {project.get("academic_year", "N/A")}
- **Existing System**: {project.get("existing_system", "Not provided")}
- **Proposed System**: {project.get("proposed_system", "Not provided")}
- **Unique Features**: {", ".join(project.get("unique_features") or []) or "Not specified"}
- **Implementation Details**: {project.get("implementation_details", "Not provided")}
- **Testing Details**: {project.get("testing_details", "Not provided")}
- **Results**: {project.get("results", "Not provided")}
- **Future Scope**: {project.get("future_scope", "Not provided")}
"""

    extra = f"\n## Additional Instructions from Student:\n{extra_instructions}\n" \
        if extra_instructions else ""

    prompt = f"""You are an expert academic technical writer helping students write formal project reports.

{project_info}
{context_section}
{extra}
## Your Task:
Write **Chapter {chapter_number}: {meta["title"]}** of the academic project report.

The chapter MUST include the following sections:
{sections_text}

## Writing Guidelines:
1. Write in a formal, academic tone suitable for a university-level engineering project report.
2. Each section must have a clear numbered heading (e.g., **1.1 Introduction to Project**).
3. Use complete paragraphs with a minimum of 3–5 sentences per section.
4. Draw accurate, specific details from the project information and uploaded documents provided above.
5. Do NOT invent technical details not present in the context — write "To be filled by student" for any missing specific data (e.g., screenshots, test cases).
6. Use bullet points, tables, or numbered lists where appropriate (e.g., for objectives, requirements, test cases).
7. Format the output in clean Markdown.
8. Start directly with the chapter heading — do not include preamble or commentary.

Now write Chapter {chapter_number}: {meta["title"]}:
"""
    return prompt.strip()


def get_chapter_title(chapter_number: int) -> str:
    return CHAPTER_METADATA[chapter_number]["title"]
