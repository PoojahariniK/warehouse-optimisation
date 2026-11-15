package com.cap12.warehouse.repository;

import com.cap12.warehouse.model.OrderAffinity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class AffinityRepository {

    private final JdbcTemplate jdbcTemplate;

    public AffinityRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<OrderAffinity> rowMapper = (rs, rowNum) -> new OrderAffinity(
            (int) Math.round(rs.getDouble("PAIR_ID")),
            rs.getString("SKU_A"),
            rs.getString("PRODUCT_A"),
            rs.getString("CATEGORY_A"),
            rs.getString("SKU_B"),
            rs.getString("PRODUCT_B"),
            rs.getString("CATEGORY_B"),
            (int) Math.round(rs.getDouble("CO_OCCURRENCE_COUNT")),
            (int) Math.round(rs.getDouble("ORDERS_A")),
            (int) Math.round(rs.getDouble("ORDERS_B")),
            rs.getDouble("AFFINITY_SCORE"),
            rs.getDouble("JACCARD_INDEX"),
            rs.getString("PAIR_LABEL")
    );

    public List<OrderAffinity> findAll() {
        String sql = """
            SELECT
                PAIR_ID, SKU_A, PRODUCT_A, CATEGORY_A,
                SKU_B, PRODUCT_B, CATEGORY_B,
                CO_OCCURRENCE_COUNT, ORDERS_A, ORDERS_B,
                AFFINITY_SCORE, JACCARD_INDEX, PAIR_LABEL
            FROM ORDER_AFFINITY
            ORDER BY CO_OCCURRENCE_COUNT DESC, AFFINITY_SCORE DESC
        """;
        return jdbcTemplate.query(sql, rowMapper);
    }

    public List<OrderAffinity> findBySku(String skuId) {
        String sql = """
            SELECT
                PAIR_ID, SKU_A, PRODUCT_A, CATEGORY_A,
                SKU_B, PRODUCT_B, CATEGORY_B,
                CO_OCCURRENCE_COUNT, ORDERS_A, ORDERS_B,
                AFFINITY_SCORE, JACCARD_INDEX, PAIR_LABEL
            FROM ORDER_AFFINITY
            WHERE SKU_A = ? OR SKU_B = ?
            ORDER BY CO_OCCURRENCE_COUNT DESC, AFFINITY_SCORE DESC
        """;
        return jdbcTemplate.query(sql, rowMapper, skuId, skuId);
    }
}

