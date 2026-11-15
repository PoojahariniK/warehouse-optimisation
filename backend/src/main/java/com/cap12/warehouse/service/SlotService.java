package com.cap12.warehouse.service;

import com.cap12.warehouse.dto.ApprovalResponseDto;
import com.cap12.warehouse.dto.DemandItemDto;
import com.cap12.warehouse.model.OrderAffinity;
import com.cap12.warehouse.model.Product;
import com.cap12.warehouse.model.SlotRecommendation;
import com.cap12.warehouse.model.WarehouseLocation;
import com.cap12.warehouse.repository.AffinityRepository;
import com.cap12.warehouse.repository.DemandRepository;
import com.cap12.warehouse.repository.LocationRepository;
import com.cap12.warehouse.repository.ProductRepository;
import com.cap12.warehouse.repository.SlotRecommendationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class SlotService {

    private final SlotRecommendationRepository recommendationRepository;
    private final ProductRepository productRepository;
    private final LocationRepository locationRepository;
    private final DemandRepository demandRepository;
    private final AffinityRepository affinityRepository;

    public SlotService(
            SlotRecommendationRepository recommendationRepository,
            ProductRepository productRepository,
            LocationRepository locationRepository,
            DemandRepository demandRepository,
            AffinityRepository affinityRepository
    ) {
        this.recommendationRepository = recommendationRepository;
        this.productRepository = productRepository;
        this.locationRepository = locationRepository;
        this.demandRepository = demandRepository;
        this.affinityRepository = affinityRepository;
    }

    public List<SlotRecommendation> getRecommendations() {
        return recommendationRepository.findAll();
    }

    @Transactional
    public ApprovalResponseDto approveRecommendation(String recommendationId) {
        SlotRecommendation rec = recommendationRepository.findById(recommendationId)
                .orElseThrow(() -> new IllegalArgumentException("Recommendation not found with ID: " + recommendationId));

        if (!"RECOMMENDED".equalsIgnoreCase(rec.recommendationStatus())) {
            throw new IllegalStateException("Cannot approve recommendation in status: " + rec.recommendationStatus());
        }

        String targetLocId = rec.recommendedLocation();
        if (targetLocId == null || "NONE".equalsIgnoreCase(targetLocId)) {
            throw new IllegalStateException("Recommendation has no feasible target location to assign.");
        }

        // Validate target location availability
        WarehouseLocation targetLoc = locationRepository.findByLocationId(targetLocId)
                .orElseThrow(() -> new IllegalArgumentException("Target location not found: " + targetLocId));

        if (!"EMPTY".equalsIgnoreCase(targetLoc.status())) {
            throw new IllegalStateException("Conflict: Target location " + targetLocId + " is no longer EMPTY (Status: " + targetLoc.status() + "). Approval blocked to prevent duplicate assignment.");
        }

        Product product = productRepository.findBySkuId(rec.skuId())
                .orElseThrow(() -> new IllegalArgumentException("Product not found: " + rec.skuId()));

        // Validate warehouse constraints before assignment
        if (targetLoc.capacity() < product.requiredCapacity()) {
            throw new IllegalStateException("Capacity Violation: Target location " + targetLocId + " capacity (" + targetLoc.capacity() + ") is less than required (" + product.requiredCapacity() + ").");
        }

        if (!"ALL".equalsIgnoreCase(targetLoc.allowedCategory()) && !targetLoc.allowedCategory().equalsIgnoreCase(product.category())) {
            throw new IllegalStateException("Category Violation: Location " + targetLocId + " allows only " + targetLoc.allowedCategory() + ", but product is " + product.category() + ".");
        }

        String prodHazard = product.hazardClass() == null ? "GENERAL" : product.hazardClass().trim().toUpperCase();
        String locHazard = targetLoc.hazardAllowed() == null ? "GENERAL" : targetLoc.hazardAllowed().trim().toUpperCase();
        if (!"GENERAL".equalsIgnoreCase(prodHazard) && !"ALL".equalsIgnoreCase(locHazard) && !prodHazard.equalsIgnoreCase(locHazard)) {
            throw new IllegalStateException("Hazard Violation: Product " + product.skuId() + " (" + prodHazard + ") cannot be stored in location " + targetLocId + " (" + locHazard + ").");
        }

        String oldLocId = product.currentLocation();

        // 1. Update product's current location
        productRepository.updateLocation(product.skuId(), targetLocId);

        // 2. Mark old location as EMPTY (if previously assigned to a physical bin)
        if (oldLocId != null && !oldLocId.isBlank() && !"UNASSIGNED".equalsIgnoreCase(oldLocId)) {
            locationRepository.updateStatus(oldLocId, "EMPTY");
        }

        // 3. Mark new location as OCCUPIED
        locationRepository.updateStatus(targetLocId, "OCCUPIED");

        // 4. Record recommendation status as APPROVED
        recommendationRepository.updateStatus(recommendationId, "APPROVED");

        // 5. Reactive Re-Slotting: Check if vacated old location can be utilized by another candidate
        String vacatedInfo = "";
        if (oldLocId != null && !oldLocId.isBlank() && !"UNASSIGNED".equalsIgnoreCase(oldLocId)) {
            Optional<SlotRecommendation> replacement = findBestCandidateForEmptyLocation(oldLocId, product.skuId());
            if (replacement.isPresent()) {
                SlotRecommendation r = replacement.get();
                vacatedInfo = " Reactive Re-Slotting: Vacated slot " + oldLocId + " allocated to proposal " + r.recommendationId() + " (" + r.productName() + ", Saves " + r.distanceSaved() + " u).";
            }
        }

        return new ApprovalResponseDto(
                true,
                "Recommendation " + recommendationId + " approved. Product " + product.skuId() + " moved from " + oldLocId + " to " + targetLocId + "." + vacatedInfo,
                recommendationId,
                product.skuId(),
                oldLocId,
                targetLocId,
                "APPROVED"
        );
    }

    @Transactional
    public ApprovalResponseDto rejectRecommendation(String recommendationId) {
        SlotRecommendation rec = recommendationRepository.findById(recommendationId)
                .orElseThrow(() -> new IllegalArgumentException("Recommendation not found with ID: " + recommendationId));

        if ("APPROVED".equalsIgnoreCase(rec.recommendationStatus())) {
            throw new IllegalStateException("Cannot reject an already APPROVED recommendation.");
        }

        // 1. Permanently update recommendation status to REJECTED (original audit trail and reason intact)
        recommendationRepository.updateStatus(recommendationId, "REJECTED");

        // 2. Reactive Re-Slotting: Target location remains empty! Find next best constrained candidate SKU.
        String dynamicInfo = "";
        String targetLocId = rec.recommendedLocation();
        if (targetLocId != null && !"NONE".equalsIgnoreCase(targetLocId)) {
            // Explicitly pass rec.skuId() so the rejected SKU can NEVER be re-recommended for this slot!
            Optional<SlotRecommendation> replacement = findBestCandidateForEmptyLocation(targetLocId, rec.skuId());
            if (replacement.isPresent()) {
                SlotRecommendation rep = replacement.get();
                dynamicInfo = " Reactive Re-Slotting: Slot " + targetLocId + " remains empty; generated alternative proposal " +
                        rep.recommendationId() + " for " + rep.productName() + " (" + rep.skuId() + ", Saves " + rep.distanceSaved() + " u).";
            }
        }

        return new ApprovalResponseDto(
                true,
                "Recommendation " + recommendationId + " rejected. Product " + rec.skuId() + " remains at " + rec.currentLocation() + "." + dynamicInfo,
                recommendationId,
                rec.skuId(),
                rec.currentLocation(),
                rec.currentLocation(),
                "REJECTED"
        );
    }

    @Transactional
    public List<SlotRecommendation> reEvaluateEmptySlots() {
        List<WarehouseLocation> emptyLocations = locationRepository.findAll().stream()
                .filter(l -> "EMPTY".equalsIgnoreCase(l.status()))
                .sorted(Comparator.comparingDouble(l -> (double) (l.x() + l.y())))
                .toList();

        for (WarehouseLocation loc : emptyLocations) {
            findBestCandidateForEmptyLocation(loc.locationId(), null);
        }

        return recommendationRepository.findAll();
    }

    /**
     * Evaluates candidate SKUs for a specific empty warehouse slot.
     * Selects the highest priority product (Fast > Medium > Slow) that satisfies capacity, category,
     * hazard class, and achieves positive travel distance reduction.
     * Excludes any SKU that is currently RECOMMENDED, APPROVED, or REJECTED.
     */
    public Optional<SlotRecommendation> findBestCandidateForEmptyLocation(String emptyLocId, String excludedSkuId) {
        WarehouseLocation targetLoc = locationRepository.findByLocationId(emptyLocId).orElse(null);
        if (targetLoc == null || !"EMPTY".equalsIgnoreCase(targetLoc.status())) {
            return Optional.empty();
        }

        List<SlotRecommendation> allRecs = recommendationRepository.findAll();
        // Check if target location already has a pending RECOMMENDED proposal
        boolean alreadyPending = allRecs.stream()
                .anyMatch(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus())
                        && emptyLocId.equalsIgnoreCase(r.recommendedLocation()));
        if (alreadyPending) {
            return Optional.empty();
        }

        double targetDist = targetLoc.x() + targetLoc.y();
        List<Product> products = productRepository.findAll();
        List<WarehouseLocation> locations = locationRepository.findAll();
        Map<String, WarehouseLocation> locMap = locations.stream()
                .collect(Collectors.toMap(WarehouseLocation::locationId, l -> l, (a, b) -> a));

        List<DemandItemDto> demandList = demandRepository.findDemandAnalysis();
        Map<String, DemandItemDto> demandMap = demandList.stream()
                .collect(Collectors.toMap(DemandItemDto::skuId, d -> d, (a, b) -> a));

        // Candidates:
        // Exclude SKUs that:
        // 1. Have active pending RECOMMENDED proposal for a different location
        // 2. Are APPROVED
        Set<String> pendingOrApprovedSkus = allRecs.stream()
                .filter(r -> "RECOMMENDED".equalsIgnoreCase(r.recommendationStatus())
                        || "APPROVED".equalsIgnoreCase(r.recommendationStatus()))
                .map(SlotRecommendation::skuId)
                .collect(Collectors.toSet());

        // 3. Exclude SKUs explicitly REJECTED for this specific target slot
        Set<String> rejectedForThisLoc = allRecs.stream()
                .filter(r -> "REJECTED".equalsIgnoreCase(r.recommendationStatus())
                        && emptyLocId.equalsIgnoreCase(r.recommendedLocation()))
                .map(SlotRecommendation::skuId)
                .collect(Collectors.toSet());

        String allowedCat = targetLoc.allowedCategory() == null ? "ALL" : targetLoc.allowedCategory().trim().toUpperCase();
        String locHaz = targetLoc.hazardAllowed() == null ? "GENERAL" : targetLoc.hazardAllowed().trim().toUpperCase();

        record Candidate(Product product, DemandItemDto demand, double currentDist, double distSaved, int priority, boolean isUnassigned) {}
        List<Candidate> candidates = new ArrayList<>();

        for (Product p : products) {
            if (pendingOrApprovedSkus.contains(p.skuId())) {
                continue;
            }
            if (rejectedForThisLoc.contains(p.skuId())) {
                continue;
            }
            if (excludedSkuId != null && excludedSkuId.equalsIgnoreCase(p.skuId())) {
                continue;
            }
            if (emptyLocId.equalsIgnoreCase(p.currentLocation())) {
                continue;
            }

            boolean isUnassigned = (p.currentLocation() == null
                    || p.currentLocation().isBlank()
                    || "UNASSIGNED".equalsIgnoreCase(p.currentLocation()));

            WarehouseLocation currLoc = isUnassigned ? null : locMap.get(p.currentLocation());
            if (!isUnassigned && currLoc == null) {
                continue;
            }

            double currentDist;
            double distSaved;
            if (isUnassigned) {
                currentDist = 60.0;
                distSaved = Math.max(5.0, Math.round((currentDist - targetDist) * 100.0) / 100.0);
            } else {
                currentDist = currLoc.x() + currLoc.y();
                distSaved = Math.round((currentDist - targetDist) * 100.0) / 100.0;
                if (distSaved < 5.0) {
                    // Relocation must meaningfully save distance (>= 5 units)
                    continue;
                }
            }

            // Capacity constraint
            if (targetLoc.capacity() < p.requiredCapacity()) {
                continue;
            }

            // Category constraint
            String prodCat = p.category() == null ? "" : p.category().trim().toUpperCase();
            if (!"ALL".equals(allowedCat) && !allowedCat.equalsIgnoreCase(prodCat)) {
                continue;
            }

            // Hazard constraint
            String prodHaz = p.hazardClass() == null ? "GENERAL" : p.hazardClass().trim().toUpperCase();
            if (!"GENERAL".equals(prodHaz) && !"ALL".equals(locHaz) && !prodHaz.equalsIgnoreCase(locHaz)) {
                continue;
            }
            if (("HAZMAT_BATTERY".equals(locHaz) || "HAZMAT_FLAMMABLE".equals(locHaz)) && !prodHaz.equalsIgnoreCase(locHaz)) {
                continue;
            }

            DemandItemDto demandDto = demandMap.get(p.skuId());
            String dClass = demandDto != null ? demandDto.demandClass() : "Slow";
            int priority = 3;
            if ("Fast".equalsIgnoreCase(dClass)) priority = 1;
            else if ("Medium".equalsIgnoreCase(dClass)) priority = 2;

            candidates.add(new Candidate(p, demandDto, currentDist, distSaved, priority, isUnassigned));
        }

        if (candidates.isEmpty()) {
            return Optional.empty();
        }

        // Sort candidates: Priority asc (Fast first), distSaved desc, orderFrequency desc
        candidates.sort((c1, c2) -> {
            if (c1.priority != c2.priority) return Integer.compare(c1.priority, c2.priority);
            int distCmp = Double.compare(c2.distSaved, c1.distSaved);
            if (distCmp != 0) return distCmp;
            int freq1 = c1.demand != null ? c1.demand.orderFrequency() : 0;
            int freq2 = c2.demand != null ? c2.demand.orderFrequency() : 0;
            return Integer.compare(freq2, freq1);
        });

        Candidate best = candidates.get(0);
        Product p = best.product();
        String prodHaz = p.hazardClass() == null ? "GENERAL" : p.hazardClass().trim().toUpperCase();

        // Check if candidate has affinity co-occurrence partners
        List<OrderAffinity> affinities = affinityRepository.findBySku(p.skuId());
        String affinityNote = "";
        if (affinities != null && !affinities.isEmpty()) {
            OrderAffinity topAff = affinities.get(0);
            String partnerName = p.skuId().equalsIgnoreCase(topAff.skuA()) ? topAff.productB() : topAff.productA();
            String partnerSku = p.skuId().equalsIgnoreCase(topAff.skuA()) ? topAff.skuB() : topAff.skuA();
            affinityNote = String.format(" Co-ordered with %s (%s, %d orders).", partnerName, partnerSku, topAff.coOccurrenceCount());
        }

        String reason;
        if (best.isUnassigned()) {
            reason = String.format(
                    "Dynamic Re-Slotting: Unassigned product allocated to available empty slot %s (aisle %s, distance %.1f). Relocation saves ~%.1f travel units.%s Capacity (%d>=%d), category '%s', hazard '%s' compliant.",
                    targetLoc.locationId(),
                    targetLoc.aisle(),
                    targetDist,
                    best.distSaved(),
                    affinityNote,
                    targetLoc.capacity(),
                    p.requiredCapacity(),
                    targetLoc.allowedCategory(),
                    prodHaz
            );
        } else {
            reason = String.format(
                    "Dynamic Re-Slotting: Allocated to available empty slot %s. Relocation reduces dispatch distance from %.1f to %.1f (-%.1f units).%s Capacity (%d>=%d), category '%s', hazard '%s' compliant.",
                    targetLoc.locationId(),
                    best.currentDist(),
                    targetDist,
                    best.distSaved(),
                    affinityNote,
                    targetLoc.capacity(),
                    p.requiredCapacity(),
                    targetLoc.allowedCategory(),
                    prodHaz
            );
        }

        Optional<SlotRecommendation> existingRec = recommendationRepository.findBySkuId(p.skuId());
        SlotRecommendation resultRec;
        if (existingRec.isPresent()) {
            resultRec = new SlotRecommendation(
                    existingRec.get().recommendationId(),
                    p.skuId(),
                    p.productName(),
                    best.demand != null ? best.demand.demandClass() : "General",
                    p.currentLocation(),
                    targetLoc.locationId(),
                    targetDist,
                    best.distSaved(),
                    "RECOMMENDED",
                    reason
            );
            recommendationRepository.updateRecommendation(resultRec);
        } else {
            String newId = recommendationRepository.findNextRecommendationId();
            resultRec = new SlotRecommendation(
                    newId,
                    p.skuId(),
                    p.productName(),
                    best.demand != null ? best.demand.demandClass() : "General",
                    p.currentLocation(),
                    targetLoc.locationId(),
                    targetDist,
                    best.distSaved(),
                    "RECOMMENDED",
                    reason
            );
            recommendationRepository.insert(resultRec);
        }

        return Optional.of(resultRec);
    }

    public Optional<SlotRecommendation> findBestCandidateForEmptyLocation(String emptyLocId) {
        return findBestCandidateForEmptyLocation(emptyLocId, null);
    }
}
