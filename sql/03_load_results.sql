-- ============================================================================
-- CAP-12 Warehouse Slotting & Pick-Path Optimization
-- Script 03: Data Loading & Merge Patterns for Optimization Results
-- Database: CAP12_WAREHOUSE | Schema: CLEAN | Warehouse: CAP12_WH
-- ============================================================================

USE WAREHOUSE CAP12_WH;
USE DATABASE CAP12_WAREHOUSE;
USE SCHEMA CLEAN;

-- ----------------------------------------------------------------------------
-- Method A: Internal Stage and COPY INTO (Batch Loading Pattern)
-- ----------------------------------------------------------------------------

-- 1. Create file format for CSV loading
CREATE OR REPLACE FILE FORMAT CSV_OPTIMIZATION_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    NULL_IF = ('NULL', 'NONE', '');

-- 2. Stage definition (if not already existing)
CREATE OR REPLACE STAGE CAP12_RESULTS_STAGE
    FILE_FORMAT = CSV_OPTIMIZATION_FORMAT;

-- 3. COPY INTO Commands (Execute after staging outputs)
-- COPY INTO SLOT_RECOMMENDATIONS (RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION, RECOMMENDED_LOCATION, DISTANCE, RECOMMENDATION_STATUS, REASON)
-- FROM @CAP12_RESULTS_STAGE/slot_recommendations.csv;

-- COPY INTO ROUTE_RESULTS (ORDER_ID, BASELINE_ROUTE_SEQUENCE, OPTIMIZED_ROUTE_SEQUENCE, BASELINE_DISTANCE, OPTIMIZED_DISTANCE, DISTANCE_SAVED, PCT_DISTANCE_REDUCTION, BASELINE_TIME_SEC, OPTIMIZED_TIME_SEC, TIME_SAVED_SEC, ROUTE_STATUS, NOTES)
-- FROM @CAP12_RESULTS_STAGE/route_comparison.csv;

-- COPY INTO REPLENISHMENT_ALERTS (SKU_ID, PRODUCT_NAME, CURRENT_STOCK, MINIMUM_STOCK, STOCK_STATUS, REPLENISHMENT_REQUIRED)
-- FROM @CAP12_RESULTS_STAGE/replenishment_alerts.csv;

-- ----------------------------------------------------------------------------
-- Method B: Supervisor Approval Transaction Pattern (Stored Procedure / SQL)
-- ----------------------------------------------------------------------------

-- Transaction pattern for approving a slot change:
-- 1. Updates product current location.
-- 2. Marks old location as EMPTY.
-- 3. Marks new location as OCCUPIED.
-- 4. Sets recommendation status to APPROVED.
-- Wrapped in an atomic transaction to prevent inconsistent states.

-- Example approval execution template:
-- BEGIN TRANSACTION;
--     -- Check that new location is still EMPTY
--     -- UPDATE PRODUCTS SET CURRENT_LOCATION = :new_loc WHERE SKU_ID = :sku_id;
--     -- UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'EMPTY' WHERE LOCATION_ID = :old_loc;
--     -- UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'OCCUPIED' WHERE LOCATION_ID = :new_loc;
--     -- UPDATE SLOT_RECOMMENDATIONS SET RECOMMENDATION_STATUS = 'APPROVED', UPDATED_AT = CURRENT_TIMESTAMP() WHERE RECOMMENDATION_ID = :rec_id;
-- COMMIT;

