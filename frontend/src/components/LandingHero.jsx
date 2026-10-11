import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  FileText, 
  ArrowRight, 
  Zap, 
  CheckCircle, 
  Cpu, 
  Database, 
  BookOpen,
  Terminal,
  Layers,
  Activity,
  Award
} from 'lucide-react';
import Footer from './Footer';
import RocketBackToTop from './RocketBackToTop';

const SIMULATION_SNIPPETS = [
  "CHAPTER 3: SYSTEM ARCHITECTURE & METHODOLOGY\n\n3.1 High-Level Architecture\nThe proposed system employs a modular, distributed architecture combining vector retrieval with state-of-the-art transformer models. In order to guarantee deterministic citation alignment, all uploaded technical documents are parsed, chunked, and embedded into high-dimensional vector spaces...",
  "CHAPTER 4: DETAILED DESIGN & DATA MODEL\n\n4.1 Database Design\nThe persistence layer is hosted on Supabase PostgreSQL, enforcing strict foreign key constraints and Row-Level Security (RLS). Entity Relationship models define distinct schemas for user profiles, project metadata, and vectorized document chunks...",
  "CHAPTER 5: IMPLEMENTATION & EXPERIMENTAL RESULTS\n\n5.1 Core Algorithm Implementation\nThe document compilation engine utilizes Python's ReportLab with pre-sanitized styling pipelines. Unicode characters and technical flowcharts are sanitized against font glyph constraints to eliminate missing-character artifacts..."
];

export default function LandingHero({ onLaunchStudio, onNewProject, onSelectTab }) {
  const [snippetIndex, setSnippetIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [charIndex, setCharIndex] = useState(0);
  const [progressVal, setProgressVal] = useState(72);

  // Live typewriter simulation effect
  useEffect(() => {
    const currentTarget = SIMULATION_SNIPPETS[snippetIndex];
    if (charIndex < currentTarget.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(prev => prev + currentTarget[charIndex]);
        setCharIndex(prev => prev + 1);
        setProgressVal(Math.min(99, 50 + Math.floor((charIndex / currentTarget.length) * 49)));
      }, 25);
      return () => clearTimeout(timeout);
    } else {
      const pauseTimeout = setTimeout(() => {
        setDisplayedText('');
        setCharIndex(0);
        setSnippetIndex(prev => (prev + 1) % SIMULATION_SNIPPETS.length);
        setProgressVal(50);
      }, 3500);
      return () => clearTimeout(pauseTimeout);
    }
  }, [charIndex, snippetIndex]);

  return (
    <div className="landing-container">
      {/* Background Animated Ambient Lights */}
      <div className="ambient-orb ambient-orb-1" aria-hidden="true"></div>
      <div className="ambient-orb ambient-orb-2" aria-hidden="true"></div>

      {/* Hero Section */}
      <div className="landing-hero">
        <div className="hero-badge">
          <Sparkles size={16} />
          <span>INSTITUTION-READY ACADEMIC REPORT GENERATOR</span>
        </div>
        
        <h1 className="hero-title">
          Automate Academic Project Reports <br />
          <span className="hero-title-gradient">With High-Precision AI</span>
        </h1>
        
        <p className="hero-subtitle">
          Transform raw project code, specifications, and architecture into publication-ready 
          multipage academic reports. Built for university standards with Times New Roman typography, 
          RAG vector context, and instant PDF/DOCX exports.
        </p>

        {/* CTA Buttons */}
        <div className="hero-cta-group">
          <button className="btn btn-primary btn-lg" onClick={onLaunchStudio}>
            <span>Launch Studio</span>
            <ArrowRight size={18} />
          </button>
          
          <button className="btn btn-secondary btn-lg" onClick={onNewProject}>
            <FileText size={18} />
            <span>Create New Project</span>
          </button>
        </div>

        {/* Quick Spec Pills */}
        <div className="spec-pills">
          <div className="spec-pill">
            <CheckCircle size={14} className="pill-icon" />
            <span>Font: Times New Roman</span>
          </div>
          <div className="spec-pill">
            <CheckCircle size={14} className="pill-icon" />
            <span>H1: 16pt Bold | H2: 14pt Bold | Body: 12pt Justified</span>
          </div>
          <div className="spec-pill">
            <CheckCircle size={14} className="pill-icon" />
            <span>PDF &amp; DOCX Export</span>
          </div>
          <div className="spec-pill">
            <CheckCircle size={14} className="pill-icon" />
            <span>Secure User Authentication</span>
          </div>
        </div>

        {/* Live Animated Interactive Report Generation Simulator */}
        <div className="simulation-wrapper">
          {/* Floating Live Badge Left */}
          <div className="float-badge float-badge-left">
            <Activity size={16} className="text-accent" />
            <div>
              <div className="float-badge-title">Live AI Engine</div>
              <div className="float-badge-sub">14 Pages / Chapter</div>
            </div>
          </div>

          {/* Floating Live Badge Right */}
          <div className="float-badge float-badge-right">
            <Award size={16} className="text-accent" />
            <div>
              <div className="float-badge-title">Times New Roman</div>
              <div className="float-badge-sub">Strict University Standard</div>
            </div>
          </div>

          {/* Interactive Document Card Simulator */}
          <div className="sim-card">
            <div className="sim-card-header">
              <div className="sim-window-dots">
                <span className="dot dot-red"></span>
                <span className="dot dot-amber"></span>
                <span className="dot dot-green"></span>
              </div>
              <div className="sim-card-title">
                <Terminal size={14} />
                <span>Live Academic Generation Stream</span>
              </div>
              <div className="sim-live-indicator">
                <span className="live-dot-pulse"></span>
                <span>INFERENCE ACTIVE</span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="sim-progress-strip">
              <div className="sim-progress-label">
                <span>Compilation Progress</span>
                <span className="sim-progress-num">{progressVal}%</span>
              </div>
              <div className="sim-progress-bar-bg">
                <div 
                  className="sim-progress-bar-fill" 
                  style={{ width: `${progressVal}%` }}
                ></div>
              </div>
            </div>

            {/* Simulated Report Viewport */}
            <div className="sim-viewport">
              <div className="sim-doc-paper">
                <div className="sim-doc-header-mark">CONFIDENTIAL &amp; ACADEMIC SUBMISSION</div>
                <pre className="sim-doc-content">
                  {displayedText}
                  <span className="typewriter-cursor">|</span>
                </pre>
              </div>
            </div>

            <div className="sim-card-footer">
              <div className="sim-stat">
                <Layers size={14} />
                <span>Format: 1.5 Line Spacing</span>
              </div>
              <div className="sim-stat">
                <BookOpen size={14} />
                <span>Standard University Structure</span>
              </div>
              <button className="btn-sim-action" onClick={onLaunchStudio}>
                <span>Try In Studio</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="landing-features">
        <div className="section-header">
          <h2>Engineered for Technical Excellence</h2>
          <p>Everything you need to produce comprehensive university-standard report documentation.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card" onClick={onLaunchStudio}>
            <div className="feature-icon"><Cpu size={24} /></div>
            <h3>120B AI Generation</h3>
            <p>Powered by high-parameter LLMs capable of expanding concise prompts into detailed 14-page academic chapters.</p>
          </div>

          <div className="feature-card" onClick={onLaunchStudio}>
            <div className="feature-icon"><Database size={24} /></div>
            <h3>RAG Vector Search</h3>
            <p>Upload project documentation and PDFs. Context chunks are vectorized into ChromaDB for accurate output grounding.</p>
          </div>

          <div className="feature-card" onClick={() => onSelectTab && onSelectTab('tab-full-preview')}>
            <div className="feature-icon"><BookOpen size={24} /></div>
            <h3>Strict Academic Rules</h3>
            <p>Strictly adheres to 16pt main headings, 14pt subheadings, 12pt justified body text, and native PDF grid tables.</p>
          </div>
        </div>
      </div>

      {/* 3 Step Workflow */}
      <div className="landing-steps">
        <div className="section-header">
          <h2>3 Steps to Your Final Report</h2>
        </div>

        <div className="steps-grid">
          <div className="step-card">
            <div className="step-num">01</div>
            <h4>Setup Project &amp; RAG Files</h4>
            <p>Create a project title, guide info, and upload relevant reference documents for AI vectorization.</p>
          </div>

          <div className="step-card">
            <div className="step-num">02</div>
            <h4>Generate &amp; Edit Chapters</h4>
            <p>Generate individual chapters (Introduction, System Design, Implementation) with custom instructions.</p>
          </div>

          <div className="step-card">
            <div className="step-num">03</div>
            <h4>Export PDF or DOCX</h4>
            <p>Download your complete project report in clean Times New Roman PDF or fully editable DOCX format.</p>
          </div>
        </div>
      </div>

      {/* Footer Banner CTA */}
      <div className="landing-footer-banner">
        <div className="banner-content">
          <h3>Ready to generate your report?</h3>
          <p>Sign in to access Report Studio and generate publication-ready academic reports.</p>
        </div>
        <button className="btn btn-primary btn-lg" onClick={onLaunchStudio}>
          <Zap size={18} />
          <span>Enter Workspace</span>
        </button>
      </div>

      {/* Global Comprehensive Landing Footer */}
      <Footer onSelectTab={onSelectTab} onLaunchStudio={onLaunchStudio} />

      {/* Floating Rocket Back-To-Top Button in Bottom-Right Corner */}
      <RocketBackToTop />
    </div>
  );
}
