"""
Reset Snowflake Database back to baseline:
1. WAREHOUSE_LOCATIONS: 10 clean empty slots (A02, A06, B02, B06, C04, C08, D07, D08, E07, E08)
2. PRODUCTS: baseline locations from DEMAND_ANALYSIS
3. SLOT_RECOMMENDATIONS: baseline from outputs/slot_recommendations.csv
"""

import os
from dotenv import load_dotenv
import pandas as pd
import snowflake.connector

load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)
cur = conn.cursor()

print("1. Resetting WAREHOUSE_LOCATIONS empty bins...")
cur.execute("UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'OCCUPIED' WHERE LOCATION_ID NOT IN ('A02', 'A06', 'B02', 'B06', 'C04', 'C08', 'D07', 'D08', 'E07', 'E08')")
cur.execute("UPDATE WAREHOUSE_LOCATIONS SET STATUS = 'EMPTY' WHERE LOCATION_ID IN ('A02', 'A06', 'B02', 'B06', 'C04', 'C08', 'D07', 'D08', 'E07', 'E08')")

print("2. Resetting PRODUCTS to baseline locations from DEMAND_ANALYSIS...")
cur.execute("UPDATE PRODUCTS P SET CURRENT_LOCATION = D.CURRENT_LOCATION FROM DEMAND_ANALYSIS D WHERE P.SKU_ID = D.SKU_ID")

print("3. Restoring SLOT_RECOMMENDATIONS from outputs/slot_recommendations.csv...")
df = pd.read_csv("outputs/slot_recommendations.csv")
for _, r in df.iterrows():
    pname = str(r["Product_Name"]).replace("'", "''")
    reason = str(r["Reason"]).replace("'", "''")
    dist = float(r["Distance"]) if pd.notnull(r["Distance"]) else 0.0
    dist_saved = float(r.get("Distance_Saved", 0.0)) if pd.notnull(r.get("Distance_Saved")) else 0.0
    rec_loc = str(r["Recommended_Location"]) if pd.notnull(r["Recommended_Location"]) else "NONE"
    cur_loc = str(r["Current_Location"]) if pd.notnull(r["Current_Location"]) else "NONE"
    st = str(r["Recommendation_Status"])
    cur.execute(f"""
        UPDATE SLOT_RECOMMENDATIONS 
        SET SKU_ID = '{r["SKU_ID"]}',
            PRODUCT_NAME = '{pname}',
            DEMAND_CLASS = '{r["Demand_Class"]}',
            CURRENT_LOCATION = '{cur_loc}',
            RECOMMENDED_LOCATION = '{rec_loc}',
            DISTANCE = {dist},
            DISTANCE_SAVED = {dist_saved},
            RECOMMENDATION_STATUS = '{st}',
            REASON = '{reason}'
        WHERE RECOMMENDATION_ID = '{r["Recommendation_ID"]}'
    """)

print("4. Verification of statuses in Snowflake:")
cur.execute("SELECT RECOMMENDATION_STATUS, COUNT(*) FROM SLOT_RECOMMENDATIONS GROUP BY RECOMMENDATION_STATUS")
for row in cur.fetchall():
    print(f"   - {row[0]}: {row[1]}")

print("\nValid RECOMMENDED items:")
cur.execute("SELECT RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, CURRENT_LOCATION, RECOMMENDED_LOCATION, DISTANCE_SAVED, RECOMMENDATION_STATUS FROM SLOT_RECOMMENDATIONS WHERE RECOMMENDATION_STATUS = 'RECOMMENDED'")
for row in cur.fetchall():
    print(f"   {row[0]} | {row[1]} | {row[2]} | Current: {row[3]} -> Proposed: {row[4]} | Saved: {row[5]} u")

conn.close()
print("✅ Baseline reset completed successfully!")

