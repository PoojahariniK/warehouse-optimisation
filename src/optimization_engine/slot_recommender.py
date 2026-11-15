from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import math
import pandas as pd
import logging

from src.optimization_engine.aisle_network import (
    build_warehouse_graph,
    get_dispatch_node,
    get_shortest_distance,
    Graph,
)
from src.optimization_engine.affinity import get_sku_affinity_partners

logger = logging.getLogger(__name__)


def recommend_slots(
    products_df: pd.DataFrame,
    locations_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    dispatch_point: Tuple[float, float] = (0.0, 0.0),
    output_path: Optional[str] = "outputs/slot_recommendations.csv",
    graph: Optional[Graph] = None,
    dispatch_node: Optional[str] = None,
    affinity_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Generates slot recommendations for products into currently empty locations.

    Ranking & Assignment Algorithm:
    1. Filter locations where Status == 'EMPTY'.
    2. Calculate aisle-network shortest-path distance from each empty location to the
       configurable dispatch point (using Dijkstra's algorithm on the warehouse graph).
    3. Rank empty locations by aisle-network distance to dispatch point ascending (closest first).
    4. Rank products by Demand_Class (Fast > Medium > Slow), then Order_Frequency descending,
       then Total_Quantity descending.
    5. For each prioritized product, search for the best available empty location that satisfies:
       - Location is not already allocated to another product in this run (1-to-1).
       - Location Capacity >= Product Required_Capacity.
       - Location Allowed_Category is 'ALL' or matches Product Category (case-insensitive).
    6. If a compatible empty location is found, assign it with status 'RECOMMENDED'.
    7. If no compatible empty location exists (either due to constraints or all empty locations
       being assigned), assign status 'NO_FEASIBLE_LOCATION' with an explainable reason.
    8. Existing product locations remain untouched until supervisor approves.

    Args:
        products_df:   Products master DataFrame.
        locations_df:  Warehouse locations master DataFrame.
        demand_df:     Demand analysis DataFrame containing Demand_Class, Order_Frequency,
                       Total_Quantity.
        dispatch_point: (X, Y) coordinates of the dispatch / depot point.
        output_path:   Path to save recommendations CSV.
        graph:         Pre-built warehouse aisle-network graph (optional — built from
                       locations_df if not supplied).
        dispatch_node: Graph node ID for the dispatch point (optional — resolved from
                       dispatch_point if not supplied).

    Returns:
        DataFrame containing slot recommendations.
    """
    logger.info(
        f"Starting slot recommendation with dispatch point at {dispatch_point}..."
    )

    # Build graph if not supplied
    if graph is None:
        graph = build_warehouse_graph(locations_df)
    if dispatch_node is None:
        dispatch_node = get_dispatch_node(graph, dispatch_point, locations_df)

    # 1. Merge products with demand information
    prod_data = products_df.copy()
    if "Demand_Class" not in prod_data.columns:
        prod_data = prod_data.merge(
            demand_df[["SKU_ID", "Demand_Class", "Order_Frequency", "Total_Quantity"]],
            on="SKU_ID",
            how="left",
        )

    # Map priority: Fast (1), Medium (2), Slow (3)
    priority_map = {"Fast": 1, "Medium": 2, "Slow": 3}
    prod_data["Priority"] = prod_data["Demand_Class"].map(priority_map).fillna(4)

    # Sort products: Priority asc, Order_Frequency desc, Total_Quantity desc, SKU_ID asc
    sorted_products = prod_data.sort_values(
        by=["Priority", "Order_Frequency", "Total_Quantity", "SKU_ID"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)

    # 2. Extract and evaluate EMPTY locations only
    empty_locs = locations_df[locations_df["Status"] == "EMPTY"].copy()
    logger.info(f"Identified {len(empty_locs)} empty locations in warehouse.")

    if empty_locs.empty:
        logger.warning("No empty locations available in warehouse.")

    # Calculate aisle-network shortest-path distance to dispatch node
    empty_locs["Distance_To_Dispatch"] = empty_locs["Location_ID"].apply(
        lambda loc_id: get_shortest_distance(graph, dispatch_node, loc_id)
    )

    # Sort empty locations: closest to dispatch point first, then higher capacity first
    sorted_empty = empty_locs.sort_values(
        by=["Distance_To_Dispatch", "Capacity"], ascending=[True, False]
    ).reset_index(drop=True)

    # 3. Perform 1-to-1 feasible assignments with Order Affinity Clustering
    assigned_location_ids: Set[str] = set()
    recommendation_rows: List[Dict] = []
    rec_counter = 1

    # Track dynamic locations of SKUs for affinity proximity calculations
    sku_current_locations = dict(zip(products_df["SKU_ID"], products_df["Current_Location"]))
    prod_name_map = dict(zip(products_df["SKU_ID"], products_df["Product_Name"]))

    for _, prod in sorted_products.iterrows():
        sku = prod["SKU_ID"]
        pname = prod["Product_Name"]
        dclass = prod["Demand_Class"]
        curr_loc = prod["Current_Location"]
        req_cap = prod["Required_Capacity"]
        category = str(prod["Category"]).strip().upper()
        prod_hazard = str(prod.get("Hazard_Class", "GENERAL")).strip().upper()

        current_dist = get_shortest_distance(graph, dispatch_node, curr_loc)
        assigned = False

        # Get top affinity partners for this SKU
        affinity_partners = (
            get_sku_affinity_partners(sku, affinity_df, min_count=2)
            if affinity_df is not None
            else []
        )

        feasible_candidates = []

        for _, eloc in sorted_empty.iterrows():
            loc_id = eloc["Location_ID"]
            loc_cap = eloc["Capacity"]
            allowed_cat = str(eloc["Allowed_Category"]).strip().upper()
            loc_hazard = str(eloc.get("Hazard_Allowed", "GENERAL")).strip().upper()
            loc_dist = eloc["Distance_To_Dispatch"]

            # Check if already assigned
            if loc_id in assigned_location_ids:
                continue

            # Check capacity
            if loc_cap < req_cap:
                continue

            # Check category compatibility
            if allowed_cat != "ALL" and allowed_cat != category:
                continue

            # Check hazard compatibility
            if prod_hazard != "GENERAL" and loc_hazard != prod_hazard and loc_hazard != "ALL":
                continue
            if loc_hazard in ["HAZMAT_BATTERY", "HAZMAT_FLAMMABLE"] and prod_hazard != loc_hazard:
                continue

            # Check distance improvement (only relocate if candidate is closer to dispatch!)
            dist_saved = round(current_dist - loc_dist, 2)
            if dist_saved <= 0:
                continue

            # Calculate proximity penalty to affinity partners
            affinity_dist = 0.0
            affinity_partner_note = ""
            if affinity_partners:
                total_weight = 0
                weighted_dist = 0.0
                top_partner_sku, top_cnt = affinity_partners[0]
                top_partner_loc = sku_current_locations.get(top_partner_sku, "")

                for partner_sku, p_cnt in affinity_partners:
                    p_loc = sku_current_locations.get(partner_sku)
                    if p_loc and p_loc in graph:
                        d_partner = get_shortest_distance(graph, loc_id, p_loc)
                        weighted_dist += p_cnt * d_partner
                        total_weight += p_cnt

                if total_weight > 0:
                    affinity_dist = weighted_dist / total_weight
                    partner_pname = prod_name_map.get(top_partner_sku, top_partner_sku)
                    affinity_partner_note = (
                        f" Co-ordered with {partner_pname} ({top_partner_sku}, {top_cnt} orders) in {top_partner_loc}."
                    )

            # Composite optimization score: 70% dispatch proximity, 30% affinity clustering
            composite_score = loc_dist + (0.30 * affinity_dist)

            feasible_candidates.append(
                {
                    "loc_id": loc_id,
                    "loc_cap": loc_cap,
                    "allowed_cat": allowed_cat,
                    "loc_dist": loc_dist,
                    "dist_saved": dist_saved,
                    "composite_score": composite_score,
                    "affinity_note": affinity_partner_note,
                }
            )

        if feasible_candidates:
            # Select best candidate by lowest composite score
            feasible_candidates.sort(
                key=lambda c: (c["composite_score"], -c["dist_saved"], -c["loc_cap"])
            )
            best = feasible_candidates[0]
            loc_id = best["loc_id"]
            loc_dist = best["loc_dist"]
            dist_saved = best["dist_saved"]
            loc_cap = best["loc_cap"]
            allowed_cat = best["allowed_cat"]
            aff_note = best["affinity_note"]

            assigned_location_ids.add(loc_id)
            sku_current_locations[sku] = loc_id  # Update mapped location for subsequent assignments

            recommendation_rows.append(
                {
                    "Recommendation_ID": f"REC{rec_counter:03d}",
                    "SKU_ID": sku,
                    "Product_Name": pname,
                    "Demand_Class": dclass,
                    "Current_Location": curr_loc,
                    "Recommended_Location": loc_id,
                    "Distance": round(loc_dist, 2),
                    "Distance_Saved": dist_saved,
                    "Recommendation_Status": "RECOMMENDED",
                    "Reason": (
                        f"Relocation reduces dispatch distance from {current_dist:.1f} to {loc_dist:.1f} "
                        f"(-{dist_saved:.1f} units).{aff_note} Capacity ({loc_cap}>={req_cap}), "
                        f"category '{allowed_cat}', hazard '{prod_hazard}' compliant."
                    ),
                }
            )
            rec_counter += 1
            assigned = True

        if not assigned:
            # Determine specific explanation
            remaining_unassigned = sorted_empty[
                ~sorted_empty["Location_ID"].isin(assigned_location_ids)
            ]
            if remaining_unassigned.empty:
                reason = "All available empty warehouse locations have been allocated to higher-priority products"
            else:
                # Check if any remaining empty location is closer
                closer_locs = remaining_unassigned[remaining_unassigned["Distance_To_Dispatch"] < current_dist]
                if closer_locs.empty:
                    reason = (
                        f"Current location '{curr_loc}' (dispatch distance {current_dist:.1f}) is already closer "
                        f"to dispatch than any remaining empty bin"
                    )
                else:
                    reason = (
                        f"No remaining empty location satisfies capacity (>= {req_cap}), "
                        f"category ('{category}'), and hazard ('{prod_hazard}') constraints"
                    )

            recommendation_rows.append(
                {
                    "Recommendation_ID": f"REC{rec_counter:03d}",
                    "SKU_ID": sku,
                    "Product_Name": pname,
                    "Demand_Class": dclass,
                    "Current_Location": curr_loc,
                    "Recommended_Location": "NONE",
                    "Distance": 0.0,
                    "Distance_Saved": 0.0,
                    "Recommendation_Status": "NO_FEASIBLE_LOCATION",
                    "Reason": reason,
                }
            )
            rec_counter += 1

    recommendations_df = pd.DataFrame(recommendation_rows)

    # Save to file if path provided
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        recommendations_df.to_csv(out_file, index=False)
        logger.info(f"Slot recommendations saved to {out_file.resolve()}")

    rec_counts = recommendations_df["Recommendation_Status"].value_counts().to_dict()
    logger.info(f"Slot recommendations summary: {rec_counts}")

    return recommendations_df

