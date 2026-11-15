package com.cap12.warehouse.repository;

import com.cap12.warehouse.model.SlotRecommendation;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public class SlotRecommendationRepository {

    private final JdbcTemplate jdbcTemplate;

    public SlotRecommendationRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<SlotRecommendation> rowMapper = (rs, rowNum) -> new SlotRecommendation(
            rs.getString("RECOMMENDATION_ID"),
            rs.getString("SKU_ID"),
            rs.getString("PRODUCT_NAME"),
            rs.getString("DEMAND_CLASS"),
            rs.getString("CURRENT_LOCATION"),
            rs.getString("RECOMMENDED_LOCATION"),
            rs.getDouble("DISTANCE"),
            rs.getDouble("DISTANCE_SAVED"),
            rs.getString("RECOMMENDATION_STATUS"),
            rs.getString("REASON")
    );

    public List<SlotRecommendation> findAll() {
        String sql = "SELECT RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION, " +
                     "RECOMMENDED_LOCATION, DISTANCE, DISTANCE_SAVED, RECOMMENDATION_STATUS, REASON " +
                     "FROM SLOT_RECOMMENDATIONS ORDER BY RECOMMENDATION_ID";
        return jdbcTemplate.query(sql, rowMapper);
    }

    public Optional<SlotRecommendation> findById(String recommendationId) {
        String sql = "SELECT RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION, " +
                     "RECOMMENDED_LOCATION, DISTANCE, DISTANCE_SAVED, RECOMMENDATION_STATUS, REASON " +
                     "FROM SLOT_RECOMMENDATIONS WHERE RECOMMENDATION_ID = ?";
        List<SlotRecommendation> results = jdbcTemplate.query(sql, rowMapper, recommendationId);
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    public int updateStatus(String recommendationId, String newStatus) {
        String sql = "UPDATE SLOT_RECOMMENDATIONS SET RECOMMENDATION_STATUS = ?, UPDATED_AT = CURRENT_TIMESTAMP WHERE RECOMMENDATION_ID = ?";
        return jdbcTemplate.update(sql, newStatus, recommendationId);
    }

    public Optional<SlotRecommendation> findBySkuId(String skuId) {
        String sql = "SELECT RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION, " +
                     "RECOMMENDED_LOCATION, DISTANCE, DISTANCE_SAVED, RECOMMENDATION_STATUS, REASON " +
                     "FROM SLOT_RECOMMENDATIONS WHERE SKU_ID = ?";
        List<SlotRecommendation> results = jdbcTemplate.query(sql, rowMapper, skuId);
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    public int updateRecommendation(SlotRecommendation rec) {
        String sql = "UPDATE SLOT_RECOMMENDATIONS SET SKU_ID = ?, PRODUCT_NAME = ?, DEMAND_CLASS = ?, " +
                     "CURRENT_LOCATION = ?, RECOMMENDED_LOCATION = ?, DISTANCE = ?, DISTANCE_SAVED = ?, " +
                     "RECOMMENDATION_STATUS = ?, REASON = ?, UPDATED_AT = CURRENT_TIMESTAMP WHERE RECOMMENDATION_ID = ?";
        return jdbcTemplate.update(sql,
                rec.skuId(),
                rec.productName(),
                rec.demandClass(),
                rec.currentLocation(),
                rec.recommendedLocation(),
                rec.distance(),
                rec.distanceSaved(),
                rec.recommendationStatus(),
                rec.reason(),
                rec.recommendationId()
        );
    }

    public int insert(SlotRecommendation rec) {
        String sql = "INSERT INTO SLOT_RECOMMENDATIONS (RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, " +
                     "CURRENT_LOCATION, RECOMMENDED_LOCATION, DISTANCE, DISTANCE_SAVED, RECOMMENDATION_STATUS, REASON, UPDATED_AT) " +
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)";
        return jdbcTemplate.update(sql,
                rec.recommendationId(),
                rec.skuId(),
                rec.productName(),
                rec.demandClass(),
                rec.currentLocation(),
                rec.recommendedLocation(),
                rec.distance(),
                rec.distanceSaved(),
                rec.recommendationStatus(),
                rec.reason()
        );
    }

    public String findNextRecommendationId() {
        String sql = "SELECT RECOMMENDATION_ID FROM SLOT_RECOMMENDATIONS WHERE RECOMMENDATION_ID LIKE 'REC%'";
        List<String> ids = jdbcTemplate.query(sql, (rs, rowNum) -> rs.getString(1));
        int maxNum = 0;
        for (String id : ids) {
            try {
                int num = Integer.parseInt(id.substring(3).trim());
                if (num > maxNum) maxNum = num;
            } catch (Exception ignored) {}
        }
        return String.format("REC%03d", maxNum + 1);
    }
}
