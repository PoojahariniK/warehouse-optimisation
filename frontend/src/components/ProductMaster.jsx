import React, { useState } from 'react';

export default function ProductMaster({ products }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  if (!products) return <div className="state-container"><div className="spinner"></div>Loading products...</div>;

  const categories = ['ALL', ...new Set(products.map(p => p.category))];

  const filtered = products.filter(p => {
    const matchesSearch = p.skuId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          p.productName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = categoryFilter === 'ALL' || p.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="section-card">
      <div className="section-header">
        <div>
          <h2 className="section-title">2. Product Master Catalog ({products.length} SKUs)</h2>
          <p className="section-desc">SKU details, category groups, required capacity units, and active storage slot assignments</p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            placeholder="Search SKU or Name..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              background: '#0f172a',
              border: '1px solid #334155',
              color: '#f8fafc',
              padding: '0.5rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.85rem'
            }}
          />
          <select
            value={categoryFilter}
            onChange={e => setCategoryFilter(e.target.value)}
            style={{
              background: '#0f172a',
              border: '1px solid #334155',
              color: '#f8fafc',
              padding: '0.5rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.85rem'
            }}
          >
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th>SKU ID</th>
              <th>Product Name</th>
              <th>Category</th>
              <th>Required Capacity</th>
              <th>Current Storage Bin</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(p => (
              <tr key={p.skuId}>
                <td><strong>{p.skuId}</strong></td>
                <td>{p.productName}</td>
                <td>
                  <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.1)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                    {p.category}
                  </span>
                </td>
                <td>{p.requiredCapacity} units</td>
                <td>
                  <span className="badge badge-occupied">{p.currentLocation}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

