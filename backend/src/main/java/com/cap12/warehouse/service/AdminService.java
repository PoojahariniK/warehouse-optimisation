package com.cap12.warehouse.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import org.springframework.stereotype.Service;

import javax.sql.DataSource;
import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;

@Service
public class AdminService {

    private static final Logger logger = LoggerFactory.getLogger(AdminService.class);

    private final DataSource dataSource;
    private final JdbcTemplate jdbcTemplate;

    public AdminService(DataSource dataSource, JdbcTemplate jdbcTemplate) {
        this.dataSource = dataSource;
        this.jdbcTemplate = jdbcTemplate;
    }

    public void resetDatabase() {
        logger.info("Executing database reset to baseline seed state...");
        boolean isSnowflake = false;
        try (Connection conn = dataSource.getConnection()) {
            String dbProduct = conn.getMetaData().getDatabaseProductName().toLowerCase();
            if (dbProduct.contains("snowflake")) {
                isSnowflake = true;
            }
        } catch (Exception e) {
            logger.warn("Could not determine DB product name: {}", e.getMessage());
        }

        if (isSnowflake) {
            logger.info("Detected Snowflake Cloud database. Running in-place baseline reset...");
            try {
                resetSnowflakeFast();
                logger.info("Snowflake baseline reset completed successfully.");
            } catch (Exception e) {
                logger.error("Error during Snowflake baseline reset: {}", e.getMessage(), e);
                throw new RuntimeException("Snowflake reset failed: " + e.getMessage(), e);
            }
            return;
        }

        ResourceDatabasePopulator populator = new ResourceDatabasePopulator();
        populator.setContinueOnError(false);
        populator.setIgnoreFailedDrops(true);
        populator.addScript(new ClassPathResource("schema.sql"));
        populator.addScript(new ClassPathResource("data.sql"));
        populator.execute(dataSource);
        logger.info("Database reset completed successfully via populator.");
    }

    private void resetSnowflakeFast() {
        // 1. Reset Warehouse Locations: empty slots to EMPTY, rest to OCCUPIED
        jdbcTemplate.update("UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'OCCUPIED' WHERE LOCATION_ID NOT IN ('A02', 'A06', 'B02', 'B06', 'C04', 'C08', 'D07', 'D08', 'E07', 'E08')");
        jdbcTemplate.update("UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'EMPTY' WHERE LOCATION_ID IN ('A02', 'A06', 'B02', 'B06', 'C04', 'C08', 'D07', 'D08', 'E07', 'E08')");

        // 2. Reset Products to baseline locations from DEMAND_ANALYSIS
        jdbcTemplate.update("UPDATE PRODUCTS P SET CURRENT_LOCATION = D.CURRENT_LOCATION FROM DEMAND_ANALYSIS D WHERE P.SKU_ID = D.SKU_ID");

        // 3. Reset Slot Recommendations accurately from outputs/slot_recommendations.csv
        boolean csvRestored = restoreRecommendationsFromCsv();
        if (!csvRestored) {
            // Fallback dynamic query: only valid proposed bins are RECOMMENDED, NONE bins are NO_FEASIBLE_LOCATION
            jdbcTemplate.update("UPDATE SLOT_RECOMMENDATIONS SET RECOMMENDATION_STATUS = 'RECOMMENDED' WHERE RECOMMENDED_LOCATION IS NOT NULL AND RECOMMENDED_LOCATION != 'NONE' AND RECOMMENDED_LOCATION != ''");
            jdbcTemplate.update("UPDATE SLOT_RECOMMENDATIONS SET RECOMMENDATION_STATUS = 'NO_FEASIBLE_LOCATION' WHERE RECOMMENDED_LOCATION IS NULL OR RECOMMENDED_LOCATION = 'NONE' OR RECOMMENDED_LOCATION = ''");
        }
    }

    private boolean restoreRecommendationsFromCsv() {
        Path[] searchPaths = new Path[] {
            Paths.get("outputs/slot_recommendations.csv"),
            Paths.get("../outputs/slot_recommendations.csv")
        };
        for (Path p : searchPaths) {
            if (Files.exists(p)) {
                try (BufferedReader reader = Files.newBufferedReader(p)) {
                    String header = reader.readLine();
                    if (header == null) return false;
                    String line;
                    while ((line = reader.readLine()) != null) {
                        List<String> parts = parseCsvLine(line);
                        if (parts.size() >= 10) {
                            String recId = parts.get(0).trim();
                            String skuId = parts.get(1).trim();
                            String prodName = parts.get(2).trim();
                            String demandClass = parts.get(3).trim();
                            String curLoc = parts.get(4).trim();
                            String recLoc = parts.get(5).trim();
                            double dist = parseDoubleSafe(parts.get(6));
                            double distSaved = parseDoubleSafe(parts.get(7));
                            String status = parts.get(8).trim();
                            String reason = parts.get(9).trim();

                            jdbcTemplate.update(
                                "UPDATE SLOT_RECOMMENDATIONS SET SKU_ID = ?, PRODUCT_NAME = ?, DEMAND_CLASS = ?, " +
                                "CURRENT_LOCATION = ?, RECOMMENDED_LOCATION = ?, DISTANCE = ?, DISTANCE_SAVED = ?, " +
                                "RECOMMENDATION_STATUS = ?, REASON = ?, UPDATED_AT = CURRENT_TIMESTAMP WHERE RECOMMENDATION_ID = ?",
                                skuId, prodName, demandClass, curLoc, recLoc, dist, distSaved, status, reason, recId
                            );
                        }
                    }
                    logger.info("Successfully restored baseline recommendations from {}", p);
                    return true;
                } catch (Exception e) {
                    logger.warn("Failed reading CSV from {}: {}", p, e.getMessage());
                }
            }
        }
        return false;
    }

    private double parseDoubleSafe(String val) {
        try {
            return Double.parseDouble(val.trim());
        } catch (Exception e) {
            return 0.0;
        }
    }

    private List<String> parseCsvLine(String line) {
        List<String> result = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        boolean inQuotes = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '\"') {
                inQuotes = !inQuotes;
            } else if (c == ',' && !inQuotes) {
                result.add(cur.toString().trim());
                cur.setLength(0);
            } else {
                cur.append(c);
            }
        }
        result.add(cur.toString().trim());
        return result;
    }
}
