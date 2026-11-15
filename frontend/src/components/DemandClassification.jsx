import React, { useState } from 'react';

export default function DemandClassification({ demand, affinityPairs }) {
  const [filterClass, setFilterClass] = useState('ALL');
  const [affinityFilter, setAffinityFilter] = useState('TOP10');

  if (!demand) return <div className="state-container"><div className="spinner"></div>Loading demand data...</div>;

  const fastCount = demand.filter(d => d.demandClass === 'Fast').length;
  const mediumCount = demand.filter(d => d.demandClass === 'Medium').length;
  const slowCount = demand.filter(d => d.demandClass === 'Slow').length;

  const filtered = filterClass === 'ALL' ? demand : demand.filter(d => d.demandClass === filterClass);
  const pairs = affinityPairs || [];
  const displayedPairs = affinityFilter === 'TOP5' ? pairs.slice(0, 5)
                       : affinityFilter === 'TOP10' ? pairs.slice(0, 10)
                       : pairs;

  return (
    <div>
      <div className="section-card">
        <div className="section-header">
          <div>
            <h2 className="section-title">4. SKU Demand Classification ({demand.length} Items)</h2>
            <p className="section-desc">Order line frequency, pick volume, and volatility profiling based on historical orders</p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className={`btn ${filterClass === 'ALL' ? 'btn-approve' : ''}`}
              onClick={() => setFilterClass('ALL')}
              style={{ background: filterClass === 'ALL' ? '#38bdf8' : '#1e293b', color: filterClass === 'ALL' ? '#0f172a' : '#f8fafc' }}
            >
              All ({demand.length})
            </button>
            <button
              className="btn"
              onClick={() => setFilterClass('Fast')}
              style={{ background: filterClass === 'Fast' ? 'rgba(239, 68, 68, 0.4)' : '#1e293b', color: '#f87171', border: '1px solid rgba(239,68,68,0.3)' }}
            >
              Fast (≥10): {fastCount}
            </button>
            <button
              className="btn"
              onClick={() => setFilterClass('Medium')}
              style={{ background: filterClass === 'Medium' ? 'rgba(245, 158, 11, 0.4)' : '#1e293b', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.3)' }}
            >
              Medium (4-9): {mediumCount}
            </button>
            <button
              className="btn"
              onClick={() => setFilterClass('Slow')}
              style={{ background: filterClass === 'Slow' ? 'rgba(56, 189, 248, 0.4)' : '#1e293b', color: '#38bdf8', border: '1px solid rgba(56,189,248,0.3)' }}
            >
              Slow (&lt;4): {slowCount}
            </button>
          </div>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>SKU ID</th>
                <th>Product Name</th>
                <th>Category</th>
                <th>Current Bin</th>
                <th>Order Lines (Freq)</th>
                <th>Total Quantity Ordered</th>
                <th>Demand Segment</th>
                <th>Volatility (CV)</th>
                <th>Volatility Class</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(d => (
                <tr key={d.skuId}>
                  <td><strong>{d.skuId}</strong></td>
                  <td>{d.productName}</td>
                  <td>{d.category}</td>
                  <td><span className="badge badge-occupied">{d.currentLocation}</span></td>
                  <td><strong>{d.orderFrequency} orders</strong></td>
                  <td>{d.totalQuantity} units</td>
                  <td>
                    <span className={`badge badge-${d.demandClass.toLowerCase()}`}>
                      {d.demandClass}
                    </span>
                  </td>
                  <td>{d.demandCv !== undefined ? d.demandCv.toFixed(2) : '0.00'}</td>
                  <td>
                    <span className="badge" style={{
                      backgroundColor: d.volatilityClass === 'VOLATILE' ? 'rgba(239, 68, 68, 0.2)' : d.volatilityClass === 'MODERATE' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                      color: d.volatilityClass === 'VOLATILE' ? '#f87171' : d.volatilityClass === 'MODERATE' ? '#fbbf24' : '#4ade80',
                      border: `1px solid ${d.volatilityClass === 'VOLATILE' ? '#ef4444' : d.volatilityClass === 'MODERATE' ? '#f59e0b' : '#22c55e'}`
                    }}>
                      {d.volatilityClass || 'STABLE'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Market Basket & Order Affinity Analysis Section */}
      <div className="section-card" style={{ marginTop: '1.5rem' }}>
        <div className="section-header">
          <div>
            <h2 className="section-title">🛒 Market Basket & Order Affinity Analysis (Co-Occurrence Bundles)</h2>
            <p className="section-desc">
              Pairwise SKU co-occurrences across historical orders. High-affinity product pairs are prioritized by the Slotting Recommender
              to be clustered in neighboring bays/aisles to eliminate multi-line cross-aisle travel.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {[
              { id: 'TOP5', label: 'Top 5 Bundles' },
              { id: 'TOP10', label: 'Top 10 Bundles' },
              { id: 'ALL', label: `All Pairs (${pairs.length})` }
            ].map(b => (
              <button
                key={b.id}
                className="btn"
                onClick={() => setAffinityFilter(b.id)}
                style={{
                  background: affinityFilter === b.id ? '#a855f7' : '#1e293b',
                  color: affinityFilter === b.id ? '#ffffff' : '#f8fafc',
                  border: '1px solid #475569'
                }}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

        {pairs.length === 0 ? (
          <p style={{ color: '#94a3b8', fontStyle: 'italic' }}>No affinity pair data available.</p>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Co-Ordered Product Pair</th>
                  <th>SKU Pair</th>
                  <th>Categories</th>
                  <th>Co-Orders</th>
                  <th>Orders (A / B)</th>
                  <th>Cosine Affinity</th>
                  <th>Jaccard Index</th>
                  <th>Slotting Clustering Strategy</th>
                </tr>
              </thead>
              <tbody>
                {displayedPairs.map((p, idx) => (
                  <tr key={p.pairId || idx}>
                    <td><strong>#{idx + 1}</strong></td>
                    <td>
                      <strong>{p.pairLabel || `${p.productA} + ${p.productB}`}</strong>
                    </td>
                    <td>
                      <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>{p.skuA}</span>
                      {' + '}
                      <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>{p.skuB}</span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                        {p.categoryA} / {p.categoryB}
                      </span>
                    </td>
                    <td>
                      <strong style={{ color: '#4ade80' }}>{p.coOccurrenceCount} orders</strong>
                    </td>
                    <td>{p.ordersA} / {p.ordersB}</td>
                    <td>
                      <span className="badge" style={{
                        backgroundColor: p.affinityScore >= 0.4 ? 'rgba(34, 197, 94, 0.2)' : 'rgba(168, 85, 247, 0.2)',
                        color: p.affinityScore >= 0.4 ? '#4ade80' : '#c084fc',
                        border: `1px solid ${p.affinityScore >= 0.4 ? '#22c55e' : '#a855f7'}`
                      }}>
                        {(p.affinityScore * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td>{(p.jaccardIndex !== undefined ? p.jaccardIndex.toFixed(3) : '—')}</td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                        {p.coOccurrenceCount >= 4
                          ? '🔥 High-Priority Cluster (Slot in adjacent bays)'
                          : 'Recommended neighboring aisle/shelf placement'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
