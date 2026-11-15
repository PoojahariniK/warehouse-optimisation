import React, { useState } from 'react';

export default function ReplenishmentAlerts({ replenishment, products, locations, stockLevels, onAdjustStock }) {
  const [selectedSku, setSelectedSku] = useState(products && products[0] ? products[0].skuId : 'SKU006');
  const [deltaQty, setDeltaQty] = useState(10);

  if (!replenishment) return <div className="state-container"><div className="spinner"></div>Loading replenishment alerts...</div>;

  const outOfStock = replenishment.filter(r => r.stockStatus === 'OUT_OF_STOCK');
  const lowStock = replenishment.filter(r => r.stockStatus === 'LOW_STOCK');

  const handleAddStock = () => {
    if (onAdjustStock) onAdjustStock(selectedSku, Math.abs(Number(deltaQty)));
  };

  const handleRemoveStock = () => {
    if (onAdjustStock) onAdjustStock(selectedSku, -Math.abs(Number(deltaQty)));
  };

  const selProd = (products || []).find(p => p.skuId === selectedSku);
  const selLocId = selProd ? selProd.currentLocation : null;
  const selLoc = selLocId && locations ? locations.find(l => l.locationId === selLocId) : null;
  const binCapacity = selLoc ? selLoc.capacity : (selProd && selProd.requiredCapacity ? selProd.requiredCapacity : 30);

  const alertItem = replenishment.find(r => r.skuId === selectedSku);
  const currentStock = (stockLevels && stockLevels[selectedSku] !== undefined)
    ? stockLevels[selectedSku]
    : (alertItem ? alertItem.currentStock : 15);
  const minStock = alertItem ? alertItem.minimumStock : 10;
  const remainingSpace = Math.max(0, binCapacity - currentStock);
  const isFull = currentStock >= binCapacity;
  const fillPct = Math.min(100, Math.round((currentStock / binCapacity) * 100));

  return (
    <div className="section-card">
      <div className="section-header">
        <div>
          <h2 className="section-title">7. Replenishment Alerts &amp; Stock Health</h2>
          <p className="section-desc">
            SKUs where Current_Stock ≤ Minimum_Stock requiring immediate action
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span
            className="badge"
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.2)',
              color: '#f87171',
              border: '1px solid #ef4444',
              padding: '0.4rem 0.8rem',
              fontSize: '0.85rem'
            }}
          >
            🔴 Out of Stock: {outOfStock.length}
          </span>
          <span
            className="badge"
            style={{
              backgroundColor: 'rgba(245, 158, 11, 0.2)',
              color: '#fbbf24',
              border: '1px solid #f59e0b',
              padding: '0.4rem 0.8rem',
              fontSize: '0.85rem'
            }}
          >
            🟠 Low Stock: {lowStock.length}
          </span>
        </div>
      </div>

      {/* Alert Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <span style={{ fontSize: '0.75rem', color: '#f87171', textTransform: 'uppercase', fontWeight: '600' }}>Critical — Zero Inventory</span>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: '#f87171', marginTop: '0.25rem' }}>
            {outOfStock.length}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
            SKUs completely depleted
          </div>
        </div>

        <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
          <span style={{ fontSize: '0.75rem', color: '#fbbf24', textTransform: 'uppercase', fontWeight: '600' }}>Warning — Below Minimum</span>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: '#fbbf24', marginTop: '0.25rem' }}>
            {lowStock.length}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
            SKUs approaching stockout
          </div>
        </div>

        <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: '600' }}>Total Alerts</span>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: '#f8fafc', marginTop: '0.25rem' }}>
            {replenishment.length}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
            All replenishment actions needed
          </div>
        </div>
      </div>

      {/* Replenishment Table */}
      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th>SKU ID</th>
              <th>Product Name</th>
              <th>Assigned Shelf</th>
              <th>Current Stock / Capacity</th>
              <th>Minimum Stock</th>
              <th>Stock Deficit</th>
              <th>Stock Status</th>
              <th>Action Required</th>
            </tr>
          </thead>
          <tbody>
            {replenishment.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#4ade80' }}>
                  ✅ All inventory levels are healthy! No replenishment alerts active.
                </td>
              </tr>
            ) : (
              replenishment.map(r => {
                const deficit = r.minimumStock - r.currentStock;
                const isOut = r.stockStatus === 'OUT_OF_STOCK';
                const prod = (products || []).find(p => p.skuId === r.skuId);
                const locId = prod ? prod.currentLocation : '—';
                const loc = locId ? (locations || []).find(l => l.locationId === locId) : null;
                const cap = loc ? loc.capacity : (prod && prod.requiredCapacity ? prod.requiredCapacity : 30);
                const isBinFull = r.currentStock >= cap;
                return (
                  <tr key={r.skuId}>
                    <td><strong>{r.skuId}</strong></td>
                    <td>{r.productName}</td>
                    <td><span className="badge badge-occupied">{locId}</span></td>
                    <td>
                      <span style={{ color: isOut ? '#f87171' : isBinFull ? '#f87171' : '#fbbf24', fontWeight: '600' }}>
                        {r.currentStock}
                      </span>
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}> / {cap} u</span>
                    </td>
                    <td>{r.minimumStock}</td>
                    <td>
                      <span style={{ color: '#f87171', fontWeight: '700' }}>
                        -{deficit}
                      </span>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: isOut ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                          color: isOut ? '#f87171' : '#fbbf24',
                          border: `1px solid ${isOut ? 'rgba(239, 68, 68, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`
                        }}
                      >
                        {r.stockStatus}
                      </span>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: 'rgba(239, 68, 68, 0.15)',
                          color: '#f87171',
                          border: '1px solid rgba(239, 68, 68, 0.4)'
                        }}
                      >
                        {r.replenishmentRequired}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Interactive Stock Count Adjustment Console */}
      <div style={{ marginTop: '2rem', padding: '1.25rem', background: '#0f172a', borderRadius: '8px', border: '1px solid #334155' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.4rem' }}>
          <h3 style={{ color: '#fbbf24', fontSize: '1.1rem', margin: 0 }}>📦 Stock Count &amp; Restock Management Console</h3>
          <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid #0284c7', fontSize: '0.75rem' }}>
            Physical Shelf Limit: HARD CAP ENFORCED
          </span>
        </div>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1rem' }}>
          Simulate stock movements. Restocks cannot exceed the physical capacity limit of the assigned shelf bin.
        </p>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Select SKU:</label>
            <select
              value={selectedSku}
              onChange={e => setSelectedSku(e.target.value)}
              style={{ background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '0.45rem 0.8rem', borderRadius: '6px', fontSize: '0.9rem' }}
            >
              {(products || []).map(p => (
                <option key={p.skuId} value={p.skuId}>
                  {p.skuId} - {p.productName} ({p.currentLocation || 'N/A'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Units:</label>
            <input
              type="number"
              min="1"
              max="100"
              value={deltaQty}
              onChange={e => setDeltaQty(Number(e.target.value))}
              style={{ width: '80px', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '0.45rem', borderRadius: '6px' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignSelf: 'flex-end' }}>
            <button
              className="btn btn-approve"
              onClick={handleAddStock}
              style={{ padding: '0.45rem 1rem' }}
              title={isFull ? 'Shelf is at full capacity' : `Restock +${deltaQty} units`}
            >
              + Restock (+{deltaQty})
            </button>
            <button
              className="btn btn-reject"
              onClick={handleRemoveStock}
              style={{ padding: '0.45rem 1rem' }}
              title={`Pick / Dispatch -${deltaQty} units`}
            >
              - Dispatch/Pick (-{deltaQty})
            </button>
          </div>
        </div>

        {/* Live Physical Shelf Capacity Indicator */}
        <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: '#1e293b', borderRadius: '6px', border: '1px solid #334155', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center', flexWrap: 'wrap', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: '#94a3b8' }}>Assigned Bin: </span>
              <span className="badge badge-occupied" style={{ marginLeft: '0.3rem' }}>{selLocId || 'Unassigned'}</span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Physical Bin Capacity: </span>
              <strong style={{ color: '#f8fafc' }}>{binCapacity} units</strong>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Current Stock: </span>
              <strong style={{ color: isFull ? '#f87171' : currentStock <= minStock ? '#fbbf24' : '#4ade80' }}>
                {currentStock} / {binCapacity} units
              </strong>
              <span style={{ color: '#94a3b8', marginLeft: '0.3rem' }}>({fillPct}% fill)</span>
            </div>
          </div>
          <div>
            {isFull ? (
              <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: '1px solid #ef4444', padding: '0.35rem 0.7rem' }}>
                🚫 Shelf Full (0 space available)
              </span>
            ) : (
              <span className="badge" style={{ backgroundColor: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', border: '1px solid #22c55e', padding: '0.35rem 0.7rem' }}>
                🟢 Available Space: {remainingSpace} units
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
