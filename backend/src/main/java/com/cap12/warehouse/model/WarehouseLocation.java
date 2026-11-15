package com.cap12.warehouse.model;

public record WarehouseLocation(
    String locationId,
    String aisle,
    int x,
    int y,
    int capacity,
    String status,
    String allowedCategory,
    String hazardAllowed
) {}
