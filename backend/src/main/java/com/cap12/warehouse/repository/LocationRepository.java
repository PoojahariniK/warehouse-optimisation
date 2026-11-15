package com.cap12.warehouse.repository;

import com.cap12.warehouse.model.WarehouseLocation;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public class LocationRepository {

    private final JdbcTemplate jdbcTemplate;

    public LocationRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<WarehouseLocation> rowMapper = (rs, rowNum) -> new WarehouseLocation(
            rs.getString("LOCATION_ID"),
            rs.getString("AISLE"),
            (int) Math.round(rs.getDouble("X")),
            (int) Math.round(rs.getDouble("Y")),
            (int) Math.round(rs.getDouble("CAPACITY")),
            rs.getString("STATUS"),
            rs.getString("ALLOWED_CATEGORY"),
            rs.getString("HAZARD_ALLOWED")
    );

    public List<WarehouseLocation> findAll() {
        String sql = "SELECT LOCATION_ID, AISLE, X, Y, CAPACITY, STATUS, ALLOWED_CATEGORY, HAZARD_ALLOWED FROM WAREHOUSE_LOCATIONS ORDER BY LOCATION_ID";
        return jdbcTemplate.query(sql, rowMapper);
    }

    public Optional<WarehouseLocation> findByLocationId(String locationId) {
        String sql = "SELECT LOCATION_ID, AISLE, X, Y, CAPACITY, STATUS, ALLOWED_CATEGORY, HAZARD_ALLOWED FROM WAREHOUSE_LOCATIONS WHERE LOCATION_ID = ?";
        List<WarehouseLocation> results = jdbcTemplate.query(sql, rowMapper, locationId);
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    public int updateStatus(String locationId, String status) {
        String sql = "UPDATE WAREHOUSE_LOCATIONS SET STATUS = ? WHERE LOCATION_ID = ?";
        return jdbcTemplate.update(sql, status, locationId);
    }
}
