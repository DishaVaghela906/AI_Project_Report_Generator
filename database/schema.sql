-- ============================================================
-- AI Report Generator — Supabase Database Schema & Migration Script
-- Run this SQL in your Supabase SQL Editor (https://supabase.com/dashboard)
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────
-- 1. USERS TABLE
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         TEXT UNIQUE NOT NULL,
    full_name     TEXT NOT NULL,
    password_hash TEXT NOT NULL DEFAULT 'OAUTH_USER',
    role          TEXT NOT NULL DEFAULT 'user',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- 2. PROJECTS TABLE & MIGRATION
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    title               TEXT NOT NULL,
    domain              TEXT NOT NULL,
    category            TEXT NOT NULL,
    problem_statement   TEXT NOT NULL,
    objectives          JSONB DEFAULT '[]',         -- list of strings
    tech_stack          JSONB DEFAULT '[]',         -- list of strings
    modules             JSONB DEFAULT '[]',         -- list of strings
    methodology         TEXT NOT NULL,
    sdlc_model          TEXT NOT NULL DEFAULT 'Agile',
    database_used       TEXT,
    team_members        JSONB DEFAULT '[]',         -- list of {name, role, enrollment_no}
    guide_name          TEXT,
    institution         TEXT,
    department          TEXT,
    academic_year       TEXT,
    existing_system     TEXT,
    proposed_system     TEXT,
    unique_features     JSONB DEFAULT '[]',
    implementation_details TEXT,
    testing_details     TEXT,
    results             TEXT,
    future_scope        TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure user_id and github_url columns exist on projects table for both new and existing databases
ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS github_url TEXT;

-- ─────────────────────────────────────────────────────────────
-- 3. UPLOADED FILES TABLE
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS uploaded_files (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    file_type       TEXT NOT NULL,
    file_size       BIGINT NOT NULL,
    saved_path      TEXT,
    chunks_count    INTEGER DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'processing', -- processing | ready | error
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- 4. CHAPTERS TABLE
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chapters (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_number  INTEGER NOT NULL CHECK (chapter_number BETWEEN 1 AND 6),
    chapter_title   TEXT NOT NULL,
    content         TEXT DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'pending', -- pending | generating | done | error
    generated_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, chapter_number)             -- one row per chapter per project
);

-- ─────────────────────────────────────────────────────────────
-- 5. INDEXES (Guaranteed user_id column exists before creating index)
-- ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_project ON uploaded_files(project_id);
CREATE INDEX IF NOT EXISTS idx_chapters_project ON chapters(project_id);
CREATE INDEX IF NOT EXISTS idx_chapters_status ON chapters(status);

-- ─────────────────────────────────────────────────────────────
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- ─────────────────────────────────────────────────────────────
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE uploaded_files DISABLE ROW LEVEL SECURITY;
ALTER TABLE chapters DISABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to users') THEN
        CREATE POLICY "Allow all access to users" ON users FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to projects') THEN
        CREATE POLICY "Allow all access to projects" ON projects FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to uploaded_files') THEN
        CREATE POLICY "Allow all access to uploaded_files" ON uploaded_files FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to chapters') THEN
        CREATE POLICY "Allow all access to chapters" ON chapters FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ─────────────────────────────────────────────────────────────
-- 7. AUTO-UPDATE TIMESTAMP TRIGGERS
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS projects_updated_at ON projects;
CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS chapters_updated_at ON chapters;
CREATE TRIGGER chapters_updated_at
    BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
