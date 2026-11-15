"""
Data Loader Module for Warehouse Optimization Engine.
Connects directly to Snowflake using snowflake.connector and pandas.read_sql()
to pull historical warehouse tables (PRODUCTS, WAREHOUSE_LOCATIONS, ORDER_LINES, INVENTORY).
Securely loads credentials from environment variables / .env.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
import pandas as pd

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

EXPECTED_SCHEMAS = {
    "products": {
        "filename": "products_clean.csv",
        "table_name": "PRODUCTS",
        "required_columns": [
            "SKU_ID",
            "Product_Name",
            "Category",
            "Required_Capacity",
            "Current_Location",
        ],
        "numeric_columns": ["Required_Capacity"],
    },
    "locations": {
        "filename": "warehouse_locations_clean.csv",
        "table_name": "WAREHOUSE_LOCATIONS",
        "required_columns": [
            "Location_ID",
            "Aisle",
            "X",
            "Y",
            "Capacity",
            "Status",
            "Allowed_Category",
        ],
        "numeric_columns": ["X", "Y", "Capacity"],
    },
    "order_lines": {
        "filename": "order_lines_clean.csv",
        "table_name": "ORDER_LINES",
        "required_columns": [
            "Order_Line_ID",
            "Order_ID",
            "Order_Date",
            "SKU_ID",
            "Quantity",
        ],
        "numeric_columns": ["Quantity"],
    },
    "inventory": {
        "filename": "inventory_clean.csv",
        "table_name": "INVENTORY",
        "required_columns": ["SKU_ID", "Current_Stock", "Minimum_Stock"],
        "numeric_columns": ["Current_Stock", "Minimum_Stock"],
    },
}

COLUMN_MAPPINGS = {
    "sku_id": "SKU_ID",
    "product_name": "Product_Name",
    "category": "Category",
    "required_capacity": "Required_Capacity",
    "current_location": "Current_Location",
    "hazard_class": "Hazard_Class",
    "location_id": "Location_ID",
    "aisle": "Aisle",
    "x": "X",
    "y": "Y",
    "capacity": "Capacity",
    "status": "Status",
    "allowed_category": "Allowed_Category",
    "hazard_allowed": "Hazard_Allowed",
    "order_line_id": "Order_Line_ID",
    "order_id": "Order_ID",
    "order_date": "Order_Date",
    "quantity": "Quantity",
    "current_stock": "Current_Stock",
    "minimum_stock": "Minimum_Stock",
}


def get_snowflake_credentials() -> Dict[str, str]:
    """
    Securely reads Snowflake connection parameters from environment variables / .env.
    """
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT", "").strip(),
        "user": os.getenv("SNOWFLAKE_USER", "").strip(),
        "password": os.getenv("SNOWFLAKE_PASSWORD", "").strip(),
        "database": os.getenv("SNOWFLAKE_DATABASE", "CAPSTONE_12_DB").strip(),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "CLEAN").strip(),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CAP12_WH").strip(),
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN").strip(),
    }


def standardize_dataset(df: pd.DataFrame, dataset_key: str) -> pd.DataFrame:
    """
    Normalizes column casing, trims string fields, casts numerics, and assigns default hazard tags.
    """
    df = df.copy()
    # Normalize column casing (e.g. PRODUCT_NAME -> Product_Name)
    df = df.rename(columns={col: COLUMN_MAPPINGS.get(col.lower(), col) for col in df.columns})

    schema = EXPECTED_SCHEMAS[dataset_key]
    missing = set(schema["required_columns"]) - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset '{dataset_key}' is missing required columns: {sorted(list(missing))}"
        )

    # Trim whitespace on string/object columns
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()

    # Convert numeric columns
    for num_col in schema["numeric_columns"]:
        try:
            df[num_col] = pd.to_numeric(df[num_col], errors="raise")
        except Exception as e:
            raise ValueError(
                f"Failed to convert column '{num_col}' in {dataset_key} to numeric: {str(e)}"
            )

    # Default hazard metadata
    if dataset_key == "products" and "Hazard_Class" not in df.columns:
        df["Hazard_Class"] = "GENERAL"
    if dataset_key == "locations" and "Hazard_Allowed" not in df.columns:
        df["Hazard_Allowed"] = "GENERAL"

    return df


def _load_local_csv(
    base_dir: str = "datasets/cleaned",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Internal loader for local CSV fixtures used during offline test execution.
    """
    data_dir = Path(base_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Cleaned datasets directory not found at: {data_dir.resolve()}")

    loaded = {}
    for key, schema in EXPECTED_SCHEMAS.items():
        file_path = data_dir / schema["filename"]
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required dataset file: {schema['filename']} at {file_path.resolve()}")
        raw_df = pd.read_csv(file_path)
        loaded[key] = standardize_dataset(raw_df, key)

    return (
        loaded["products"],
        loaded["locations"],
        loaded["order_lines"],
        loaded["inventory"],
    )


def load_data_from_snowflake(
    fallback_to_csv: bool = False,
    fallback_dir: str = "datasets/cleaned",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Connects to Snowflake using snowflake.connector, and executes pandas.read_sql()
    to pull the 4 historical warehouse datasets:
      - PRODUCTS
      - WAREHOUSE_LOCATIONS
      - ORDER_LINES
      - INVENTORY

    Credentials are securely loaded from .env.
    If fallback_to_csv is True and Snowflake connection is unreachable (e.g. offline CI/tests),
    it falls back to local cleaned CSV files.
    """
    creds = get_snowflake_credentials()
    missing = [k for k in ["account", "user", "password"] if not creds.get(k)]

    if not missing:
        try:
            import snowflake.connector
            logger.info(
                f"Connecting to Snowflake [{creds['account']}] as '{creds['user']}' "
                f"(DB: {creds['database']}, Schema: {creds['schema']}, Warehouse: {creds['warehouse']})..."
            )
            conn = snowflake.connector.connect(
                account=creds["account"],
                user=creds["user"],
                password=creds["password"],
                database=creds["database"],
                schema=creds["schema"],
                warehouse=creds["warehouse"],
                role=creds["role"],
            )

            logger.info("Executing pandas.read_sql() directly against Snowflake tables...")
            products_raw = pd.read_sql("SELECT * FROM PRODUCTS", conn)
            locations_raw = pd.read_sql("SELECT * FROM WAREHOUSE_LOCATIONS", conn)
            order_lines_raw = pd.read_sql("SELECT * FROM ORDER_LINES", conn)
            inventory_raw = pd.read_sql("SELECT * FROM INVENTORY", conn)
            conn.close()

            products_df = standardize_dataset(products_raw, "products")
            locations_df = standardize_dataset(locations_raw, "locations")
            order_lines_df = standardize_dataset(order_lines_raw, "order_lines")
            inventory_df = standardize_dataset(inventory_raw, "inventory")

            logger.info(
                f"Successfully pulled {len(products_df)} products, {len(locations_df)} locations, "
                f"{len(order_lines_df)} order lines, and {len(inventory_df)} inventory records directly from Snowflake."
            )
            return products_df, locations_df, order_lines_df, inventory_df

        except Exception as e:
            if not fallback_to_csv:
                logger.error(f"Failed to read historical data from Snowflake: {e}")
                raise RuntimeError(f"Snowflake direct read failed: {e}") from e
            logger.warning(
                f"Snowflake direct read unavailable ({e}). Falling back to local datasets..."
            )
    else:
        if not fallback_to_csv:
            raise ValueError(f"Missing required Snowflake environment variables: {missing}")
        logger.warning(
            f"Snowflake credentials missing ({missing}). Falling back to local datasets..."
        )

    # Fallback for offline environments and automated unit testing
    return _load_local_csv(fallback_dir)


def load_clean_data(
    base_dir: str = "datasets/cleaned",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Standard loader function maintaining backward-compatibility with tests and tools.
    Loads local CSV fixtures from base_dir (default: datasets/cleaned).
    For live Snowflake direct read, use load_data_from_snowflake().
    """
    return _load_local_csv(base_dir)
