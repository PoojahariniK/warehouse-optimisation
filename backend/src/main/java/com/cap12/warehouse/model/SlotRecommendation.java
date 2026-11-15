package com.cap12.warehouse.model;

public record SlotRecommendation(
    String recommendationId,
    String skuId,
    String productName,
    String demandClass,
    String currentLocation,
    String recommendedLocation,
    double distance,
    double distanceSaved,
    String recommendationStatus,
    String reason
) {}
