package com.cap12.warehouse;

import com.cap12.warehouse.controller.*;
import com.cap12.warehouse.dto.AnalyticsDto;
import com.cap12.warehouse.dto.ApprovalResponseDto;
import com.cap12.warehouse.dto.DemandItemDto;
import com.cap12.warehouse.model.*;
import org.springframework.boot.Banner;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.http.ResponseEntity;

import java.util.List;

/**
 * Programmatic verification runner for all Spring Boot Controllers, Services, and Repositories.
 * Runs inside standard sandbox without requiring physical network socket binding.
 */
public class BackendVerifier {

    public static void main(String[] args) {
        System.out.println("======================================================================");
        System.out.println("STARTING SPRING BOOT REST API VERIFICATION SUITE");
        System.out.println("======================================================================");

        ConfigurableApplicationContext context = new SpringApplicationBuilder(WarehouseApplication.class)
                .web(WebApplicationType.NONE) // Non-web mode avoids Windows sandbox SocketException
                .bannerMode(Banner.Mode.OFF)
                .run(args);

        try {
            ProductController productController = context.getBean(ProductController.class);
            LocationController locationController = context.getBean(LocationController.class);
            DemandController demandController = context.getBean(DemandController.class);
            SlotController slotController = context.getBean(SlotController.class);
            RouteController routeController = context.getBean(RouteController.class);
            ReplenishmentController replenishmentController = context.getBean(ReplenishmentController.class);
            AnalyticsController analyticsController = context.getBean(AnalyticsController.class);

            // 1. GET /api/products
            System.out.println("\n--- 1. Testing GET /api/products ---");
            ResponseEntity<List<Product>> prodResp = productController.getProducts();
            List<Product> products = prodResp.getBody();
            if (products == null || products.size() != 30) {
                throw new AssertionError("Expected 30 products, got " + (products == null ? 0 : products.size()));
            }
            System.out.println("PASSED: Retrieved " + products.size() + " products. First: " + products.get(0));

            // 2. GET /api/locations
            System.out.println("\n--- 2. Testing GET /api/locations ---");
            ResponseEntity<List<WarehouseLocation>> locResp = locationController.getLocations();
            List<WarehouseLocation> locations = locResp.getBody();
            if (locations == null || locations.size() != 40) {
                throw new AssertionError("Expected 40 locations, got " + (locations == null ? 0 : locations.size()));
            }
            long emptyCount = locations.stream().filter(l -> "EMPTY".equalsIgnoreCase(l.status())).count();
            System.out.println("PASSED: Retrieved " + locations.size() + " locations (" + emptyCount + " EMPTY).");

            // 3. GET /api/demand
            System.out.println("\n--- 3. Testing GET /api/demand ---");
            ResponseEntity<List<DemandItemDto>> demandResp = demandController.getDemandClassification();
            List<DemandItemDto> demand = demandResp.getBody();
            if (demand == null || demand.size() != 30) {
                throw new AssertionError("Expected 30 demand classifications, got " + (demand == null ? 0 : demand.size()));
            }
            long fastCount = demand.stream().filter(d -> "Fast".equalsIgnoreCase(d.demandClass())).count();
            long medCount = demand.stream().filter(d -> "Medium".equalsIgnoreCase(d.demandClass())).count();
            long slowCount = demand.stream().filter(d -> "Slow".equalsIgnoreCase(d.demandClass())).count();
            System.out.println("PASSED: Demand counts -> Fast: " + fastCount + ", Medium: " + medCount + ", Slow: " + slowCount);

            // 4. GET /api/slots/recommendations
            System.out.println("\n--- 4. Testing GET /api/slots/recommendations ---");
            ResponseEntity<List<SlotRecommendation>> recsResp = slotController.getRecommendations();
            List<SlotRecommendation> recs = recsResp.getBody();
            if (recs == null || recs.size() != 30) {
                throw new AssertionError("Expected 30 recommendations, got " + (recs == null ? 0 : recs.size()));
            }
            long recommendedCount = recs.stream().filter(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus())).count();
            long noFeasibleCount = recs.stream().filter(r -> "NO_FEASIBLE_LOCATION".equalsIgnoreCase(r.recommendationStatus())).count();
            System.out.println("PASSED: Recommendations -> RECOMMENDED: " + recommendedCount + ", NO_FEASIBLE_LOCATION: " + noFeasibleCount);

            // 5. POST /api/slots/approve/{id}
            System.out.println("\n--- 5. Testing POST /api/slots/approve/REC001 ---");
            ResponseEntity<ApprovalResponseDto> approveResp = slotController.approveRecommendation("REC001");
            ApprovalResponseDto approveDto = approveResp.getBody();
            if (approveDto == null || !approveDto.success() || !"APPROVED".equals(approveDto.updatedStatus())) {
                throw new AssertionError("Failed to approve REC001");
            }
            System.out.println("PASSED: " + approveDto.message());

            // Test conflict: duplicate approval must be rejected
            try {
                slotController.approveRecommendation("REC001");
                throw new AssertionError("Expected duplicate approval to fail, but it succeeded!");
            } catch (IllegalStateException ex) {
                System.out.println("PASSED: Duplicate approval prevented -> " + ex.getMessage());
            }

            // 6. POST /api/slots/reject/{id}
            System.out.println("\n--- 6. Testing POST /api/slots/reject/REC002 ---");
            ResponseEntity<ApprovalResponseDto> rejectResp = slotController.rejectRecommendation("REC002");
            ApprovalResponseDto rejectDto = rejectResp.getBody();
            if (rejectDto == null || !rejectDto.success() || !"REJECTED".equals(rejectDto.updatedStatus())) {
                throw new AssertionError("Failed to reject REC002");
            }
            System.out.println("PASSED: " + rejectDto.message());

            // 7. GET /api/routes/{orderId}
            System.out.println("\n--- 7. Testing GET /api/routes/ORD001 ---");
            ResponseEntity<RouteResult> routeResp = routeController.getRouteByOrderId("ORD001");
            RouteResult route = routeResp.getBody();
            if (route == null) {
                throw new AssertionError("Route ORD001 not found");
            }
            System.out.println("PASSED: ORD001 -> Baseline: " + route.baselineDistance() + ", Optimized: " + route.optimizedDistance());

            // 8. GET /api/routes/comparison/{orderId}
            System.out.println("\n--- 8. Testing GET /api/routes/comparison/ORD001 ---");
            ResponseEntity<RouteResult> compResp = routeController.getRouteComparison("ORD001");
            RouteResult comp = compResp.getBody();
            if (comp == null) {
                throw new AssertionError("Route comparison for ORD001 not found");
            }
            System.out.println("PASSED: Distance Saved: " + comp.distanceSaved() + " (" + comp.pctDistanceReduction() + "%)");

            // 9. GET /api/replenishment
            System.out.println("\n--- 9. Testing GET /api/replenishment ---");
            ResponseEntity<List<ReplenishmentAlert>> repResp = replenishmentController.getReplenishmentAlerts();
            List<ReplenishmentAlert> alerts = repResp.getBody();
            if (alerts == null || alerts.size() != 6) {
                throw new AssertionError("Expected 6 replenishment alerts, got " + (alerts == null ? 0 : alerts.size()));
            }
            System.out.println("PASSED: " + alerts.size() + " replenishment alerts identified. Critical item: " + alerts.get(0));

            // 10. GET /api/analytics
            System.out.println("\n--- 10. Testing GET /api/analytics ---");
            ResponseEntity<AnalyticsDto> analyticsResp = analyticsController.getWarehouseAnalytics();
            AnalyticsDto kpis = analyticsResp.getBody();
            if (kpis == null) {
                throw new AssertionError("Failed to calculate warehouse analytics");
            }
            System.out.println("PASSED: Analytics KPIs:");
            System.out.println("  - Total Products: " + kpis.totalProducts());
            System.out.println("  - Total Locations: " + kpis.totalLocations() + " (Occupied: " + kpis.occupiedLocations() + ", Empty: " + kpis.emptyLocations() + ")");
            System.out.println("  - Total Orders: " + kpis.totalOrders());
            System.out.println("  - Avg Baseline Distance: " + kpis.averageBaselineDistance());
            System.out.println("  - Avg Optimized Distance: " + kpis.averageOptimizedDistance());
            System.out.println("  - Total Distance Saved: " + kpis.totalDistanceSaved());
            System.out.println("  - Distance Reduction: " + kpis.averageDistanceReductionPct() + "%");
            System.out.println("  - Orders Improved: " + kpis.improvedOrdersCount() + ", Worse: " + kpis.worseOrdersCount());
            System.out.println("  - Approved Slots: " + kpis.approvedSlotsCount() + ", Rejected Slots: " + kpis.rejectedSlotsCount());

            System.out.println("\n======================================================================");
            System.out.println("ALL 10 SPRING BOOT REST APIS VERIFIED AND WORKING 100%!");
            System.out.println("======================================================================");

        } finally {
            context.close();
        }
    }
}

