import React from 'react';
import { AlertCircle } from 'lucide-react';

export function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div style={{
      padding: '12px 16px',
      backgroundColor: 'rgba(239, 68, 68, 0.12)',
      border: '1px solid #ef4444',
      borderRadius: 'var(--radius-sm)',
      color: '#f87171',
      fontSize: '13px',
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      marginBottom: '16px'
    }}>
      <AlertCircle size={18} />
      <span>{message}</span>
    </div>
  );
}

export default ErrorBanner;
