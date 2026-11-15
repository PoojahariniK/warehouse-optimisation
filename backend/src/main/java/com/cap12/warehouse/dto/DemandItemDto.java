package com.cap12.warehouse.dto;

public record DemandItemDto(
    String skuId,
    String productName,
    String category,
    String currentLocation,
    int orderFrequency,
    int totalQuantity,
    String demandClass,
    double demandCv,
    String volatilityClass
) {}
