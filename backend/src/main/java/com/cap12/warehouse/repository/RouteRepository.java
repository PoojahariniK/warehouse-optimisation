package com.cap12.warehouse.repository;

import com.cap12.warehouse.model.RouteResult;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public class RouteRepository {

    private final JdbcTemplate jdbcTemplate;

    public RouteRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<RouteResult> rowMapper = (rs, rowNum) -> new RouteResult(
            rs.getString("ORDER_ID"),
            rs.getString("BASELINE_ROUTE_SEQUENCE"),
            rs.getString("OPTIMIZED_ROUTE_SEQUENCE"),
            rs.getDouble("BASELINE_DISTANCE"),
            rs.getDouble("ROUTE_ONLY_DISTANCE"),
            rs.getDouble("SLOT_ONLY_DISTANCE"),
            rs.getDouble("OPTIMIZED_DISTANCE"),
            rs.getDouble("DISTANCE_SAVED"),
            rs.getDouble("PCT_DISTANCE_REDUCTION"),
            rs.getDouble("BASELINE_TIME_SEC"),
            rs.getDouble("OPTIMIZED_TIME_SEC"),
            rs.getDouble("TIME_SAVED_SEC"),
            rs.getString("ROUTE_STATUS"),
            rs.getString("NOTES")
    );

    public List<RouteResult> findAll() {
        String sql = "SELECT ORDER_ID, BASELINE_ROUTE_SEQUENCE, OPTIMIZED_ROUTE_SEQUENCE, BASELINE_DISTANCE, " +
                     "ROUTE_ONLY_DISTANCE, SLOT_ONLY_DISTANCE, OPTIMIZED_DISTANCE, DISTANCE_SAVED, PCT_DISTANCE_REDUCTION, BASELINE_TIME_SEC, " +
                     "OPTIMIZED_TIME_SEC, TIME_SAVED_SEC, ROUTE_STATUS, NOTES " +
                     "FROM ROUTE_RESULTS ORDER BY ORDER_ID";
        return jdbcTemplate.query(sql, rowMapper);
    }

    public Optional<RouteResult> findByOrderId(String orderId) {
        String sql = "SELECT ORDER_ID, BASELINE_ROUTE_SEQUENCE, OPTIMIZED_ROUTE_SEQUENCE, BASELINE_DISTANCE, " +
                     "ROUTE_ONLY_DISTANCE, SLOT_ONLY_DISTANCE, OPTIMIZED_DISTANCE, DISTANCE_SAVED, PCT_DISTANCE_REDUCTION, BASELINE_TIME_SEC, " +
                     "OPTIMIZED_TIME_SEC, TIME_SAVED_SEC, ROUTE_STATUS, NOTES " +
                     "FROM ROUTE_RESULTS WHERE ORDER_ID = ?";
        List<RouteResult> results = jdbcTemplate.query(sql, rowMapper, orderId);
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }
}
