import React, { useState } from 'react';

export default function NewProjectModal({ isOpen, onClose, onCreateProject }) {
  const [formData, setFormData] = useState({
    title: '',
    domain: 'Web Application',
    category: 'Application or System Development',
    problem_statement: '',
    methodology: 'Agile Iterative Development',
    tech_stack: 'Python, FastAPI, Supabase, ChromaDB, Groq LLM',
    institution: '',
    department: 'Computer Science & Engineering',
  });

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      tech_stack: formData.tech_stack.split(',').map(s => s.trim()).filter(Boolean),
      sdlc_model: 'Agile',
    };
    onCreateProject(payload);
  };

  return (
    <div class="modal-overlay active">
      <div class="modal-card">
        <div class="modal-header">
          <h2>Create New Academic Project</h2>
          <button class="modal-close" onClick={onClose}>&times;</button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div class="form-group">
            <label>Project Title *</label>
            <input 
              type="text" 
              class="form-control" 
              required 
              value={formData.title} 
              onChange={e => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g. AI-Powered Project Report Generator" 
            />
          </div>

          <div class="form-grid-2">
            <div class="form-group">
              <label>Domain *</label>
              <input 
                type="text" 
                class="form-control" 
                required 
                value={formData.domain} 
                onChange={e => setFormData({ ...formData, domain: e.target.value })}
              />
            </div>
            <div class="form-group">
              <label>Category *</label>
              <select 
                class="form-control" 
                value={formData.category} 
                onChange={e => setFormData({ ...formData, category: e.target.value })}
              >
                <option value="Application or System Development">Application or System Development</option>
                <option value="Research Project">Research Project</option>
                <option value="Data Science & ML">Data Science & ML</option>
                <option value="Embedded Systems / IoT">Embedded Systems / IoT</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Problem Statement *</label>
            <textarea 
              class="form-control" 
              required 
              value={formData.problem_statement} 
              onChange={e => setFormData({ ...formData, problem_statement: e.target.value })}
              placeholder="Describe the academic problem being addressed..."
            />
          </div>

          <div class="form-grid-2">
            <div class="form-group">
              <label>Methodology</label>
              <input 
                type="text" 
                class="form-control" 
                value={formData.methodology} 
                onChange={e => setFormData({ ...formData, methodology: e.target.value })}
              />
            </div>
            <div class="form-group">
              <label>Tech Stack (comma separated)</label>
              <input 
                type="text" 
                class="form-control" 
                value={formData.tech_stack} 
                onChange={e => setFormData({ ...formData, tech_stack: e.target.value })}
              />
            </div>
          </div>

          <div class="form-grid-2">
            <div class="form-group">
              <label>Institution</label>
              <input 
                type="text" 
                class="form-control" 
                value={formData.institution} 
                onChange={e => setFormData({ ...formData, institution: e.target.value })}
                placeholder="e.g. University Name"
              />
            </div>
            <div class="form-group">
              <label>Department</label>
              <input 
                type="text" 
                class="form-control" 
                value={formData.department} 
                onChange={e => setFormData({ ...formData, department: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '1.5rem' }}>
            <button type="button" class="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" class="btn btn-primary">Create Project</button>
          </div>
        </form>
      </div>
    </div>
  );
}
