import React from 'react';
import { ShieldAlert, ListOrdered, CheckSquare, Sparkles, AlertTriangle, BookOpen, CheckCircle2 } from 'lucide-react';

export function ProposedResolution({ resolution }) {
  if (!resolution) {
    return (
      <div className="panel" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>PROPOSED RESOLUTION RECOMMENDATION</h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Resolution recommendation generation in progress or pending AI analysis...</p>
      </div>
    );
  }

  const isGrounded = Boolean(resolution.is_grounded);
  const groundingType = resolution.grounding_type || (isGrounded ? 'rag_grounded' : 'insufficient_evidence');
  const evidenceSources = resolution.evidence_sources || [];

  return (
    <div className="panel" style={{
      marginBottom: '24px',
      border: isGrounded ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid rgba(245, 158, 11, 0.4)'
    }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isGrounded ? (
            <Sparkles size={18} color="var(--brand-primary)" />
          ) : (
            <AlertTriangle size={18} color="#fbbf24" />
          )}
          <h3 style={{ fontSize: '15px', color: '#ffffff' }}>PROPOSED RESOLUTION RECOMMENDATION</h3>
        </div>
        <span style={{
          fontSize: '11px',
          fontWeight: '700',
          padding: '2px 8px',
          borderRadius: '4px',
          backgroundColor: isGrounded ? 'rgba(52, 211, 153, 0.15)' : 'rgba(245, 158, 11, 0.15)',
          color: isGrounded ? '#34d399' : '#fbbf24',
          border: isGrounded ? '1px solid rgba(52, 211, 153, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
          textTransform: 'uppercase'
        }}>
          {isGrounded ? '✓ RAG Grounded & Verified' : 'Ungrounded / Insufficient Evidence'}
        </span>
      </div>

      {/* Grounding Warning Banner if Ungrounded */}
      {!isGrounded && (
        <div style={{
          padding: '12px 14px',
          borderRadius: '6px',
          backgroundColor: 'rgba(245, 158, 11, 0.12)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: '#fbbf24',
          fontSize: '12px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '8px'
        }}>
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>Grounding Notice:</strong> No verified runbooks or postmortems in the knowledge base supported an automated resolution. Normal human approval is blocked to prevent ungrounded operational changes.
          </div>
        </div>
      )}

      {/* Recommendation Summary */}
      <div style={{
        backgroundColor: isGrounded ? 'rgba(56, 189, 248, 0.08)' : 'rgba(255, 255, 255, 0.03)',
        border: isGrounded ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '16px 20px',
        marginBottom: '20px'
      }}>
        <h4 style={{ fontSize: '11px', color: isGrounded ? 'var(--brand-primary)' : 'var(--text-muted)', marginBottom: '6px' }}>
          HIGH-LEVEL RECOMMENDATION
        </h4>
        <p style={{ fontSize: '14px', fontWeight: '600', color: '#ffffff', lineHeight: '1.5' }}>
          {resolution.recommendation}
        </p>
      </div>

      {/* Actionable Steps */}
      {resolution.steps && resolution.steps.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <ListOrdered size={16} color="var(--text-secondary)" />
            <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>ACTIONABLE RECOVERY STEPS</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {resolution.steps.map((step, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  backgroundColor: 'var(--bg-dark)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  padding: '12px 14px',
                  fontSize: '13px',
                  color: 'var(--text-primary)'
                }}
              >
                <span className="code-mono" style={{ fontWeight: '700', color: 'var(--brand-primary)', flexShrink: 0 }}>
                  0{idx + 1}
                </span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Operational Risks */}
      {resolution.risks && resolution.risks.length > 0 && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          borderRadius: '8px',
          padding: '14px 16px',
          marginBottom: evidenceSources.length > 0 ? '20px' : '0px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <ShieldAlert size={16} color="#f87171" />
            <h4 style={{ fontSize: '12px', color: '#f87171' }}>IDENTIFIED OPERATIONAL RISKS</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {resolution.risks.map((risk, idx) => (
              <div key={idx} style={{ fontSize: '12px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: '#f87171' }}>⚠</span>
                <span>{risk}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Provenance (Rule 6) */}
      {evidenceSources.length > 0 && (
        <div style={{
          backgroundColor: 'var(--bg-dark)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          padding: '14px 16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <BookOpen size={16} color="var(--brand-primary)" />
            <h4 style={{ fontSize: '12px', color: 'var(--brand-primary)' }}>EVIDENCE PROVENANCE & RUNBOOK SOURCES</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {evidenceSources.map((ev, idx) => (
              <div key={idx} style={{
                fontSize: '12px',
                color: 'var(--text-secondary)',
                backgroundColor: 'var(--bg-surface)',
                padding: '8px 12px',
                borderRadius: '4px',
                borderLeft: '3px solid var(--brand-primary)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                    {ev.source || `Chunk ${ev.chunk_id}`}
                  </span>
                  <span className="code-mono" style={{ fontSize: '11px', color: 'var(--brand-primary)' }}>
                    [{ev.chunk_id}] {ev.score ? `Score: ${Math.round(ev.score * 100)}%` : ''}
                  </span>
                </div>
                {ev.snippet && (
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    "{ev.snippet}..."
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProposedResolution;

