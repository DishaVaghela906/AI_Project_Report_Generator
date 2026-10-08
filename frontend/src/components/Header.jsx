import React from 'react';
import { Plus, Home, Layout } from 'lucide-react';

export default function Header({ llmHealth, activeTab, onSelectTab, onOpenNewProjectModal }) {
  const isReady = llmHealth?.ready;
  const provider = llmHealth?.provider?.toUpperCase() || 'LLM';
  const model = llmHealth?.model || '';

  return (
    <header class="app-header">
      <div class="brand-container" style={{ cursor: 'pointer' }} onClick={() => onSelectTab('tab-home')}>
        <div class="brand-logo">AI</div>
        <span class="brand-title">AI Report Generator</span>
      </div>

      <nav class="header-nav">
        <button 
          class={`header-nav-btn ${activeTab === 'tab-home' ? 'active' : ''}`}
          onClick={() => onSelectTab('tab-home')}
        >
          <Home size={16} />
          <span>Home</span>
        </button>
        
        <button 
          class={`header-nav-btn ${activeTab !== 'tab-home' ? 'active' : ''}`}
          onClick={() => onSelectTab('tab-generator')}
        >
          <Layout size={16} />
          <span>Report Studio</span>
        </button>
      </nav>
      
      <div class="header-actions">
        <div 
          class="llm-badge"
          style={{
            backgroundColor: isReady ? 'var(--brand-accent-light)' : 'var(--status-error-bg)',
            color: isReady ? 'var(--brand-accent)' : 'var(--status-error-text)',
            borderColor: isReady ? 'var(--border-color)' : 'var(--status-error-text)'
          }}
        >
          <span 
            class="status-dot" 
            style={{ backgroundColor: isReady ? '#10B981' : '#EF4444' }}
          ></span>
          <span>{isReady ? `${provider}: ${model}` : `LLM Offline (${provider})`}</span>
        </div>
        <button class="btn btn-primary btn-sm" onClick={onOpenNewProjectModal}>
          <Plus size={16} /> New Project
        </button>
      </div>
    </header>
  );
}

