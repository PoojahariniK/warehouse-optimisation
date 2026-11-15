/**
 * Warehouse API Client using Axios
 * Connects React frontend to Spring Boot backend REST endpoints.
 */

const API_BASE_URL = (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_BASE_URL)
  ? process.env.REACT_APP_API_BASE_URL
  : 'http://localhost:8080/api';

// Create a lightweight wrapper that uses window.axios if present or standard fetch
async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  if (typeof window !== 'undefined' && window.axios) {
    try {
      const resp = await window.axios({
        url,
        method: options.method || 'GET',
        data: options.body ? JSON.parse(options.body) : undefined,
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
      });
      return resp.data;
    } catch (err) {
      if (err.response && err.response.data) {
        throw new Error(err.response.data.message || err.response.statusText);
      }
      throw err;
    }
  }

  // Fallback to fetch
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.message || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export const warehouseApi = {
  getProducts: () => request('/products'),
  getLocations: () => request('/locations'),
  vacateLocation: (locationId) => request(`/locations/${locationId}/vacate`, { method: 'POST' }),
  getDemand: () => request('/demand'),
  getSlotRecommendations: () => request('/slots/recommendations'),
  approveSlot: (recommendationId) => request(`/slots/approve/${recommendationId}`, { method: 'POST' }),
  rejectSlot: (recommendationId) => request(`/slots/reject/${recommendationId}`, { method: 'POST' }),
  reEvaluateSlots: () => request('/slots/re-evaluate', { method: 'POST' }),
  getRoute: (orderId) => request(`/routes/${orderId}`),
  getRouteComparison: (orderId) => request(`/routes/comparison/${orderId}`),
  getAllRoutes: () => request('/routes'),
  getReplenishmentAlerts: () => request('/replenishment'),
  getAnalytics: () => request('/analytics'),
  getAffinity: () => request('/affinity'),
  resetDemoState: () => request('/admin/reset', { method: 'POST' }),
};

export default warehouseApi;

