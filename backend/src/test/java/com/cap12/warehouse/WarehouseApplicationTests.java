package com.cap12.warehouse;

import com.cap12.warehouse.dto.AnalyticsDto;
import com.cap12.warehouse.dto.ApprovalResponseDto;
import com.cap12.warehouse.dto.DemandItemDto;
import com.cap12.warehouse.model.OrderAffinity;
import com.cap12.warehouse.model.Product;
import com.cap12.warehouse.model.ReplenishmentAlert;
import com.cap12.warehouse.model.RouteResult;
import com.cap12.warehouse.model.SlotRecommendation;
import com.cap12.warehouse.service.AdminService;
import com.cap12.warehouse.service.AffinityService;
import com.cap12.warehouse.service.AnalyticsService;
import com.cap12.warehouse.service.DemandService;
import com.cap12.warehouse.service.ProductService;
import com.cap12.warehouse.service.ReplenishmentService;
import com.cap12.warehouse.service.RouteService;
import com.cap12.warehouse.service.SlotService;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class WarehouseApplicationTests {

    @Autowired
    private ProductService productService;

    @Autowired
    private DemandService demandService;

    @Autowired
    private SlotService slotService;

    @Autowired
    private RouteService routeService;

    @Autowired
    private ReplenishmentService replenishmentService;

    @Autowired
    private AnalyticsService analyticsService;

    @Autowired
    private AffinityService affinityService;

    @Autowired
    private AdminService adminService;

    @Test
    @Order(1)
    void contextLoads() {
        assertNotNull(productService);
        assertNotNull(slotService);
        assertNotNull(analyticsService);
    }

    @Test
    @Order(2)
    void testGetAllProducts() {
        List<Product> products = productService.getAllProducts();
        assertEquals(30, products.size(), "Should load exactly 30 products");
        assertTrue(products.stream().anyMatch(p -> "SKU001".equals(p.skuId())));
    }

    @Test
    @Order(3)
    void testDemandClassification() {
        List<DemandItemDto> demand = demandService.getDemandClassification();
        assertEquals(30, demand.size(), "Demand items count should be 30");

        long fastCount = demand.stream().filter(d -> "Fast".equalsIgnoreCase(d.demandClass())).count();
        long mediumCount = demand.stream().filter(d -> "Medium".equalsIgnoreCase(d.demandClass())).count();
        long slowCount = demand.stream().filter(d -> "Slow".equalsIgnoreCase(d.demandClass())).count();

        assertEquals(10, fastCount, "Should have 10 Fast SKUs");
        assertEquals(10, mediumCount, "Should have 10 Medium SKUs");
        assertEquals(10, slowCount, "Should have 10 Slow SKUs");
    }

    @Test
    @Order(4)
    void testGetSlotRecommendations() {
        List<SlotRecommendation> recs = slotService.getRecommendations();
        assertEquals(30, recs.size(), "Should have 30 slot recommendations");

        long recommended = recs.stream().filter(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus())).count();
        long noLocation = recs.stream().filter(r -> "NO_FEASIBLE_LOCATION".equalsIgnoreCase(r.recommendationStatus())).count();

        assertTrue(recommended > 0, "Should have recommended slots");
        assertTrue(noLocation > 0, "Should have products with NO_FEASIBLE_LOCATION");
    }

    @Test
    @Order(5)
    void testSupervisorApprovalTransaction() {
        // Find first RECOMMENDED item
        List<SlotRecommendation> recs = slotService.getRecommendations();
        SlotRecommendation rec = recs.stream()
                .filter(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus()))
                .findFirst()
                .orElseThrow();

        String recId = rec.recommendationId();
        String targetLoc = rec.recommendedLocation();

        // Execute approval
        ApprovalResponseDto response = slotService.approveRecommendation(recId);
        assertTrue(response.success());
        assertEquals("APPROVED", response.updatedStatus());
        assertEquals(targetLoc, response.assignedLocation());

        // Verify that trying to approve the same recommendation again throws IllegalStateException
        assertThrows(IllegalStateException.class, () -> slotService.approveRecommendation(recId));
    }

    @Test
    @Order(6)
    void testSupervisorRejection() {
        // Find a different RECOMMENDED item to reject
        List<SlotRecommendation> recs = slotService.getRecommendations();
        SlotRecommendation rec = recs.stream()
                .filter(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus()))
                .findFirst()
                .orElseThrow();

        String recId = rec.recommendationId();
        ApprovalResponseDto response = slotService.rejectRecommendation(recId);
        assertTrue(response.success());
        assertEquals("REJECTED", response.updatedStatus());
    }

    @Test
    @Order(7)
    void testRouteResults() {
        List<RouteResult> routes = routeService.getAllRoutes();
        assertEquals(50, routes.size(), "Should have 50 route evaluations");

        Optional<RouteResult> ord1 = routeService.getRouteByOrderId("ORD001");
        assertTrue(ord1.isPresent(), "ORD001 should be present");

        // Verify that suboptimal route case exists in database
        long worseCount = routes.stream().filter(r -> "WORSE".equalsIgnoreCase(r.routeStatus())).count();
        assertTrue(worseCount > 0, "Honest route evaluation must include orders where NN was worse");
    }

    @Test
    @Order(8)
    void testReplenishmentAlerts() {
        List<ReplenishmentAlert> alerts = replenishmentService.getReplenishmentAlerts();
        assertEquals(6, alerts.size(), "Should identify 6 SKUs requiring replenishment");
        assertTrue(alerts.stream().anyMatch(a -> "OUT_OF_STOCK".equalsIgnoreCase(a.stockStatus())));
    }

    @Test
    @Order(9)
    void testAnalyticsKpiSummary() {
        AnalyticsDto analytics = analyticsService.getWarehouseAnalytics();
        assertEquals(30, analytics.totalProducts());
        assertEquals(40, analytics.totalLocations());
        assertEquals(50, analytics.totalOrders());
        assertTrue(analytics.averageBaselineDistance() > 0);
        assertTrue(analytics.averageOptimizedDistance() > 0);
        assertTrue(analytics.averageDistanceReductionPct() > 0);
        assertTrue(analytics.worseOrdersCount() > 0);
        assertEquals(6, analytics.replenishmentAlertsCount());
    }

    @Test
    @Order(10)
    void testOrderAffinity() {
        List<OrderAffinity> pairs = affinityService.getAllAffinityPairs();
        assertFalse(pairs.isEmpty(), "Affinity pairs should be present in database");
        assertTrue(pairs.size() <= 25, "Top affinity pairs should be at most 25");

        OrderAffinity topPair = pairs.get(0);
        assertTrue(topPair.coOccurrenceCount() >= 2, "Top co-occurrence count should be >= 2");
        assertTrue(topPair.affinityScore() > 0, "Affinity score should be positive");
        assertNotNull(topPair.pairLabel());

        List<OrderAffinity> laptopAffinity = affinityService.getAffinityForSku("SKU001");
        assertFalse(laptopAffinity.isEmpty(), "SKU001 (Laptop) should have affinity partners");
    }

    @Test
    @Order(11)
    void testResetDatabase() {
        // First confirm that reset restores initial recommended state
        adminService.resetDatabase();

        List<SlotRecommendation> recs = slotService.getRecommendations();
        assertEquals(30, recs.size(), "Should restore all 30 recommendations");

        long recommendedCount = recs.stream().filter(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus())).count();
        assertTrue(recommendedCount > 0, "Should restore pending recommendations");

        long approvedCount = recs.stream().filter(r -> "APPROVED".equalsIgnoreCase(r.recommendationStatus())).count();
        assertEquals(0, approvedCount, "Approved count should be reset to 0");

        List<Product> products = productService.getAllProducts();
        assertEquals(30, products.size(), "Should have 30 products");
    }

    @Test
    @Order(12)
    void testReactiveReSlottingOnRejectionAndReEvaluate() {
        // Find REC001 (Laptop to A02)
        Optional<SlotRecommendation> rec001 = slotService.getRecommendations().stream()
                .filter(r -> "REC001".equals(r.recommendationId()))
                .findFirst();
        assertTrue(rec001.isPresent());

        // Reject REC001
        ApprovalResponseDto rejectResp = slotService.rejectRecommendation("REC001");
        assertTrue(rejectResp.success());
        assertEquals("REJECTED", rejectResp.updatedStatus());
        assertTrue(rejectResp.message().contains("Reactive Re-Slotting"));

        // A02 was kept empty, so a replacement recommendation targeting A02 should now be RECOMMENDED
        List<SlotRecommendation> updatedRecs = slotService.getRecommendations();
        boolean hasReplacementForA02 = updatedRecs.stream()
                .anyMatch(r -> "A02".equalsIgnoreCase(r.recommendedLocation()) && "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus()));
        assertTrue(hasReplacementForA02, "Reactive slotting must assign empty slot A02 to an alternative candidate SKU");

        // Re-evaluate empty slots
        List<SlotRecommendation> reEvaluated = slotService.reEvaluateEmptySlots();
        assertNotNull(reEvaluated);
        assertFalse(reEvaluated.isEmpty());
    }

    @Test
    @Order(13)
    void testMultipleConsecutiveRejectionsAdvanceCandidates() {
        // Reset database to ensure clean state
        adminService.resetDatabase();

        // Reject REC001 (Laptop to A02)
        ApprovalResponseDto resp1 = slotService.rejectRecommendation("REC001");
        assertTrue(resp1.success());
        assertEquals("REJECTED", resp1.updatedStatus());

        // A02 should have replacement candidate (e.g. Webcam REC007)
        List<SlotRecommendation> recs1 = slotService.getRecommendations();
        SlotRecommendation rep1 = recs1.stream()
                .filter(r -> "A02".equalsIgnoreCase(r.recommendedLocation()) && "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus()))
                .findFirst()
                .orElseThrow();
        assertEquals("SKU005", rep1.skuId(), "First replacement for A02 should be Webcam SKU005");

        // Now reject this replacement as well!
        ApprovalResponseDto resp2 = slotService.rejectRecommendation(rep1.recommendationId());
        assertTrue(resp2.success());
        assertEquals("REJECTED", resp2.updatedStatus());

        // A02 should advance to the NEXT candidate (e.g. Smartphone SKU003), NOT pick SKU005 or SKU001 again!
        List<SlotRecommendation> recs2 = slotService.getRecommendations();
        SlotRecommendation rep2 = recs2.stream()
                .filter(r -> "A02".equalsIgnoreCase(r.recommendedLocation()) && "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus()))
                .findFirst()
                .orElseThrow();
        assertNotEquals("SKU001", rep2.skuId(), "Must not re-pick SKU001");
        assertNotEquals("SKU005", rep2.skuId(), "Must not re-pick SKU005");
        assertEquals("SKU003", rep2.skuId(), "Second replacement should advance to Smartphone SKU003");

        // Reset back to baseline seed
        adminService.resetDatabase();
    }
}

