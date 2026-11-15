package com.cap12.warehouse.service;

import com.cap12.warehouse.model.Product;
import com.cap12.warehouse.model.SlotRecommendation;
import com.cap12.warehouse.model.WarehouseLocation;
import com.cap12.warehouse.repository.LocationRepository;
import com.cap12.warehouse.repository.ProductRepository;
import com.cap12.warehouse.repository.SlotRecommendationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class LocationService {

    private final LocationRepository locationRepository;
    private final ProductRepository productRepository;
    private final SlotRecommendationRepository recommendationRepository;
    private final SlotService slotService;

    public LocationService(
            LocationRepository locationRepository,
            ProductRepository productRepository,
            SlotRecommendationRepository recommendationRepository,
            SlotService slotService
    ) {
        this.locationRepository = locationRepository;
        this.productRepository = productRepository;
        this.recommendationRepository = recommendationRepository;
        this.slotService = slotService;
    }

    public List<WarehouseLocation> getAllLocations() {
        return locationRepository.findAll();
    }

    @Transactional
    public Map<String, Object> vacateLocation(String locationId) {
        WarehouseLocation loc = locationRepository.findByLocationId(locationId)
                .orElseThrow(() -> new IllegalArgumentException("Location not found: " + locationId));

        // 1. Find product occupying this location (if any) and unassign it
        Optional<Product> prodOpt = productRepository.findByLocation(locationId);
        String unassignedSku = null;
        String unassignedName = null;
        if (prodOpt.isPresent()) {
            Product p = prodOpt.get();
            unassignedSku = p.skuId();
            unassignedName = p.productName();
            productRepository.updateLocation(p.skuId(), "UNASSIGNED");
        }

        // 2. Mark warehouse location status as EMPTY in database
        locationRepository.updateStatus(locationId, "EMPTY");

        // 3. Update any slot recommendations referencing this location as current location
        recommendationRepository.findAll().stream()
                .filter(r -> locationId.equalsIgnoreCase(r.currentLocation()))
                .forEach(r -> {
                    SlotRecommendation updated = new SlotRecommendation(
                            r.recommendationId(),
                            r.skuId(),
                            r.productName(),
                            r.demandClass(),
                            "UNASSIGNED",
                            r.recommendedLocation(),
                            r.distance(),
                            r.distanceSaved(),
                            r.recommendationStatus(),
                            r.reason()
                    );
                    recommendationRepository.updateRecommendation(updated);
                });

        // 4. Reactive Evaluation: Generate proposal to occupy this vacated slot
        Optional<SlotRecommendation> newProposal = slotService.findBestCandidateForEmptyLocation(locationId, unassignedSku);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("locationId", locationId);
        response.put("unassignedSku", unassignedSku);
        response.put("unassignedProductName", unassignedName);
        if (newProposal.isPresent()) {
            SlotRecommendation r = newProposal.get();
            response.put("newRecommendationId", r.recommendationId());
            response.put("newCandidateSku", r.skuId());
            response.put("newCandidateName", r.productName());
            response.put("message", "Location " + locationId + " vacated to EMPTY in database. Product " + (unassignedName != null ? unassignedName : "") + " unassigned. Generated proposal " + r.recommendationId() + " (" + r.productName() + " -> " + locationId + ").");
        } else {
            response.put("message", "Location " + locationId + " vacated to EMPTY in database. Product " + (unassignedName != null ? unassignedName : "") + " unassigned.");
        }
        return response;
    }
}

