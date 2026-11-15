package com.cap12.warehouse.controller;

import com.cap12.warehouse.model.WarehouseLocation;
import com.cap12.warehouse.service.LocationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/locations")
public class LocationController {

    private final LocationService locationService;

    public LocationController(LocationService locationService) {
        this.locationService = locationService;
    }

    @GetMapping
    public ResponseEntity<List<WarehouseLocation>> getLocations() {
        return ResponseEntity.ok(locationService.getAllLocations());
    }

    @PostMapping("/{locationId}/vacate")
    public ResponseEntity<Map<String, Object>> vacateLocation(@PathVariable String locationId) {
        return ResponseEntity.ok(locationService.vacateLocation(locationId));
    }
}

