package com.cap12.warehouse.controller;

import com.cap12.warehouse.model.RouteResult;
import com.cap12.warehouse.service.RouteService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/routes")
public class RouteController {

    private final RouteService routeService;

    public RouteController(RouteService routeService) {
        this.routeService = routeService;
    }

    @GetMapping
    public ResponseEntity<List<RouteResult>> getAllRoutes() {
        return ResponseEntity.ok(routeService.getAllRoutes());
    }

    @GetMapping("/{orderId}")
    public ResponseEntity<RouteResult> getRouteByOrderId(@PathVariable String orderId) {
        return routeService.getRouteByOrderId(orderId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/comparison/{orderId}")
    public ResponseEntity<RouteResult> getRouteComparison(@PathVariable String orderId) {
        return routeService.getRouteByOrderId(orderId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

