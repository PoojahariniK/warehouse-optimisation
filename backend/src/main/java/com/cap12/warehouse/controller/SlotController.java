package com.cap12.warehouse.controller;

import com.cap12.warehouse.dto.ApprovalResponseDto;
import com.cap12.warehouse.model.SlotRecommendation;
import com.cap12.warehouse.service.SlotService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/slots")
public class SlotController {

    private final SlotService slotService;

    public SlotController(SlotService slotService) {
        this.slotService = slotService;
    }

    @GetMapping("/recommendations")
    public ResponseEntity<List<SlotRecommendation>> getRecommendations() {
        return ResponseEntity.ok(slotService.getRecommendations());
    }

    @PostMapping("/approve/{recommendationId}")
    public ResponseEntity<ApprovalResponseDto> approveRecommendation(@PathVariable String recommendationId) {
        ApprovalResponseDto response = slotService.approveRecommendation(recommendationId);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/reject/{recommendationId}")
    public ResponseEntity<ApprovalResponseDto> rejectRecommendation(@PathVariable String recommendationId) {
        ApprovalResponseDto response = slotService.rejectRecommendation(recommendationId);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/re-evaluate")
    public ResponseEntity<List<SlotRecommendation>> reEvaluateEmptySlots() {
        return ResponseEntity.ok(slotService.reEvaluateEmptySlots());
    }
}

