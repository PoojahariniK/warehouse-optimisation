import React, { useState } from 'react';

export default function WarehouseLocations({ locations, products, demand, onVacateLocation }) {
  const [selectedLoc, setSelectedLoc] = useState(null);

  if (!locations) return <div className="state-container"><div className="spinner"></div>Loading locations...</div>;

  const aisles = ['A', 'B', 'C', 'D', 'E'];
  const byAisle = {};
  aisles.forEach(a => {
    byAisle[a] = locations.filter(l => l.aisle === a).sort((x, y) => x.locationId.localeCompare(y.locationId));
  });

  return (
    <div className="section-card">
      <div className="section-header">
        <div>
          <h2 className="section-title">3. Warehouse Physical Layout Grid (40 Locations)</h2>
          <p className="section-desc">5 Aisles (A-E) x 8 Slots each. Click any bin to inspect physical coordinates, capacity, and occupying SKU details.</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', backgroundColor: '#6366f1', borderRadius: '3px', display: 'inline-block' }}></span>
            <span>Occupied ({locations.filter(l => l.status === 'OCCUPIED').length})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', backgroundColor: '#22c55e', borderRadius: '3px', display: 'inline-block' }}></span>
            <span>Available Empty ({locations.filter(l => l.status === 'EMPTY').length})</span>
          </div>
        </div>
      </div>

      <div className="warehouse-aisle-container">
        {aisles.map(aisle => (
          <div key={aisle} className="aisle-row">
            <div className="aisle-label">Aisle {aisle}</div>
            <div className="aisle-slots">
              {byAisle[aisle].map(loc => {
                const isEmpty = loc.status === 'EMPTY';
                const occupant = (products || []).find(p => p.currentLocation === loc.locationId);
                const isSelected = selectedLoc && selectedLoc.locationId === loc.locationId;
                return (
                  <div
                    key={loc.locationId}
                    className={`slot-box ${isEmpty ? 'empty' : 'occupied'}`}
                    onClick={() => setSelectedLoc(loc)}
                    style={{
                      outline: isSelected ? '2px solid #38bdf8' : 'none',
                      boxShadow: isSelected ? '0 0 10px rgba(56, 189, 248, 0.5)' : 'none',
                      padding: '0.45rem 0.35rem',
                      minWidth: '75px',
                      minHeight: '75px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="slot-id" style={{ color: isEmpty ? '#4ade80' : '#818cf8', fontSize: '0.8rem' }}>{loc.locationId}</span>
                      <span style={{ fontSize: '0.6rem', color: '#64748b' }}>({loc.x},{loc.y})</span>
                    </div>
                    <div style={{ margin: '0.2rem 0', minHeight: '1.6rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      {isEmpty ? (
                        <span style={{ fontSize: '0.68rem', color: '#4ade80', fontWeight: 'bold' }}>EMPTY</span>
                      ) : occupant ? (
                        <>
                          <span style={{ fontSize: '0.72rem', fontWeight: 'bold', color: '#f8fafc', lineHeight: 1.1 }}>{occupant.skuId}</span>
                          <span style={{ fontSize: '0.62rem', color: '#cbd5e1', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '70px' }} title={occupant.productName}>
                            {occupant.productName}
                          </span>
                        </>
                      ) : (
                        <span style={{ fontSize: '0.68rem', color: '#818cf8', fontWeight: 'bold' }}>OCCUPIED</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.62rem', color: '#94a3b8' }}>
                      <span>Cap:{loc.capacity}</span>
                      <span style={{ color: loc.hazardAllowed === 'HAZMAT_BATTERY' ? '#f87171' : loc.hazardAllowed === 'HAZMAT_FLAMMABLE' ? '#fbbf24' : '#64748b', fontWeight: 'bold' }}>
                        {loc.hazardAllowed === 'HAZMAT_BATTERY' ? '⚡' : loc.hazardAllowed === 'HAZMAT_FLAMMABLE' ? '🔥' : ''}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {selectedLoc && (() => {
        const occupants = (products || []).filter(p => p.currentLocation === selectedLoc.locationId);
        const isOccupied = occupants.length > 0;
        const primaryOccupant = occupants[0];
        const demandInfo = primaryOccupant && demand ? demand.find(d => d.skuId === primaryOccupant.skuId) : null;
        const utilizationPct = primaryOccupant ? Math.round((primaryOccupant.requiredCapacity / selectedLoc.capacity) * 100) : 0;

        return (
          <div style={{ marginTop: '1.5rem', background: '#0f172a', padding: '1.25rem 1.5rem', borderRadius: '8px', border: `1px solid ${isOccupied ? '#818cf8' : '#22c55e'}` }}>
            {/* Header Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', paddingBottom: '0.75rem', borderBottom: '1px solid #1e293b', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', margin: 0 }}>
                  📍 Location: <strong style={{ color: isOccupied ? '#818cf8' : '#4ade80' }}>{selectedLoc.locationId}</strong> (Aisle {selectedLoc.aisle})
                </h3>
                <span className={`badge ${selectedLoc.status === 'EMPTY' ? 'badge-empty' : 'badge-occupied'}`}>
                  {selectedLoc.status === 'EMPTY' ? '🟢 AVAILABLE EMPTY' : '🟣 OCCUPIED'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {selectedLoc.status === 'OCCUPIED' && onVacateLocation && (
                  <button
                    className="btn btn-reject"
                    style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                    onClick={() => {
                      onVacateLocation(selectedLoc.locationId);
                      setSelectedLoc(prev => ({ ...prev, status: 'EMPTY' }));
                    }}
                  >
                    🗑️ Vacate Slot (Remove SKU)
                  </button>
                )}
                <button
                  className="btn"
                  onClick={() => setSelectedLoc(null)}
                  style={{ background: '#334155', color: '#f8fafc', padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                >
                  ✕ Close
                </button>
              </div>
            </div>

            {/* Details Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
              {/* Left: Physical Bin Specs */}
              <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '6px', border: '1px solid #334155' }}>
                <h4 style={{ color: '#38bdf8', fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.6rem', letterSpacing: '0.05em' }}>
                  📐 Physical Slot Specifications
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', fontSize: '0.82rem' }}>
                  <div>
                    <span style={{ color: '#94a3b8' }}>Grid Coordinates:</span>
                    <div style={{ fontWeight: 600, color: '#f8fafc' }}>({selectedLoc.x}, {selectedLoc.y})</div>
                  </div>
                  <div>
                    <span style={{ color: '#94a3b8' }}>Max Physical Capacity:</span>
                    <div style={{ fontWeight: 600, color: '#f8fafc' }}>{selectedLoc.capacity} units</div>
                  </div>
                  <div>
                    <span style={{ color: '#94a3b8' }}>Allowed Category:</span>
                    <div style={{ fontWeight: 600, color: '#f8fafc' }}>{selectedLoc.allowedCategory}</div>
                  </div>
                  <div>
                    <span style={{ color: '#94a3b8' }}>Hazard Compatibility:</span>
                    <div style={{
                      fontWeight: 600,
                      color: selectedLoc.hazardAllowed === 'HAZMAT_BATTERY' ? '#f87171' : selectedLoc.hazardAllowed === 'HAZMAT_FLAMMABLE' ? '#fbbf24' : '#4ade80'
                    }}>
                      {selectedLoc.hazardAllowed || 'GENERAL'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Right: Occupant SKU Details */}
              <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '6px', border: `1px solid ${isOccupied ? 'rgba(129, 140, 248, 0.4)' : 'rgba(34, 197, 94, 0.4)'}` }}>
                <h4 style={{ color: isOccupied ? '#c084fc' : '#4ade80', fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.6rem', letterSpacing: '0.05em' }}>
                  {isOccupied ? '📦 Occupying SKU & Product Details' : '🟢 Slot Availability Status'}
                </h4>

                {isOccupied && primaryOccupant ? (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.4rem' }}>
                      <div>
                        <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                          {primaryOccupant.productName}
                        </span>
                        <span className="badge badge-occupied" style={{ marginLeft: '0.5rem', fontSize: '0.75rem' }}>
                          {primaryOccupant.skuId}
                        </span>
                      </div>
                      {demandInfo && (
                        <span className={`badge badge-${demandInfo.demandClass.toLowerCase()}`}>
                          {demandInfo.demandClass} Velocity
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', fontSize: '0.82rem' }}>
                      <div>
                        <span style={{ color: '#94a3b8' }}>Product Category:</span>
                        <div style={{ fontWeight: 600, color: '#f8fafc' }}>{primaryOccupant.category}</div>
                      </div>
                      <div>
                        <span style={{ color: '#94a3b8' }}>Required Capacity:</span>
                        <div style={{ fontWeight: 600, color: '#f8fafc' }}>{primaryOccupant.requiredCapacity} units</div>
                      </div>
                      <div>
                        <span style={{ color: '#94a3b8' }}>Hazard Classification:</span>
                        <div style={{
                          fontWeight: 600,
                          color: primaryOccupant.hazardClass === 'HAZMAT_BATTERY' ? '#f87171' : primaryOccupant.hazardClass === 'HAZMAT_FLAMMABLE' ? '#fbbf24' : '#94a3b8'
                        }}>
                          {primaryOccupant.hazardClass || 'GENERAL'}
                        </div>
                      </div>
                      <div>
                        <span style={{ color: '#94a3b8' }}>Slot Utilization:</span>
                        <div style={{ fontWeight: 600, color: utilizationPct > 80 ? '#fbbf24' : '#4ade80' }}>
                          {utilizationPct}% ({primaryOccupant.requiredCapacity}/{selectedLoc.capacity} u)
                        </div>
                      </div>
                    </div>

                    {demandInfo && (
                      <div style={{ marginTop: '0.6rem', paddingTop: '0.5rem', borderTop: '1px solid #334155', fontSize: '0.8rem', color: '#94a3b8' }}>
                        Order Frequency: <strong style={{ color: '#f8fafc' }}>{demandInfo.orderFrequency} orders</strong> · Total Quantity Picked: <strong style={{ color: '#f8fafc' }}>{demandInfo.totalQuantity} units</strong>
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: '1.6' }}>
                    <p style={{ color: '#4ade80', fontWeight: 600, margin: 0 }}>
                      ✅ This location is completely unoccupied and available.
                    </p>
                    <p style={{ marginTop: '0.4rem', marginBottom: 0 }}>
                      Can accept candidate SKUs up to <strong style={{ color: '#f8fafc' }}>{selectedLoc.capacity} required capacity</strong> matching category <strong style={{ color: '#f8fafc' }}>{selectedLoc.allowedCategory}</strong> and hazard clearance <strong style={{ color: '#f8fafc' }}>{selectedLoc.hazardAllowed || 'GENERAL'}</strong>.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
