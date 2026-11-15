package com.cap12.warehouse.service;

import com.cap12.warehouse.model.OrderAffinity;
import com.cap12.warehouse.repository.AffinityRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AffinityService {

    private final AffinityRepository affinityRepository;

    public AffinityService(AffinityRepository affinityRepository) {
        this.affinityRepository = affinityRepository;
    }

    public List<OrderAffinity> getAllAffinityPairs() {
        return affinityRepository.findAll();
    }

    public List<OrderAffinity> getAffinityForSku(String skuId) {
        return affinityRepository.findBySku(skuId);
    }
}

