import React from 'react';
import { 
  FileText, 
  ShieldCheck, 
  Cpu, 
  Database, 
  ArrowUp, 
  Sparkles, 
  CheckCircle2, 
  ExternalLink 
} from 'lucide-react';

export default function Footer({ onSelectTab, onLaunchStudio }) {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="landing-footer">
      <div className="footer-top">
        {/* Brand & Mission */}
        <div className="footer-brand-col">
          <div className="footer-brand" onClick={scrollToTop} style={{ cursor: 'pointer' }}>
            <div className="brand-logo">AI</div>
            <span className="brand-title">AI Report Generator</span>
          </div>
          <p className="footer-desc">
            An enterprise-grade academic report generation platform engineered to convert project code, 
            diagrams, and SRS documentation into institution-ready, formatted multipage reports.
          </p>
          <div className="footer-status-pill">
            <span className="status-live-pulse"></span>
            <span>All AI Generation Engines Operational</span>
          </div>
        </div>

        {/* Column 1: Workspace */}
        <div className="footer-links-col">
          <h4>Platform Studio</h4>
          <ul>
            <li>
              <button className="footer-link-btn" onClick={onLaunchStudio}>
                Report Studio
              </button>
            </li>
            <li>
              <button className="footer-link-btn" onClick={() => onSelectTab && onSelectTab('tab-project-info')}>
                Project Overview
              </button>
            </li>
            <li>
              <button className="footer-link-btn" onClick={() => onSelectTab && onSelectTab('tab-full-preview')}>
                Full Document Preview
              </button>
            </li>
            <li>
              <button className="footer-link-btn" onClick={onLaunchStudio}>
                RAG Document Vectorizer
              </button>
            </li>
          </ul>
        </div>

        {/* Column 2: Academic Standards */}
        <div className="footer-links-col">
          <h4>Formatting Standards</h4>
          <ul>
            <li><span>Font: Times New Roman</span></li>
            <li><span>H1: 16pt Bold, Centered</span></li>
            <li><span>H2: 14pt Bold, Left-Aligned</span></li>
            <li><span>Body: 12pt Justified (1.5x Spacing)</span></li>
            <li><span>Automated Certificate & Declaration</span></li>
          </ul>
        </div>

        {/* Column 3: Architecture */}
        <div className="footer-links-col">
          <h4>Core Technologies</h4>
          <ul>
            <li><span>High-Capacity LLM Inference</span></li>
            <li><span>ChromaDB Vector Embeddings</span></li>
            <li><span>Supabase Cloud PostgreSQL</span></li>
            <li><span>ReportLab Sanitized PDF Engine</span></li>
            <li><span>python-docx Academic Formatter</span></li>
          </ul>
        </div>
      </div>

      {/* Footer Bottom Bar */}
      <div className="footer-bottom">
        <div className="footer-copyright">
          © {new Date().getFullYear()} AI Academic Project Report Generator. Designed for University Excellence.
        </div>
      </div>
    </footer>
  );
}
