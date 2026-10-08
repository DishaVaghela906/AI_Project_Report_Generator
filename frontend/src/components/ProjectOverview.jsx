import React from 'react';

export default function ProjectOverview({ project }) {
  if (!project) return null;

  return (
    <div>
      <h2>Project Specifications & Grounding Context</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Core parameters stored in Supabase PostgreSQL used to prompt the AI report engine.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div style={{ background: 'var(--bg-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
          <h4 style={{ marginBottom: '8px' }}>General Information</h4>
          <p><strong>Title:</strong> {project.title}</p>
          <p><strong>Domain:</strong> {project.domain}</p>
          <p><strong>Category:</strong> {project.category}</p>
          <p><strong>Institution:</strong> {project.institution || 'N/A'}</p>
          <p><strong>Department:</strong> {project.department || 'N/A'}</p>
        </div>

        <div style={{ background: 'var(--bg-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
          <h4 style={{ marginBottom: '8px' }}>Technical Architecture</h4>
          <p><strong>Methodology:</strong> {project.methodology}</p>
          <p><strong>SDLC Model:</strong> {project.sdlc_model || 'Agile'}</p>
          <p><strong>Tech Stack:</strong> {(project.tech_stack || []).join(', ')}</p>
          <p><strong>Database:</strong> {project.database_used || 'Supabase PostgreSQL'}</p>
        </div>

        <div style={{ gridColumn: 'span 2', background: 'var(--bg-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
          <h4 style={{ marginBottom: '8px' }}>Problem Statement</h4>
          <p>{project.problem_statement}</p>
        </div>
      </div>
    </div>
  );
}
