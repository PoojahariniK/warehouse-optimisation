package com.cap12.warehouse.model;

public record OrderAffinity(
    int pairId,
    String skuA,
    String productA,
    String categoryA,
    String skuB,
    String productB,
    String categoryB,
    int coOccurrenceCount,
    int ordersA,
    int ordersB,
    double affinityScore,
    double jaccardIndex,
    String pairLabel
) {}

