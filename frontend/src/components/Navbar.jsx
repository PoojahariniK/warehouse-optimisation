import React from 'react';

export default function Navbar({ activeTab, setActiveTab, counts }) {
  const tabs = [
    { id: 'overview', label: '1. Overview & KPIs' },
    { id: 'products', label: '2. Product Master', count: counts.products },
    { id: 'locations', label: '3. Warehouse Grid', count: counts.locations },
    { id: 'demand', label: '4. Demand Profile', count: counts.demand },
    { id: 'recommendations', label: '5. Slotting Engine', count: counts.recommendations },
    { id: 'pickpath', label: '6. Pick-Path Routing', count: counts.routes },
    { id: 'replenishment', label: '7. Replenishment', count: counts.replenishment, alert: counts.replenishment > 0 },
    { id: 'approval', label: '8. Supervisor Approval', count: counts.pendingApproval, success: true },
  ];

  return (
    <nav className="nav-tabs">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => setActiveTab(tab.id)}
        >
          {tab.label}
          {tab.count !== undefined && (
            <span className={`tab-badge ${tab.alert ? 'alert' : tab.success ? 'success' : ''}`}>
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </nav>
  );
}
