"""
Validation and Replenishment Module.
Validates warehouse slot compatibility constraints (capacity, category, status, unique assignment)
and generates replenishment alerts based on minimum stock thresholds.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def validate_slot_assignment(
    sku_id: str,
    target_location_id: str,
    products_df: pd.DataFrame,
    locations_df: pd.DataFrame,
    active_assignments: Optional[Set[str]] = None,
) -> Tuple[bool, str]:
    """
    Validates whether an SKU can legally be placed into target_location_id.

    Checks:
    1. SKU and Location existence.
    2. Location is currently EMPTY.
    3. Location is not already allocated in the current batch (active_assignments).
    4. Location Capacity >= Product Required_Capacity.
    5. Location Allowed_Category is 'ALL' or matches Product Category.

    Returns:
        Tuple of (is_valid: bool, reason_message: str).
    """
    # 1. Check SKU existence
    prod_row = products_df[products_df["SKU_ID"] == sku_id]
    if prod_row.empty:
        return False, f"Constraint Violation: SKU '{sku_id}' not found in product master."
    prod = prod_row.iloc[0]

    # 2. Check Location existence
    loc_row = locations_df[locations_df["Location_ID"] == target_location_id]
    if loc_row.empty:
        return False, f"Constraint Violation: Location '{target_location_id}' does not exist in warehouse."
    loc = loc_row.iloc[0]

    # 3. Check Location current status
    if str(loc["Status"]).strip().upper() != "EMPTY":
        return False, f"Constraint Violation: Location '{target_location_id}' is already OCCUPIED."

    # 4. Check duplicate assignment in current batch
    if active_assignments and target_location_id in active_assignments:
        return False, f"Constraint Violation: Location '{target_location_id}' is already assigned to another SKU in this batch."

    # 5. Check Capacity
    req_cap = int(prod["Required_Capacity"])
    loc_cap = int(loc["Capacity"])
    if loc_cap < req_cap:
        return (
            False,
            f"Constraint Violation: Capacity shortfall. Location '{target_location_id}' has capacity {loc_cap}, but SKU '{sku_id}' requires {req_cap}.",
        )

    # 6. Check Category Compatibility
    prod_cat = str(prod["Category"]).strip().upper()
    allowed_cat = str(loc["Allowed_Category"]).strip().upper()
    if allowed_cat != "ALL" and allowed_cat != prod_cat:
        return (
            False,
            f"Constraint Violation: Category mismatch. Location '{target_location_id}' only allows '{allowed_cat}', but SKU '{sku_id}' is '{prod_cat}'.",
        )

    # 7. Check Hazard Compatibility
    prod_hazard = str(prod.get("Hazard_Class", "GENERAL")).strip().upper()
    loc_hazard = str(loc.get("Hazard_Allowed", "GENERAL")).strip().upper()
    if prod_hazard != "GENERAL" and loc_hazard != prod_hazard and loc_hazard != "ALL":
        return (
            False,
            f"Constraint Violation: Hazard mismatch. Product '{sku_id}' ({prod_hazard}) cannot be stored in Location '{target_location_id}' (Certified: '{loc_hazard}').",
        )
    if loc_hazard in ["HAZMAT_BATTERY", "HAZMAT_FLAMMABLE"] and prod_hazard != loc_hazard:
        return (
            False,
            f"Constraint Violation: Zone safety constraint. Dedicated bay '{target_location_id}' ({loc_hazard}) cannot store '{prod_hazard}' item '{sku_id}'.",
        )

    return True, f"Valid assignment: SKU '{sku_id}' ({prod_cat}, Req: {req_cap}, Hazard: {prod_hazard}) fits into Location '{target_location_id}' (Cap: {loc_cap}, Allowed: '{allowed_cat}', Hazard: '{loc_hazard}')."


def check_replenishment_alerts(
    inventory_df: pd.DataFrame,
    products_df: pd.DataFrame,
    output_path: Optional[str] = "outputs/replenishment_alerts.csv",
) -> pd.DataFrame:
    """
    Identifies inventory items requiring replenishment.

    Condition:
        Current_Stock <= Minimum_Stock

    Outputs:
        SKU_ID, Product_Name, Current_Stock, Minimum_Stock, Stock_Status, Replenishment_Required

    Returns:
        DataFrame of replenishment alerts.
    """
    logger.info("Evaluating inventory replenishment status...")

    merged = inventory_df.merge(
        products_df[["SKU_ID", "Product_Name"]],
        on="SKU_ID",
        how="left",
    )

    alert_rows = []
    for _, row in merged.iterrows():
        curr_stock = int(row["Current_Stock"])
        min_stock = int(row["Minimum_Stock"])
        sku = row["SKU_ID"]
        pname = row["Product_Name"]

        if curr_stock <= min_stock:
            if curr_stock == 0:
                stock_status = "OUT_OF_STOCK"
            else:
                stock_status = "LOW_STOCK"

            alert_rows.append(
                {
                    "SKU_ID": sku,
                    "Product_Name": pname,
                    "Current_Stock": curr_stock,
                    "Minimum_Stock": min_stock,
                    "Stock_Status": stock_status,
                    "Replenishment_Required": "YES",
                }
            )

    alerts_df = pd.DataFrame(alert_rows)

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        alerts_df.to_csv(out_file, index=False)
        logger.info(f"Replenishment alerts saved to {out_file.resolve()}")

    logger.info(f"Identified {len(alerts_df)} SKUs requiring replenishment.")
    return alerts_df

