package com.cap12.warehouse.model;

public record Product(
    String skuId,
    String productName,
    String category,
    int requiredCapacity,
    String currentLocation,
    String hazardClass
) {}
