import React, { useRef } from 'react';
import { Upload, FileText, Download, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

const GithubIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

const CHAPTER_TITLES = {
  1: "Ch 1: Introduction",
  2: "Ch 2: Requirements",
  3: "Ch 3: System Design",
  4: "Ch 4: Implementation",
  5: "Ch 5: Results & Discussion",
  6: "Ch 6: Conclusion"
};

export default function Sidebar({
  projects,
  currentProject,
  onSelectProject,
  uploadedFiles,
  onFileUpload,
  onOpenImportCodeModal,
  chaptersData,
  currentChapterNumber,
  onSelectChapter,
  onExport
}) {
  const fileInputRef = useRef(null);

  const readyCount = Object.values(chaptersData).filter(c => c.status === 'done' && c.content).length;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileUpload(e.dataTransfer.files);
    }
  };

  return (
    <aside class="app-sidebar">
      {/* Project Selector */}
      <div class="sidebar-card">
        <div class="sidebar-card-header">
          <h4>Active Project</h4>
        </div>
        <select 
          class="project-select" 
          value={currentProject?.id || ''} 
          onChange={(e) => {
            const p = projects.find(item => item.id === e.target.value);
            if (p) onSelectProject(p);
          }}
        >
          {projects.length === 0 ? (
            <option value="" disabled>No projects found</option>
          ) : (
            projects.map(p => (
              <option key={p.id} value={p.id}>{p.title} ({p.academic_year || '2024-25'})</option>
            ))
          )}
        </select>
      </div>

      {/* Knowledge Files Uploader (RAG) */}
      <div className="sidebar-card">
        <div className="sidebar-card-header">
          <h4>Knowledge Files (RAG)</h4>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
          Upload PDFs, code files, or import directly from GitHub to index into ChromaDB.
        </p>

        <button
          type="button"
          className="btn btn-secondary btn-block btn-github-side"
          onClick={onOpenImportCodeModal}
          style={{
            marginBottom: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '0.82rem',
            padding: '8px 12px'
          }}
        >
          <GithubIcon size={15} />
          <span>Import Code from GitHub</span>
        </button>

        <div 
          class="upload-dropzone"
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <Upload size={24} style={{ marginBottom: '6px', color: 'var(--text-secondary)' }} />
          <p style={{ fontSize: '0.85rem', fontWeight: 600 }}>Drag & Drop or Click to Upload</p>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PDF, DOCX, PPTX, TXT, PY</p>
          <input 
            type="file" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            multiple 
            onChange={handleFileChange} 
          />
        </div>

        <div class="file-list">
          {uploadedFiles.length === 0 ? (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>No files uploaded yet.</p>
          ) : (
            uploadedFiles.map(f => (
              <div key={f.id} class="file-item">
                <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '170px' }}>
                  📄 {f.filename}
                </span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{f.chunks_count || 0} chunks</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chapters Sidebar Progress */}
      <div class="sidebar-card">
        <div class="sidebar-card-header">
          <h4>Report Chapters</h4>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{readyCount} / 6 Ready</span>
        </div>

        <div class="chapter-progress-list">
          {[1, 2, 3, 4, 5, 6].map(n => {
            const data = chaptersData[n] || { status: 'pending', content: '' };
            const isDone = data.status === 'done' && data.content;
            const isGenerating = data.status === 'generating';
            const isActive = n === currentChapterNumber;

            let badgeClass = 'badge-pending';
            let badgeText = 'Pending';
            if (isDone) { badgeClass = 'badge-done'; badgeText = 'Ready'; }
            else if (isGenerating) { badgeClass = 'badge-generating'; badgeText = 'Generating...'; }

            return (
              <div 
                key={n}
                class={`chapter-progress-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectChapter(n)}
              >
                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{CHAPTER_TITLES[n]}</span>
                <span class={`chapter-badge ${badgeClass}`}>{badgeText}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Export Actions Card */}
      <div class="sidebar-card">
        <div class="sidebar-card-header">
          <h4>Export Report</h4>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button class="btn btn-secondary btn-block" onClick={() => onExport('pdf')}>
            <FileText size={16} /> Export PDF Report
          </button>
          <button class="btn btn-secondary btn-block" onClick={() => onExport('docx')}>
            <Download size={16} /> Export Word (DOCX)
          </button>
        </div>
      </div>
    </aside>
  );
}
