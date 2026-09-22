import React, { useState } from 'react';
import { XCircle, X } from 'lucide-react';

export function RejectionModal({ isOpen, onClose, onConfirm, issueKey }) {
  const [reason, setReason] = useState('');
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    await onConfirm({ reason, feedback });
    setSubmitting(false);
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <XCircle size={20} color="#f87171" />
            <h3 style={{ fontSize: '17px', color: '#ffffff', fontWeight: '700' }}>Reject Resolution ({issueKey})</h3>
          </div>
          <button onClick={onClose} style={{ color: 'var(--text-muted)' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              Why are you rejecting this recommendation?
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Inaccurate root cause or unsafe steps for production"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-dark)',
                border: '1px solid var(--border-medium)',
                borderRadius: '6px',
                padding: '10px 12px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none',
                marginBottom: '12px'
              }}
            />

            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              Additional Feedback / Notes
            </label>
            <textarea
              rows={4}
              placeholder="Provide context or instructions for engineering team..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-dark)',
                border: '1px solid var(--border-medium)',
                borderRadius: '6px',
                padding: '10px 12px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn-reject">
              {submitting ? 'Submitting...' : 'Reject Resolution'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RejectionModal;
