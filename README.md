# 🚀 AI-Powered Academic Project Report Generator

A full-stack, enterprise-grade AI platform designed to transform raw project code, specifications, SRS documents, and architecture diagrams into publication-ready, multipage academic reports following strict university formatting standards.

![UI Theme](https://img.shields.io/badge/Theme-Beige%20%26%20Black-2C2621?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react)
![LLM Model](https://img.shields.io/badge/LLM-Groq%20120B-8C7355?style=for-the-badge)
![Vector DB](https://img.shields.io/badge/Vector%20Store-ChromaDB-FF6F00?style=for-the-badge)

---

## 🌟 Key Features

### 1. 🎨 Modern Beige & Black Frontend Interface
- Custom-tailored React interface using a curated color system: **80% Warm Cream Beige (`#F9F6F0`)**, **15% Deep Charcoal Black (`#1F1C18`)**, and **5% Bronze Accents (`#8C7355`)**.
- Integrated **Landing Hero Page** showcasing feature capabilities, quick specification pills, and 3-step workflow.
- **Login/Signup Bypass**: Instant entry into the studio workspace without friction or authentication gates.

### 2. 🎓 Strict Academic Formatting Engine
Enforces rigid university and institutional report standards automatically across exported documents:
- **Font**: Times New Roman throughout the entire document.
- **Main Headings (H1)**: 16 pt (Bold).
- **Sub Headings (H2 / H3)**: 14 pt (Bold).
- **Body Content & Bullets**: 12 pt (Justified text alignment).
- **Tables**: Full-width A4 native grid tables with header highlighting.

### 3. 📄 Zero Black-Box PDF & DOCX Export Pipeline
- Built-in Unicode sanitization engine converts complex ASCII/Unicode box drawings, structured flowcharts, arrows (`->`), bullet points (`&bull;`), and block elements.
- **Eliminates missing glyph squares (`■`)** when exported via ReportLab or Python-Docx.

### 4. 🧠 120B Parameter AI Model Integration
- Direct integration with Groq API supporting high-parameter models (`openai/gpt-oss-120b`).
- Built-in exponential backoff retry mechanism to gracefully handle HTTP 429 rate limits.
### 5. 🔐 Full User Authentication Module
- Secure JWT authentication (`pyjwt` with HS256) and password hashing (`bcrypt`).
- API Endpoints: `POST /api/v1/auth/signup`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`.
- React `AuthModal` matching the Beige & Black theme with Sign In / Sign Up tabs, persistent session storage, and header user avatar badge.

---

## 🏗️ System Architecture

```
AI_Report_Generator/
├── app/
│   ├── main.py                   # FastAPI application initialization & routes
│   ├── core/
│   │   ├── config.py             # App environment configuration (Pydantic Settings)
│   │   └── database.py           # Supabase client connection
│   ├── models/
│   │   └── schemas.py            # Request / Response Pydantic schemas
│   ├── routers/
│   │   ├── projects.py           # Project CRUD API endpoints
│   │   ├── uploads.py            # RAG document upload & extraction
│   │   ├── chapters.py           # Chapter generation AI pipeline
│   │   └── reports.py            # PDF & DOCX export handlers
│   └── services/
│       ├── document_processor.py # Multi-format document parser (PDF, DOCX, PPTX, Code)
│       ├── vector_store.py       # ChromaDB vector embedding & context search
│       ├── prompt_builder.py     # Academic chapter prompt templates
│       ├── llm_service.py        # Groq / Ollama / HF LLM routing with backoff retry
│       └── report_exporter.py    # ReportLab PDF & DOCX academic exporter
├── database/
│   └── schema.sql                # Supabase PostgreSQL database schema
├── frontend/                     # React + Vite Frontend Application
│   ├── src/
│   │   ├── components/           # Header, Sidebar, ChapterStudio, LandingHero, etc.
│   │   ├── App.jsx               # Main application component & tab router
│   │   └── index.css             # Beige & Black Design System CSS tokens
│   ├── package.json
│   └── vite.config.js
├── tests/
│   └── test_api.py               # Backend Pytest test suite
├── requirements.txt              # Python backend dependencies
├── .env.example                  # Template environment file
├── .gitignore                    # Git ignore file
└── run.py                        # Uvicorn server entrypoint
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

---

### 1. Backend Setup

```bash
# Navigate to project root
cd AI_Report_Generator

# Create & activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Example `.env` configuration for Groq API:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
LLM_MAX_TOKENS=4096

SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Database Initialization
Run the contents of `database/schema.sql` inside your Supabase project's **SQL Editor**.

---

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build React production bundle (served directly by FastAPI)
npm run build
```

---

### 5. Running the Application

```bash
# From project root directory
python run.py
```

- **Web Application**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Running Tests

Run the full pytest suite to verify API endpoints, vector store integration, and export service:

```bash
python -m pytest tests/ -v
```

---

## 📝 License
Distributed under the MIT License.
