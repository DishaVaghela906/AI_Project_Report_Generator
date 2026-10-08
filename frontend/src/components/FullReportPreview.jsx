import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download } from 'lucide-react';

export default function FullReportPreview({ project, chaptersData, onExport }) {
  let combinedMarkdown = `# ${project ? project.title : 'Academic Project Report'}\n\n`;

  let hasContent = false;
  for (let n = 1; n <= 6; n++) {
    const ch = chaptersData[n];
    if (ch && ch.content) {
      hasContent = true;
      combinedMarkdown += ch.content + "\n\n---\n\n";
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2>Full Academic Project Report</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Combined view of all generated chapters ready for export.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button class="btn btn-primary" onClick={() => onExport('pdf')}>
            <Download size={16} /> Export PDF Report
          </button>
        </div>
      </div>

      <div class="markdown-output" style={{ maxHeight: '750px' }}>
        {hasContent ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{combinedMarkdown}</ReactMarkdown>
        ) : (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '100px' }}>
            No chapters generated yet. Navigate to Chapter Generator to create your report chapters.
          </p>
        )}
      </div>
    </div>
  );
}
