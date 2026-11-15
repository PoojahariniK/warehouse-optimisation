-- ============================================================================
-- CAP-12 Warehouse Slotting & Pick-Path Optimization
-- Script 01: Create Optimization Result Tables in Snowflake
-- Database: CAPSTONE_12_DB | Schema: CLEAN | Warehouse: CAP12_WH
-- ============================================================================

CREATE DATABASE IF NOT EXISTS CAPSTONE_12_DB;
USE DATABASE CAPSTONE_12_DB;
CREATE SCHEMA IF NOT EXISTS CLEAN;
USE SCHEMA CLEAN;
USE WAREHOUSE CAP12_WH;

-- 1. SLOT_RECOMMENDATIONS Table
-- Stores generated slot reallocation recommendations, approval statuses, and audit timestamps.
CREATE TABLE IF NOT EXISTS SLOT_RECOMMENDATIONS (
    RECOMMENDATION_ID      VARCHAR(20) PRIMARY KEY,
    SKU_ID                 VARCHAR(20) NOT NULL,
    PRODUCT_NAME           VARCHAR(100),
    DEMAND_CLASS           VARCHAR(20),
    CURRENT_LOCATION       VARCHAR(20),
    RECOMMENDED_LOCATION   VARCHAR(20),
    DISTANCE               NUMBER(10, 2),
    DISTANCE_SAVED         NUMBER(10, 2) DEFAULT 0.0,
    RECOMMENDATION_STATUS  VARCHAR(30) NOT NULL, -- 'RECOMMENDED', 'NO_FEASIBLE_LOCATION', 'APPROVED', 'REJECTED'
    REASON                 VARCHAR(500),
    CREATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 2. ROUTE_RESULTS Table
-- Stores baseline vs optimized Nearest Neighbor pick-path distances, times, and status per order.
CREATE TABLE IF NOT EXISTS ROUTE_RESULTS (
    ORDER_ID                  VARCHAR(20) PRIMARY KEY,
    BASELINE_ROUTE_SEQUENCE   VARCHAR(1000),
    OPTIMIZED_ROUTE_SEQUENCE  VARCHAR(1000),
    BASELINE_DISTANCE         NUMBER(10, 2),
    ROUTE_ONLY_DISTANCE       NUMBER(10, 2) DEFAULT 0.0,
    SLOT_ONLY_DISTANCE        NUMBER(10, 2) DEFAULT 0.0,
    OPTIMIZED_DISTANCE        NUMBER(10, 2),
    DISTANCE_SAVED            NUMBER(10, 2),
    PCT_DISTANCE_REDUCTION    NUMBER(5, 2),
    BASELINE_TIME_SEC         NUMBER(10, 2),
    OPTIMIZED_TIME_SEC        NUMBER(10, 2),
    TIME_SAVED_SEC            NUMBER(10, 2),
    ROUTE_STATUS              VARCHAR(20), -- 'IMPROVED', 'WORSE', 'IDENTICAL'
    NOTES                     VARCHAR(500),
    CREATED_AT                TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 3. REPLENISHMENT_ALERTS Table
-- Stores SKUs that meet or fall below the minimum stock replenishment threshold.
CREATE TABLE IF NOT EXISTS REPLENISHMENT_ALERTS (
    SKU_ID                 VARCHAR(20) PRIMARY KEY,
    PRODUCT_NAME           VARCHAR(100),
    CURRENT_STOCK          NUMBER(10, 0),
    MINIMUM_STOCK          NUMBER(10, 0),
    STOCK_STATUS           VARCHAR(30), -- 'LOW_STOCK', 'OUT_OF_STOCK'
    REPLENISHMENT_REQUIRED VARCHAR(10), -- 'YES', 'NO'
    CREATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

