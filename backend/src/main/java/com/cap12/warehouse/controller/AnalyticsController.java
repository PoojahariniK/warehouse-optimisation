package com.cap12.warehouse.controller;

import com.cap12.warehouse.dto.AnalyticsDto;
import com.cap12.warehouse.service.AnalyticsService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/analytics")
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    public AnalyticsController(AnalyticsService analyticsService) {
        this.analyticsService = analyticsService;
    }

    @GetMapping
    public ResponseEntity<AnalyticsDto> getWarehouseAnalytics() {
        return ResponseEntity.ok(analyticsService.getWarehouseAnalytics());
    }
}

