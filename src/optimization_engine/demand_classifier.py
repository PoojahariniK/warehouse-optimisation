"""
Demand Classifier Module.
Calculates SKU order frequency, total quantity, and classifies SKUs into Fast, Medium, and Slow.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def classify_frequency(freq: int, fast_threshold: int = 10, medium_threshold: int = 4) -> str:
    """
    Classifies a frequency count into Fast, Medium, or Slow.
    """
    if freq >= fast_threshold:
        return "Fast"
    elif freq >= medium_threshold:
        return "Medium"
    else:
        return "Slow"


def classify_demand(
    order_lines_df: pd.DataFrame,
    products_df: pd.DataFrame,
    output_path: Optional[str] = "outputs/demand_analysis.csv",
    summary_path: Optional[str] = "outputs/demand_summary.csv",
    fast_threshold: int = 10,
    medium_threshold: int = 4,
) -> pd.DataFrame:
    """
    Computes order frequency (number of order lines) and total quantity per SKU,
    assigns Demand_Class, and merges with product metadata.

    Args:
        order_lines_df: DataFrame of order lines with SKU_ID and Quantity.
        products_df: DataFrame of products with SKU_ID, Product_Name, Category, Current_Location.
        output_path: File path to save the demand analysis CSV.
        summary_path: File path to save the demand class distribution summary CSV.
        fast_threshold: Threshold for Fast demand (inclusive).
        medium_threshold: Threshold for Medium demand (inclusive).

    Returns:
        DataFrame containing demand classification metrics.
    """
    logger.info("Computing demand frequency and total quantity per SKU...")

    # Group order lines by SKU for total frequency and quantity
    demand_agg = (
        order_lines_df.groupby("SKU_ID")
        .agg(
            Order_Frequency=("Order_Line_ID", "count"),
            Total_Quantity=("Quantity", "sum"),
        )
        .reset_index()
    )

    # Compute daily demand volatility (Coefficient of Variation: CV = std / mean)
    if "Order_Date" in order_lines_df.columns:
        daily_sku = (
            order_lines_df.groupby(["SKU_ID", "Order_Date"])["Quantity"]
            .sum()
            .unstack(fill_value=0)
        )
        daily_mean = daily_sku.mean(axis=1)
        daily_std = daily_sku.std(axis=1)
        cv_series = (daily_std / (daily_mean + 1e-6)).round(2)
        vol_df = pd.DataFrame({
            "SKU_ID": cv_series.index,
            "Demand_CV": cv_series.values,
        })
        vol_df["Volatility_Class"] = vol_df["Demand_CV"].apply(
            lambda cv: "STABLE" if cv <= 1.2 else ("MODERATE" if cv <= 1.6 else "VOLATILE")
        )
        demand_agg = demand_agg.merge(vol_df, on="SKU_ID", how="left")
    else:
        demand_agg["Demand_CV"] = 0.0
        demand_agg["Volatility_Class"] = "STABLE"

    # Merge with products to ensure all products are included even with 0 orders
    demand_merged = products_df.merge(demand_agg, on="SKU_ID", how="left")
    demand_merged["Order_Frequency"] = demand_merged["Order_Frequency"].fillna(0).astype(int)
    demand_merged["Total_Quantity"] = demand_merged["Total_Quantity"].fillna(0).astype(int)
    demand_merged["Demand_CV"] = demand_merged["Demand_CV"].fillna(0.0).astype(float)
    demand_merged["Volatility_Class"] = demand_merged["Volatility_Class"].fillna("STABLE")

    # Classify demand
    demand_merged["Demand_Class"] = demand_merged["Order_Frequency"].apply(
        lambda f: classify_frequency(f, fast_threshold, medium_threshold)
    )

    # Arrange target columns
    target_columns = [
        "SKU_ID",
        "Product_Name",
        "Category",
        "Hazard_Class",
        "Current_Location",
        "Order_Frequency",
        "Total_Quantity",
        "Demand_CV",
        "Volatility_Class",
        "Demand_Class",
    ]
    # Filter to existing columns in target order
    final_cols = [c for c in target_columns if c in demand_merged.columns]
    result_df = demand_merged[final_cols].sort_values(
        by=["Order_Frequency", "Total_Quantity"], ascending=[False, False]
    ).reset_index(drop=True)

    # Save to output_path if provided
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(out_file, index=False)
        logger.info(f"Demand analysis saved to {out_file.resolve()}")

    # Save demand summary if provided
    if summary_path:
        sum_file = Path(summary_path)
        sum_file.parent.mkdir(parents=True, exist_ok=True)
        summary_df = (
            result_df["Demand_Class"]
            .value_counts()
            .reindex(["Fast", "Medium", "Slow"])
            .fillna(0)
            .astype(int)
            .reset_index()
        )
        summary_df.columns = ["Demand_Class", "Product_Count"]
        summary_df.to_csv(sum_file, index=False)
        logger.info(f"Demand summary saved to {sum_file.resolve()}")

    counts = result_df["Demand_Class"].value_counts().to_dict()
    logger.info(f"Demand classification complete: {counts}")

    return result_df

