package com.cap12.warehouse.repository;

import com.cap12.warehouse.model.Product;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public class ProductRepository {

    private final JdbcTemplate jdbcTemplate;

    public ProductRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<Product> rowMapper = (rs, rowNum) -> new Product(
            rs.getString("SKU_ID"),
            rs.getString("PRODUCT_NAME"),
            rs.getString("CATEGORY"),
            (int) Math.round(rs.getDouble("REQUIRED_CAPACITY")),
            rs.getString("CURRENT_LOCATION"),
            rs.getString("HAZARD_CLASS")
    );

    public List<Product> findAll() {
        String sql = "SELECT SKU_ID, PRODUCT_NAME, CATEGORY, REQUIRED_CAPACITY, CURRENT_LOCATION, HAZARD_CLASS FROM PRODUCTS ORDER BY SKU_ID";
        return jdbcTemplate.query(sql, rowMapper);
    }

    public Optional<Product> findBySkuId(String skuId) {
        String sql = "SELECT SKU_ID, PRODUCT_NAME, CATEGORY, REQUIRED_CAPACITY, CURRENT_LOCATION, HAZARD_CLASS FROM PRODUCTS WHERE SKU_ID = ?";
        List<Product> results = jdbcTemplate.query(sql, rowMapper, skuId);
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    public int updateLocation(String skuId, String newLocation) {
        String sql = "UPDATE PRODUCTS SET CURRENT_LOCATION = ? WHERE SKU_ID = ?";
        return jdbcTemplate.update(sql, newLocation, skuId);
    }

    public Optional<Product> findByLocation(String locationId) {
        String sql = "SELECT SKU_ID, PRODUCT_NAME, CATEGORY, REQUIRED_CAPACITY, CURRENT_LOCATION, HAZARD_CLASS FROM PRODUCTS WHERE CURRENT_LOCATION = ?";
        List<Product> results = jdbcTemplate.query(sql, rowMapper, locationId);
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    public int unassignByLocation(String locationId) {
        String sql = "UPDATE PRODUCTS SET CURRENT_LOCATION = 'UNASSIGNED' WHERE CURRENT_LOCATION = ?";
        return jdbcTemplate.update(sql, locationId);
    }
}
