import React from 'react';

export default function PerformanceAnalytics({ analytics, routes, recommendations, replenishment }) {
  if (!analytics) return <div className="state-container"><div className="spinner"></div>Loading performance analytics...</div>;

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

  const recCount = recommendations ? recommendations.filter(r => r.recommendationStatus === 'RECOMMENDED').length : 0;
  const appCount = recommendations ? recommendations.filter(r => r.recommendationStatus === 'APPROVED').length : 0;
  const rejCount = recommendations ? recommendations.filter(r => r.recommendationStatus === 'REJECTED').length : 0;
  const noFeasCount = recommendations ? recommendations.filter(r => r.recommendationStatus === 'NO_FEASIBLE_LOCATION').length : 0;

  const replenCount = replenishment ? replenishment.length : 0;

  // Helper for progress bar width percentage (safe)
  const pct = (val, max) => max > 0 ? Math.round((val / max) * 100) : 0;

  return (
    <div>
      {/* KPI Summary */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="kpi-card">
          <span className="kpi-label">Avg Baseline Distance</span>
          <span className="kpi-value">{avgBaseline}</span>
          <span className="kpi-subtext">Euclidean units (sequential)</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Avg Optimized Distance</span>
          <span className="kpi-value" style={{ color: '#38bdf8' }}>{avgOptimized}</span>
          <span className="kpi-subtext">Euclidean units (Nearest Neighbor)</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Mean Reduction</span>
          <span className="kpi-value" style={{ color: '#4ade80' }}>{analytics.averageDistanceReductionPct}%</span>
          <span className="kpi-subtext positive">Total Saved: {analytics.totalDistanceSaved} units</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Avg Time Saved</span>
          <span className="kpi-value" style={{ color: '#38bdf8' }}>{(avgBaselineTime - avgOptimizedTime).toFixed(1)}s</span>
          <span className="kpi-subtext">Per order pick cycle</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Suboptimal Cases</span>
          <span className="kpi-value" style={{ color: '#f87171' }}>{worseRoutes}</span>
          <span className="kpi-subtext warning">NN heuristic underperformed baseline</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Replenishment Alerts</span>
          <span className="kpi-value" style={{ color: replenCount > 0 ? '#f87171' : '#4ade80' }}>{replenCount}</span>
          <span className="kpi-subtext warning">Stock below minimum threshold</span>
        </div>
      </div>

      {/* Distance Comparison Visual */}
      <div className="section-card">
        <div className="section-header">
          <div>
            <h2 className="section-title">9. Before / After Distance Comparison</h2>
            <p className="section-desc">
              Visual comparison of baseline (sequential) vs optimized (Nearest Neighbor) pick path distances.
              Uses Euclidean distance — not actual aisle-constrained walking distance.
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          {/* Baseline Bar */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: '600' }}>Baseline (Sequential)</span>
              <span style={{ color: '#f8fafc', fontWeight: '700' }}>{avgBaseline} units</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '20px' }}>
              <div
                className="progress-bar-fill"
                style={{
                  width: '100%',
                  backgroundColor: '#64748b'
                }}
              ></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.4rem' }}>
              Avg Time: {avgBaselineTime}s · Walk Speed: 1.2 u/s · Pick: 15s/item
            </div>
          </div>

          {/* Optimized Bar */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#38bdf8', fontSize: '0.85rem', fontWeight: '600' }}>Optimized (Nearest Neighbor)</span>
              <span style={{ color: '#38bdf8', fontWeight: '700' }}>{avgOptimized} units</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '20px' }}>
              <div
                className="progress-bar-fill"
                style={{
                  width: `${avgBaseline > 0 ? Math.round((avgOptimized / avgBaseline) * 100) : 100}%`,
                  backgroundColor: '#38bdf8'
                }}
              ></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.4rem' }}>
              Avg Time: {avgOptimizedTime}s · Reduction: {analytics.averageDistanceReductionPct}%
            </div>
          </div>
        </div>
      </div>

      {/* Route Outcome Distribution */}
      <div className="section-card">
        <div className="section-header">
          <div>
            <h2 className="section-title">Route Outcome Distribution</h2>
            <p className="section-desc">{totalRoutes} orders evaluated — honest reporting of heuristic performance</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(34, 197, 94, 0.3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#4ade80', fontWeight: '600' }}>IMPROVED</span>
              <span style={{ color: '#4ade80', fontSize: '1.5rem', fontWeight: '700' }}>{improvedRoutes}</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '8px', marginTop: '0.75rem' }}>
              <div className="progress-bar-fill" style={{ width: `${pct(improvedRoutes, totalRoutes)}%`, backgroundColor: '#22c55e' }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.4rem' }}>{pct(improvedRoutes, totalRoutes)}% of orders</div>
          </div>

          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#f87171', fontWeight: '600' }}>WORSE (Suboptimal)</span>
              <span style={{ color: '#f87171', fontSize: '1.5rem', fontWeight: '700' }}>{worseRoutes}</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '8px', marginTop: '0.75rem' }}>
              <div className="progress-bar-fill" style={{ width: `${pct(worseRoutes, totalRoutes)}%`, backgroundColor: '#ef4444' }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.4rem' }}>{pct(worseRoutes, totalRoutes)}% of orders — NN heuristic worse</div>
          </div>

          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#94a3b8', fontWeight: '600' }}>IDENTICAL</span>
              <span style={{ color: '#94a3b8', fontSize: '1.5rem', fontWeight: '700' }}>{identicalRoutes}</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '8px', marginTop: '0.75rem' }}>
              <div className="progress-bar-fill" style={{ width: `${pct(identicalRoutes, totalRoutes)}%`, backgroundColor: '#64748b' }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.4rem' }}>{pct(identicalRoutes, totalRoutes)}% of orders</div>
          </div>
        </div>
      </div>

      {/* Demand Distribution */}
      <div className="section-card">
        <div className="section-header">
          <div>
            <h2 className="section-title">Demand Distribution Breakdown</h2>
            <p className="section-desc">SKU demand segmentation: Fast (≥10 orders), Medium (4-9), Slow (&lt;4)</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span className="badge badge-fast">FAST MOVERS</span>
              <span style={{ fontWeight: '700', color: '#f87171' }}>{analytics.fastProducts}</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '12px' }}>
              <div className="progress-bar-fill" style={{ width: `${pct(analytics.fastProducts, analytics.totalProducts)}%`, backgroundColor: '#ef4444' }}></div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span className="badge badge-medium">MEDIUM MOVERS</span>
              <span style={{ fontWeight: '700', color: '#fbbf24' }}>{analytics.mediumProducts}</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '12px' }}>
              <div className="progress-bar-fill" style={{ width: `${pct(analytics.mediumProducts, analytics.totalProducts)}%`, backgroundColor: '#f59e0b' }}></div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span className="badge badge-slow">SLOW MOVERS</span>
              <span style={{ fontWeight: '700', color: '#38bdf8' }}>{analytics.slowProducts}</span>
            </div>
            <div className="progress-bar-bg" style={{ height: '12px' }}>
              <div className="progress-bar-fill" style={{ width: `${pct(analytics.slowProducts, analytics.totalProducts)}%`, backgroundColor: '#38bdf8' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Slot Recommendation Summary */}
      <div className="section-card">
        <div className="section-header">
          <div>
            <h2 className="section-title">Slot Recommendation Summary</h2>
            <p className="section-desc">Distribution of recommendation outcomes across 30 products and 10 empty locations</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
          {[
            { label: 'Recommended', count: recCount, color: '#38bdf8' },
            { label: 'Approved', count: appCount, color: '#4ade80' },
            { label: 'Rejected', count: rejCount, color: '#f87171' },
            { label: 'No Feasible Location', count: noFeasCount, color: '#fbbf24' }
          ].map(item => (
            <div key={item.label} style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #334155' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: '700', color: item.color }}>{item.count}</div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>{item.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Methodology Disclaimer */}
      <div className="section-card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)' }}>
        <div className="section-header">
          <div>
            <h2 className="section-title" style={{ color: '#fbbf24' }}>⚠️ Methodology Disclaimer</h2>
          </div>
        </div>
        <ul style={{ listStyleType: 'disc', paddingLeft: '1.2rem', color: '#94a3b8', fontSize: '0.85rem', lineHeight: '1.8' }}>
          <li><strong>Euclidean Distance Model:</strong> All distances are straight-line Euclidean approximations and do not represent actual aisle-constrained walking paths in a physical warehouse.</li>
          <li><strong>Nearest Neighbor Heuristic:</strong> The NN algorithm is a greedy heuristic and does <em>not</em> guarantee an optimal tour. It can produce routes longer than the baseline when pick locations are clustered or when the greedy choice leads to backtracking.</li>
          <li><strong>Suboptimal Cases ({worseRoutes} of {totalRoutes}):</strong> These are honestly reported. The NN heuristic underperformed sequential picking for {pct(worseRoutes, totalRoutes)}% of orders, typically on orders where the original sequence happened to visit nearby locations efficiently.</li>
          <li><strong>Slot Recommendations:</strong> Only 10 empty locations exist among 40 total slots. Recommendations move products <em>farther</em> from dispatch when the only available slots are in distant aisles (D07, D08, E01–E08).</li>
          <li><strong>Walking Speed &amp; Pick Time:</strong> Configurable parameters (default 1.2 units/sec, 15 sec/pick). Real-world times vary with warehouse topology, equipment, and picker experience.</li>
        </ul>
      </div>
    </div>
  );
}

