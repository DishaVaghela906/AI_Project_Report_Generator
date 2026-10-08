import React from 'react';
import { 
  Sparkles, 
  FileText, 
  ArrowRight, 
  Zap, 
  CheckCircle, 
  Cpu, 
  Database, 
  Download, 
  ShieldCheck, 
  BookOpen 
} from 'lucide-react';

export default function LandingHero({ onLaunchStudio, onNewProject, onSelectTab }) {
  return (
    <div class="landing-container">
      {/* Hero Section */}
      <div class="landing-hero">
        <div class="hero-badge">
          <Sparkles size={16} />
          <span>INSTITUTION-READY ACADEMIC REPORT GENERATOR</span>
        </div>
        
        <h1 class="hero-title">
          Automate Academic Project Reports <br />
          <span class="hero-title-gradient">With High-Precision AI</span>
        </h1>
        
        <p class="hero-subtitle">
          Transform raw project code, specifications, and architecture into publication-ready 
          multipage academic reports. Built for university standards with Times New Roman typography, 
          RAG vector context, and instant PDF/DOCX exports.
        </p>

        {/* CTA Buttons - Bypass Login */}
        <div class="hero-cta-group">
          <button class="btn btn-primary btn-lg" onClick={onLaunchStudio}>
            <span>Launch Studio</span>
            <ArrowRight size={18} />
          </button>
          
          <button class="btn btn-secondary btn-lg" onClick={onNewProject}>
            <FileText size={18} />
            <span>Create New Project</span>
          </button>
        </div>

        {/* Quick Spec Pills */}
        <div class="spec-pills">
          <div class="spec-pill">
            <CheckCircle size={14} class="pill-icon" />
            <span>Font: Times New Roman</span>
          </div>
          <div class="spec-pill">
            <CheckCircle size={14} class="pill-icon" />
            <span>H1: 16pt Bold | H2: 14pt Bold | Body: 12pt Justified</span>
          </div>
          <div class="spec-pill">
            <CheckCircle size={14} class="pill-icon" />
            <span>PDF & DOCX Export</span>
          </div>
          <div class="spec-pill">
            <CheckCircle size={14} class="pill-icon" />
            <span>No Signup Required</span>
          </div>
        </div>
      </div>

      {/* Feature Grid */}
      <div class="landing-features">
        <div class="section-header">
          <h2>Engineered for Technical Excellence</h2>
          <p>Everything you need to produce comprehensive university-standard report documentation.</p>
        </div>

        <div class="features-grid">
          <div class="feature-card" onClick={onLaunchStudio}>
            <div class="feature-icon"><Cpu size={24} /></div>
            <h3>120B AI Generation</h3>
            <p>Powered by high-parameter LLMs capable of expanding concise prompts into detailed 14-page academic chapters.</p>
          </div>

          <div class="feature-card" onClick={onLaunchStudio}>
            <div class="feature-icon"><Database size={24} /></div>
            <h3>RAG Vector Search</h3>
            <p>Upload project documentation and PDFs. Context chunks are vectorized into ChromaDB for accurate output grounding.</p>
          </div>

          <div class="feature-card" onClick={() => onSelectTab && onSelectTab('tab-full-preview')}>
            <div class="feature-icon"><BookOpen size={24} /></div>
            <h3>Strict Academic Rules</h3>
            <p>Strictly adheres to 16pt main headings, 14pt subheadings, 12pt justified body text, and native PDF grid tables.</p>
          </div>

          <div class="feature-card" onClick={onLaunchStudio}>
            <div class="feature-icon"><Download size={24} /></div>
            <h3>Zero Black Box Exports</h3>
            <p>Sanitized ReportLab & DOCX export pipeline ensures clean diagrams, ASCII charts, and clean typography with no missing glyphs.</p>
          </div>
        </div>
      </div>

      {/* 3 Step Workflow */}
      <div class="landing-steps">
        <div class="section-header">
          <h2>3 Steps to Your Final Report</h2>
        </div>

        <div class="steps-grid">
          <div class="step-card">
            <div class="step-num">01</div>
            <h4>Setup Project & RAG Files</h4>
            <p>Create a project title, guide info, and upload relevant reference documents for AI vectorization.</p>
          </div>

          <div class="step-card">
            <div class="step-num">02</div>
            <h4>Generate & Edit Chapters</h4>
            <p>Generate individual chapters (Introduction, System Design, Implementation) with custom instructions.</p>
          </div>

          <div class="step-card">
            <div class="step-num">03</div>
            <h4>Export PDF or DOCX</h4>
            <p>Download your complete project report in clean Times New Roman PDF or fully editable DOCX format.</p>
          </div>
        </div>
      </div>

      {/* Footer Banner */}
      <div class="landing-footer-banner">
        <div class="banner-content">
          <h3>Ready to generate your report?</h3>
          <p>Bypass signup and start using the Report Studio immediately.</p>
        </div>
        <button class="btn btn-primary btn-lg" onClick={onLaunchStudio}>
          <Zap size={18} />
          <span>Enter Workspace</span>
        </button>
      </div>
    </div>
  );
}
