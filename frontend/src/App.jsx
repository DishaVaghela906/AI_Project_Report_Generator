import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import NewProjectModal from './components/NewProjectModal';
import ChapterStudio from './components/ChapterStudio';
import ProjectOverview from './components/ProjectOverview';
import FullReportPreview from './components/FullReportPreview';
import LandingHero from './components/LandingHero';
import AuthModal from './components/AuthModal';

export default function App() {
  const [llmHealth, setLlmHealth] = useState(null);
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [chaptersData, setChaptersData] = useState({});
  const [currentChapterNumber, setCurrentChapterNumber] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('tab-home');
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // User Auth State
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('auth_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });

  const [authToken, setAuthToken] = useState(() => localStorage.getItem('auth_token') || null);

  // Configure Axios Auth Header Interceptor
  useEffect(() => {
    if (authToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
      localStorage.setItem('auth_token', authToken);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('auth_token');
    }
  }, [authToken]);

  // Initial Load
  useEffect(() => {
    checkHealth();
    loadProjects();
  }, []);

  const handleAuthSuccess = (user, token, message) => {
    setCurrentUser(user);
    setAuthToken(token);
    localStorage.setItem('auth_user', JSON.stringify(user));
    localStorage.setItem('auth_token', token);
    showToast(`✓ Welcome ${user.full_name}! ${message}`);
  };

  const handleLogout = async () => {
    try {
      if (authToken) {
        await axios.post('/api/v1/auth/logout');
      }
    } catch (e) {
      // Ignore
    }
    setCurrentUser(null);
    setAuthToken(null);
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_token');
    delete axios.defaults.headers.common['Authorization'];
    showToast('You have been logged out.');
  };

  // When active project changes, load uploaded files & chapters
  useEffect(() => {
    if (currentProject) {
      loadUploadedFiles(currentProject.id);
      loadChapters(currentProject.id);
    }
  }, [currentProject]);

  const showToast = (msg, type = 'info') => {
    setToastMessage({ msg, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // API 1: Health Check
  const checkHealth = async () => {
    try {
      const res = await axios.get('/health');
      setLlmHealth(res.data?.llm || {});
    } catch (err) {
      setLlmHealth({ ready: false, provider: 'offline', model: 'N/A' });
    }
  };

  // API 2: Projects List
  const loadProjects = async () => {
    try {
      const res = await axios.get('/api/v1/projects/');
      const list = res.data || [];
      setProjects(list);
      if (list.length > 0 && !currentProject) {
        setCurrentProject(list[0]);
      }
    } catch (err) {
      showToast('Failed to load projects from backend', 'error');
    }
  };

  // API 3: Create Project
  const handleCreateProject = async (payload) => {
    try {
      const res = await axios.post('/api/v1/projects/', payload);
      const newProj = res.data;
      setProjects(prev => [newProj, ...prev]);
      setCurrentProject(newProj);
      setIsNewProjectModalOpen(false);
      setActiveTab('tab-generator');
      showToast(`✓ Project "${newProj.title}" created successfully!`);
    } catch (err) {
      showToast('Error creating project: ' + (err.response?.data?.detail || err.message), 'error');
    }
  };

  // API 4: RAG File Upload
  const handleFileUpload = async (files) => {
    if (!currentProject) {
      showToast('Please select or create a project first', 'error');
      return;
    }

    for (let file of files) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        showToast(`Uploading & vectorizing ${file.name}...`);
        const res = await axios.post(`/api/v1/uploads/${currentProject.id}`, formData);
        showToast(`✓ Indexed ${file.name} (${res.data.chunks_count || 0} chunks)`);
      } catch (err) {
        showToast(`Upload failed for ${file.name}: ` + err.message, 'error');
      }
    }
    loadUploadedFiles(currentProject.id);
  };

  // API 5: Load Uploaded Files List
  const loadUploadedFiles = async (projectId) => {
    try {
      const res = await axios.get(`/api/v1/uploads/${projectId}`);
      setUploadedFiles(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  // API 6: Load Chapters List
  const loadChapters = async (projectId) => {
    try {
      const res = await axios.get(`/api/v1/chapters/${projectId}`);
      const map = {};
      (res.data || []).forEach(ch => {
        map[ch.chapter_number] = ch;
      });
      setChaptersData(map);
    } catch (err) {
      console.error(err);
    }
  };

  // API 7: Generate Chapter
  const handleGenerateChapter = async (chapterNumber, extraInstructions) => {
    if (!currentProject) {
      showToast('Please select a project first', 'error');
      return;
    }

    setIsGenerating(true);
    showToast(`Generating Chapter ${chapterNumber} with AI...`);

    try {
      const res = await axios.post('/api/v1/chapters/generate', {
        project_id: currentProject.id,
        chapter_number: chapterNumber,
        extra_instructions: extraInstructions || undefined,
      });

      const updatedChapter = res.data;
      setChaptersData(prev => ({
        ...prev,
        [chapterNumber]: updatedChapter,
      }));
      showToast(`✓ Chapter ${chapterNumber} generated successfully!`);
    } catch (err) {
      showToast('Generation failed: ' + (err.response?.data?.detail || err.message), 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  // API 8: Save Chapter Content
  const handleSaveChapterContent = async (chapterNumber, content) => {
    if (!currentProject) return;
    try {
      const res = await axios.patch(`/api/v1/chapters/${currentProject.id}/${chapterNumber}`, {
        content,
      });
      setChaptersData(prev => ({
        ...prev,
        [chapterNumber]: res.data,
      }));
      showToast('✓ Chapter content saved!');
    } catch (err) {
      showToast('Failed to save chapter: ' + err.message, 'error');
    }
  };

  // API 9: Report Export (PDF / DOCX)
  const handleExport = async (format) => {
    if (!currentProject) {
      showToast('Please select a project first', 'error');
      return;
    }

    try {
      showToast(`Generating ${format.toUpperCase()} report...`);
      const res = await axios.post(`/api/v1/reports/export/${format}`, {
        project_id: currentProject.id,
      });

      const filename = res.data.filename;
      const downloadUrl = `/api/v1/reports/download/${filename}`;

      // Trigger Download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      showToast(`✓ Downloaded ${filename}`);
    } catch (err) {
      showToast(`Export failed: ${err.message}`, 'error');
    }
  };

  return (
    <div>
      {/* Header */}
      <Header
        llmHealth={llmHealth}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenNewProjectModal={() => setIsNewProjectModalOpen(true)}
        currentUser={currentUser}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Container: Landing Page or Workspace */}
      {activeTab === 'tab-home' ? (
        <LandingHero
          onLaunchStudio={() => setActiveTab('tab-generator')}
          onNewProject={() => setIsNewProjectModalOpen(true)}
          onSelectTab={setActiveTab}
        />
      ) : (
        <div class="app-container">
          <Sidebar
            projects={projects}
            currentProject={currentProject}
            onSelectProject={setCurrentProject}
            uploadedFiles={uploadedFiles}
            onFileUpload={handleFileUpload}
            chaptersData={chaptersData}
            currentChapterNumber={currentChapterNumber}
            onSelectChapter={setCurrentChapterNumber}
            onExport={handleExport}
          />

          <main class="app-main">
            <div class="workspace-card">

              {/* Workspace Tabs */}
              <nav class="workspace-nav">
                <div
                  class={`nav-tab ${activeTab === 'tab-generator' ? 'active' : ''}`}
                  onClick={() => setActiveTab('tab-generator')}
                >
                  Chapter Generator
                </div>
                <div
                  class={`nav-tab ${activeTab === 'tab-project-info' ? 'active' : ''}`}
                  onClick={() => setActiveTab('tab-project-info')}
                >
                  Project Overview
                </div>
                <div
                  class={`nav-tab ${activeTab === 'tab-full-preview' ? 'active' : ''}`}
                  onClick={() => setActiveTab('tab-full-preview')}
                >
                  Full Document Preview
                </div>
              </nav>

              {/* Tab 1: Studio */}
              {activeTab === 'tab-generator' && (
                <ChapterStudio
                  currentChapterNumber={currentChapterNumber}
                  chapterData={chaptersData[currentChapterNumber]}
                  isGenerating={isGenerating}
                  onGenerate={handleGenerateChapter}
                  onSaveContent={handleSaveChapterContent}
                />
              )}

              {/* Tab 2: Overview */}
              {activeTab === 'tab-project-info' && (
                <ProjectOverview project={currentProject} />
              )}

              {/* Tab 3: Full Report Preview */}
              {activeTab === 'tab-full-preview' && (
                <FullReportPreview
                  project={currentProject}
                  chaptersData={chaptersData}
                  onExport={handleExport}
                />
              )}

            </div>
          </main>
        </div>
      )}

      {/* Modals */}
      <NewProjectModal
        isOpen={isNewProjectModalOpen}
        onClose={() => setIsNewProjectModalOpen(false)}
        onCreateProject={handleCreateProject}
      />

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div class="toast-container">
          <div
            class="toast"
            style={{
              backgroundColor: toastMessage.type === 'error' ? 'var(--status-error-bg)' : 'var(--brand-primary)',
              color: toastMessage.type === 'error' ? 'var(--status-error-text)' : 'var(--bg-main)'
            }}
          >
            {toastMessage.msg}
          </div>
        </div>
      )}
    </div>
  );
}
