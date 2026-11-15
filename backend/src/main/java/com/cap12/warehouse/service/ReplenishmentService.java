package com.cap12.warehouse.service;

import com.cap12.warehouse.model.ReplenishmentAlert;
import com.cap12.warehouse.repository.ReplenishmentRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ReplenishmentService {

    private final ReplenishmentRepository replenishmentRepository;

    public ReplenishmentService(ReplenishmentRepository replenishmentRepository) {
        this.replenishmentRepository = replenishmentRepository;
    }

    public List<ReplenishmentAlert> getReplenishmentAlerts() {
        return replenishmentRepository.findAll();
    }
}

