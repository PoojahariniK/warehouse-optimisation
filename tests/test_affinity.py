import pytest
import pandas as pd
from pathlib import Path
from src.optimization_engine.affinity import calculate_order_affinity, get_sku_affinity_partners
from src.optimization_engine.slot_recommender import recommend_slots
from src.optimization_engine.aisle_network import build_warehouse_graph


@pytest.fixture
def sample_orders_and_products():
    products_df = pd.DataFrame([
        {"SKU_ID": "SKU001", "Product_Name": "Laptop", "Category": "Computing", "Required_Capacity": 10, "Current_Location": "D04", "Hazard_Class": "GENERAL"},
        {"SKU_ID": "SKU002", "Product_Name": "Tablet", "Category": "Computing", "Required_Capacity": 10, "Current_Location": "D05", "Hazard_Class": "GENERAL"},
        {"SKU_ID": "SKU007", "Product_Name": "Wireless Mouse", "Category": "Accessories", "Required_Capacity": 5, "Current_Location": "B03", "Hazard_Class": "GENERAL"},
    ])

    order_lines_df = pd.DataFrame([
        {"Order_ID": "ORD001", "SKU_ID": "SKU001", "Quantity": 1},
        {"Order_ID": "ORD001", "SKU_ID": "SKU007", "Quantity": 2},
        {"Order_ID": "ORD002", "SKU_ID": "SKU001", "Quantity": 1},
        {"Order_ID": "ORD002", "SKU_ID": "SKU007", "Quantity": 1},
        {"Order_ID": "ORD003", "SKU_ID": "SKU002", "Quantity": 1},
        {"Order_ID": "ORD003", "SKU_ID": "SKU007", "Quantity": 1},
    ])

    return order_lines_df, products_df


def test_order_affinity_calculation(sample_orders_and_products):
    order_lines_df, products_df = sample_orders_and_products
    pairs_df, matrix_df = calculate_order_affinity(
        order_lines_df, products_df, min_co_occurrence=1, output_path=None, matrix_path=None
    )

    assert not pairs_df.empty
    assert "Co_Occurrence_Count" in pairs_df.columns
    assert "Affinity_Score" in pairs_df.columns
    assert "Jaccard_Index" in pairs_df.columns

    # SKU001 + SKU007 co-occur in 2 orders
    pair_001_007 = pairs_df[
        ((pairs_df["SKU_A"] == "SKU001") & (pairs_df["SKU_B"] == "SKU007")) |
        ((pairs_df["SKU_A"] == "SKU007") & (pairs_df["SKU_B"] == "SKU001"))
    ]
    assert not pair_001_007.empty
    assert pair_001_007.iloc[0]["Co_Occurrence_Count"] == 2


def test_co_occurrence_matrix_symmetry(sample_orders_and_products):
    order_lines_df, products_df = sample_orders_and_products
    _, matrix_df = calculate_order_affinity(
        order_lines_df, products_df, min_co_occurrence=1, output_path=None, matrix_path=None
    )

    # Matrix should be symmetric: count(A, B) == count(B, A)
    assert matrix_df.loc["SKU001", "SKU007"] == matrix_df.loc["SKU007", "SKU001"]
    assert matrix_df.loc["SKU001", "SKU007"] == 2
    # Diagonal should be 0
    assert matrix_df.loc["SKU001", "SKU001"] == 0


def test_get_sku_affinity_partners(sample_orders_and_products):
    order_lines_df, products_df = sample_orders_and_products
    pairs_df, _ = calculate_order_affinity(
        order_lines_df, products_df, min_co_occurrence=1, output_path=None, matrix_path=None
    )

    partners_001 = get_sku_affinity_partners("SKU001", pairs_df, min_count=1)
    assert len(partners_001) > 0
    partner_skus = [p[0] for p in partners_001]
    assert "SKU007" in partner_skus

