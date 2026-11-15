import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Navbar from './components/Navbar';
import WarehouseOverview from './components/WarehouseOverview';
import ProductMaster from './components/ProductMaster';
import WarehouseLocations from './components/WarehouseLocations';
import DemandClassification from './components/DemandClassification';
import SlotRecommendations from './components/SlotRecommendations';
import PickPathOptimization from './components/PickPathOptimization';
import ReplenishmentAlerts from './components/ReplenishmentAlerts';
import SupervisorApproval from './components/SupervisorApproval';
import warehouseApi from './api/warehouseApi';

const INITIAL_STOCK = {
  SKU001: 19, SKU002: 8,  SKU003: 33, SKU004: 21, SKU005: 30,
  SKU006: 0,  SKU007: 35, SKU008: 24, SKU009: 34, SKU010: 9,
  SKU011: 4,  SKU012: 28, SKU013: 38, SKU014: 24, SKU015: 5,
  SKU016: 22, SKU017: 26, SKU018: 27, SKU019: 28, SKU020: 10,
  SKU021: 34, SKU022: 32, SKU023: 1,  SKU024: 26, SKU025: 13,
  SKU026: 33, SKU027: 16, SKU028: 5,  SKU029: 36, SKU030: 39
};

const INITIAL_MIN_STOCK = {
  SKU001: 13, SKU002: 8,  SKU003: 15, SKU004: 9,  SKU005: 11,
  SKU006: 8,  SKU007: 6,  SKU008: 9,  SKU009: 10, SKU010: 5,
  SKU011: 8,  SKU012: 12, SKU013: 9,  SKU014: 6,  SKU015: 10,
  SKU016: 13, SKU017: 15, SKU018: 10, SKU019: 14, SKU020: 8,
  SKU021: 9,  SKU022: 5,  SKU023: 10, SKU024: 8,  SKU025: 8,
  SKU026: 12, SKU027: 6,  SKU028: 7,  SKU029: 13, SKU030: 15
};

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState(false);
  const [toast, setToast] = useState(null);

  // Core Data States
  const [products, setProducts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [demand, setDemand] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [replenishment, setReplenishment] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [affinityPairs, setAffinityPairs] = useState([]);
  const [isResetting, setIsResetting] = useState(false);
  const [stockLevels, setStockLevels] = useState({});

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      // Attempt to load from Spring Boot REST endpoints in parallel
      const [
        prodsData,
        locsData,
        demandData,
        recsData,
        routesData,
        replenData,
        analyticsData,
        affinityData,
      ] = await Promise.all([
        warehouseApi.getProducts().catch(() => null),
        warehouseApi.getLocations().catch(() => null),
        warehouseApi.getDemand().catch(() => null),
        warehouseApi.getSlotRecommendations().catch(() => null),
        warehouseApi.getAllRoutes().catch(() => null),
        warehouseApi.getReplenishmentAlerts().catch(() => null),
        warehouseApi.getAnalytics().catch(() => null),
        warehouseApi.getAffinity().catch(() => null),
      ]);

      if (prodsData && locsData && analyticsData) {
        setProducts(prodsData);
        setLocations(locsData);
        setDemand(demandData || []);
        setRecommendations(recsData || []);
        setRoutes(routesData || []);
        setReplenishment(replenData || []);
        setAnalytics(analyticsData);
        setAffinityPairs(affinityData || (window.__SEED_DATA__ && window.__SEED_DATA__.affinityPairs) || []);
        setBackendOnline(true);
      } else {
        // Fallback to static seed data if backend is offline
        loadFallbackData();
      }
    } catch (err) {
      console.warn('Backend connection failed, falling back to local dataset snapshot:', err);
      loadFallbackData();
    } finally {
      setLoading(false);
    }
  }, []);

  const loadFallbackData = () => {
    setBackendOnline(false);
    // Use fallback snapshot if backend is not reachable in local test mode
    if (window.__SEED_DATA__) {
      const data = JSON.parse(JSON.stringify(window.__SEED_DATA__));
      setProducts(data.products || []);
      setLocations(data.locations || []);
      setDemand(data.demand || []);
      setRecommendations(data.recommendations || []);
      setRoutes(data.routes || []);
      setReplenishment(data.replenishment || []);
      setAnalytics(data.analytics || null);
      setAffinityPairs(data.affinityPairs || []);
    }
  };

  const [isReEvaluating, setIsReEvaluating] = useState(false);

  const handleReEvaluate = async () => {
    setIsReEvaluating(true);
    try {
      if (backendOnline) {
        const updatedRecs = await warehouseApi.reEvaluateSlots();
        const [updatedAnalytics, updatedProds, updatedLocs] = await Promise.all([
          warehouseApi.getAnalytics(),
          warehouseApi.getProducts().catch(() => null),
          warehouseApi.getLocations().catch(() => null)
        ]);
        setRecommendations(updatedRecs);
        setAnalytics(updatedAnalytics);
        if (updatedProds) setProducts(updatedProds);
        if (updatedLocs) setLocations(updatedLocs);
        showToast('⚡ Dynamic Re-evaluation complete: Empty slots scanned and matched with candidate SKUs.', 'success');
      } else {
        showToast('⚡ Evaluated empty warehouse slots (offline mode).', 'success');
      }
    } catch (e) {
      showToast(e.message || 'Re-evaluation failed', 'error');
    } finally {
      setIsReEvaluating(false);
    }
  };

  const handleVacateLocation = async (locationId) => {
    try {
      if (backendOnline) {
        const resp = await warehouseApi.vacateLocation(locationId);
        showToast(resp.message || `Location ${locationId} vacated to EMPTY in database.`, 'success');
        const [updatedLocs, updatedProds, updatedRecs, updatedAnalytics] = await Promise.all([
          warehouseApi.getLocations(),
          warehouseApi.getProducts().catch(() => null),
          warehouseApi.getSlotRecommendations().catch(() => null),
          warehouseApi.getAnalytics().catch(() => null)
        ]);
        if (updatedLocs) setLocations(updatedLocs);
        if (updatedProds) setProducts(updatedProds);
        if (updatedRecs) setRecommendations(updatedRecs);
        if (updatedAnalytics) setAnalytics(updatedAnalytics);
      } else {
        setLocations(prev => prev.map(l => l.locationId === locationId ? { ...l, status: 'EMPTY' } : l));
        setProducts(prev => prev.map(p => p.currentLocation === locationId ? { ...p, currentLocation: 'UNASSIGNED' } : p));
        setAnalytics(prev => prev ? {
          ...prev,
          occupiedLocations: Math.max(0, prev.occupiedLocations - 1),
          emptyLocations: prev.emptyLocations + 1
        } : prev);
        showToast(`Location ${locationId} vacated to EMPTY (offline mode).`, 'success');
      }
    } catch (err) {
      showToast(err.message || 'Failed to vacate location', 'error');
    }
  };

  const handleResetDemo = async () => {
    if (!window.confirm('Reset warehouse demo state back to baseline? All approved slot changes will be reverted.')) {
      return;
    }
    setIsResetting(true);
    try {
      setStockLevels({});
      if (backendOnline) {
        const resp = await warehouseApi.resetDemoState();
        showToast(resp.message || 'Warehouse reset to baseline seed state.', 'success');
        await loadAllData();
      } else {
        loadFallbackData();
        showToast('Warehouse reset to baseline seed state (offline mode).', 'success');
      }
    } catch (err) {
      showToast(err.message || 'Failed to reset demo state', 'error');
    } finally {
      setIsResetting(false);
    }
  };

  const updateReplenishmentList = (skuId, prodName, newStock, minStock) => {
    setReplenishment(prev => {
      const status = newStock === 0 ? 'OUT_OF_STOCK' : (newStock <= minStock ? 'LOW_STOCK' : 'HEALTHY');
      const isAlert = newStock <= minStock;
      const existing = prev.find(r => r.skuId === skuId);

      if (isAlert) {
        const newItem = {
          skuId,
          productName: prodName,
          currentStock: newStock,
          minimumStock: minStock,
          stockStatus: status,
          replenishmentRequired: 'YES'
        };
        if (existing) {
          return prev.map(r => r.skuId === skuId ? newItem : r);
        } else {
          return [...prev, newItem];
        }
      } else {
        return prev.filter(r => r.skuId !== skuId);
      }
    });
  };

  const handleAdjustStock = (skuId, delta) => {
    const prod = (products || []).find(p => p.skuId === skuId);
    const prodName = prod ? prod.productName : skuId;
    const locId = prod ? prod.currentLocation : null;
    const loc = locId && locations ? locations.find(l => l.locationId === locId) : null;
    const maxCapacity = loc ? loc.capacity : (prod && prod.requiredCapacity ? prod.requiredCapacity : 30);

    const alertItem = (replenishment || []).find(r => r.skuId === skuId);
    const currentStock = stockLevels[skuId] !== undefined
      ? stockLevels[skuId]
      : (alertItem ? alertItem.currentStock : (INITIAL_STOCK[skuId] ?? 15));
    const minStock = alertItem ? alertItem.minimumStock : (INITIAL_MIN_STOCK[skuId] ?? 10);

    if (delta > 0) {
      // Restock: Check shelf capacity constraint
      if (currentStock >= maxCapacity) {
        showToast(
          `⚠️ Shelf Capacity Limit Reached: ${skuId} (${prodName}) in shelf ${locId || 'N/A'} is already at 100% capacity (${currentStock}/${maxCapacity} units). Restock blocked.`,
          'error'
        );
        return;
      }

      if (currentStock + delta > maxCapacity) {
        const allowableAdd = maxCapacity - currentStock;
        const rejectedQty = delta - allowableAdd;
        const newStock = maxCapacity; // Enforce hard cap

        setStockLevels(prev => ({ ...prev, [skuId]: newStock }));
        updateReplenishmentList(skuId, prodName, newStock, minStock);

        showToast(
          `⚠️ Shelf Capacity Hard Cap: Shelf ${locId || ''} capacity limit is ${maxCapacity} units (Current: ${currentStock}). Added +${allowableAdd} units to fill shelf. ${rejectedQty} units rejected due to physical capacity constraint.`,
          'error'
        );
        return;
      }

      const newStock = currentStock + delta;
      setStockLevels(prev => ({ ...prev, [skuId]: newStock }));
      updateReplenishmentList(skuId, prodName, newStock, minStock);

      const status = newStock <= minStock ? 'LOW_STOCK' : 'HEALTHY';
      showToast(
        `Restocked (+) ${delta} units of ${skuId} into shelf ${locId || 'N/A'}. Current stock: ${newStock}/${maxCapacity} units (${status}).`,
        'success'
      );
    } else {
      // Pick / Dispatch: delta < 0
      const pickQty = Math.abs(delta);
      if (currentStock === 0) {
        showToast(`⚠️ Cannot dispatch ${skuId}: Shelf ${locId || 'N/A'} is completely out of stock (0 units).`, 'error');
        return;
      }

      const actualPicked = Math.min(pickQty, currentStock);
      const newStock = Math.max(0, currentStock - pickQty);
      setStockLevels(prev => ({ ...prev, [skuId]: newStock }));
      updateReplenishmentList(skuId, prodName, newStock, minStock);

      const status = newStock === 0 ? 'OUT_OF_STOCK' : (newStock <= minStock ? 'LOW_STOCK' : 'HEALTHY');
      showToast(
        `Dispatched (-) ${actualPicked} units of ${skuId} from shelf ${locId || 'N/A'}. Current stock: ${newStock}/${maxCapacity} units (${status}).`,
        newStock <= minStock ? 'error' : 'success'
      );
    }
  };

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const handleApprove = async (recommendationId) => {
    try {
      if (backendOnline) {
        const resp = await warehouseApi.approveSlot(recommendationId);
        showToast(resp.message || `Slot ${recommendationId} approved successfully`, 'success');
        // Refresh recommendations & analytics
        const [updatedRecs, updatedAnalytics, updatedProds, updatedLocs] = await Promise.all([
          warehouseApi.getSlotRecommendations(),
          warehouseApi.getAnalytics(),
          warehouseApi.getProducts().catch(() => null),
          warehouseApi.getLocations().catch(() => null)
        ]);
        setRecommendations(updatedRecs);
        setAnalytics(updatedAnalytics);
        if (updatedProds) setProducts(updatedProds);
        if (updatedLocs) setLocations(updatedLocs);
      } else {
        // Optimistic UI update in offline fallback
        const rec = recommendations.find(r => r.recommendationId === recommendationId);
        setRecommendations(prev =>
          prev.map(r => r.recommendationId === recommendationId ? { ...r, recommendationStatus: 'APPROVED' } : r)
        );
        if (rec && rec.recommendedLocation !== 'NONE') {
          setProducts(prev => prev.map(p => p.skuId === rec.skuId ? { ...p, currentLocation: rec.recommendedLocation } : p));
          setLocations(prev => prev.map(l => {
            if (l.locationId === rec.recommendedLocation) return { ...l, status: 'OCCUPIED' };
            if (l.locationId === rec.currentLocation) return { ...l, status: 'EMPTY' };
            return l;
          }));
        }
        showToast(`Slot recommendation ${recommendationId} approved (offline update)`, 'success');
      }
    } catch (err) {
      showToast(err.message || 'Approval failed: Check warehouse constraints', 'error');
    }
  };

  const handleReject = async (recommendationId) => {
    try {
      if (backendOnline) {
        const resp = await warehouseApi.rejectSlot(recommendationId);
        showToast(resp.message || `Slot ${recommendationId} rejected`, 'success');
        // Refresh
        const [updatedRecs, updatedAnalytics] = await Promise.all([
          warehouseApi.getSlotRecommendations(),
          warehouseApi.getAnalytics()
        ]);
        setRecommendations(updatedRecs);
        setAnalytics(updatedAnalytics);
      } else {
        // Optimistic update
        setRecommendations(prev =>
          prev.map(r => r.recommendationId === recommendationId ? { ...r, recommendationStatus: 'REJECTED' } : r)
        );
        showToast(`Slot recommendation ${recommendationId} rejected (offline update)`, 'success');
      }
    } catch (err) {
      showToast(err.message || 'Rejection failed', 'error');
    }
  };

  const counts = {
    products: products.length,
    locations: locations.length,
    demand: demand.length,
    recommendations: recommendations.length,
    routes: routes.length,
    replenishment: replenishment.length,
    pendingApproval: recommendations.filter(r => r.recommendationStatus === 'RECOMMENDED').length
  };

  return (
    <div className="dashboard-container">
      <Header />
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} counts={counts} />

      <main className="main-content">
        {loading ? (
          <div className="state-container">
            <div className="spinner"></div>
            <p>Loading CAP-12 Warehouse Management System...</p>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <WarehouseOverview
                analytics={analytics}
                routes={routes}
                recommendations={recommendations}
                replenishment={replenishment}
              />
            )}
            {activeTab === 'products' && <ProductMaster products={products} />}
            {activeTab === 'locations' && (
              <WarehouseLocations
                locations={locations}
                products={products}
                demand={demand}
                onVacateLocation={handleVacateLocation}
              />
            )}
            {activeTab === 'demand' && <DemandClassification demand={demand} affinityPairs={affinityPairs} />}
            {activeTab === 'recommendations' && (
              <SlotRecommendations
                recommendations={recommendations}
                onResetDemo={handleResetDemo}
                isResetting={isResetting}
              />
            )}
            {activeTab === 'pickpath' && <PickPathOptimization routes={routes} />}
            {activeTab === 'replenishment' && (
              <ReplenishmentAlerts
                replenishment={replenishment}
                products={products}
                locations={locations}
                stockLevels={stockLevels}
                onAdjustStock={handleAdjustStock}
              />
            )}
            {activeTab === 'approval' && (
              <SupervisorApproval
                recommendations={recommendations}
                onApprove={handleApprove}
                onReject={handleReject}
                onReEvaluate={handleReEvaluate}
                isReEvaluating={isReEvaluating}
                onResetDemo={handleResetDemo}
                isResetting={isResetting}
                toast={toast}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

