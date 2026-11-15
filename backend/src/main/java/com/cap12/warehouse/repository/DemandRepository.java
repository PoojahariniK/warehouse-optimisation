package com.cap12.warehouse.repository;

import com.cap12.warehouse.dto.DemandItemDto;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class DemandRepository {

    private final JdbcTemplate jdbcTemplate;

    public DemandRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<DemandItemDto> rowMapper = (rs, rowNum) -> new DemandItemDto(
            rs.getString("SKU_ID"),
            rs.getString("PRODUCT_NAME"),
            rs.getString("CATEGORY"),
            rs.getString("CURRENT_LOCATION"),
            (int) Math.round(rs.getDouble("ORDER_FREQUENCY")),
            (int) Math.round(rs.getDouble("TOTAL_QUANTITY")),
            rs.getString("DEMAND_CLASS"),
            rs.getDouble("DEMAND_CV"),
            rs.getString("VOLATILITY_CLASS")
    );

    public List<DemandItemDto> findDemandAnalysis() {
        String sql = """
            SELECT
                SKU_ID,
                PRODUCT_NAME,
                CATEGORY,
                CURRENT_LOCATION,
                ORDER_FREQUENCY,
                TOTAL_QUANTITY,
                DEMAND_CLASS,
                DEMAND_CV,
                VOLATILITY_CLASS
            FROM DEMAND_ANALYSIS
            ORDER BY ORDER_FREQUENCY DESC, TOTAL_QUANTITY DESC
        """;
        return jdbcTemplate.query(sql, rowMapper);
    }
}
