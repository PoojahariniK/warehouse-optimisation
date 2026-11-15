package com.cap12.warehouse.controller;

import com.cap12.warehouse.service.AdminService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final AdminService adminService;

    public AdminController(AdminService adminService) {
        this.adminService = adminService;
    }

    @PostMapping("/reset")
    public ResponseEntity<Map<String, Object>> resetDemoState() {
        adminService.resetDatabase();
        return ResponseEntity.ok(Map.of(
            "success", true,
            "message", "Database successfully reset to baseline seed state."
        ));
    }
}

