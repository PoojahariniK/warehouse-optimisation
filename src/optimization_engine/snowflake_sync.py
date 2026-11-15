"""
Snowflake Synchronization Module for Warehouse Optimization Engine.
Provides secure, environment-variable driven connectivity to Snowflake (CAP12_WAREHOUSE.CLEAN)
to read base datasets and sync generated optimization results.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

# Try importing python-dotenv
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try importing snowflake connector
try:
    import snowflake.connector
    from snowflake.connector.pandas_tools import write_pandas

    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False


def get_snowflake_config() -> Dict[str, str]:
    """
    Reads Snowflake connection parameters from environment variables.
    """
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
        "user": os.getenv("SNOWFLAKE_USER", ""),
        "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
        "database": os.getenv("SNOWFLAKE_DATABASE", "CAPSTONE_12_DB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "CLEAN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CAP12_WH"),
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    }


def is_snowflake_configured() -> Tuple[bool, str]:
    """
    Checks if minimum required Snowflake credentials are set in environment.
    """
    config = get_snowflake_config()
    missing = [k for k in ["account", "user", "password"] if not config.get(k)]
    if missing:
        return (
            False,
            f"Snowflake environment variables missing: {', '.join([f'SNOWFLAKE_{m.upper()}' for m in missing])}",
        )
    return True, "Snowflake credentials present in environment."


class SnowflakeSync:
    """
    Manages reading and writing data between the optimization engine and Snowflake.
    """

    def __init__(self):
        self.config = get_snowflake_config()
        self.configured, self.status_message = is_snowflake_configured()

    def get_connection(self):
        """
        Creates and returns a Snowflake connection.
        """
        if not SNOWFLAKE_AVAILABLE:
            raise ImportError(
                "snowflake-connector-python is not installed. Run: pip install snowflake-connector-python"
            )

        if not self.configured:
            raise ValueError(f"Cannot connect to Snowflake: {self.status_message}")

        return snowflake.connector.connect(
            account=self.config["account"],
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"],
            schema=self.config["schema"],
            warehouse=self.config["warehouse"],
            role=self.config["role"],
        )

    def test_connection(self) -> Tuple[bool, str]:
        """
        Tests whether connection to Snowflake can be established.
        """
        if not SNOWFLAKE_AVAILABLE:
            return False, "snowflake-connector-python library not installed."

        if not self.configured:
            return False, self.status_message

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
            db, sc, wh = cursor.fetchone()
            conn.close()
            return True, f"Successfully connected to Snowflake [Database: {db}, Schema: {sc}, Warehouse: {wh}]"
        except Exception as e:
            return False, f"Snowflake connection failed: {str(e)}"

    def load_base_datasets(self) -> Optional[Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        Reads base datasets (PRODUCTS, WAREHOUSE_LOCATIONS, ORDER_LINES, INVENTORY) directly from Snowflake.
        """
        if not self.configured or not SNOWFLAKE_AVAILABLE:
            logger.warning(f"Cannot load from Snowflake: {self.status_message}. Falling back to CSV.")
            return None

        try:
            conn = self.get_connection()
            logger.info("Reading base datasets from Snowflake CAPSTONE_12_DB.CLEAN...")

            from src.optimization_engine.data_loader import standardize_dataset

            products_raw = pd.read_sql("SELECT * FROM PRODUCTS", conn)
            locations_raw = pd.read_sql("SELECT * FROM WAREHOUSE_LOCATIONS", conn)
            order_lines_raw = pd.read_sql("SELECT * FROM ORDER_LINES", conn)
            inventory_raw = pd.read_sql("SELECT * FROM INVENTORY", conn)

            conn.close()
            logger.info("Successfully fetched all 4 tables from Snowflake.")

            products = standardize_dataset(products_raw, "products")
            locations = standardize_dataset(locations_raw, "locations")
            order_lines = standardize_dataset(order_lines_raw, "order_lines")
            inventory = standardize_dataset(inventory_raw, "inventory")

            return products, locations, order_lines, inventory
        except Exception as e:
            logger.error(f"Error reading tables from Snowflake: {e}")
            return None

    def sync_results(
        self,
        slot_recs_df: pd.DataFrame,
        route_comparison_df: pd.DataFrame,
        baseline_routes_df: pd.DataFrame,
        optimized_routes_df: pd.DataFrame,
        replenishment_df: pd.DataFrame,
    ) -> bool:
        """
        Syncs generated optimization results to Snowflake result tables:
        - SLOT_RECOMMENDATIONS
        - ROUTE_RESULTS
        - REPLENISHMENT_ALERTS
        """
        if not self.configured or not SNOWFLAKE_AVAILABLE:
            logger.info(
                f"Snowflake sync skipped ({self.status_message}). Results remain preserved in outputs/."
            )
            return False

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Ensure tables exist
            sql_script_path = Path("sql/01_create_result_tables.sql")
            if sql_script_path.exists():
                ddl = sql_script_path.read_text(encoding="utf-8")
                for raw_cmd in ddl.split(";"):
                    lines = [line for line in raw_cmd.splitlines() if not line.strip().startswith("--")]
                    cmd = "\n".join(lines).strip()
                    if cmd:
                        cursor.execute(cmd)

            # Sync SLOT_RECOMMENDATIONS
            logger.info("Syncing SLOT_RECOMMENDATIONS to Snowflake...")
            cursor.execute("TRUNCATE TABLE IF EXISTS SLOT_RECOMMENDATIONS")
            for _, r in slot_recs_df.iterrows():
                cursor.execute(
                    """
                    INSERT INTO SLOT_RECOMMENDATIONS
                    (RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION,
                     RECOMMENDED_LOCATION, DISTANCE, RECOMMENDATION_STATUS, REASON)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        r["Recommendation_ID"],
                        r["SKU_ID"],
                        r["Product_Name"],
                        r["Demand_Class"],
                        r["Current_Location"],
                        r["Recommended_Location"],
                        float(r["Distance"]),
                        r["Recommendation_Status"],
                        r["Reason"],
                    ),
                )

            # Sync ROUTE_RESULTS
            logger.info("Syncing ROUTE_RESULTS to Snowflake...")
            cursor.execute("TRUNCATE TABLE IF EXISTS ROUTE_RESULTS")

            # Merge route sequences into comparison df
            b_seq = baseline_routes_df.set_index("Order_ID")["Route_Sequence"].to_dict()
            o_seq = optimized_routes_df.set_index("Order_ID")["Route_Sequence"].to_dict()

            for _, r in route_comparison_df.iterrows():
                oid = r["Order_ID"]
                cursor.execute(
                    """
                    INSERT INTO ROUTE_RESULTS
                    (ORDER_ID, BASELINE_ROUTE_SEQUENCE, OPTIMIZED_ROUTE_SEQUENCE, BASELINE_DISTANCE,
                     ROUTE_ONLY_DISTANCE, SLOT_ONLY_DISTANCE,
                     OPTIMIZED_DISTANCE, DISTANCE_SAVED, PCT_DISTANCE_REDUCTION, BASELINE_TIME_SEC,
                     OPTIMIZED_TIME_SEC, TIME_SAVED_SEC, ROUTE_STATUS, NOTES)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        oid,
                        b_seq.get(oid, ""),
                        o_seq.get(oid, ""),
                        float(r["Baseline_Distance"]),
                        float(r.get("Route_Only_Distance", 0.0)),
                        float(r.get("Slot_Only_Distance", 0.0)),
                        float(r["Optimized_Distance"]),
                        float(r["Distance_Saved"]),
                        float(r["Pct_Distance_Reduction"]),
                        float(r["Baseline_Time_Sec"]),
                        float(r["Optimized_Time_Sec"]),
                        float(r["Time_Saved_Sec"]),
                        r["Route_Status"],
                        r["Notes"],
                    ),
                )

            # Sync REPLENISHMENT_ALERTS
            logger.info("Syncing REPLENISHMENT_ALERTS to Snowflake...")
            cursor.execute("TRUNCATE TABLE IF EXISTS REPLENISHMENT_ALERTS")
            for _, r in replenishment_df.iterrows():
                cursor.execute(
                    """
                    INSERT INTO REPLENISHMENT_ALERTS
                    (SKU_ID, PRODUCT_NAME, CURRENT_STOCK, MINIMUM_STOCK, STOCK_STATUS, REPLENISHMENT_REQUIRED)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        r["SKU_ID"],
                        r["Product_Name"],
                        int(r["Current_Stock"]),
                        int(r["Minimum_Stock"]),
                        r["Stock_Status"],
                        r["Replenishment_Required"],
                    ),
                )

            conn.commit()
            conn.close()
            logger.info("Successfully synced all optimization results to Snowflake!")
            return True
        except Exception as e:
            logger.error(f"Failed to sync results to Snowflake: {e}")
            return False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    sync = SnowflakeSync()
    is_ok, msg = sync.test_connection()
    logger.info(f"Snowflake Connection Check: configured={sync.configured} | message={msg}")

    # Check if outputs exist
    out_dir = Path("outputs")
    if (out_dir / "slot_recommendations.csv").exists():
        logger.info("Outputs found locally. Ready for Snowflake sync.")
    else:
        logger.info("No local outputs found. Run 'python -m src.optimization_engine.main' first.")


if __name__ == "__main__":
    main()

