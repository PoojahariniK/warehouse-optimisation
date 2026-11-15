import React from 'react';

export default function WarehouseOverview({ analytics, routes, recommendations, replenishment }) {
  if (!analytics) return <div className="state-container"><div className="spinner"></div>Loading overview &amp; performance analytics...</div>;

  const improvedRoutes = routes ? routes.filter(r => r.routeStatus === 'IMPROVED').length : 0;
  const worseRoutes = routes ? routes.filter(r => r.routeStatus === 'WORSE').length : 0;
  const identicalRoutes = routes ? routes.filter(r => r.routeStatus === 'IDENTICAL').length : 0;
  const totalRoutes = routes ? routes.length : 0;

  const avgBaseline = routes && routes.length > 0
    ? (routes.reduce((s, r) => s + r.baselineDistance, 0) / routes.length).toFixed(2)
    : 0;
  const avgOptimized = routes && routes.length > 0
    ? (routes.reduce((s, r) => s + r.optimizedDistance, 0) / routes.length).toFixed(2)
    : 0;

  const avgBaselineTime = routes && routes.length > 0
    ? (routes.reduce((s, r) => s + r.baselineTimeSec, 0) / routes.length).toFixed(1)
    : 0;
  const avgOptimizedTime = routes && routes.length > 0
    ? (routes.reduce((s, r) => s + r.optimizedTimeSec, 0) / routes.length).toFixed(1)
    : 0;

  const pct = (val, max) => max > 0 ? Math.round((val / max) * 100) : 0;
  const occupancyPct = Math.round((analytics.occupiedLocations / analytics.totalLocations) * 100);
  const emptyPct = Math.round((analytics.emptyLocations / analytics.totalLocations) * 100);

  return (
    <div>
      {/* Executive KPI Section Heading */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>📈 Warehouse Key Performance Indicators (KPIs)</span>
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: '0.2rem 0 0 0' }}>
            Executive operational benchmarks, inventory segmentation, and routing performance
          </p>
        </div>
      </div>

      {/* Executive KPI Summary Grid */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="kpi-card">
          <span className="kpi-label">Total SKUs</span>
          <span className="kpi-value">{analytics.totalProducts}</span>
          <span className="kpi-subtext">Active Master Catalog</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Storage Locations</span>
          <span className="kpi-value">{analytics.totalLocations}</span>
          <span className="kpi-subtext">
            {analytics.occupiedLocations} Occupied · <strong style={{ color: '#4ade80' }}>{analytics.emptyLocations} Empty</strong>
          </span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Demand Segments</span>
          <span className="kpi-value">{analytics.fastProducts} / {analytics.mediumProducts} / {analytics.slowProducts}</span>
          <span className="kpi-subtext">Fast (≥10) · Med (4-9) · Slow (&lt;4)</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Mean Distance Reduction</span>
          <span className="kpi-value" style={{ color: '#38bdf8' }}>
            {analytics.averageDistanceReductionPct}%
          </span>
          <span className="kpi-subtext positive">Total Saved: {analytics.totalDistanceSaved} units</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Suboptimal Edge Cases</span>
          <span className="kpi-value" style={{ color: '#f87171' }}>{worseRoutes}</span>
          <span className="kpi-subtext warning">NN heuristic worse than baseline</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Replenishment Alerts</span>
          <span className="kpi-value" style={{ color: analytics.replenishmentAlertsCount > 0 ? '#f87171' : '#4ade80' }}>
            {analytics.replenishmentAlertsCount}
          </span>
          <span className="kpi-subtext warning">Stock below minimum threshold</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Supervisor Approvals</span>
          <span className="kpi-value">
            {analytics.approvedSlotsCount} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>approved</span>
          </span>
          <span className="kpi-subtext">
            {analytics.recommendedSlotsCount} candidate slots pending review
          </span>
        </div>
      </div>

      {/* Performance Comparison: Baseline vs Optimized Travel Distance */}
      <div className="section-card">
        <div className="section-header">
          <div>
            <h2 className="section-title">📊 Travel Distance &amp; Picking Time Performance</h2>
            <p className="section-desc">Comparison of baseline sequential travel distance vs Nearest Neighbor heuristic path across all order batches.</p>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: '600' }}>Baseline (Sequential Route)</span>
              <span style={{ color: '#f8fafc', fontWeight: '700' }}>{avgBaseline} units</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '20px' }}>
              <div className="progress-bar-fill" style={{ width: '100%', backgroundColor: '#64748b' }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.4rem' }}>
              Avg Time: <strong>{avgBaselineTime}s</strong> · Walk Speed: 1.2 u/s · Pick: 15s/item
            </div>
          </div>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#38bdf8', fontSize: '0.85rem', fontWeight: '600' }}>Optimized (Nearest Neighbor Route)</span>
              <span style={{ color: '#38bdf8', fontWeight: '700' }}>{avgOptimized} units</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '20px' }}>
              <div className="progress-bar-fill" style={{ width: `${avgBaseline > 0 ? Math.round((avgOptimized / avgBaseline) * 100) : 100}%`, backgroundColor: '#38bdf8' }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginTop: '0.4rem' }}>
              Avg Time: <strong>{avgOptimizedTime}s</strong> · Reduction: <strong>{analytics.averageDistanceReductionPct}%</strong> (Saved: {(avgBaselineTime - avgOptimizedTime).toFixed(1)}s/pick cycle)
            </div>
          </div>
        </div>
      </div>

      {/* Dual Metrics: Warehouse Physical Occupancy & Route Outcome Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Occupancy Card */}
        <div className="section-card" style={{ margin: 0 }}>
          <div className="section-header">
            <div>
              <h2 className="section-title">Warehouse Facility Occupancy</h2>
              <p className="section-desc">Physical slot utilization across 40 grid locations</p>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
            <span>Occupied Slots: <strong>{analytics.occupiedLocations} / {analytics.totalLocations}</strong></span>
            <span style={{ color: '#818cf8', fontWeight: 'bold' }}>{occupancyPct}%</span>
          </div>
          <div className="progress-bar-bg" style={{ height: '14px' }}>
            <div className="progress-bar-fill" style={{ width: `${occupancyPct}%`, backgroundColor: '#6366f1' }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.25rem', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
            <span>Available Empty Bins:</span>
            <span style={{ color: '#4ade80', fontWeight: 'bold' }}>{analytics.emptyLocations} Empty Slots ({emptyPct}%)</span>
          </div>
          <div className="progress-bar-bg" style={{ height: '14px' }}>
            <div className="progress-bar-fill" style={{ width: `${emptyPct}%`, backgroundColor: '#22c55e' }}></div>
          </div>
        </div>

        {/* Route Outcome Distribution Card */}
        <div className="section-card" style={{ margin: 0 }}>
          <div className="section-header">
            <div>
              <h2 className="section-title">Route Optimization Outcomes</h2>
              <p className="section-desc">{totalRoutes} total order batches evaluated</p>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '0.5rem' }}>
            <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(34, 197, 94, 0.3)', textAlign: 'center' }}>
              <div style={{ color: '#4ade80', fontSize: '0.75rem', fontWeight: 600 }}>IMPROVED</div>
              <div style={{ color: '#4ade80', fontSize: '1.5rem', fontWeight: 700, margin: '0.2rem 0' }}>{improvedRoutes}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{pct(improvedRoutes, totalRoutes)}% of orders</div>
            </div>
            <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)', textAlign: 'center' }}>
              <div style={{ color: '#f87171', fontSize: '0.75rem', fontWeight: 600 }}>SUBOPTIMAL</div>
              <div style={{ color: '#f87171', fontSize: '1.5rem', fontWeight: 700, margin: '0.2rem 0' }}>{worseRoutes}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{pct(worseRoutes, totalRoutes)}% edge cases</div>
            </div>
            <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', border: '1px solid #334155', textAlign: 'center' }}>
              <div style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600 }}>IDENTICAL</div>
              <div style={{ color: '#cbd5e1', fontSize: '1.5rem', fontWeight: 700, margin: '0.2rem 0' }}>{identicalRoutes}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{pct(identicalRoutes, totalRoutes)}% same</div>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Strategy & Heuristic Auditing */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <div className="section-card" style={{ margin: 0 }}>
          <div className="section-header">
            <div>
              <h2 className="section-title" style={{ color: '#38bdf8' }}>🎯 Optimization Objectives</h2>
              <p className="section-desc">Core algorithmic design and operational priorities</p>
            </div>
          </div>
          <ul style={{ listStyleType: 'disc', paddingLeft: '1.2rem', color: '#94a3b8', fontSize: '0.85rem', lineHeight: '1.8' }}>
            <li><strong>Slotting Optimization:</strong> Position fast-moving items closer to dispatch point while strictly enforcing storage capacity and category compatibility.</li>
            <li><strong>Pick-Path Routing:</strong> Reduce picker travel distance and picking time using Nearest Neighbor heuristic across historical order batches.</li>
            <li><strong>Supervisor Governance:</strong> Retain strict human-in-the-loop approvals before updating physical bin allocations.</li>
            <li><strong>Live Capacity Guard:</strong> Enforce physical shelf limits during restocking with overflow prevention.</li>
          </ul>
        </div>

        <div className="section-card" style={{ margin: 0, borderColor: 'rgba(245, 158, 11, 0.3)' }}>
          <div className="section-header">
            <div>
              <h2 className="section-title" style={{ color: '#fbbf24' }}>⚠️ Heuristic Trade-offs &amp; Honest Auditing</h2>
              <p className="section-desc">Transparent limitations of heuristic models</p>
            </div>
          </div>
          <ul style={{ listStyleType: 'disc', paddingLeft: '1.2rem', color: '#94a3b8', fontSize: '0.85rem', lineHeight: '1.8' }}>
            <li><strong>Euclidean vs Graph Traversal:</strong> Straight-line metrics approximate walking paths; physical turns and racking traversal require graph shortest paths.</li>
            <li><strong>Greedy Suboptimal Edge Cases:</strong> In {worseRoutes} of {totalRoutes} orders ({pct(worseRoutes, totalRoutes)}%), Nearest Neighbor greedily picks early nearby items that trap the picker far from remaining picks.</li>
            <li><strong>Fixed Slot Availability:</strong> With only 10 empty locations initially available, candidate relocations are limited to available empty bins.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
