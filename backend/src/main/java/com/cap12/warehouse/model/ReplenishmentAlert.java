package com.cap12.warehouse.model;

public record ReplenishmentAlert(
    String skuId,
    String productName,
    int currentStock,
    int minimumStock,
    String stockStatus,
    String replenishmentRequired
) {}

