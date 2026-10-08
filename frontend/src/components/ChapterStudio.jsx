import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Sparkles, Edit3, Save, Loader2 } from 'lucide-react';

const CHAPTER_META = {
  1: { title: "Chapter 1: Introduction", desc: "Overview, Background, Problem Statement, Objectives & Scope" },
  2: { title: "Chapter 2: Requirement Analysis", desc: "User Requirements, Functional Requirements & Hardware/Software Specs" },
  3: { title: "Chapter 3: System Design", desc: "Design Approach, Class Diagram, DFDs, Data Dictionary & Database Schema" },
  4: { title: "Chapter 4: Implementation & Testing", desc: "Implementation Details, Module Breakdown & Test Cases" },
  5: { title: "Chapter 5: Results & Discussion", desc: "Performance Metrics, Outputs & Screen Descriptions" },
  6: { title: "Chapter 6: Conclusion & Future Scope", desc: "Project Summary, Key Contributions & Future Enhancements" }
};

export default function ChapterStudio({
  currentChapterNumber,
  chapterData,
  isGenerating,
  onGenerate,
  onSaveContent
}) {
  const [extraInstructions, setExtraInstructions] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState('');

  const meta = CHAPTER_META[currentChapterNumber];

  useEffect(() => {
    setContent(chapterData?.content || '');
    setIsEditing(false);
  }, [currentChapterNumber, chapterData]);

  const handleToggleEdit = () => {
    if (isEditing) {
      onSaveContent(currentChapterNumber, content);
      setIsEditing(false);
    } else {
      setIsEditing(true);
    }
  };

  return (
    <div>
      {/* Chapter Toolbar */}
      <div class="chapter-toolbar">
        <div>
          <h2>{meta.title}</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{meta.desc}</p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            class="btn btn-accent" 
            disabled={isGenerating} 
            onClick={() => onGenerate(currentChapterNumber, extraInstructions)}
          >
            {isGenerating ? <Loader2 size={16} class="spinner" /> : <Sparkles size={16} />}
            {isGenerating ? 'Generating AI Content...' : 'Generate Chapter'}
          </button>
          <button class="btn btn-secondary" onClick={handleToggleEdit}>
            {isEditing ? <Save size={16} /> : <Edit3 size={16} />}
            {isEditing ? 'Save Changes' : 'Edit Chapter'}
          </button>
        </div>
      </div>

      {/* Optional Prompt Box */}
      <div class="form-group" style={{ marginBottom: '1.5rem' }}>
        <label>Custom Prompt Tuning Instructions (Optional)</label>
        <input 
          type="text" 
          class="form-control" 
          value={extraInstructions}
          onChange={e => setExtraInstructions(e.target.value)}
          placeholder="e.g. Include specific architectural diagram references for FastAPI and Supabase..."
        />
      </div>

      {/* Workspace Display */}
      {isEditing ? (
        <textarea 
          class="form-control" 
          style={{ minHeight: '500px', fontFamily: 'monospace', fontSize: '0.9rem' }}
          value={content}
          onChange={e => setContent(e.target.value)}
        />
      ) : (
        <div class="markdown-output">
          {isGenerating ? (
            <div style={{ textAlign: 'center', marginTop: '100px', color: 'var(--text-secondary)' }}>
              <div class="spinner" style={{ borderTopColor: 'var(--brand-primary)', width: '32px', height: '32px', marginBottom: '16px' }}></div>
              <p style={{ fontWeight: 600 }}>Generating {meta.title} with AI...</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Retrieving ChromaDB context & querying Groq LLM model...</p>
            </div>
          ) : content ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontStyle: 'italic', textAlign: 'center', marginTop: '100px' }}>
              Chapter {currentChapterNumber} has not been generated yet. Click <strong>"Generate Chapter"</strong> above to generate it with AI.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
