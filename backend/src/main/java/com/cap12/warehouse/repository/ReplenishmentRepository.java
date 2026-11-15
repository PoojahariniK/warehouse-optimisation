package com.cap12.warehouse.repository;

import com.cap12.warehouse.model.ReplenishmentAlert;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class ReplenishmentRepository {

    private final JdbcTemplate jdbcTemplate;

    public ReplenishmentRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<ReplenishmentAlert> rowMapper = (rs, rowNum) -> new ReplenishmentAlert(
            rs.getString("SKU_ID"),
            rs.getString("PRODUCT_NAME"),
            (int) Math.round(rs.getDouble("CURRENT_STOCK")),
            (int) Math.round(rs.getDouble("MINIMUM_STOCK")),
            rs.getString("STOCK_STATUS"),
            rs.getString("REPLENISHMENT_REQUIRED")
    );

    public List<ReplenishmentAlert> findAll() {
        String sql = "SELECT SKU_ID, PRODUCT_NAME, CURRENT_STOCK, MINIMUM_STOCK, STOCK_STATUS, REPLENISHMENT_REQUIRED " +
                     "FROM REPLENISHMENT_ALERTS ORDER BY (MINIMUM_STOCK - CURRENT_STOCK) DESC";
        return jdbcTemplate.query(sql, rowMapper);
    }
}

