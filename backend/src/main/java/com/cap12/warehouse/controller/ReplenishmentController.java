package com.cap12.warehouse.controller;

import com.cap12.warehouse.model.ReplenishmentAlert;
import com.cap12.warehouse.service.ReplenishmentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/replenishment")
public class ReplenishmentController {

    private final ReplenishmentService replenishmentService;

    public ReplenishmentController(ReplenishmentService replenishmentService) {
        this.replenishmentService = replenishmentService;
    }

    @GetMapping
    public ResponseEntity<List<ReplenishmentAlert>> getReplenishmentAlerts() {
        return ResponseEntity.ok(replenishmentService.getReplenishmentAlerts());
    }
}

