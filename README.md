# 📚 AI Project Report Generator

An easy-to-use web application that automatically creates complete, university-standard project reports from your software projects or GitHub repositories.

---

## 💡 What Does This Project Do?

Writing college or university project reports takes hours of manual work. This application automates the entire process:
- **Imports your GitHub repository** with one click.
- **Analyzes your project files and database (`.sql` files)** to understand how your app works.
- **Writes complete chapters (Chapters 1 to 6)** with structured, professional content.
- **Generates visual diagrams** (System Architecture & Database ER Diagrams) using Hugging Face AI.
- **Exports ready-to-submit documents** in **PDF** or **Word (.docx)** format with formal academic styling (Times New Roman, proper headings, and neat tables).

---

## 🔄 Simple Project Flow

```
1. Sign In ──► 2. Create Project / Paste GitHub Link ──► 3. Auto-Analyze Code & SQL
                                                                  │
6. Export PDF / Word ◄── 5. Generate Diagrams (HF AI) ◄── 4. Generate Chapters (1 to 6)
```

1. **Sign Up & Log In**: Create your account and log into your personal workspace.
2. **Import or Create Project**:
   - You can enter your project details manually, **OR**
   - Simply paste a public GitHub repository URL (e.g. `https://github.com/username/project`).
3. **Automatic Project Analysis**:
   - The app reads every folder and file in your repository.
   - It finds any database `.sql` files and automatically extracts your tables, columns, primary keys, and foreign keys.
4. **Generate Chapters**:
   - Open any chapter (Chapters 1 through 6) and click **"Generate Chapter"**.
   - The AI writes in-depth, structured academic content based on your actual code and database schema.
5. **Generate Diagrams**:
   - For Chapter 3 (System Design), click **"System Architecture"** or **"Database ER Diagram"**.
   - The app uses the Hugging Face model (`Maelstrome/mermaid-gemmma-7b`) to draw clear, high-resolution diagram images that fit right into your report.
6. **Preview & Export**:
   - Review your report in the live editor.
   - Click **"Export PDF"** or **"Export DOCX"** to download your final report, complete with formal tables and embedded diagram pictures.

---

## 📖 Report Structure (Chapters 1 to 6)

| Chapter | Title | Content Covered |
| :---: | :--- | :--- |
| **1** | Introduction & Overview | Project background, problem statement, objectives, scope, and target audience |
| **2** | Literature Survey & Tech Stack | Feasibility study, related work, programming languages, frameworks, and tools |
| **3** | System Design & Diagrams | Architecture design, data flow, entity relationships, and generated diagram images |
| **4** | Implementation & Modules | Folder breakdown, core logic, key functions, API routes, and testing results |
| **5** | Database & Data Dictionary | Full database schema, table lists, columns, data types, primary and foreign keys |
| **6** | Conclusion & Future Work | Summary of accomplishments, limitations, and future enhancement scope |

---

## ⚙️ Requirements Before Starting

You will need the following installed on your computer:
- **Python 3.10+** (Python 3.11, 3.12, or 3.13)
- **Node.js 18+** and **npm**

You will also need three free accounts:
1. **[Supabase](https://supabase.com)** (Free PostgreSQL database to save users and projects)
2. **[Groq Console](https://console.groq.com/keys)** (Free API key for fast report text generation)
3. **[Hugging Face](https://huggingface.co/settings/tokens)** (Free token for diagram generation)

---

## 🚀 Easy Setup Guide

### 1. Download & Backend Setup

Open your terminal or command prompt in the project folder:

```bash
# 1. Create a Python virtual environment
python -m venv venv

# 2. Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install Python requirements
pip install -r requirements.txt
```

---

### 2. Configure Your Settings (`.env`)

Create a file named `.env` in the root folder (or copy `.env.example`):

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your details:

```env
# Supabase Database (https://supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# Groq API for Writing Chapters (https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Hugging Face for Generating Diagrams (https://huggingface.co/settings/tokens)
HF_API_KEY=hf_your_huggingface_token_here
HF_IMAGE_MODEL=Maelstrome/mermaid-gemmma-7b

# Secret Key (Any random text for session security)
SECRET_KEY=any-random-secret-key-12345
```

> **How to get your free Hugging Face Token:**
> 1. Sign in to [huggingface.co](https://huggingface.co/).
> 2. Go to **Settings** → **Access Tokens**.
> 3. Click **New token**, choose **Read** permission, and copy your token starting with `hf_...`.

---

### 3. Initialize the Database

1. Open your **Supabase Dashboard**.
2. Go to the **SQL Editor** tab on the left.
3. Open the file `database/schema.sql` from this project, paste its contents into the SQL Editor, and click **Run**.
4. This creates all necessary tables (`users`, `projects`, `chapters`, `diagrams`).

---

### 4. Frontend Setup

Open a new terminal window:

```bash
cd frontend

# Install frontend packages
npm install
```

---

### 5. Run the Application

Start both the backend and frontend servers:

**Terminal 1 (Backend Server):**
```bash
python run.py
```
*The backend API will run at `http://localhost:8000`.*

**Terminal 2 (Frontend Interface):**
```bash
cd frontend
npm run dev
```
*Open your browser and visit `http://localhost:5173` to use the application.*

---

## 📁 Project Directory Overview

```
AI_Report_Generator/
├── app/
│   ├── main.py              # Main FastAPI application and routing
│   ├── core/
│   │   ├── config.py        # Settings and environment loader
│   │   ├── auth.py          # User login and password protection
│   │   └── database.py      # Supabase connection
│   ├── routers/             # Web API routes (auth, projects, chapters, reports)
│   └── services/
│       ├── github_service.py    # Reads GitHub repositories and parses .sql files
│       ├── diagram_service.py   # Hugging Face & visual diagram generation
│       ├── llm_service.py       # Groq AI text generation
│       └── report_exporter.py   # PDF and Word document generator
├── database/
│   └── schema.sql           # Database setup script
├── frontend/                # React user interface
│   ├── src/
│   │   ├── components/      # UI components (Header, Sidebar, Modals, Editor)
│   │   └── App.jsx          # Main application page
│   └── package.json
├── storage/
│   └── diagrams/            # Generated diagram image files
├── tests/
│   └── test_github_import.py# Automated tests
├── .env.example             # Clean configuration template
├── requirements.txt         # Python libraries
└── run.py                   # Starts the backend server
```

---

## 🧪 Testing

You can verify that everything is working properly by running the automated tests:

```bash
python -m pytest tests/test_github_import.py -v
```

All tests check:
- GitHub URL handling and repo reading
- Database `.sql` table and key extraction
- Hugging Face diagram generation and image delivery

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
