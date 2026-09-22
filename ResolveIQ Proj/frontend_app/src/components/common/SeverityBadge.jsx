import React from 'react';
import { AlertTriangle, AlertOctagon, Info, ShieldAlert } from 'lucide-react';

export function SeverityBadge({ severity }) {
  const sev = (severity || 'LOW').toUpperCase();

  if (sev === 'CRITICAL' || sev === 'SEV-1') {
    return (
      <span className="badge badge-sev-critical">
        <AlertOctagon size={13} />
        CRITICAL
      </span>
    );
  }

  if (sev === 'HIGH' || sev === 'SEV-2') {
    return (
      <span className="badge badge-sev-high">
        <AlertTriangle size={13} />
        HIGH
      </span>
    );
  }

  if (sev === 'MEDIUM' || sev === 'SEV-3') {
    return (
      <span className="badge badge-sev-medium">
        <ShieldAlert size={13} />
        MEDIUM
      </span>
    );
  }

  return (
    <span className="badge badge-sev-low">
      <Info size={13} />
      LOW
    </span>
  );
}

export default SeverityBadge;
