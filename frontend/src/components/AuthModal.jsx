import React, { useState } from 'react';
import axios from 'axios';
import { X, Lock, Mail, User, ShieldCheck, ArrowRight, AlertCircle } from 'lucide-react';

export default function AuthModal({ isOpen, onClose, onAuthSuccess, initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode); // 'login' | 'signup'
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      const endpoint = mode === 'signup' ? '/api/v1/auth/signup' : '/api/v1/auth/login';
      const payload = mode === 'signup' 
        ? { full_name: fullName.trim(), email: email.trim(), password }
        : { email: email.trim(), password };

      const res = await axios.post(endpoint, payload);
      const { access_token, user } = res.data;

      // Reset form fields
      setFullName('');
      setEmail('');
      setPassword('');

      onAuthSuccess(user, access_token, mode === 'signup' ? 'Registered & logged in!' : 'Logged in successfully!');
      onClose();
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Authentication failed.';
      setErrorMessage(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card auth-modal-card">
        {/* Header */}
        <div className="modal-header">
          <div className="auth-header-title">
            <ShieldCheck size={24} className="auth-icon-gold" />
            <h2>{mode === 'signup' ? 'Create User Account' : 'Welcome Back'}</h2>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Auth Tabs */}
        <div className="auth-tabs">
          <button 
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setErrorMessage(null); }}
          >
            Sign In
          </button>
          <button 
            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => { setMode('signup'); setErrorMessage(null); }}
          >
            Sign Up
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div class="auth-error-alert">
            <AlertCircle size={16} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} class="auth-form">
          {mode === 'signup' && (
            <div class="form-group">
              <label>Full Name</label>
              <div class="input-with-icon">
                <User size={16} class="input-icon" />
                <input 
                  type="text"
                  class="form-control"
                  placeholder="e.g. Disha Vaghela"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required={mode === 'signup'}
                />
              </div>
            </div>
          )}

          <div class="form-group">
            <label>Email Address</label>
            <div class="input-with-icon">
              <Mail size={16} class="input-icon" />
              <input 
                type="email"
                class="form-control"
                placeholder="name@institution.ac.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label>Password</label>
            <div class="input-with-icon">
              <Lock size={16} class="input-icon" />
              <input 
                type="password"
                class="form-control"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
          </div>

          <button 
            type="submit" 
            class="btn btn-primary btn-block btn-lg" 
            disabled={loading}
            style={{ marginTop: '1.25rem' }}
          >
            {loading ? (
              <span class="spinner"></span>
            ) : (
              <>
                <span>{mode === 'signup' ? 'Create Account' : 'Sign In'}</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Footer switch */}
        <div class="auth-footer">
          {mode === 'signup' ? (
            <p>
              Already have an account?{' '}
              <span class="auth-link" onClick={() => { setMode('login'); setErrorMessage(null); }}>
                Sign In
              </span>
            </p>
          ) : (
            <p>
              Don't have an account yet?{' '}
              <span class="auth-link" onClick={() => { setMode('signup'); setErrorMessage(null); }}>
                Create one now
              </span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
