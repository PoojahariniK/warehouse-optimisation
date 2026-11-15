package com.cap12.warehouse.service;

import com.cap12.warehouse.model.RouteResult;
import com.cap12.warehouse.repository.RouteRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class RouteService {

    private final RouteRepository routeRepository;

    public RouteService(RouteRepository routeRepository) {
        this.routeRepository = routeRepository;
    }

    public List<RouteResult> getAllRoutes() {
        return routeRepository.findAll();
    }

    public Optional<RouteResult> getRouteByOrderId(String orderId) {
        return routeRepository.findByOrderId(orderId);
    }
}

