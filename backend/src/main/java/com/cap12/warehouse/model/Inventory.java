package com.cap12.warehouse.model;

public record Inventory(
    String skuId,
    int currentStock,
    int minimumStock
) {}

