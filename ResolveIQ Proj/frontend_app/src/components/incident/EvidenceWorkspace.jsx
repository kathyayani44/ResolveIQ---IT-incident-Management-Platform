import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText, ExternalLink } from 'lucide-react';

export function EvidenceWorkspace({ evidence = [] }) {
  const [expandedId, setExpandedId] = useState(evidence[0]?.chunk_id || null);

  if (evidence.length === 0) {
    return (
      <div className="panel" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>KNOWLEDGE & RETRIEVED EVIDENCE</h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>No retrieved knowledge chunks associated with this incident.</p>
      </div>
    );
  }

  return (
    <div className="panel" style={{ marginBottom: '24px' }}>
      <div className="panel-header">
        <div>
          <h3 style={{ fontSize: '15px' }}>KNOWLEDGE & EVIDENCE WORKSPACE</h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Top dense vector retrieved postmortems, runbooks, and SOPs</p>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--brand-primary)', fontWeight: '600', backgroundColor: 'rgba(56,189,248,0.12)', padding: '4px 10px', borderRadius: '4px' }}>
          {evidence.length} Relevant Sources
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {evidence.map((item) => {
          const isExpanded = expandedId === item.chunk_id;
          const scorePct = Math.round((item.score || 0.85) * 100);

          return (
            <div
              key={item.chunk_id}
              style={{
                backgroundColor: 'var(--bg-dark)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '14px 16px',
                transition: 'border-color 0.15s ease'
              }}
            >
              <div
                onClick={() => setExpandedId(isExpanded ? null : item.chunk_id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <BookOpen size={16} color="var(--brand-primary)" />
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                      {item.source || `Knowledge Chunk ${item.chunk_id}`}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Type: <span style={{ textTransform: 'uppercase', color: 'var(--text-secondary)' }}>{item.document_type || 'DOCUMENT'}</span> • ID: <span className="code-mono">{item.chunk_id}</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  {/* Score bar */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '120px' }}>
                    <div style={{ flex: 1, height: '6px', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${scorePct}%`, height: '100%', backgroundColor: scorePct > 90 ? '#10b981' : 'var(--brand-primary)', borderRadius: '3px' }} />
                    </div>
                    <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-secondary)', width: '32px' }}>
                      {scorePct}%
                    </span>
                  </div>

                  {isExpanded ? <ChevronUp size={16} color="var(--text-muted)" /> : <ChevronDown size={16} color="var(--text-muted)" />}
                </div>
              </div>

              {isExpanded && (
                <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                  <div style={{
                    fontSize: '13px',
                    fontFamily: 'var(--font-sans)',
                    color: 'var(--text-primary)',
                    backgroundColor: 'var(--bg-surface)',
                    padding: '12px 14px',
                    borderRadius: '6px',
                    lineHeight: '1.6',
                    borderLeft: '3px solid var(--brand-primary)'
                  }}>
                    "{item.text}"
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default EvidenceWorkspace;
