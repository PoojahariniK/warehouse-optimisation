package com.cap12.warehouse.controller;

import com.cap12.warehouse.model.OrderAffinity;
import com.cap12.warehouse.service.AffinityService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/affinity")
public class AffinityController {

    private final AffinityService affinityService;

    public AffinityController(AffinityService affinityService) {
        this.affinityService = affinityService;
    }

    @GetMapping
    public ResponseEntity<List<OrderAffinity>> getAllAffinityPairs() {
        return ResponseEntity.ok(affinityService.getAllAffinityPairs());
    }

    @GetMapping("/{skuId}")
    public ResponseEntity<List<OrderAffinity>> getAffinityForSku(@PathVariable String skuId) {
        return ResponseEntity.ok(affinityService.getAffinityForSku(skuId));
    }
}

