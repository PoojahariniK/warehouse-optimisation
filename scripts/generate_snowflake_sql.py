"""
Generates sql/snowflake_complete_setup.sql containing table creation,
data insertion, and analytical views ready to run in Snowflake web worksheet.
"""
import pandas as pd

# Load outputs
recs = pd.read_csv('outputs/slot_recommendations.csv')
routes = pd.read_csv('outputs/route_comparison.csv')
base = pd.read_csv('outputs/baseline_routes.csv').set_index('Order_ID')
opt = pd.read_csv('outputs/optimized_routes.csv').set_index('Order_ID')
rep = pd.read_csv('outputs/replenishment_alerts.csv')

with open('sql/snowflake_complete_setup.sql', 'w', encoding='utf-8') as f:
    f.write('''-- ============================================================================
-- CAP-12 Warehouse Slotting & Pick-Path Optimization
-- COMPLETE SNOWFLAKE SETUP SCRIPT
-- Paste and Run this in your Snowflake Worksheet (sample.sql)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS CAPSTONE_12_DB;
USE DATABASE CAPSTONE_12_DB;
CREATE SCHEMA IF NOT EXISTS CLEAN;
USE SCHEMA CLEAN;
USE WAREHOUSE CAP12_WH;

-- ----------------------------------------------------------------------------
-- 1. CREATE 3 OPTIMIZATION RESULT TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS SLOT_RECOMMENDATIONS (
    RECOMMENDATION_ID      VARCHAR(20) PRIMARY KEY,
    SKU_ID                 VARCHAR(20) NOT NULL,
    PRODUCT_NAME           VARCHAR(100),
    DEMAND_CLASS           VARCHAR(20),
    CURRENT_LOCATION       VARCHAR(20),
    RECOMMENDED_LOCATION   VARCHAR(20),
    DISTANCE               NUMBER(10, 2),
    RECOMMENDATION_STATUS  VARCHAR(30) NOT NULL,
    REASON                 VARCHAR(500),
    CREATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS ROUTE_RESULTS (
    ORDER_ID                  VARCHAR(20) PRIMARY KEY,
    BASELINE_ROUTE_SEQUENCE   VARCHAR(1000),
    OPTIMIZED_ROUTE_SEQUENCE  VARCHAR(1000),
    BASELINE_DISTANCE         NUMBER(10, 2),
    OPTIMIZED_DISTANCE        NUMBER(10, 2),
    DISTANCE_SAVED            NUMBER(10, 2),
    PCT_DISTANCE_REDUCTION    NUMBER(5, 2),
    BASELINE_TIME_SEC         NUMBER(10, 2),
    OPTIMIZED_TIME_SEC        NUMBER(10, 2),
    TIME_SAVED_SEC            NUMBER(10, 2),
    ROUTE_STATUS              VARCHAR(20),
    NOTES                     VARCHAR(500),
    CREATED_AT                TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS REPLENISHMENT_ALERTS (
    SKU_ID                 VARCHAR(20) PRIMARY KEY,
    PRODUCT_NAME           VARCHAR(100),
    CURRENT_STOCK          NUMBER(10, 0),
    MINIMUM_STOCK          NUMBER(10, 0),
    STOCK_STATUS           VARCHAR(30),
    REPLENISHMENT_REQUIRED VARCHAR(10),
    CREATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ----------------------------------------------------------------------------
-- 2. POPULATE DATA INTO RESULT TABLES
-- ----------------------------------------------------------------------------

TRUNCATE TABLE IF EXISTS SLOT_RECOMMENDATIONS;
''')

    # Slot recommendations inserts
    for _, r in recs.iterrows():
        reason = str(r['Reason']).replace("'", "''")
        pname = str(r['Product_Name']).replace("'", "''")
        f.write(f"INSERT INTO SLOT_RECOMMENDATIONS (RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION, RECOMMENDED_LOCATION, DISTANCE, RECOMMENDATION_STATUS, REASON) VALUES ('{r['Recommendation_ID']}', '{r['SKU_ID']}', '{pname}', '{r['Demand_Class']}', '{r['Current_Location']}', '{r['Recommended_Location']}', {r['Distance']}, '{r['Recommendation_Status']}', '{reason}');\n")

    f.write('\nTRUNCATE TABLE IF EXISTS ROUTE_RESULTS;\n')
    # Route results inserts
    for _, r in routes.iterrows():
        oid = r['Order_ID']
        b_seq = str(base.loc[oid, 'Route_Sequence']).replace("'", "''") if oid in base.index else ''
        o_seq = str(opt.loc[oid, 'Route_Sequence']).replace("'", "''") if oid in opt.index else ''
        notes = str(r['Notes']).replace("'", "''")
        f.write(f"INSERT INTO ROUTE_RESULTS (ORDER_ID, BASELINE_ROUTE_SEQUENCE, OPTIMIZED_ROUTE_SEQUENCE, BASELINE_DISTANCE, OPTIMIZED_DISTANCE, DISTANCE_SAVED, PCT_DISTANCE_REDUCTION, BASELINE_TIME_SEC, OPTIMIZED_TIME_SEC, TIME_SAVED_SEC, ROUTE_STATUS, NOTES) VALUES ('{oid}', '{b_seq}', '{o_seq}', {r['Baseline_Distance']}, {r['Optimized_Distance']}, {r['Distance_Saved']}, {r['Pct_Distance_Reduction']}, {r['Baseline_Time_Sec']}, {r['Optimized_Time_Sec']}, {r['Time_Saved_Sec']}, '{r['Route_Status']}', '{notes}');\n")

    f.write('\nTRUNCATE TABLE IF EXISTS REPLENISHMENT_ALERTS;\n')
    # Replenishment alerts inserts
    for _, r in rep.iterrows():
        pname = str(r['Product_Name']).replace("'", "''")
        f.write(f"INSERT INTO REPLENISHMENT_ALERTS (SKU_ID, PRODUCT_NAME, CURRENT_STOCK, MINIMUM_STOCK, STOCK_STATUS, REPLENISHMENT_REQUIRED) VALUES ('{r['SKU_ID']}', '{pname}', {r['Current_Stock']}, {r['Minimum_Stock']}, '{r['Stock_Status']}', '{r['Replenishment_Required']}');\n")

    f.write('''
-- ----------------------------------------------------------------------------
-- 3. CREATE 5 ANALYTICAL VIEWS FOR POWER BI & REPORTING
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW VW_PERFORMANCE_ANALYTICS AS
SELECT
    COUNT(ORDER_ID) AS TOTAL_ORDERS,
    ROUND(AVG(BASELINE_DISTANCE), 2) AS AVG_BASELINE_DISTANCE,
    ROUND(AVG(OPTIMIZED_DISTANCE), 2) AS AVG_OPTIMIZED_DISTANCE,
    ROUND(SUM(DISTANCE_SAVED), 2) AS TOTAL_DISTANCE_SAVED,
    ROUND(AVG(PCT_DISTANCE_REDUCTION), 2) AS AVG_PCT_DISTANCE_REDUCTION,
    ROUND(AVG(BASELINE_TIME_SEC), 2) AS AVG_BASELINE_TIME_SEC,
    ROUND(AVG(OPTIMIZED_TIME_SEC), 2) AS AVG_OPTIMIZED_TIME_SEC,
    ROUND(SUM(TIME_SAVED_SEC), 2) AS TOTAL_TIME_SAVED_SEC,
    COUNT(CASE WHEN ROUTE_STATUS = 'IMPROVED' THEN 1 END) AS ORDERS_IMPROVED,
    COUNT(CASE WHEN ROUTE_STATUS = 'WORSE' THEN 1 END) AS ORDERS_WORSE,
    COUNT(CASE WHEN ROUTE_STATUS = 'IDENTICAL' THEN 1 END) AS ORDERS_IDENTICAL
FROM ROUTE_RESULTS;

CREATE OR REPLACE VIEW VW_DEMAND_DISTRIBUTION AS
SELECT
    DEMAND_CLASS,
    COUNT(SKU_ID) AS PRODUCT_COUNT,
    ROUND(COUNT(SKU_ID) * 100.0 / (SELECT COUNT(*) FROM PRODUCTS), 2) AS PCT_OF_TOTAL
FROM (
    SELECT
        P.SKU_ID,
        CASE
            WHEN COUNT(O.ORDER_LINE_ID) >= 10 THEN 'Fast'
            WHEN COUNT(O.ORDER_LINE_ID) >= 4 THEN 'Medium'
            ELSE 'Slow'
        END AS DEMAND_CLASS
    FROM PRODUCTS P
    LEFT JOIN ORDER_LINES O ON P.SKU_ID = O.SKU_ID
    GROUP BY P.SKU_ID
)
GROUP BY DEMAND_CLASS;

CREATE OR REPLACE VIEW VW_WAREHOUSE_OCCUPANCY AS
SELECT
    COUNT(LOCATION_ID) AS TOTAL_LOCATIONS,
    COUNT(CASE WHEN STATUS = 'OCCUPIED' THEN 1 END) AS OCCUPIED_LOCATIONS,
    COUNT(CASE WHEN STATUS = 'EMPTY' THEN 1 END) AS EMPTY_LOCATIONS,
    ROUND(COUNT(CASE WHEN STATUS = 'OCCUPIED' THEN 1 END) * 100.0 / COUNT(LOCATION_ID), 2) AS OCCUPANCY_RATE_PCT,
    SUM(CAPACITY) AS TOTAL_CAPACITY
FROM WAREHOUSE_LOCATIONS;

CREATE OR REPLACE VIEW VW_SLOT_APPROVAL_STATUS AS
SELECT
    RECOMMENDATION_STATUS,
    COUNT(RECOMMENDATION_ID) AS RECOMMENDATION_COUNT,
    ROUND(COUNT(RECOMMENDATION_ID) * 100.0 / (SELECT COUNT(*) FROM PRODUCTS), 2) AS PCT_OF_PRODUCTS
FROM SLOT_RECOMMENDATIONS
GROUP BY RECOMMENDATION_STATUS;

CREATE OR REPLACE VIEW VW_REPLENISHMENT_PRIORITY AS
SELECT
    A.SKU_ID,
    A.PRODUCT_NAME,
    P.CATEGORY,
    P.CURRENT_LOCATION,
    A.CURRENT_STOCK,
    A.MINIMUM_STOCK,
    (A.MINIMUM_STOCK - A.CURRENT_STOCK) AS STOCK_DEFICIT,
    A.STOCK_STATUS,
    A.REPLENISHMENT_REQUIRED
FROM REPLENISHMENT_ALERTS A
LEFT JOIN PRODUCTS P ON A.SKU_ID = P.SKU_ID
ORDER BY STOCK_DEFICIT DESC;

-- ----------------------------------------------------------------------------
-- 4. VERIFY: SHOW ALL 7 TABLES AND 5 VIEWS
-- ----------------------------------------------------------------------------
SHOW TABLES IN SCHEMA CAPSTONE_12_DB.CLEAN;
SHOW VIEWS IN SCHEMA CAPSTONE_12_DB.CLEAN;
''')

print("Successfully generated sql/snowflake_complete_setup.sql!")

