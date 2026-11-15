import React, { useState } from 'react';

export default function PickPathOptimization({ routes }) {
  const [selectedOrderId, setSelectedOrderId] = useState('ORD001');
  const [filterWorse, setFilterWorse] = useState(false);

  if (!routes || routes.length === 0) {
    return <div className="state-container"><div className="spinner"></div>Loading routes...</div>;
  }

  const selectedRoute = routes.find(r => r.orderId === selectedOrderId) || routes[0];
  const worseCases = routes.filter(r => r.routeStatus === 'WORSE');
  const displayList = filterWorse ? worseCases : routes;

  // 4-Way Operational Matrix Averages
  const avgBaseline = (routes.reduce((s, r) => s + r.baselineDistance, 0) / routes.length).toFixed(1);
  const avgRouteOnly = (routes.reduce((s, r) => s + (r.routeOnlyDistance || r.optimizedDistance), 0) / routes.length).toFixed(1);
  const avgSlotOnly = (routes.reduce((s, r) => s + (r.slotOnlyDistance || r.baselineDistance), 0) / routes.length).toFixed(1);
  const avgDualOpt = (routes.reduce((s, r) => s + r.optimizedDistance, 0) / routes.length).toFixed(1);

  const roSavingsPct = (((avgBaseline - avgRouteOnly) / avgBaseline) * 100).toFixed(1);
  const soSavingsPct = (((avgBaseline - avgSlotOnly) / avgBaseline) * 100).toFixed(1);
  const dualSavingsPct = (((avgBaseline - avgDualOpt) / avgBaseline) * 100).toFixed(1);

  return (
    <div className="section-card">
      <div className="section-header">
        <div>
          <h2 className="section-title">6. Pick-Path Optimization & Routing Engine</h2>
          <p className="section-desc">2x2 Operational Matrix: Disentangling routing heuristic gains from slot relocation gains across 50 orders</p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            className="btn"
            onClick={() => setFilterWorse(!filterWorse)}
            style={{
              background: filterWorse ? 'rgba(239, 68, 68, 0.3)' : '#1e293b',
              color: filterWorse ? '#f87171' : '#94a3b8',
              border: '1px solid #ef4444'
            }}
          >
            ⚠️ {filterWorse ? `Showing Suboptimal Cases Only (${worseCases.length})` : `Show Suboptimal Edge Cases (${worseCases.length})`}
          </button>

          <select
            value={selectedOrderId}
            onChange={e => setSelectedOrderId(e.target.value)}
            style={{
              background: '#0f172a',
              border: '1px solid #38bdf8',
              color: '#f8fafc',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.9rem',
              fontWeight: '600'
            }}
          >
            {displayList.map(r => (
              <option key={r.orderId} value={r.orderId}>
                {r.orderId} - {r.routeStatus} ({r.pctDistanceReduction > 0 ? `-${r.pctDistanceReduction}%` : `+${Math.abs(r.pctDistanceReduction)}%`})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 2x2 Operational Comparison Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>1. Baseline (Old Layout + Naive)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#f8fafc', marginTop: '0.2rem' }}>{avgBaseline} <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>units</span></div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.3rem' }}>Original layout & FIFO route</div>
        </div>

        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', border: '1px solid #38bdf8' }}>
          <div style={{ fontSize: '0.75rem', color: '#38bdf8', textTransform: 'uppercase' }}>2. Route-Only (Old Layout + NN)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#38bdf8', marginTop: '0.2rem' }}>{avgRouteOnly} <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>units</span></div>
          <div style={{ fontSize: '0.8rem', color: '#4ade80', marginTop: '0.3rem' }}>-{roSavingsPct}% travel reduction</div>
        </div>

        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', border: '1px solid #a855f7' }}>
          <div style={{ fontSize: '0.75rem', color: '#a855f7', textTransform: 'uppercase' }}>3. Slot-Only (New Layout + Naive)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#c084fc', marginTop: '0.2rem' }}>{avgSlotOnly} <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>units</span></div>
          <div style={{ fontSize: '0.8rem', color: '#c084fc', marginTop: '0.3rem' }}>-{soSavingsPct}% travel reduction</div>
        </div>

        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', border: '1px solid #22c55e' }}>
          <div style={{ fontSize: '0.75rem', color: '#4ade80', textTransform: 'uppercase' }}>4. Dual Opt (New Layout + NN)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#4ade80', marginTop: '0.2rem' }}>{avgDualOpt} <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>units</span></div>
          <div style={{ fontSize: '0.8rem', color: '#4ade80', marginTop: '0.3rem' }}>-{dualSavingsPct}% net synergy saved</div>
        </div>
      </div>

      {filterWorse && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem', color: '#fca5a5', fontSize: '0.88rem' }}>
          <strong>⚠️ AI-Resistant Heuristic Analysis: Why is Nearest Neighbor worse on {worseCases.length} orders?</strong>
          <p style={{ marginTop: '0.4rem', color: '#f87171' }}>
            Nearest Neighbor is a greedy heuristic that always visits the nearest unvisited SKU. In certain warehouse layouts with scattered picks across parallel aisles, a greedy early pick can trap the picker at the far corner of the warehouse, forcing an expensive empty return trip back across multiple aisles. This proves why claims of heuristic "optimality" are mathematically unsound without full 2-opt/TSP solving.
          </p>
        </div>
      )}

      {selectedRoute && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Baseline Sequential Route (Old Layout)</span>
            <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#f8fafc', marginTop: '0.25rem' }}>
              {selectedRoute.baselineDistance} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>units</span>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.5rem' }}>
              Est. Time: <strong>{selectedRoute.baselineTimeSec}s</strong> (Walk: 1.2 u/s + 15s/pick)
            </div>
            <div className="route-sequence-box" style={{ borderColor: '#64748b', color: '#cbd5e1' }}>
              {selectedRoute.baselineRouteSequence}
            </div>
          </div>

          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: `1px solid ${selectedRoute.routeStatus === 'WORSE' ? '#ef4444' : '#38bdf8'}` }}>
            <span style={{ fontSize: '0.75rem', color: selectedRoute.routeStatus === 'WORSE' ? '#f87171' : '#38bdf8', textTransform: 'uppercase', fontWeight: '600' }}>
              Dual Optimization (New Layout + NN)
            </span>
            <div style={{ fontSize: '1.75rem', fontWeight: '700', color: selectedRoute.routeStatus === 'WORSE' ? '#f87171' : '#38bdf8', marginTop: '0.25rem' }}>
              {selectedRoute.optimizedDistance} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>units</span>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.5rem' }}>
              Est. Time: <strong>{selectedRoute.optimizedTimeSec}s</strong> ({selectedRoute.timeSavedSec > 0 ? `Saved: ${selectedRoute.timeSavedSec}s` : `Added: ${Math.abs(selectedRoute.timeSavedSec)}s`})
            </div>
            <div className="route-sequence-box" style={{ borderColor: selectedRoute.routeStatus === 'WORSE' ? '#ef4444' : '#38bdf8' }}>
              {selectedRoute.optimizedRouteSequence}
            </div>
          </div>

          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Operational Variance & Details</span>
            <div style={{ fontSize: '1.75rem', fontWeight: '700', color: selectedRoute.distanceSaved >= 0 ? '#4ade80' : '#f87171', marginTop: '0.25rem' }}>
              {selectedRoute.pctDistanceReduction}%
            </div>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.5rem' }}>
              Distance Saved: <strong>{selectedRoute.distanceSaved > 0 ? `+${selectedRoute.distanceSaved}` : selectedRoute.distanceSaved} units</strong>
            </div>
            <div style={{ fontSize: '0.82rem', color: '#cbd5e1', marginTop: '0.5rem', lineHeight: '1.4' }}>
              Route-Only: <strong>{selectedRoute.routeOnlyDistance || selectedRoute.optimizedDistance} u</strong> · Slot-Only: <strong>{selectedRoute.slotOnlyDistance || selectedRoute.baselineDistance} u</strong>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.82rem', color: selectedRoute.routeStatus === 'WORSE' ? '#fca5a5' : '#94a3b8' }}>
              {selectedRoute.notes}
            </div>
          </div>
        </div>
      )}

      <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#f8fafc' }}>Batch Order Pick-Path Comparison Table (50 Orders)</h3>
      <div className="table-responsive" style={{ maxHeight: '350px' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>1. Baseline Old</th>
              <th>2. Route-Only NN</th>
              <th>3. Slot-Only New</th>
              <th>4. Dual Opt</th>
              <th>Dist Saved</th>
              <th>Reduction %</th>
              <th>Base Time</th>
              <th>Dual Time</th>
              <th>Result Status</th>
            </tr>
          </thead>
          <tbody>
            {displayList.map(r => (
              <tr
                key={r.orderId}
                onClick={() => setSelectedOrderId(r.orderId)}
                style={{ cursor: 'pointer', background: r.orderId === selectedOrderId ? 'rgba(56, 189, 248, 0.08)' : 'transparent' }}
              >
                <td><strong>{r.orderId}</strong></td>
                <td>{r.baselineDistance}</td>
                <td style={{ color: '#38bdf8' }}>{r.routeOnlyDistance || r.optimizedDistance}</td>
                <td style={{ color: '#c084fc' }}>{r.slotOnlyDistance || r.baselineDistance}</td>
                <td style={{ color: '#4ade80', fontWeight: 'bold' }}>{r.optimizedDistance}</td>
                <td style={{ color: r.distanceSaved > 0 ? '#4ade80' : r.distanceSaved < 0 ? '#f87171' : '#94a3b8', fontWeight: '600' }}>
                  {r.distanceSaved > 0 ? `+${r.distanceSaved}` : r.distanceSaved}
                </td>
                <td>
                  <span className={`badge ${r.pctDistanceReduction > 0 ? 'badge-improved' : r.pctDistanceReduction < 0 ? 'badge-worse' : ''}`}>
                    {r.pctDistanceReduction}%
                  </span>
                </td>
                <td>{r.baselineTimeSec}s</td>
                <td>{r.optimizedTimeSec}s</td>
                <td>
                  <span className={`badge ${r.routeStatus === 'IMPROVED' ? 'badge-improved' : r.routeStatus === 'WORSE' ? 'badge-worse' : ''}`}>
                    {r.routeStatus}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
