package com.cap12.warehouse.dto;

public record ApprovalResponseDto(
    boolean success,
    String message,
    String recommendationId,
    String skuId,
    String previousLocation,
    String assignedLocation,
    String updatedStatus
) {}

