package com.cap12.warehouse.controller;

import com.cap12.warehouse.dto.DemandItemDto;
import com.cap12.warehouse.service.DemandService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/demand")
public class DemandController {

    private final DemandService demandService;

    public DemandController(DemandService demandService) {
        this.demandService = demandService;
    }

    @GetMapping
    public ResponseEntity<List<DemandItemDto>> getDemandClassification() {
        return ResponseEntity.ok(demandService.getDemandClassification());
    }
}

