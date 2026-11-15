"""
Snowflake Cloud Sync Executor using SnowSQL.
Reads credentials securely from .env and executes sql/snowflake_complete_setup.sql.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_sync():
    env_file = Path(".env")
    if not env_file.exists():
        print("[ERROR] .env file not found.")
        sys.exit(1)

    # Parse .env
    env_vars = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")

    account = env_vars.get("SNOWFLAKE_ACCOUNT")
    user = env_vars.get("SNOWFLAKE_USER")
    password = env_vars.get("SNOWFLAKE_PASSWORD")
    database = env_vars.get("SNOWFLAKE_DATABASE", "CAPSTONE_12_DB")
    schema = env_vars.get("SNOWFLAKE_SCHEMA", "CLEAN")
    warehouse = env_vars.get("SNOWFLAKE_WAREHOUSE", "CAP12_WH")

    if not account or not user or not password:
        print("[ERROR] Missing required SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, or SNOWFLAKE_PASSWORD in .env.")
        sys.exit(1)

    sql_file = Path("sql/snowflake_complete_setup.sql")
    if not sql_file.exists():
        print(f"[ERROR] SQL file not found: {sql_file}")
        sys.exit(1)

    print(f"Connecting to Snowflake account: {account} as user: {user}...")
    print(f"Target Database: {database} | Schema: {schema} | Warehouse: {warehouse}")
    print(f"Executing: {sql_file}...")

    # Method 1: Use snowflake-connector-python if installed
    try:
        import snowflake.connector
        print("[INFO] Using snowflake-connector-python to stream and execute SQL...")
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            database=database,
            schema=schema,
            warehouse=warehouse,
            role=env_vars.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        )
        with open(sql_file, "r", encoding="utf-8") as f:
            for cur in conn.execute_stream(f):
                # Consume result
                for row in cur:
                    pass
        conn.close()
        print("\n✅ Successfully synced all tables and views to Snowflake via snowflake-connector!")
        return
    except ImportError:
        print("[INFO] snowflake-connector-python not found, falling back to SnowSQL CLI...")
    except Exception as e:
        print(f"[ERROR] Snowflake connector execution failed: {e}")
        print("[INFO] Attempting fallback to SnowSQL CLI if available...")

    # Method 2: Fallback to SnowSQL CLI if present
    snowsql_exe = Path(r"C:\Program Files\Snowflake SnowSQL\snowsql.exe")
    if not snowsql_exe.exists():
        print(f"[ERROR] snowsql.exe not found at {snowsql_exe}")
        print("Tip: Either install snowflake-connector-python (`pip install snowflake-connector-python`) or install SnowSQL CLI, or paste sql/snowflake_complete_setup.sql directly into Snowflake Web Worksheet.")
        sys.exit(1)

    # Pass password securely via environment variable
    proc_env = os.environ.copy()
    proc_env["SNOWSQL_PWD"] = password
    proc_env["SNOWSQL_ACCOUNT"] = account
    proc_env["SNOWSQL_USER"] = user
    proc_env["SNOWSQL_DATABASE"] = database
    proc_env["SNOWSQL_SCHEMA"] = schema
    proc_env["SNOWSQL_WAREHOUSE"] = warehouse

    cmd = [
        str(snowsql_exe),
        "-a", account,
        "-u", user,
        "-d", database,
        "-s", schema,
        "-w", warehouse,
        "-f", str(sql_file),
        "-o", "friendly=false",
        "-o", "header=true"
    ]

    res = subprocess.run(cmd, env=proc_env, capture_output=True, text=True)
    
    print("\n--- STDOUT ---")
    print(res.stdout)
    if res.stderr:
        print("--- STDERR ---")
        print(res.stderr)

    if res.returncode == 0:
        print("\n✅ Successfully synced all tables and views to Snowflake!")
    else:
        print(f"\n[ERROR] SnowSQL exited with code {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    run_sync()

