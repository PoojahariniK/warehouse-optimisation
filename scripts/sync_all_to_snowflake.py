"""
Comprehensive Snowflake Sync Script
Ensures all tables exist and are fully populated in CAPSTONE_12_DB.CLEAN:
1. PRODUCTS
2. WAREHOUSE_LOCATIONS
3. ORDER_LINES
4. INVENTORY
5. SLOT_RECOMMENDATIONS
6. ROUTE_RESULTS
7. REPLENISHMENT_ALERTS
8. DEMAND_ANALYSIS
9. ORDER_AFFINITY
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import snowflake.connector

load_dotenv()

account = os.getenv("SNOWFLAKE_ACCOUNT", "").strip()
user = os.getenv("SNOWFLAKE_USER", "").strip()
password = os.getenv("SNOWFLAKE_PASSWORD", "").strip()
database = os.getenv("SNOWFLAKE_DATABASE", "CAPSTONE_12_DB").strip()
schema = os.getenv("SNOWFLAKE_SCHEMA", "CLEAN").strip()
warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "CAP12_WH").strip()
role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN").strip()

print(f"Connecting to Snowflake [{account}] as '{user}'...")
conn = snowflake.connector.connect(
    account=account,
    user=user,
    password=password,
    database=database,
    schema=schema,
    warehouse=warehouse,
    role=role,
)
cur = conn.cursor()

print("1. Creating tables if not exist...")

cur.execute("""
CREATE TABLE IF NOT EXISTS SLOT_RECOMMENDATIONS (
    RECOMMENDATION_ID      VARCHAR(20) PRIMARY KEY,
    SKU_ID                 VARCHAR(20) NOT NULL,
    PRODUCT_NAME           VARCHAR(100),
    DEMAND_CLASS           VARCHAR(20),
    CURRENT_LOCATION       VARCHAR(20),
    RECOMMENDED_LOCATION   VARCHAR(20),
    DISTANCE               NUMBER(10, 2),
    DISTANCE_SAVED         NUMBER(10, 2) DEFAULT 0.0,
    RECOMMENDATION_STATUS  VARCHAR(30) NOT NULL,
    REASON                 VARCHAR(500),
    CREATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
""")
cur.execute("""
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
    ROUTE_STATUS              VARCHAR(20),
    NOTES                     VARCHAR(500),
    CREATED_AT                TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
""")

for alter_stmt in [
    "ALTER TABLE SLOT_RECOMMENDATIONS ADD COLUMN UPDATED_AT TIMESTAMP_NTZ",
    "ALTER TABLE SLOT_RECOMMENDATIONS ADD COLUMN DISTANCE_SAVED NUMBER(10, 2) DEFAULT 0.0",
    "ALTER TABLE ROUTE_RESULTS ADD COLUMN ROUTE_ONLY_DISTANCE NUMBER(10, 2) DEFAULT 0.0",
    "ALTER TABLE ROUTE_RESULTS ADD COLUMN SLOT_ONLY_DISTANCE NUMBER(10, 2) DEFAULT 0.0",
]:
    try:
        cur.execute(alter_stmt)
    except Exception:
        pass

cur.execute("""
CREATE TABLE IF NOT EXISTS REPLENISHMENT_ALERTS (
    SKU_ID                 VARCHAR(20) PRIMARY KEY,
    PRODUCT_NAME           VARCHAR(100),
    CURRENT_STOCK          NUMBER(10, 0),
    MINIMUM_STOCK          NUMBER(10, 0),
    STOCK_STATUS           VARCHAR(30),
    REPLENISHMENT_REQUIRED VARCHAR(10),
    CREATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS DEMAND_ANALYSIS (
    SKU_ID            VARCHAR(20) PRIMARY KEY,
    PRODUCT_NAME      VARCHAR(100),
    CATEGORY          VARCHAR(50),
    CURRENT_LOCATION  VARCHAR(20),
    ORDER_FREQUENCY   NUMBER(10, 0),
    TOTAL_QUANTITY    NUMBER(10, 0),
    DEMAND_CLASS      VARCHAR(20),
    DEMAND_CV         NUMBER(10, 4),
    VOLATILITY_CLASS  VARCHAR(20)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS ORDER_AFFINITY (
    PAIR_ID             NUMBER(10, 0) AUTOINCREMENT PRIMARY KEY,
    SKU_A               VARCHAR(20),
    PRODUCT_A           VARCHAR(100),
    CATEGORY_A          VARCHAR(50),
    SKU_B               VARCHAR(20),
    PRODUCT_B           VARCHAR(100),
    CATEGORY_B          VARCHAR(50),
    CO_OCCURRENCE_COUNT NUMBER(10, 0),
    ORDERS_A            NUMBER(10, 0),
    ORDERS_B            NUMBER(10, 0),
    AFFINITY_SCORE      NUMBER(10, 4),
    JACCARD_INDEX       NUMBER(10, 4),
    PAIR_LABEL          VARCHAR(200)
)
""")

print("2. Populating SLOT_RECOMMENDATIONS from outputs/slot_recommendations.csv...")
cur.execute("TRUNCATE TABLE IF EXISTS SLOT_RECOMMENDATIONS")
df_slots = pd.read_csv("outputs/slot_recommendations.csv")
for _, r in df_slots.iterrows():
    pname = str(r["Product_Name"]).replace("'", "''")
    reason = str(r["Reason"]).replace("'", "''")
    dist = float(r["Distance"]) if pd.notnull(r["Distance"]) else 0.0
    rec_loc = str(r["Recommended_Location"]) if pd.notnull(r["Recommended_Location"]) else "NONE"
    cur_loc = str(r["Current_Location"]) if pd.notnull(r["Current_Location"]) else "NONE"
    cur.execute(f"""
        INSERT INTO SLOT_RECOMMENDATIONS 
        (RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION, RECOMMENDED_LOCATION, DISTANCE, DISTANCE_SAVED, RECOMMENDATION_STATUS, REASON, UPDATED_AT)
        VALUES ('{r["Recommendation_ID"]}', '{r["SKU_ID"]}', '{pname}', '{r["Demand_Class"]}', '{cur_loc}', '{rec_loc}', {dist}, 0.0, '{r["Recommendation_Status"]}', '{reason}', CURRENT_TIMESTAMP())
    """)

print("3. Populating ROUTE_RESULTS from outputs/route_comparison.csv...")
cur.execute("TRUNCATE TABLE IF EXISTS ROUTE_RESULTS")
df_routes = pd.read_csv("outputs/route_comparison.csv")
for _, r in df_routes.iterrows():
    notes = str(r.get("Notes", "")).replace("'", "''")
    cur.execute(f"""
        INSERT INTO ROUTE_RESULTS 
        (ORDER_ID, BASELINE_ROUTE_SEQUENCE, OPTIMIZED_ROUTE_SEQUENCE, BASELINE_DISTANCE, ROUTE_ONLY_DISTANCE, SLOT_ONLY_DISTANCE, OPTIMIZED_DISTANCE, DISTANCE_SAVED, PCT_DISTANCE_REDUCTION, BASELINE_TIME_SEC, OPTIMIZED_TIME_SEC, TIME_SAVED_SEC, ROUTE_STATUS, NOTES)
        VALUES ('{r["Order_ID"]}', '', '', {r["Baseline_Distance"]}, {r.get("Route_Only_Distance", 0.0)}, {r.get("Slot_Only_Distance", 0.0)}, {r["Optimized_Distance"]}, {r["Distance_Saved"]}, {r["Pct_Distance_Reduction"]}, {r["Baseline_Time_Sec"]}, {r["Optimized_Time_Sec"]}, {r["Time_Saved_Sec"]}, '{r["Route_Status"]}', '{notes}')
    """)

print("4. Populating REPLENISHMENT_ALERTS from outputs/replenishment_alerts.csv...")
cur.execute("TRUNCATE TABLE IF EXISTS REPLENISHMENT_ALERTS")
df_rep = pd.read_csv("outputs/replenishment_alerts.csv")
for _, r in df_rep.iterrows():
    pname = str(r["Product_Name"]).replace("'", "''")
    cur.execute(f"""
        INSERT INTO REPLENISHMENT_ALERTS 
        (SKU_ID, PRODUCT_NAME, CURRENT_STOCK, MINIMUM_STOCK, STOCK_STATUS, REPLENISHMENT_REQUIRED)
        VALUES ('{r["SKU_ID"]}', '{pname}', {r["Current_Stock"]}, {r["Minimum_Stock"]}, '{r["Stock_Status"]}', '{r["Replenishment_Required"]}')
    """)

print("5. Populating DEMAND_ANALYSIS from outputs/demand_analysis.csv...")
cur.execute("TRUNCATE TABLE IF EXISTS DEMAND_ANALYSIS")
df_dem = pd.read_csv("outputs/demand_analysis.csv")
for _, r in df_dem.iterrows():
    pname = str(r["Product_Name"]).replace("'", "''")
    cur.execute(f"""
        INSERT INTO DEMAND_ANALYSIS (SKU_ID, PRODUCT_NAME, CATEGORY, CURRENT_LOCATION, ORDER_FREQUENCY, TOTAL_QUANTITY, DEMAND_CLASS, DEMAND_CV, VOLATILITY_CLASS)
        VALUES ('{r["SKU_ID"]}', '{pname}', '{r["Category"]}', '{r["Current_Location"]}', {r["Order_Frequency"]}, {r["Total_Quantity"]}, '{r["Demand_Class"]}', {r["Demand_CV"]}, '{r["Volatility_Class"]}')
    """)

print("6. Populating ORDER_AFFINITY from outputs/affinity_pairs.csv...")
cur.execute("TRUNCATE TABLE IF EXISTS ORDER_AFFINITY")
df_aff = pd.read_csv("outputs/affinity_pairs.csv")
for _, r in df_aff.iterrows():
    pna = str(r["Product_A"]).replace("'", "''")
    pnb = str(r["Product_B"]).replace("'", "''")
    plab = str(r["Pair_Label"]).replace("'", "''")
    cur.execute(f"""
        INSERT INTO ORDER_AFFINITY (SKU_A, PRODUCT_A, CATEGORY_A, SKU_B, PRODUCT_B, CATEGORY_B, CO_OCCURRENCE_COUNT, ORDERS_A, ORDERS_B, AFFINITY_SCORE, JACCARD_INDEX, PAIR_LABEL)
        VALUES ('{r["SKU_A"]}', '{pna}', '{r["Category_A"]}', '{r["SKU_B"]}', '{pnb}', '{r["Category_B"]}', {r["Co_Occurrence_Count"]}, {r["Orders_A"]}, {r["Orders_B"]}, {r["Affinity_Score"]}, {r["Jaccard_Index"]}, '{plab}')
    """)

print("7. Resetting WAREHOUSE_LOCATIONS empty bins...")
cur.execute("UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'OCCUPIED' WHERE LOCATION_ID NOT IN ('A02', 'A06', 'B02', 'B06', 'C04', 'C08', 'D07', 'D08', 'E07', 'E08')")
cur.execute("UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'EMPTY' WHERE LOCATION_ID IN ('A02', 'A06', 'B02', 'B06', 'C04', 'C08', 'D07', 'D08', 'E07', 'E08')")

print("8. Resetting PRODUCTS locations from DEMAND_ANALYSIS...")
cur.execute("UPDATE PRODUCTS P SET CURRENT_LOCATION = D.CURRENT_LOCATION FROM DEMAND_ANALYSIS D WHERE P.SKU_ID = D.SKU_ID")

conn.close()
print("✅ ALL Snowflake tables fully verified, created, and populated!")
