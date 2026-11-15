-- ============================================================================
-- CAP-12 Warehouse Slotting & Pick-Path Optimization
-- S3 to Snowflake Ingestion Script
-- File: sql/03_s3_ingestion.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. DATABASE, SCHEMA & WAREHOUSE CONTEXT
-- ----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS CAPSTONE_12_DB;
USE DATABASE CAPSTONE_12_DB;

CREATE SCHEMA IF NOT EXISTS CLEAN;
USE SCHEMA CLEAN;

USE WAREHOUSE CAP12_WH;

-- ----------------------------------------------------------------------------
-- 2. FILE FORMAT & STAGE CONFIGURATION
-- ----------------------------------------------------------------------------
-- Reusable CSV File Format matching ERP export specifications
CREATE OR REPLACE FILE FORMAT S3_CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    NULL_IF = ('NULL', 'NONE', '', 'NaN')
    EMPTY_FIELD_AS_NULL = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- External S3 Stage Definition (Pre-tested stage: erp_s3_stage)
-- Note: Credentials can be sourced directly from the stage or defined as below:

-- ----------------------------------------------------------------------------
-- 3. CREATE THE 4 MAIN BASE TABLES
-- ----------------------------------------------------------------------------

-- Table 1: PRODUCTS
-- Stores SKU definitions, dimensional capacity demands, initial locations, and hazard zones.
CREATE TABLE IF NOT EXISTS PRODUCTS (
    SKU_ID            VARCHAR(20) PRIMARY KEY,
    PRODUCT_NAME      VARCHAR(100) NOT NULL,
    CATEGORY          VARCHAR(50),
    REQUIRED_CAPACITY NUMBER(10, 0) NOT NULL,
    CURRENT_LOCATION  VARCHAR(20),
    HAZARD_CLASS      VARCHAR(50) DEFAULT 'GENERAL'
);

-- Table 2: WAREHOUSE_LOCATIONS
-- Physical bin coordinates (X, Y), physical storage capacity, status, and category/hazard rules.
CREATE TABLE IF NOT EXISTS WAREHOUSE_LOCATIONS (
    LOCATION_ID      VARCHAR(20) PRIMARY KEY,
    AISLE            VARCHAR(10) NOT NULL,
    X                NUMBER(10, 2) NOT NULL,
    Y                NUMBER(10, 2) NOT NULL,
    CAPACITY         NUMBER(10, 0) NOT NULL,
    STATUS           VARCHAR(20) NOT NULL,
    ALLOWED_CATEGORY VARCHAR(50) DEFAULT 'ALL',
    HAZARD_ALLOWED   VARCHAR(50) DEFAULT 'GENERAL'
);

-- Table 3: ORDER_LINES
-- Historical order pick requests used for velocity classification, co-occurrence, and pick routing.
CREATE TABLE IF NOT EXISTS ORDER_LINES (
    ORDER_LINE_ID VARCHAR(20) PRIMARY KEY,
    ORDER_ID      VARCHAR(20) NOT NULL,
    ORDER_DATE    VARCHAR(30),
    SKU_ID        VARCHAR(20) NOT NULL,
    QUANTITY      NUMBER(10, 0) NOT NULL
);

-- Table 4: INVENTORY
-- Current stock levels and replenishment safety thresholds.
CREATE TABLE IF NOT EXISTS INVENTORY (
    SKU_ID        VARCHAR(20) PRIMARY KEY,
    CURRENT_STOCK NUMBER(10, 0) NOT NULL,
    MINIMUM_STOCK NUMBER(10, 0) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. COPY INTO STATEMENTS (PULL DATA FROM @erp_s3_stage)
-- ----------------------------------------------------------------------------

-- 4.1 Ingest PRODUCTS from s3://cap12-warehouse-erp-drop/products.csv
TRUNCATE TABLE IF EXISTS PRODUCTS;

COPY INTO PRODUCTS (SKU_ID, PRODUCT_NAME, CATEGORY, REQUIRED_CAPACITY, CURRENT_LOCATION, HAZARD_CLASS)
FROM (
    SELECT 
        $1,                             -- SKU_ID
        $2,                             -- Product_Name
        $3,                             -- Category
        $4::NUMBER(10, 0),              -- Required_Capacity
        $5,                             -- Current_Location
        COALESCE($6, 'GENERAL')         -- Hazard_Class (default GENERAL if not in CSV)
    FROM @erp_s3_stage/products.csv
)
FILE_FORMAT = S3_CSV_FORMAT
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

-- 4.2 Ingest WAREHOUSE_LOCATIONS from s3://cap12-warehouse-erp-drop/warehouse_locations.csv
TRUNCATE TABLE IF EXISTS WAREHOUSE_LOCATIONS;

COPY INTO WAREHOUSE_LOCATIONS (LOCATION_ID, AISLE, X, Y, CAPACITY, STATUS, ALLOWED_CATEGORY, HAZARD_ALLOWED)
FROM (
    SELECT 
        $1,                             -- Location_ID
        $2,                             -- Aisle
        $3::NUMBER(10, 2),              -- X coordinate
        $4::NUMBER(10, 2),              -- Y coordinate
        $5::NUMBER(10, 0),              -- Capacity
        $6,                             -- Status (OCCUPIED / EMPTY)
        COALESCE($7, 'ALL'),            -- Allowed_Category
        COALESCE($8, 'GENERAL')         -- Hazard_Allowed
    FROM @erp_s3_stage/warehouse_locations.csv
)
FILE_FORMAT = S3_CSV_FORMAT
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

-- 4.3 Ingest ORDER_LINES from s3://cap12-warehouse-erp-drop/order_lines.csv
TRUNCATE TABLE IF EXISTS ORDER_LINES;

COPY INTO ORDER_LINES (ORDER_LINE_ID, ORDER_ID, ORDER_DATE, SKU_ID, QUANTITY)
FROM (
    SELECT 
        $1,                             -- Order_Line_ID
        $2,                             -- Order_ID
        $3,                             -- Order_Date
        $4,                             -- SKU_ID
        $5::NUMBER(10, 0)               -- Quantity
    FROM @erp_s3_stage/order_lines.csv
)
FILE_FORMAT = S3_CSV_FORMAT
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

-- 4.4 Ingest INVENTORY from s3://cap12-warehouse-erp-drop/inventory.csv
TRUNCATE TABLE IF EXISTS INVENTORY;

COPY INTO INVENTORY (SKU_ID, CURRENT_STOCK, MINIMUM_STOCK)
FROM (
    SELECT 
        $1,                             -- SKU_ID
        $2::NUMBER(10, 0),              -- Current_Stock
        $3::NUMBER(10, 0)               -- Minimum_Stock
    FROM @erp_s3_stage/inventory.csv
)
FILE_FORMAT = S3_CSV_FORMAT
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

-- ----------------------------------------------------------------------------
-- 5. VERIFICATION: VALIDATE INGESTED ROW COUNTS
-- ----------------------------------------------------------------------------
SELECT 'PRODUCTS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM PRODUCTS
UNION ALL
SELECT 'WAREHOUSE_LOCATIONS', COUNT(*) FROM WAREHOUSE_LOCATIONS
UNION ALL
SELECT 'ORDER_LINES', COUNT(*) FROM ORDER_LINES
UNION ALL
SELECT 'INVENTORY', COUNT(*) FROM INVENTORY;

