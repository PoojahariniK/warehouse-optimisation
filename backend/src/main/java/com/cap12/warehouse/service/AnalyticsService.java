package com.cap12.warehouse.service;

import com.cap12.warehouse.dto.AnalyticsDto;
import com.cap12.warehouse.dto.DemandItemDto;
import com.cap12.warehouse.model.ReplenishmentAlert;
import com.cap12.warehouse.model.RouteResult;
import com.cap12.warehouse.model.SlotRecommendation;
import com.cap12.warehouse.model.WarehouseLocation;
import com.cap12.warehouse.repository.*;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AnalyticsService {

    private final ProductRepository productRepository;
    private final LocationRepository locationRepository;
    private final DemandRepository demandRepository;
    private final RouteRepository routeRepository;
    private final SlotRecommendationRepository recommendationRepository;
    private final ReplenishmentRepository replenishmentRepository;

    public AnalyticsService(
            ProductRepository productRepository,
            LocationRepository locationRepository,
            DemandRepository demandRepository,
            RouteRepository routeRepository,
            SlotRecommendationRepository recommendationRepository,
            ReplenishmentRepository replenishmentRepository
    ) {
        this.productRepository = productRepository;
        this.locationRepository = locationRepository;
        this.demandRepository = demandRepository;
        this.routeRepository = routeRepository;
        this.recommendationRepository = recommendationRepository;
        this.replenishmentRepository = replenishmentRepository;
    }

    public AnalyticsDto getWarehouseAnalytics() {
        int totalProducts = productRepository.findAll().size();

        List<WarehouseLocation> locations = locationRepository.findAll();
        int totalLocations = locations.size();
        int occupiedLocations = (int) locations.stream().filter(l -> "OCCUPIED".equalsIgnoreCase(l.status())).count();
        int emptyLocations = (int) locations.stream().filter(l -> "EMPTY".equalsIgnoreCase(l.status())).count();

        List<DemandItemDto> demand = demandRepository.findDemandAnalysis();
        int fast = (int) demand.stream().filter(d -> "Fast".equalsIgnoreCase(d.demandClass())).count();
        int medium = (int) demand.stream().filter(d -> "Medium".equalsIgnoreCase(d.demandClass())).count();
        int slow = (int) demand.stream().filter(d -> "Slow".equalsIgnoreCase(d.demandClass())).count();

        List<RouteResult> routes = routeRepository.findAll();
        int totalOrders = routes.size();

        double avgBaseline = routes.isEmpty() ? 0.0 :
                Math.round(routes.stream().mapToDouble(RouteResult::baselineDistance).average().orElse(0.0) * 100.0) / 100.0;
        double avgRouteOnly = routes.isEmpty() ? 0.0 :
                Math.round(routes.stream().mapToDouble(RouteResult::routeOnlyDistance).average().orElse(0.0) * 100.0) / 100.0;
        double avgSlotOnly = routes.isEmpty() ? 0.0 :
                Math.round(routes.stream().mapToDouble(RouteResult::slotOnlyDistance).average().orElse(0.0) * 100.0) / 100.0;
        double avgOptimized = routes.isEmpty() ? 0.0 :
                Math.round(routes.stream().mapToDouble(RouteResult::optimizedDistance).average().orElse(0.0) * 100.0) / 100.0;
        double totalSaved = routes.isEmpty() ? 0.0 :
                Math.round(routes.stream().mapToDouble(RouteResult::distanceSaved).sum() * 100.0) / 100.0;
        double avgReductionPct = routes.isEmpty() ? 0.0 :
                Math.round(routes.stream().mapToDouble(RouteResult::pctDistanceReduction).average().orElse(0.0) * 100.0) / 100.0;

        int improved = (int) routes.stream().filter(r -> "IMPROVED".equalsIgnoreCase(r.routeStatus())).count();
        int worse = (int) routes.stream().filter(r -> "WORSE".equalsIgnoreCase(r.routeStatus())).count();
        int identical = (int) routes.stream().filter(r -> "IDENTICAL".equalsIgnoreCase(r.routeStatus())).count();

        List<ReplenishmentAlert> alerts = replenishmentRepository.findAll();
        int replenishmentCount = alerts.size();

        List<SlotRecommendation> recs = recommendationRepository.findAll();
        int recommendedCount = (int) recs.stream().filter(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus())).count();
        int approvedCount = (int) recs.stream().filter(r -> "APPROVED".equalsIgnoreCase(r.recommendationStatus())).count();
        int rejectedCount = (int) recs.stream().filter(r -> "REJECTED".equalsIgnoreCase(r.recommendationStatus())).count();

        return new AnalyticsDto(
                totalProducts,
                totalLocations,
                occupiedLocations,
                emptyLocations,
                fast,
                medium,
                slow,
                totalOrders,
                avgBaseline,
                avgRouteOnly,
                avgSlotOnly,
                avgOptimized,
                totalSaved,
                avgReductionPct,
                improved,
                worse,
                identical,
                replenishmentCount,
                recommendedCount,
                approvedCount,
                rejectedCount
        );
    }
}
