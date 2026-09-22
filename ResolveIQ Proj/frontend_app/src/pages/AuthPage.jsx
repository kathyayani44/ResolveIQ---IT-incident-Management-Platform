import React, { useState } from 'react';
import { Cpu, ShieldCheck, Mail, Lock, User, ArrowRight, AlertCircle, Eye, EyeOff } from 'lucide-react';

export function AuthPage({ onLogin, onRegister }) {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Basic frontend validation
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!password || password.length < 4) {
      setError('Password must be at least 4 characters.');
      return;
    }
    if (isRegisterMode && !name.trim()) {
      setError('Please provide your full name.');
      return;
    }

    setLoading(true);
    try {
      if (isRegisterMode) {
        const res = await onRegister(email.trim(), password, name.trim());
        if (!res.ok) {
          setError(res.error || 'Failed to create account. Please try again.');
        }
      } else {
        const res = await onLogin(email.trim(), password);
        if (!res.ok) {
          setError(res.error || 'Invalid email or password.');
        }
      }
    } catch (err) {
      setError(err.message || 'Authentication error. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (regMode) => {
    setIsRegisterMode(regMode);
    setError(null);
  };

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      backgroundColor: '#0c0e14',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      boxSizing: 'border-box',
      background: 'radial-gradient(circle at 50% 20%, rgba(56, 189, 248, 0.08) 0%, transparent 60%), #0c0e14'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        backgroundColor: '#12151f',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '36px 32px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 40px -10px rgba(56, 189, 248, 0.15)',
        boxSizing: 'border-box'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            color: '#ffffff',
            boxShadow: '0 8px 20px -4px rgba(56, 189, 248, 0.4)'
          }}>
            <Cpu size={28} />
          </div>
          <h1 style={{
            fontSize: '24px',
            fontWeight: '800',
            color: '#ffffff',
            margin: '0 0 6px',
            letterSpacing: '-0.02em'
          }}>
            ResolveIQ
          </h1>
          <p style={{
            fontSize: '13px',
            color: 'rgba(255, 255, 255, 0.6)',
            margin: 0
          }}>
            Autonomous Incident Operations & SRE Co-Pilot
          </p>
        </div>

        {/* Tab Switcher */}
        <div style={{
          display: 'flex',
          backgroundColor: '#1a1e2c',
          borderRadius: '8px',
          padding: '4px',
          marginBottom: '24px',
          border: '1px solid rgba(255, 255, 255, 0.06)'
        }}>
          <button
            type="button"
            onClick={() => switchMode(false)}
            style={{
              flex: 1,
              padding: '8px 14px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: !isRegisterMode ? '#252a3d' : 'transparent',
              color: !isRegisterMode ? '#ffffff' : 'rgba(255, 255, 255, 0.6)',
              fontWeight: !isRegisterMode ? '600' : '500',
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => switchMode(true)}
            style={{
              flex: 1,
              padding: '8px 14px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: isRegisterMode ? '#252a3d' : 'transparent',
              color: isRegisterMode ? '#ffffff' : 'rgba(255, 255, 255, 0.6)',
              fontWeight: isRegisterMode ? '600' : '500',
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            padding: '12px 14px',
            borderRadius: '8px',
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            color: '#f87171',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '20px'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Authentication Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {isRegisterMode && (
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'rgba(255, 255, 255, 0.75)', marginBottom: '6px' }}>
                Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <User size={16} color="rgba(255, 255, 255, 0.4)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Jane Doe"
                  required={isRegisterMode}
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    padding: '10px 12px 10px 38px',
                    borderRadius: '8px',
                    backgroundColor: '#171b28',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    color: '#ffffff',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'rgba(255, 255, 255, 0.75)', marginBottom: '6px' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color="rgba(255, 255, 255, 0.4)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@company.com"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: '10px 12px 10px 38px',
                  borderRadius: '8px',
                  backgroundColor: '#171b28',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: '#ffffff',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'rgba(255, 255, 255, 0.75)', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="rgba(255, 255, 255, 0.4)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: '10px 38px 10px 38px',
                  borderRadius: '8px',
                  backgroundColor: '#171b28',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: '#ffffff',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '10px',
                  background: 'none',
                  border: 'none',
                  color: 'rgba(255, 255, 255, 0.4)',
                  cursor: 'pointer',
                  padding: 0
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: '8px',
              padding: '12px 18px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
              color: '#ffffff',
              fontWeight: '700',
              fontSize: '14px',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              opacity: loading ? 0.7 : 1,
              transition: 'opacity 0.15s ease',
              boxShadow: '0 4px 14px 0 rgba(56, 189, 248, 0.35)'
            }}
          >
            <span>{loading ? 'Authenticating...' : isRegisterMode ? 'Create ResolveIQ Account' : 'Sign In to Console'}</span>
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>

        {/* Security / Architecture Footer */}
        <div style={{
          marginTop: '28px',
          paddingTop: '20px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <ShieldCheck size={18} color="#34d399" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '11px', color: 'rgba(255, 255, 255, 0.5)', lineHeight: '1.4' }}>
            Enterprise PBKDF2 HMAC SHA-256 password security with per-user salt. Jira Cloud credentials managed securely at system level.
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
