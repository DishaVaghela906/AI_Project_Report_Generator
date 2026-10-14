"""
Prompt Builder Service.

Constructs precise, context-rich prompts for each of the 6 report chapters.
Follows the exact MSU Baroda (Faculty of Technology & Engineering, CSE Department)
project report format guidelines.
"""
from __future__ import annotations

from app.models.schemas import ProjectCreateRequest


# ─── Chapter Metadata (MSU Baroda Format) ─────────────────────────────────────

CHAPTER_METADATA: dict[int, dict] = {
    1: {
        "title": "Introduction",
        "sections": [
            "1.1 Introduction to Project",
            "1.2 Project Category (Internet Based / Application or System Development / Research Based / Industry Automation / Network or System Administration)",
            "1.3 Objectives",
            "1.4 Problem Formulation",
            "1.5 Identification / Recognition of Need",
            "1.6 Existing System",
            "1.7 Proposed System",
            "1.8 Unique Features of the System",
        ],
        "word_count_guide": "Each section should be 200–400 words. Total chapter: 1500–2500 words.",
        "humanize_note": (
            "Write as a student explaining their project to a faculty examiner. "
            "Use phrases like 'The proposed system aims to...', 'One of the key challenges observed...', "
            "'During the requirement gathering phase, it was identified that...'. "
            "Avoid robotic enumeration. Make each section flow naturally into the next."
        ),
    },
    2: {
        "title": "Requirement Analysis and System Specification",
        "sections": [
            "2.1 Feasibility Study",
            "  2.1.1 Technical Feasibility",
            "  2.1.2 Economical Feasibility",
            "  2.1.3 Operational Feasibility",
            "2.2 Software Requirement Specification (SRS)",
            "  2.2.1 Data Requirement",
            "  2.2.2 Functional Requirements",
            "  2.2.3 Performance Requirements",
            "  2.2.4 Dependability Requirements",
            "  2.2.5 Maintainability Requirements",
            "  2.2.6 Security Requirements",
            "  2.2.7 Look and Feel Requirements",
            "2.3 Validation",
            "2.4 Expected Hurdles",
            "2.5 SDLC Model to be Used",
        ],
        "word_count_guide": "SRS section must be detailed with numbered functional requirements (FR1, FR2…). Total chapter: 2000–3000 words.",
        "humanize_note": (
            "Write SRS requirements in a formal but student-natural tone. "
            "For functional requirements, use the pattern: 'The system shall allow the user to...'. "
            "For feasibility, write genuine paragraph analysis, not just a checklist. "
            "The SDLC section should justify WHY that model was chosen for this specific project."
        ),
    },
    3: {
        "title": "System Design",
        "sections": [
            "3.1 Design Approach (Function-Oriented or Object-Oriented)",
            "3.2 Detail Design",
            "3.3 System Design using Structured Analysis & Design Tools",
            "  3.3.1 Data Flow Diagram (DFD) — Level 0 (Context Diagram) and Level 1",
            "  3.3.2 Data Dictionary",
            "  3.3.3 Flowchart of System Process",
            "  3.3.4 UML Diagrams (Use Case, Class, Sequence or Activity Diagram)",
            "3.4 User Interface Design",
            "3.5 Database Design",
            "  3.5.1 ER Diagrams",
            "  3.5.2 Normalization (1NF, 2NF, 3NF)",
            "  3.5.3 Database Manipulation (CRUD Operations)",
            "  3.5.4 Database Connection Controls and Strings",
            "3.6 Methodology",
        ],
        "word_count_guide": "Most detailed chapter. DFD and ER Diagram sections must reference Figure 3.1 and Figure 3.2. Total chapter: 2500–3500 words.",
        "humanize_note": (
            "For DFD, describe each level textually before referencing the diagram. "
            "Write: 'As shown in Figure 3.1, the system receives input from...' "
            "For the ER Diagram, describe relationships in plain English first: 'A User can place multiple Orders. Each Order belongs to exactly one User.' "
            "Normalization must explicitly list which tables are in 1NF, 2NF, 3NF and why. "
            "Database connection section should mention the actual technology used (e.g., Supabase, PostgreSQL, SQLAlchemy)."
        ),
    },
    4: {
        "title": "Implementation, Testing, and Maintenance",
        "sections": [
            "4.1 Introduction to Languages, IDEs, Tools and Technologies Used for Implementation",
            "4.2 Coding Standards of the Language Used",
            "4.3 Project Scheduling",
            "  4.3.1 PERT Chart Description",
            "  4.3.2 GANTT Chart Description",
            "4.4 Testing Techniques and Test Plans",
            "  4.4.1 Unit Testing",
            "  4.4.2 Integration Testing",
            "  4.4.3 System Testing",
            "  4.4.4 User Acceptance Testing (UAT)",
            "  4.4.5 Test Cases Table (include actual test cases with input, expected output, actual output, pass/fail)",
        ],
        "word_count_guide": "Test cases table is mandatory. Minimum 10 test cases. Total chapter: 2000–3000 words.",
        "humanize_note": (
            "For technology justification, explain WHY each tool was chosen — not just WHAT it is. "
            "Write: 'React was selected for the frontend because of its component-based architecture, which allowed...' "
            "Test cases must read like real testing done by the student, not hypothetical ones. "
            "Coding standards should mention actual naming conventions, file structure, and comment style used in the project."
        ),
    },
    5: {
        "title": "Results and Discussions",
        "sections": [
            "5.1 User Interface Representation of the System",
            "  5.1.1 Brief Description of Various Modules of the System",
            "5.2 Snapshots of System with Brief Detail of Each Screen",
            "5.3 Back-End Representation",
            "  5.3.1 Snapshots of Database Tables with Brief Description",
        ],
        "word_count_guide": (
            "This chapter focuses on showing what was built. "
            "Each module description should be 150-250 words. "
            "Snapshot placeholders must clearly say '[Insert Screenshot: Module Name — Description]'. "
            "Total chapter: 1500–2500 words."
        ),
        "humanize_note": (
            "Describe each module as though walking the examiner through the running application. "
            "Write: 'The Login Module presents the user with a clean authentication screen where...'. "
            "For database snapshots, describe what data is visible in the table, what each column represents, and how it relates to the application functionality."
        ),
    },
    6: {
        "title": "Conclusion and Future Scope",
        "sections": [
            "6.1 Conclusion",
            "6.2 Limitations of the Current System",
            "6.3 Future Scope",
            "References / Bibliography",
        ],
        "word_count_guide": "Conclusion must NOT exceed 2 pages (approximately 600 words). References must be in IEEE format. Total chapter: 800–1200 words.",
        "humanize_note": (
            "Conclusion should honestly reflect on what was achieved vs. what was planned. "
            "Write: 'The system was successfully developed and tested for... However, during implementation, it was observed that...' "
            "Future scope should be realistic and specific, not generic. "
            "References must be real IEEE-format citations relevant to the domain (e.g., papers on the tech stack, similar systems, algorithms used)."
        ),
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
    word_guide = meta.get("word_count_guide", "")
    humanize_note = meta.get("humanize_note", "")

    # ── RAG context block ─────────────────────────────────────────────────────
    if context_chunks:
        rag_block = "\n\n".join(context_chunks)
        context_section = f"""
## Analyzed Project Source Code and Documents:
The following content was automatically extracted from the project's GitHub repository and uploaded files.
Use this to write accurate, project-specific content — not generic placeholders.
---
{rag_block}
---
"""
    else:
        context_section = "## No project documents were uploaded. Use only the project details provided below.\n"

    # ── Project info block ────────────────────────────────────────────────────
    objectives = "\n".join(f"  - {o}" for o in (project.get("objectives") or []))
    tech_stack = ", ".join(project.get("tech_stack") or [])
    modules = ", ".join(project.get("modules") or [])
    team = "; ".join(
        f"{m.get('name')} ({m.get('role')})" for m in (project.get("team_members") or [])
    )
    team_names = "; ".join(
        m.get("name", "") for m in (project.get("team_members") or [])
    )

    project_info = f"""
## Project Details:
- **Title**: {project.get("title", "N/A")}
- **Domain**: {project.get("domain", "N/A")}
- **Category**: {project.get("category", "N/A")}
- **Problem Statement**: {project.get("problem_statement", "N/A")}
- **Objectives**:
{objectives if objectives else "  - Not specified"}
- **Technology Stack**: {tech_stack or "Not specified"}
- **Major Modules**: {modules or "Not specified"}
- **Methodology**: {project.get("methodology", "Agile Development")}
- **SDLC Model**: {project.get("sdlc_model", "Agile/Iterative")}
- **Database Used**: {project.get("database_used", "Not specified")}
- **Team Members**: {team or "Not specified"}
- **Guide Name**: {project.get("guide_name", "Project Guide")}
- **Institution**: {project.get("institution", "N/A")}
- **Department**: {project.get("department", "Department of Computer Science and Engineering")}
- **Academic Year**: {project.get("academic_year", "2024-25")}
- **Existing System Limitations**: {project.get("existing_system", "Not provided")}
- **Proposed System**: {project.get("proposed_system", "Not provided")}
- **Unique Features**: {", ".join(project.get("unique_features") or []) or "Not specified"}
- **Architecture Summary**: {project.get("architecture_summary", "Not provided")}
- **Implementation Details**: {project.get("implementation_details", "Not provided")}
- **Testing Details**: {project.get("testing_details", "Not provided")}
- **Results**: {project.get("results", "Not provided")}
- **Future Scope**: {project.get("future_scope", "Not provided")}
"""

    extra = f"\n## Additional Instructions from Student:\n{extra_instructions}\n" \
        if extra_instructions else ""

    prompt = f"""You are a senior academic technical writer helping engineering students at the Faculty of Technology & Engineering, Department of Computer Science and Engineering, The Maharaja Sayajirao University of Baroda produce their final project report.

{project_info}
{context_section}
{extra}
## Your Task:
Write **Chapter {chapter_number}: {meta["title"]}** for this project report.

This report follows the MSU Baroda Minor/Major Project Report format exactly.

The chapter MUST cover all of the following sections:
{sections_text}

## Humanized Academic Writing Rules (MANDATORY):
{humanize_note}

## General Writing Standards:
1. **Tone**: Formal, confident, and academic — but written as if by a knowledgeable student, not a robot. Avoid generic AI filler phrases like "In today's rapidly evolving world..." or "This project aims to leverage cutting-edge technologies...".
2. **Section Headings**: Use exact numbered headings as specified (e.g., **1.1 Introduction to Project**, **2.2.3 Performance Requirements**).
3. **Paragraph depth**: Every section must have at minimum 3 solid paragraphs unless it is a table/list section.
4. **Project specificity**: Every claim, figure, feature, or requirement must directly relate to THIS project — use the actual project title, module names, database tables, and tech stack from the project details above.
5. **Length guidance**: {word_guide}
6. **Tables**: Use proper Markdown table syntax (| Column | Column |) for requirements, test cases, and comparisons.
7. **Figure references**: When referencing a diagram, write "As illustrated in Figure {chapter_number}.X..." — this tells the reader where to look.
8. **No placeholders unless necessary**: Only use "[Insert Screenshot: ...]" for actual UI screenshots (Chapter 5), since those require the running application. All other content must be written in full.
9. **Output format**: Clean, well-structured Markdown. Start directly with the chapter heading. Do not add any preamble or commentary before the chapter content.

Now write Chapter {chapter_number}: {meta["title"]}:
"""
    return prompt.strip()


def get_chapter_title(chapter_number: int) -> str:
    return CHAPTER_METADATA[chapter_number]["title"]
