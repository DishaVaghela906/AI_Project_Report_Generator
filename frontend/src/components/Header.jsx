import React from 'react';
import { Plus, Home, Layout, User, LogOut, LogIn } from 'lucide-react';

export default function Header({ 
  llmHealth, 
  activeTab, 
  onSelectTab, 
  onOpenNewProjectModal,
  currentUser,
  onOpenAuthModal,
  onLogout
}) {
  const getInitial = (name) => {
    if (!name) return 'U';
    return name.charAt(0).toUpperCase();
  };

  return (
    <header className="app-header">
      <div className="brand-container" style={{ cursor: 'pointer' }} onClick={() => onSelectTab('tab-home')}>
        <div className="brand-logo">AI</div>
        <span className="brand-title">AI Report Generator</span>
      </div>

      <nav className="header-nav">
        <button 
          className={`header-nav-btn ${activeTab === 'tab-home' ? 'active' : ''}`}
          onClick={() => onSelectTab('tab-home')}
        >
          <Home size={16} />
          <span>Home</span>
        </button>
        
        <button 
          className={`header-nav-btn ${activeTab !== 'tab-home' ? 'active' : ''}`}
          onClick={() => onSelectTab('tab-generator')}
        >
          <Layout size={16} />
          <span>Report Studio</span>
        </button>
      </nav>
      
      <div className="header-actions">

        {/* Auth State */}
        {currentUser ? (
          <div class="user-badge">
            <div class="user-avatar">{getInitial(currentUser.full_name)}</div>
            <span>{currentUser.full_name}</span>
            <button class="btn btn-secondary btn-logout" onClick={onLogout} title="Log Out">
              <LogOut size={14} />
            </button>
          </div>
        ) : (
          <button class="btn btn-secondary btn-sm" onClick={onOpenAuthModal}>
            <LogIn size={15} /> Sign In
          </button>
        )}

        <button class="btn btn-primary btn-sm" onClick={onOpenNewProjectModal}>
          <Plus size={16} /> New Project
        </button>
      </div>
    </header>
  );
}


