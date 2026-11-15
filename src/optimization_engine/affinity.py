"""
Order Affinity (Market Basket Co-Occurrence) Module.
Analyzes order lines to compute SKU co-occurrence frequencies, Jaccard affinities,
and product association strengths for warehouse layout clustering.
"""

from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def calculate_order_affinity(
    order_lines_df: pd.DataFrame,
    products_df: pd.DataFrame,
    min_co_occurrence: int = 1,
    top_n: int = 25,
    output_path: Optional[str] = "outputs/affinity_pairs.csv",
    matrix_path: Optional[str] = "outputs/affinity_matrix.csv",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes pair-wise SKU co-occurrences and affinity scores across historical orders.

    Affinity Score Metric:
        Affinity(A, B) = Orders(A and B) / sqrt(Orders(A) * Orders(B))   (Cosine Similarity)
        Also computes Jaccard Index: Orders(A and B) / Orders(A or B)

    Args:
        order_lines_df: DataFrame of order lines containing Order_ID and SKU_ID.
        products_df:    DataFrame of products for metadata lookup.
        min_co_occurrence: Minimum number of co-orders required to include pair.
        top_n:          Maximum number of top pairs to output in the summary.
        output_path:    File path to save the top affinity pairs CSV.
        matrix_path:    File path to save the square co-occurrence matrix CSV.

    Returns:
        Tuple of (top_pairs_df, co_occurrence_matrix_df)
    """
    logger.info("Calculating order affinity and SKU co-occurrence matrix...")

    # Build product name map
    prod_name_map = dict(zip(products_df["SKU_ID"], products_df["Product_Name"]))
    prod_cat_map = dict(zip(products_df["SKU_ID"], products_df["Category"]))

    # Individual SKU order counts
    sku_order_counts = (
        order_lines_df.groupby("SKU_ID")["Order_ID"].nunique().to_dict()
    )

    # Compute co-occurrence across orders
    pair_counts: Counter = Counter()
    for _, group in order_lines_df.groupby("Order_ID"):
        skus = sorted(group["SKU_ID"].unique())
        for a, b in combinations(skus, 2):
            pair_counts[(a, b)] += 1

    # Build full square matrix
    all_skus = sorted(products_df["SKU_ID"].unique())
    matrix_df = pd.DataFrame(0, index=all_skus, columns=all_skus)
    for (a, b), cnt in pair_counts.items():
        if a in matrix_df.index and b in matrix_df.columns:
            matrix_df.loc[a, b] = cnt
            matrix_df.loc[b, a] = cnt

    # Build top pairs list
    pair_rows = []
    for (a, b), count in pair_counts.items():
        if count < min_co_occurrence:
            continue
        cnt_a = sku_order_counts.get(a, 0)
        cnt_b = sku_order_counts.get(b, 0)
        union_cnt = cnt_a + cnt_b - count
        jaccard = round(count / union_cnt, 3) if union_cnt > 0 else 0.0
        # Cosine similarity for affinity
        cosine = round(count / ((cnt_a * cnt_b) ** 0.5), 3) if cnt_a > 0 and cnt_b > 0 else 0.0

        pair_rows.append(
            {
                "SKU_A": a,
                "Product_A": prod_name_map.get(a, a),
                "Category_A": prod_cat_map.get(a, "General"),
                "SKU_B": b,
                "Product_B": prod_name_map.get(b, b),
                "Category_B": prod_cat_map.get(b, "General"),
                "Co_Occurrence_Count": count,
                "Orders_A": cnt_a,
                "Orders_B": cnt_b,
                "Affinity_Score": cosine,
                "Jaccard_Index": jaccard,
                "Pair_Label": f"{prod_name_map.get(a, a)} + {prod_name_map.get(b, b)}",
            }
        )

    pairs_df = pd.DataFrame(pair_rows)
    if not pairs_df.empty:
        pairs_df = pairs_df.sort_values(
            by=["Co_Occurrence_Count", "Affinity_Score"], ascending=[False, False]
        ).reset_index(drop=True)

    top_pairs_df = pairs_df.head(top_n)

    if output_path:
        out_f = Path(output_path)
        out_f.parent.mkdir(parents=True, exist_ok=True)
        top_pairs_df.to_csv(out_f, index=False)
        logger.info(f"Top {len(top_pairs_df)} affinity pairs saved to {out_f.resolve()}")

    if matrix_path:
        mat_f = Path(matrix_path)
        mat_f.parent.mkdir(parents=True, exist_ok=True)
        matrix_df.to_csv(mat_f)
        logger.info(f"Full co-occurrence matrix saved to {mat_f.resolve()}")

    return top_pairs_df, matrix_df


def get_sku_affinity_partners(
    sku_id: str,
    affinity_df: pd.DataFrame,
    min_count: int = 2,
) -> List[Tuple[str, int]]:
    """
    Returns list of (partner_sku_id, co_occurrence_count) for a given SKU.
    """
    if affinity_df is None or affinity_df.empty:
        return []

    partners = []
    # Check both SKU_A and SKU_B
    matches_a = affinity_df[affinity_df["SKU_A"] == sku_id]
    for _, row in matches_a.iterrows():
        if row["Co_Occurrence_Count"] >= min_count:
            partners.append((row["SKU_B"], int(row["Co_Occurrence_Count"])))

    matches_b = affinity_df[affinity_df["SKU_B"] == sku_id]
    for _, row in matches_b.iterrows():
        if row["Co_Occurrence_Count"] >= min_count:
            partners.append((row["SKU_A"], int(row["Co_Occurrence_Count"])))

    return sorted(partners, key=lambda x: x[1], reverse=True)

