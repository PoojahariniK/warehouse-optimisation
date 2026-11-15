package com.cap12.warehouse.model;

public record OrderLine(
    String orderLineId,
    String orderId,
    String orderDate,
    String skuId,
    int quantity
) {}

