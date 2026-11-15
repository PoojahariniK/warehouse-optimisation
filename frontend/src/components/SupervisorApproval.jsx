import React, { useState } from 'react';

export default function SupervisorApproval({ recommendations, onApprove, onReject, onReEvaluate, isReEvaluating, onResetDemo, isResetting, toast }) {
  const [actionInProgress, setActionInProgress] = useState(null);

  if (!recommendations) return <div className="state-container"><div className="spinner"></div>Loading supervisor approval queue...</div>;

  const pending = recommendations.filter(r => r.recommendationStatus === 'RECOMMENDED' && r.recommendedLocation && r.recommendedLocation !== 'NONE');
  const approved = recommendations.filter(r => r.recommendationStatus === 'APPROVED');
  const rejected = recommendations.filter(r => r.recommendationStatus === 'REJECTED');
  const noFeasible = recommendations.filter(r => r.recommendationStatus === 'NO_FEASIBLE_LOCATION' || !r.recommendedLocation || r.recommendedLocation === 'NONE');

  const handleApproveAction = async (id) => {
    setActionInProgress(id);
    try {
      await onApprove(id);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleRejectAction = async (id) => {
    setActionInProgress(id);
    try {
      await onReject(id);
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div>
      {/* Toast Notification */}
      {toast && (
        <div className={`toast-alert ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
          <span>{toast.message}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '1.5rem' }}>
        <div className="kpi-card" style={{ borderColor: 'rgba(56, 189, 248, 0.4)' }}>
          <span className="kpi-label">Pending Action</span>
          <span className="kpi-value" style={{ color: '#38bdf8' }}>{pending.length}</span>
          <span className="kpi-subtext">Awaiting supervisor decision</span>
        </div>
        <div className="kpi-card" style={{ borderColor: 'rgba(34, 197, 94, 0.4)' }}>
          <span className="kpi-label">Approved Relocations</span>
          <span className="kpi-value" style={{ color: '#4ade80' }}>{approved.length}</span>
          <span className="kpi-subtext">Slot updates confirmed in warehouse</span>
        </div>
        <div className="kpi-card" style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}>
          <span className="kpi-label">Rejected Proposals</span>
          <span className="kpi-value" style={{ color: '#f87171' }}>{rejected.length}</span>
          <span className="kpi-subtext">Kept at original bin location</span>
        </div>
        <div className="kpi-card" style={{ borderColor: 'rgba(245, 158, 11, 0.4)' }}>
          <span className="kpi-label">Constrained SKUs</span>
          <span className="kpi-value" style={{ color: '#fbbf24' }}>{noFeasible.length}</span>
          <span className="kpi-subtext">No eligible empty bin available</span>
        </div>
      </div>

      {/* Pending Approval Queue Card */}
      <div className="section-card">
        <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 className="section-title">8. Supervisor Approval Queue</h2>
            <p className="section-desc">
              Review and authorize candidate slot relocations proposed by the optimization engine. Approvals update the warehouse layout transactionally.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              className="btn btn-primary"
              onClick={onReEvaluate}
              disabled={isReEvaluating}
              style={{
                backgroundColor: '#0284c7',
                color: '#fff',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                border: 'none',
                cursor: isReEvaluating ? 'not-allowed' : 'pointer'
              }}
              title="Scan warehouse for available empty or vacated slots and match against eligible candidate SKUs"
            >
              {isReEvaluating ? '⏳ Scanning Empty Slots...' : '⚡ Re-evaluate Empty Slots'}
            </button>
            {onResetDemo && (
              <button
                className="btn"
                onClick={onResetDemo}
                disabled={isResetting}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.15)',
                  color: '#f87171',
                  border: '1px solid #ef4444',
                  padding: '0.5rem 0.95rem',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                  cursor: isResetting ? 'wait' : 'pointer',
                  transition: 'all 0.2s ease'
                }}
                title="Reset warehouse database and slot allocations back to initial baseline"
              >
                <span>{isResetting ? '⏳ Resetting...' : '↺ Reset to Baseline'}</span>
              </button>
            )}
          </div>
        </div>

        {pending.length === 0 ? (
          <div className="state-container" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
            <p style={{ color: '#4ade80', fontSize: '1.2rem', fontWeight: '600' }}>✅ All Active Slotting Recommendations Have Been Resolved</p>
            <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>There are currently no pending proposals awaiting review. Click below to scan warehouse bins for unslotted SKUs or reset to baseline.</p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '1.2rem', flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary"
                onClick={onReEvaluate}
                disabled={isReEvaluating}
                style={{
                  backgroundColor: '#0284c7',
                  color: '#fff',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '6px',
                  fontWeight: 600,
                  border: 'none',
                  cursor: isReEvaluating ? 'not-allowed' : 'pointer'
                }}
              >
                {isReEvaluating ? '⏳ Scanning Empty Slots...' : '⚡ Re-evaluate Empty Slots'}
              </button>
              {onResetDemo && (
                <button
                  className="btn"
                  onClick={onResetDemo}
                  disabled={isResetting}
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                    color: '#f87171',
                    border: '1px solid #ef4444',
                    padding: '0.6rem 1.2rem',
                    borderRadius: '6px',
                    fontWeight: 600,
                    cursor: isResetting ? 'wait' : 'pointer'
                  }}
                >
                  {isResetting ? '⏳ Resetting...' : '↺ Reset to Baseline'}
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rec ID</th>
                  <th>SKU</th>
                  <th>Product Name</th>
                  <th>Demand Class</th>
                  <th>Current Bin</th>
                  <th>Proposed Bin</th>
                  <th>Dist to Depot</th>
                  <th>Distance Saved</th>
                  <th>Optimization Rationale</th>
                  <th>Supervisor Decision</th>
                </tr>
              </thead>
              <tbody>
                {pending.map(r => (
                  <tr key={r.recommendationId}>
                    <td><strong>{r.recommendationId}</strong></td>
                    <td>{r.skuId}</td>
                    <td><strong>{r.productName}</strong></td>
                    <td>
                      <span className={`badge badge-${r.demandClass.toLowerCase()}`}>
                        {r.demandClass}
                      </span>
                    </td>
                    <td><span className="badge badge-occupied">{r.currentLocation}</span></td>
                    <td>
                      <div>
                        <span className="badge badge-empty">{r.recommendedLocation}</span>
                        {r.reason && r.reason.includes('Co-ordered with') && (
                          <div style={{ marginTop: '0.25rem' }}>
                            <span className="badge" style={{ backgroundColor: 'rgba(168,85,247,0.2)', color: '#c084fc', border: '1px solid #a855f7', fontSize: '0.65rem' }}>
                              Affinity Clustered
                            </span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td>{r.distance} units</td>
                    <td>
                      {r.distanceSaved && r.distanceSaved > 0 ? (
                        <strong style={{ color: '#4ade80' }}>+{r.distanceSaved} u</strong>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>0 u</span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#cbd5e1', maxWidth: '300px' }}>{r.reason}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          className="btn btn-approve"
                          disabled={actionInProgress === r.recommendationId || !r.recommendedLocation || r.recommendedLocation === 'NONE'}
                          onClick={() => handleApproveAction(r.recommendationId)}
                          title={(!r.recommendedLocation || r.recommendedLocation === 'NONE') ? 'Cannot approve: No feasible target bin assigned' : 'Approve slot relocation'}
                          style={{
                            padding: '0.4rem 0.8rem',
                            fontSize: '0.8rem',
                            minWidth: '75px',
                            opacity: (!r.recommendedLocation || r.recommendedLocation === 'NONE') ? 0.4 : 1,
                            cursor: (!r.recommendedLocation || r.recommendedLocation === 'NONE') ? 'not-allowed' : 'pointer'
                          }}
                        >
                          {actionInProgress === r.recommendationId ? '...' : '✓ Approve'}
                        </button>
                        <button
                          className="btn btn-reject"
                          disabled={actionInProgress === r.recommendationId}
                          onClick={() => handleRejectAction(r.recommendationId)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', minWidth: '70px' }}
                        >
                          {actionInProgress === r.recommendationId ? '...' : '✗ Reject'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Decision History (Audit Trail) */}
      {(approved.length > 0 || rejected.length > 0) && (
        <div className="section-card" style={{ marginTop: '1.5rem' }}>
          <div className="section-header">
            <div>
              <h2 className="section-title">📋 Decision History & Supervisor Audit Trail</h2>
              <p className="section-desc">Historical log of all approved and rejected slot change decisions.</p>
            </div>
          </div>

          <div className="table-responsive" style={{ maxHeight: '350px' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rec ID</th>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Current / Original Bin</th>
                  <th>Assigned Bin</th>
                  <th>Decision</th>
                  <th>Audit Note</th>
                </tr>
              </thead>
              <tbody>
                {[...approved, ...rejected].map(r => (
                  <tr key={r.recommendationId}>
                    <td><strong>{r.recommendationId}</strong></td>
                    <td>{r.skuId}</td>
                    <td>{r.productName}</td>
                    <td><span className="badge badge-occupied">{r.currentLocation}</span></td>
                    <td>
                      {r.recommendationStatus === 'APPROVED' ? (
                        <span className="badge badge-empty">{r.recommendedLocation}</span>
                      ) : (
                        <span className="badge badge-occupied">{r.currentLocation} (Retained)</span>
                      )}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: r.recommendationStatus === 'APPROVED'
                            ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: r.recommendationStatus === 'APPROVED' ? '#4ade80' : '#f87171',
                          border: `1px solid ${r.recommendationStatus === 'APPROVED' ? '#22c55e' : '#ef4444'}`
                        }}
                      >
                        {r.recommendationStatus}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{r.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
