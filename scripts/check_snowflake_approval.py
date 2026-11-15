"""
Script to check Snowflake connection and verify if approved slot recommendations
have been written to Snowflake database CAPSTONE_12_DB.CLEAN.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

account = os.getenv("SNOWFLAKE_ACCOUNT", "").strip()
user = os.getenv("SNOWFLAKE_USER", "").strip()
password = os.getenv("SNOWFLAKE_PASSWORD", "").strip()
database = os.getenv("SNOWFLAKE_DATABASE", "CAPSTONE_12_DB").strip()
schema = os.getenv("SNOWFLAKE_SCHEMA", "CLEAN").strip()
warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "CAP12_WH").strip()
role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN").strip()

print("=" * 70)
print("SNOWFLAKE CONNECTION & APPROVAL AUDIT CHECKER")
print("=" * 70)
print(f"Target Account:   {account}")
print(f"User:             {user}")
print(f"Database:         {database}")
print(f"Schema:           {schema}")
print(f"Warehouse:        {warehouse}")
print(f"Role:             {role}")
print("-" * 70)

try:
    import snowflake.connector
except ImportError:
    print("[ERROR] snowflake-connector-python not installed. Run in project venv.")
    sys.exit(1)

try:
    print("[1/3] Connecting to Snowflake...")
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        database=database,
        schema=schema,
        warehouse=warehouse,
        role=role,
    )
    print("      ✅ Connected successfully to Snowflake Cloud!")
    cur = conn.cursor()

    # 1. Check current session
    cur.execute("SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
    c_user, c_db, c_schema, c_wh = cur.fetchone()
    print(f"      Active Session -> User: {c_user} | DB: {c_db} | Schema: {c_schema} | WH: {c_wh}")

    # 2. Check table existence
    print("\n[2/3] Checking SLOT_RECOMMENDATIONS table...")
    cur.execute("SHOW TABLES LIKE 'SLOT_RECOMMENDATIONS' IN SCHEMA")
    tables = cur.fetchall()
    if not tables:
        print("      ⚠️ Table SLOT_RECOMMENDATIONS does not exist yet in schema CLEAN.")
        print("      Run sql/snowflake_complete_setup.sql or sql/03_s3_ingestion.sql first.")
        conn.close()
        sys.exit(0)

    # 3. Check status breakdown
    cur.execute("""
        SELECT RECOMMENDATION_STATUS, COUNT(*) 
        FROM SLOT_RECOMMENDATIONS 
        GROUP BY RECOMMENDATION_STATUS
    """)
    breakdown = cur.fetchall()
    print("      Current Status Breakdown in Snowflake:")
    for status, count in breakdown:
        print(f"        - {status}: {count}")

    # 4. Check for APPROVED recommendations
    print("\n[3/3] Querying APPROVED recommendations in Snowflake...")
    cur.execute("""
        SELECT RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, CURRENT_LOCATION, RECOMMENDED_LOCATION, RECOMMENDATION_STATUS, UPDATED_AT
        FROM SLOT_RECOMMENDATIONS
        WHERE RECOMMENDATION_STATUS = 'APPROVED'
        ORDER BY RECOMMENDATION_ID
    """)
    approved_rows = cur.fetchall()

    if approved_rows:
        print(f"      ✅ FOUND {len(approved_rows)} APPROVED recommendations in Snowflake:")
        print(f"      {'REC_ID':<10} {'SKU_ID':<10} {'CURRENT_LOC':<14} {'RECOMMENDED_LOC':<18} {'STATUS':<10} {'UPDATED_AT'}")
        print("      " + "-" * 75)
        for r in approved_rows:
            rec_id, sku, pname, cur_loc, rec_loc, st, upd = r
            print(f"      {rec_id:<10} {sku:<10} {str(cur_loc):<14} {str(rec_loc):<18} {st:<10} {str(upd)}")
    else:
        print("      ℹ️ No recommendations currently marked as 'APPROVED' in Snowflake.")

    conn.close()
    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ Snowflake Query Failed: {e}")
    sys.exit(1)

