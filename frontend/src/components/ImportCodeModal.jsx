import React, { useState } from 'react';
import { X, Loader2, CheckCircle2, AlertCircle, FolderUp } from 'lucide-react';

export default function ImportCodeModal({ isOpen, onClose, onImportGitHub, currentProjectId }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setLoading(true);
    setErrorMessage(null);
    setStatusMessage('Connecting to repository & extracting code files...');

    try {
      await onImportGitHub(repoUrl.trim());
      setStatusMessage('✓ Repository successfully imported into RAG vector store!');
      setTimeout(() => {
        onClose();
        setRepoUrl('');
        setStatusMessage(null);
      }, 1500);
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Failed to import code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay active">
      <div className="modal-card gemini-import-modal">
        <div className="modal-header">
          <h2>Import code</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="gemini-import-form">
          <div className="gemini-input-group">
            <span className="gemini-input-label">GitHub repository or branch URL</span>
            <div className="gemini-input-row">
              <input
                type="url"
                className="form-control gemini-input"
                placeholder="e.g. https://github.com/user/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                required
                disabled={loading}
                autoFocus
              />
              <button
                type="submit"
                className="btn btn-primary gemini-import-btn"
                disabled={loading || !repoUrl.trim()}
              >
                {loading ? <Loader2 size={16} className="spin-icon" /> : 'Import'}
              </button>
            </div>
          </div>

          {statusMessage && (
            <div className="github-analysis-alert success" style={{ marginTop: '1rem' }}>
              <CheckCircle2 size={16} />
              <span>{statusMessage}</span>
            </div>
          )}

          {errorMessage && (
            <div className="github-analysis-alert error" style={{ marginTop: '1rem' }}>
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="gemini-import-footer">
            <label className="gemini-folder-link" style={{ cursor: 'pointer' }}>
              <FolderUp size={16} />
              <span>Upload folder</span>
              <input
                type="file"
                webkitdirectory=""
                directory=""
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    alert(`Selected ${e.target.files.length} files from folder. Use the sidebar dropzone to upload.`);
                  }
                }}
              />
            </label>
          </div>
        </form>
      </div>
    </div>
  );
}
