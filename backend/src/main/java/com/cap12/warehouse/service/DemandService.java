package com.cap12.warehouse.service;

import com.cap12.warehouse.dto.DemandItemDto;
import com.cap12.warehouse.repository.DemandRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DemandService {

    private final DemandRepository demandRepository;

    public DemandService(DemandRepository demandRepository) {
        this.demandRepository = demandRepository;
    }

    public List<DemandItemDto> getDemandClassification() {
        return demandRepository.findDemandAnalysis();
    }
}

