"""
Update Snowflake Schema and Sync Route Results:
1. Adds ROUTE_ONLY_DISTANCE and SLOT_ONLY_DISTANCE to ROUTE_RESULTS in Snowflake.
2. Updates ROUTE_RESULTS values from outputs/route_comparison.csv.
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

print("1. Altering ROUTE_RESULTS to add ROUTE_ONLY_DISTANCE and SLOT_ONLY_DISTANCE...")
cur.execute("ALTER TABLE ROUTE_RESULTS ADD COLUMN IF NOT EXISTS ROUTE_ONLY_DISTANCE NUMBER(10, 2) DEFAULT 0.0")
cur.execute("ALTER TABLE ROUTE_RESULTS ADD COLUMN IF NOT EXISTS SLOT_ONLY_DISTANCE NUMBER(10, 2) DEFAULT 0.0")
print("   Columns verified/added.")

print("2. Updating ROUTE_RESULTS with values from outputs/route_comparison.csv...")
df_routes = pd.read_csv("outputs/route_comparison.csv")
for _, r in df_routes.iterrows():
    cur.execute(
        """
        UPDATE ROUTE_RESULTS 
        SET ROUTE_ONLY_DISTANCE = %s,
            SLOT_ONLY_DISTANCE = %s
        WHERE ORDER_ID = %s
        """,
        (float(r["Route_Only_Distance"]), float(r["Slot_Only_Distance"]), r["Order_ID"])
    )
print(f"   Updated {len(df_routes)} rows in ROUTE_RESULTS.")

conn.close()
print("✅ Fix completed successfully!")

