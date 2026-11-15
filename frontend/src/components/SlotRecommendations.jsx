import React, { useState } from 'react';

export default function SlotRecommendations({ recommendations, onResetDemo, isResetting }) {
  const [hideInfeasible, setHideInfeasible] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');

  if (!recommendations) return <div className="state-container"><div className="spinner"></div>Loading recommendations...</div>;

  const recommendedCount = recommendations.filter(r => r.recommendationStatus === 'RECOMMENDED').length;
  const noLocCount = recommendations.filter(r => r.recommendationStatus === 'NO_FEASIBLE_LOCATION').length;
  const approvedCount = recommendations.filter(r => r.recommendationStatus === 'APPROVED').length;
  const rejectedCount = recommendations.filter(r => r.recommendationStatus === 'REJECTED').length;

  let filtered = recommendations;
  if (statusFilter !== 'ALL') {
    filtered = filtered.filter(r => r.recommendationStatus === statusFilter);
  } else if (hideInfeasible) {
    filtered = filtered.filter(r => r.recommendationStatus !== 'NO_FEASIBLE_LOCATION');
  }

  return (
    <div className="section-card">
      <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 className="section-title">5. Storage Slotting Engine — Evaluated Audit Log</h2>
          <p className="section-desc">
            Read-only optimization audit log. Evaluates all 30 SKUs against warehouse constraints (capacity, category, hazard class, and dispatch proximity).
          </p>
        </div>
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
              padding: '0.45rem 0.95rem',
              borderRadius: '6px',
              fontWeight: '600',
              fontSize: '0.85rem',
              cursor: isResetting ? 'wait' : 'pointer'
            }}
            title="Reset warehouse database and slot allocations back to initial baseline"
          >
            <span>{isResetting ? '⏳ Resetting...' : '↺ Reset to Baseline'}</span>
          </button>
        )}
      </div>

      {/* Controls: Filter Toggle and Status Filters */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.2rem', paddingBottom: '0.8rem', borderBottom: '1px solid #1e293b' }}>
        <label style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.6rem',
          cursor: 'pointer',
          background: hideInfeasible ? 'rgba(56, 189, 248, 0.12)' : '#1e293b',
          border: `1px solid ${hideInfeasible ? '#38bdf8' : '#334155'}`,
          padding: '0.45rem 0.9rem',
          borderRadius: '6px',
          fontSize: '0.85rem',
          color: hideInfeasible ? '#38bdf8' : '#94a3b8',
          fontWeight: '500',
          userSelect: 'none'
        }}>
          <input
            type="checkbox"
            checked={hideInfeasible}
            onChange={e => {
              setHideInfeasible(e.target.checked);
              if (statusFilter === 'NO_FEASIBLE_LOCATION' && e.target.checked) {
                setStatusFilter('ALL');
              }
            }}
            style={{ width: '16px', height: '16px', accentColor: '#38bdf8', cursor: 'pointer' }}
          />
          <span>Hide Infeasible Slots ({noLocCount} rows) — Show Feasible Candidates Only</span>
        </label>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {['ALL', 'RECOMMENDED', 'NO_FEASIBLE_LOCATION', 'APPROVED', 'REJECTED'].map(s => (
            <button
              key={s}
              className="btn"
              onClick={() => {
                setStatusFilter(s);
                if (s === 'NO_FEASIBLE_LOCATION') {
                  setHideInfeasible(false);
                }
              }}
              style={{
                background: statusFilter === s ? '#38bdf8' : '#1e293b',
                color: statusFilter === s ? '#0f172a' : '#f8fafc',
                border: '1px solid #334155',
                fontSize: '0.8rem',
                padding: '0.35rem 0.75rem'
              }}
            >
              {s.replace(/_/g, ' ')} ({recommendations.filter(r => s === 'ALL' || r.recommendationStatus === s).length})
            </button>
          ))}
        </div>
      </div>

      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th>Rec ID</th>
              <th>SKU</th>
              <th>Product</th>
              <th>Class</th>
              <th>Current Bin</th>
              <th>Candidate Bin</th>
              <th>Dist to Depot</th>
              <th>Distance Saved</th>
              <th>Status</th>
              <th>Explainable Audit Reason</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(r => (
              <tr key={r.recommendationId}>
                <td><strong>{r.recommendationId}</strong></td>
                <td>{r.skuId}</td>
                <td>{r.productName}</td>
                <td><span className={`badge badge-${r.demandClass.toLowerCase()}`}>{r.demandClass}</span></td>
                <td><span className="badge badge-occupied">{r.currentLocation}</span></td>
                <td>
                  {r.recommendedLocation !== 'NONE' ? (
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
                  ) : (
                    <span style={{ color: '#94a3b8' }}>—</span>
                  )}
                </td>
                <td>{r.distance > 0 ? `${r.distance} units` : '—'}</td>
                <td>
                  {r.distanceSaved && r.distanceSaved > 0 ? (
                    <strong style={{ color: '#4ade80' }}>+{r.distanceSaved} u</strong>
                  ) : (
                    <span style={{ color: '#94a3b8' }}>0 u</span>
                  )}
                </td>
                <td>
                  <span className="badge" style={{
                    backgroundColor: r.recommendationStatus === 'APPROVED' ? 'rgba(34,197,94,0.2)' :
                                     r.recommendationStatus === 'REJECTED' ? 'rgba(239,68,68,0.2)' :
                                     r.recommendationStatus === 'RECOMMENDED' ? 'rgba(56,189,248,0.2)' : 'rgba(245,158,11,0.2)',
                    color: r.recommendationStatus === 'APPROVED' ? '#4ade80' :
                           r.recommendationStatus === 'REJECTED' ? '#f87171' :
                           r.recommendationStatus === 'RECOMMENDED' ? '#38bdf8' : '#fbbf24',
                    border: `1px solid ${r.recommendationStatus === 'APPROVED' ? '#22c55e' : r.recommendationStatus === 'REJECTED' ? '#ef4444' : r.recommendationStatus === 'RECOMMENDED' ? '#38bdf8' : '#f59e0b'}`
                  }}>
                    {r.recommendationStatus}
                  </span>
                </td>
                <td style={{ fontSize: '0.8rem', color: '#cbd5e1', maxWidth: '340px' }}>{r.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
