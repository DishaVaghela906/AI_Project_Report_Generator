import React, { useState } from 'react';
import axios from 'axios';
import { Sparkles, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

const GithubIcon = ({ size = 18, className = "" }) => (
  <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

export default function NewProjectModal({ isOpen, onClose, onCreateProject }) {
  const [githubUrl, setGithubUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisSuccess, setAnalysisSuccess] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);

  const [formData, setFormData] = useState({
    title: '',
    domain: 'Web Application',
    category: 'Application or System Development',
    problem_statement: '',
    methodology: 'Agile Iterative Development',
    tech_stack: 'Python, FastAPI, Supabase, ChromaDB, Groq LLM',
    database_used: 'Supabase PostgreSQL',
    institution: '',
    department: 'Computer Science & Engineering',
    modules: [
      'User Management & Security Module',
      'Core Business Logic & API Service',
      'Database Persistence & Storage Layer',
      'Interactive Client Dashboard'
    ],
    proposed_system: '',
    github_url: '',
  });

  if (!isOpen) return null;

  // Handle GitHub Repository Analysis
  const handleAnalyzeGitHub = async () => {
    if (!githubUrl.trim()) {
      setAnalysisError('Please enter a valid GitHub repository URL.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisSuccess(null);

    try {
      const res = await axios.post('/api/v1/projects/analyze-github', {
        url: githubUrl.trim(),
      });

      const analysis = res.data;

      // Auto-populate form data from GitHub analysis
      setFormData(prev => ({
        ...prev,
        title: analysis.title || prev.title,
        domain: analysis.domain || prev.domain,
        category: analysis.category || prev.category,
        problem_statement: analysis.problem_statement || prev.problem_statement,
        tech_stack: (analysis.tech_stack && analysis.tech_stack.length > 0)
          ? analysis.tech_stack.join(', ')
          : prev.tech_stack,
        database_used: analysis.database_used || prev.database_used,
        methodology: analysis.methodology || prev.methodology,
        modules: analysis.modules && analysis.modules.length > 0 ? analysis.modules : prev.modules,
        proposed_system: analysis.proposed_system || prev.proposed_system,
        github_url: analysis.github_url || githubUrl.trim(),
      }));

      setAnalysisSuccess(
        `✓ Repository analyzed: "${analysis.owner}/${analysis.repo}" — Architecture, database schemas, and tech stack extracted!`
      );
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to analyze GitHub repository.';
      setAnalysisError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      tech_stack: typeof formData.tech_stack === 'string'
        ? formData.tech_stack.split(',').map(s => s.trim()).filter(Boolean)
        : formData.tech_stack,
      objectives: [
        'Design and implement robust system architecture',
        'Develop user-friendly interface and backend services',
        'Conduct thorough testing and evaluation'
      ],
      modules: Array.isArray(formData.modules) && formData.modules.length > 0
        ? formData.modules
        : [
            'User Management & Security Module',
            'Core Processing & API Service',
            'Database & Persistence Engine'
          ],
      sdlc_model: 'Agile',
      github_url: formData.github_url || (githubUrl.trim() || undefined),
    };

    onCreateProject(payload);
  };

  return (
    <div className="modal-overlay active">
      <div className="modal-card new-project-modal-card">
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={20} className="text-accent" />
            <h2>Create New Academic Project</h2>
          </div>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        {/* GitHub Code Import Section (Gemini Style) */}
        <div className="github-import-box">
          <div className="github-import-header">
            <div className="github-import-title">
              <GithubIcon size={18} />
              <span>Import Code from GitHub</span>
            </div>
            <span className="github-import-badge">Auto-Detects Architecture &amp; Schemas</span>
          </div>
          <p className="github-import-subtitle">
            Provide a GitHub repository URL to automatically extract project title, tech stack, database schemas, and problem statement for report generation.
          </p>

          <div className="github-import-input-row">
            <div className="github-input-wrapper">
              <GithubIcon size={16} className="github-input-icon" />
              <input
                type="url"
                className="form-control github-input"
                placeholder="e.g. https://github.com/username/project-repo"
                value={githubUrl}
                onChange={e => {
                  setGithubUrl(e.target.value);
                  setAnalysisError(null);
                }}
                disabled={isAnalyzing}
              />
            </div>
            <button
              type="button"
              className="btn btn-primary btn-analyze-github"
              onClick={handleAnalyzeGitHub}
              disabled={isAnalyzing || !githubUrl.trim()}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 size={16} className="spin-icon" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Analyze Repo</span>
                </>
              )}
            </button>
          </div>

          {/* Feedback Banners */}
          {analysisSuccess && (
            <div className="github-analysis-alert success">
              <CheckCircle2 size={16} />
              <span>{analysisSuccess}</span>
            </div>
          )}

          {analysisError && (
            <div className="github-analysis-alert error">
              <AlertCircle size={16} />
              <span>{analysisError}</span>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} style={{ marginTop: '1.25rem' }}>
          <div className="form-group">
            <label>Project Title *</label>
            <input 
              type="text" 
              className="form-control" 
              required 
              value={formData.title} 
              onChange={e => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g. AI-Powered Project Report Generator" 
            />
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Domain *</label>
              <input 
                type="text" 
                className="form-control" 
                required 
                value={formData.domain} 
                onChange={e => setFormData({ ...formData, domain: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Category *</label>
              <select 
                className="form-control" 
                value={formData.category} 
                onChange={e => setFormData({ ...formData, category: e.target.value })}
              >
                <option value="Application or System Development">Application or System Development</option>
                <option value="Internet Based">Internet Based</option>
                <option value="Research Project">Research Project</option>
                <option value="Data Science & ML">Data Science & ML</option>
                <option value="Embedded Systems / IoT">Embedded Systems / IoT</option>
                <option value="Industry Automation">Industry Automation</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Problem Statement *</label>
            <textarea 
              className="form-control" 
              required 
              rows={4}
              value={formData.problem_statement} 
              onChange={e => setFormData({ ...formData, problem_statement: e.target.value })}
              placeholder="Describe the academic problem, motivation, and solution..."
            />
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Database Used</label>
              <input 
                type="text" 
                className="form-control" 
                value={formData.database_used} 
                onChange={e => setFormData({ ...formData, database_used: e.target.value })}
                placeholder="e.g. PostgreSQL, Supabase, MongoDB"
              />
            </div>
            <div className="form-group">
              <label>Tech Stack (comma separated)</label>
              <input 
                type="text" 
                className="form-control" 
                value={formData.tech_stack} 
                onChange={e => setFormData({ ...formData, tech_stack: e.target.value })}
              />
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Institution</label>
              <input 
                type="text" 
                className="form-control" 
                value={formData.institution} 
                onChange={e => setFormData({ ...formData, institution: e.target.value })}
                placeholder="e.g. University Name"
              />
            </div>
            <div className="form-group">
              <label>Department</label>
              <input 
                type="text" 
                className="form-control" 
                value={formData.department} 
                onChange={e => setFormData({ ...formData, department: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '1.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary">Create Project</button>
          </div>
        </form>
      </div>
    </div>
  );
}
