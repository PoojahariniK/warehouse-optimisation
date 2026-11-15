package com.cap12.warehouse.dto;

public record AnalyticsDto(
    int totalProducts,
    int totalLocations,
    int occupiedLocations,
    int emptyLocations,
    int fastProducts,
    int mediumProducts,
    int slowProducts,
    int totalOrders,
    double averageBaselineDistance,
    double averageRouteOnlyDistance,
    double averageSlotOnlyDistance,
    double averageOptimizedDistance,
    double totalDistanceSaved,
    double averageDistanceReductionPct,
    int improvedOrdersCount,
    int worseOrdersCount,
    int identicalOrdersCount,
    int replenishmentAlertsCount,
    int recommendedSlotsCount,
    int approvedSlotsCount,
    int rejectedSlotsCount
) {}
