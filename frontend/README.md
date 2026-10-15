# AI Project Report Generator — Frontend Client

A modern, high-performance web interface for the **AI-Powered Academic Project Report Generator**. Built with **React 19** and **Vite**, this application provides engineering students and researchers with an interactive workspace to generate, edit, preview, and export syllabus-compliant engineering project reports with inline technical diagrams.

---

## 🎨 Design System & Aesthetics

The user interface follows an editorial **"Warm Beige & Charcoal Black"** aesthetic inspired by classic academic publications and modern minimal tooling:

* **Curated Color Palette**:
  * **80% Soft Warm Cream Beige** (`#F9F6F0`, `#F2ECE1`): Primary background and subtle cards that reduce eye fatigue during long reading and editing sessions.
  * **15% Deep Charcoal Black** (`#2C2621`, `#1F1C18`): High-contrast typography, primary action buttons, and active borders.
  * **5% Bronze & Muted Gold Accents** (`#8C7355`): Focus indicators, progress highlights, and status tags.
* **Typography**:
  * **Headings**: `Playfair Display` — Elegant editorial serif font for report covers, main titles, and section headers.
  * **Interface & Body Text**: `Plus Jakarta Sans` — Crisp, modern sans-serif for UI controls, inputs, and reading readability.
  * **Code & Markdown**: Monospace (`Courier New`, monospace) for code snippets, database schemas, and raw markdown editing.
* **Micro-interactions & Responsiveness**:
  * Subtle hover elevations and soft shadows (`rgba(44, 38, 33, 0.07)`).
  * Smooth chapter status transitions (`Pending`, `Generating...`, `Ready`).
  * Fully responsive two-column layout with collapsible sidebar and floating navigation.

---

## 📂 Folder Architecture

```text
frontend/
├── index.html                   # HTML entry point with Google Fonts preloads
├── package.json                 # Dependencies (React 19, Vite, Axios, Lucide, ReactMarkdown)
├── vite.config.js               # Vite configuration with /api & /health backend reverse proxy
├── public/                      # Static assets & favicon
└── src/
    ├── main.jsx                 # React root renderer
    ├── App.jsx                  # Top-level state coordinator, tab routing, and API handlers
    ├── App.css                  # App-specific utility styles
    ├── index.css                # Global design system, CSS variables, typography, and component styling
    └── components/
        ├── Header.jsx           # Top navigation bar, LLM health badge, tab switcher & auth controls
        ├── LandingHero.jsx      # Marketing hero, live simulation preview, features & call-to-actions
        ├── Sidebar.jsx          # Active project picker, file uploader, GitHub trigger & chapter progress
        ├── ChapterStudio.jsx    # Core chapter editor with live markdown rendering & inline diagram support
        ├── ProjectOverview.jsx  # Grounding parameters view (methodology, SDLC, tech stack, database)
        ├── FullReportPreview.jsx# Comprehensive multi-chapter continuous document view & export triggers
        ├── NewProjectModal.jsx  # Project creation modal with instant GitHub URL architectural analysis
        ├── ImportCodeModal.jsx  # Direct GitHub repository code & SQL schema import into ChromaDB RAG
        ├── AuthModal.jsx        # User login and registration modal with JWT token management
        ├── Footer.jsx           # Academic footer with institutional branding and project links
        └── RocketBackToTop.jsx  # Animated floating scroll-to-top button
```

---

## 🧩 Component Breakdown & Responsibilities

| Component | Purpose & Description |
| :--- | :--- |
| **`App.jsx`** | Acts as the central state hub. Coordinates projects, active chapters, knowledge files, user authentication tokens, and communicates with FastAPI backend endpoints. |
| **`ChapterStudio.jsx`** | The primary workspace for chapters 1 through 6. Features a chapter toolbar (Generate AI Content, Edit Raw Markdown, Save), custom prompt tuning input, and live GitHub-flavored Markdown rendering with auto-embedded technical diagrams. |
| **`Sidebar.jsx`** | Left-hand navigation panel. Houses the active project dropdown, knowledge file upload dropzone (PDF, DOCX, TXT, Python), GitHub import launcher, chapter readiness indicators, and PDF/DOCX export buttons. |
| **`LandingHero.jsx`** | The landing experience. Displays platform value propositions, an interactive live generation simulator with realistic typing animations, and quick actions to launch the studio or create a project. |
| **`NewProjectModal.jsx`** | Modal for initializing academic projects. Supports instant GitHub repository analysis to auto-detect project title, tech stack, database schemas, modules, and problem statements. |
| **`ImportCodeModal.jsx`** | Connects to public GitHub repositories to clone file trees, analyze dependencies, parse `.sql` database schemas, and index chunks into the ChromaDB vector store. |
| **`ProjectOverview.jsx`** | Displays stored grounding parameters (domain, category, methodology, SDLC model, tech stack, database, problem statement) stored in Supabase PostgreSQL. |
| **`FullReportPreview.jsx`** | Renders all generated chapters into a single unified continuous document with real-time word counts and quick export actions. |
| **`Header.jsx`** | Displays system status (live Groq model connectivity badge), view switching tabs (*Chapter Generator*, *Project Overview*, *Full Document Preview*), and user login/profile controls. |
| **`AuthModal.jsx`** | Modal dialog handling user registration and login via the Supabase auth backend with automatic Axios JWT bearer header configuration. |
| **`RocketBackToTop.jsx`** | Smooth-scrolling floating action button that appears after scrolling past 300px with a playful launch animation. |

---

## 🚀 Key Workflows

### 1. Unified Inline Diagram Generation
* Diagrams are generated **inline during chapter content generation** — eliminating separate manual diagram blocks.
* **Chapter 3 (System Design)** automatically embeds:
  * **Figure 3.1: System Architecture Diagram** (Presentation, Router, and Database layers).
  * **Figure 3.2: Database Entity-Relationship (ER) Diagram** (relational tables, keys, and schemas).
* Embedded diagrams render directly in `ChapterStudio` via `/api/v1/diagrams/{project_id}/{filename}.png` and export seamlessly into PDF and Word DOCX formats with standard figure captions placed beneath each image.

### 2. GitHub Codebase Grounding
* Students provide a GitHub repository link during project creation or via `ImportCodeModal`.
* The backend downloads the repository archive, indexes code modules, parses SQL migration/schema files, and generates a structured data dictionary into ChromaDB.
* The frontend displays real-time analysis badges and alerts once repository schemas are vectorized.

### 3. Live Dual-Mode Editing
* **Preview Mode**: Clean GitHub-Flavored Markdown rendering (`remark-gfm`) supporting tables, code blocks, bold/italic text, and diagrams.
* **Edit Mode**: Direct monospace textarea editor allowing manual refinement and immediate persistence to Supabase via the `Save Changes` button.

---

## 🛠️ Technology Stack

* **Core Framework**: React 19 (`react`, `react-dom`)
* **Build Tooling**: Vite 8 (`@vitejs/plugin-react`)
* **Styling**: Vanilla CSS with comprehensive CSS custom properties and HSL-tailored tokens (`index.css`)
* **HTTP Client**: Axios with request/response interceptors for JWT bearer tokens
* **Markdown Rendering**: `react-markdown` + `remark-gfm`
* **Icons**: `lucide-react`
* **Linting**: Oxlint

---

## 💻 Development & Build Setup

### Prerequisites
* Node.js 18+ or 20+
* Backend FastAPI server running on `http://localhost:8000`

### Installation
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install
```

### Run Locally (Development)
```bash
npm run dev
```
The application will start on `http://localhost:5173`. Requests to `/api/*` and `/health` are automatically proxied to `http://localhost:8000` via `vite.config.js`.

### Production Build
```bash
npm run build
```
Creates an optimized production bundle in the `dist/` directory.

### Preview Production Build
```bash
npm run preview
```
