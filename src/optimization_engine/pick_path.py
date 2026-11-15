"""
Pick-Path Optimization Module.
Calculates baseline order picking routes and optimized Nearest Neighbor routes,
and compares operational travel distance and estimated picking time.

Distance Model: Aisle-constrained shortest-path distance using Dijkstra's algorithm
on a warehouse graph (see aisle_network.py). This replaces the previous Euclidean
straight-line approximation and provides realistic walking distances along aisles.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math
import pandas as pd
import logging

from src.optimization_engine.aisle_network import (
    build_warehouse_graph,
    get_dispatch_node,
    find_shortest_path,
    get_shortest_distance,
    Graph,
)

logger = logging.getLogger(__name__)


def calculate_picking_time(
    distance: float,
    num_picks: int,
    walking_speed: float = 1.2,
    pick_handling_time: float = 15.0,
) -> float:
    """
    Estimates order picking time in seconds.

    Args:
        distance: Total travel distance in warehouse units.
        num_picks: Number of distinct pick stops visited.
        walking_speed: Picker travel speed in distance units per second (default 1.2).
        pick_handling_time: Time spent handling/picking at each location in seconds (default 15.0).

    Returns:
        Estimated total picking time in seconds.
    """
    travel_time = distance / walking_speed if walking_speed > 0 else 0.0
    handling_time = num_picks * pick_handling_time
    return round(travel_time + handling_time, 2)


def calculate_baseline_routes(
    order_lines_df: pd.DataFrame,
    products_df: pd.DataFrame,
    locations_df: pd.DataFrame,
    location_overrides: Optional[Dict[str, str]] = None,
    dispatch_point: Tuple[float, float] = (0.0, 0.0),
    walking_speed: float = 1.2,
    pick_handling_time: float = 15.0,
    output_path: Optional[str] = "outputs/baseline_routes.csv",
    graph: Optional[Graph] = None,
    dispatch_node: Optional[str] = None,
) -> pd.DataFrame:
    """
    Calculates baseline picking routes for all orders:
    - Uses existing product storage locations (or location_overrides if provided).
    - Follows original order-line sequence.
    - Visits each distinct required location only once.
    - Starts and ends at the configurable dispatch point.
    - Distances are calculated using aisle-constrained shortest-path (Dijkstra).
    """
    logger.info("Calculating baseline routes using original sequence...")

    # Build graph if not supplied
    if graph is None:
        graph = build_warehouse_graph(locations_df)
    if dispatch_node is None:
        dispatch_node = get_dispatch_node(graph, dispatch_point, locations_df)

    # Map SKU to Location_ID (with overrides if provided)
    loc_overrides = location_overrides or {}
    sku_to_loc_id: Dict[str, str] = {
        row["SKU_ID"]: loc_overrides.get(row["SKU_ID"], row["Current_Location"])
        for _, row in products_df.iterrows()
    }

    results = []

    # Preserve order of orders as they appear
    order_ids = order_lines_df["Order_ID"].unique()

    for order_id in order_ids:
        lines = order_lines_df[order_lines_df["Order_ID"] == order_id]

        # Extract distinct locations visited in order of occurrence
        visited_locs: List[str] = []
        for _, line in lines.iterrows():
            sku = line["SKU_ID"]
            if sku in sku_to_loc_id:
                lid = sku_to_loc_id[sku]
                if lid not in visited_locs:
                    visited_locs.append(lid)

        # Calculate aisle-network distance: dispatch → loc1 → loc2 → … → dispatch
        total_dist = 0.0
        current_node = dispatch_node

        for loc_id in visited_locs:
            segment_dist = get_shortest_distance(graph, current_node, loc_id)
            total_dist += segment_dist
            current_node = loc_id

        # Return to dispatch
        total_dist += get_shortest_distance(graph, current_node, dispatch_node)
        total_dist = round(total_dist, 2)

        est_time = calculate_picking_time(
            total_dist, len(visited_locs), walking_speed, pick_handling_time
        )
        dispatch_label = dispatch_node
        route_str = (
            f"START({dispatch_label}) -> "
            + " -> ".join(visited_locs)
            + f" -> END({dispatch_label})"
        )

        results.append(
            {
                "Order_ID": order_id,
                "Route_Sequence": route_str,
                "Locations_Visited": " -> ".join(visited_locs),
                "Stops_Count": len(visited_locs),
                "Total_Distance": total_dist,
                "Estimated_Time_Sec": est_time,
            }
        )

    baseline_df = pd.DataFrame(results)
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        baseline_df.to_csv(out_file, index=False)
        logger.info(f"Baseline routes saved to {out_file.resolve()}")

    return baseline_df


def calculate_optimized_routes(
    order_lines_df: pd.DataFrame,
    products_df: pd.DataFrame,
    locations_df: pd.DataFrame,
    location_overrides: Optional[Dict[str, str]] = None,
    dispatch_point: Tuple[float, float] = (0.0, 0.0),
    walking_speed: float = 1.2,
    pick_handling_time: float = 15.0,
    output_path: Optional[str] = "outputs/optimized_routes.csv",
    graph: Optional[Graph] = None,
    dispatch_node: Optional[str] = None,
) -> pd.DataFrame:
    """
    Calculates optimized picking routes using the Nearest Neighbor algorithm:
    - Uses recommended storage locations for approved/proposed slot changes (if provided).
    - Starts at the configurable dispatch point.
    - At every step, greedily selects the nearest unvisited picking location
      (measured by aisle-network shortest-path distance).
    - Returns to the dispatch point after the final pick.
    """
    logger.info("Calculating optimized routes using Nearest Neighbor algorithm...")

    # Build graph if not supplied
    if graph is None:
        graph = build_warehouse_graph(locations_df)
    if dispatch_node is None:
        dispatch_node = get_dispatch_node(graph, dispatch_point, locations_df)

    # Build SKU to location mapping with any proposed overrides
    loc_overrides = location_overrides or {}
    sku_to_loc_id: Dict[str, str] = {}
    for _, r in products_df.iterrows():
        sku = r["SKU_ID"]
        loc_id = loc_overrides.get(sku, r["Current_Location"])
        sku_to_loc_id[sku] = loc_id

    results = []
    order_ids = order_lines_df["Order_ID"].unique()

    for order_id in order_ids:
        lines = order_lines_df[order_lines_df["Order_ID"] == order_id]

        # Collect distinct stops required for this order
        required_stops: List[str] = []
        for _, line in lines.iterrows():
            sku = line["SKU_ID"]
            if sku in sku_to_loc_id:
                lid = sku_to_loc_id[sku]
                if lid not in required_stops:
                    required_stops.append(lid)

        # Nearest Neighbor route construction using aisle-network distances
        unvisited: List[str] = list(required_stops)
        current_node_id = dispatch_node
        visited_sequence: List[str] = []
        total_dist = 0.0

        while unvisited:
            nearest_loc: Optional[str] = None
            min_dist = float("inf")
            for loc_id in unvisited:
                d = get_shortest_distance(graph, current_node_id, loc_id)
                if d < min_dist:
                    min_dist = d
                    nearest_loc = loc_id

            if nearest_loc is not None:
                total_dist += min_dist
                current_node_id = nearest_loc
                visited_sequence.append(nearest_loc)
                unvisited.remove(nearest_loc)

        # Return to dispatch point
        total_dist += get_shortest_distance(graph, current_node_id, dispatch_node)
        total_dist = round(total_dist, 2)

        est_time = calculate_picking_time(
            total_dist, len(visited_sequence), walking_speed, pick_handling_time
        )
        dispatch_label = dispatch_node
        route_str = (
            f"START({dispatch_label}) -> "
            + " -> ".join(visited_sequence)
            + f" -> END({dispatch_label})"
        )

        results.append(
            {
                "Order_ID": order_id,
                "Route_Sequence": route_str,
                "Locations_Visited": " -> ".join(visited_sequence),
                "Stops_Count": len(visited_sequence),
                "Total_Distance": total_dist,
                "Estimated_Time_Sec": est_time,
            }
        )

    optimized_df = pd.DataFrame(results)
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        optimized_df.to_csv(out_file, index=False)
        logger.info(f"Optimized routes saved to {out_file.resolve()}")

    return optimized_df


def compare_routes(
    baseline_df: pd.DataFrame,
    optimized_df: pd.DataFrame,
    output_path: Optional[str] = "outputs/route_comparison.csv",
    route_only_df: Optional[pd.DataFrame] = None,
    slot_only_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Compares baseline and optimized routes across all orders,
    calculates distance and time savings, and identifies cases where Nearest Neighbor was worse.
    Supports 4-way evaluation (Old Baseline, Route-Only NN, Slot-Only Naive, Dual Optimization).
    """
    logger.info("Comparing baseline and optimized routes...")

    merged = baseline_df.merge(
        optimized_df,
        on="Order_ID",
        suffixes=("_Baseline", "_Optimized"),
    )

    ro_map = (
        route_only_df.set_index("Order_ID")["Total_Distance"].to_dict()
        if route_only_df is not None and "Total_Distance" in route_only_df.columns
        else {}
    )
    so_map = (
        slot_only_df.set_index("Order_ID")["Total_Distance"].to_dict()
        if slot_only_df is not None and "Total_Distance" in slot_only_df.columns
        else {}
    )

    comparison_rows = []
    worse_cases_count = 0

    for _, row in merged.iterrows():
        oid = row["Order_ID"]
        b_dist = row["Total_Distance_Baseline"]
        o_dist = row["Total_Distance_Optimized"]
        b_time = row["Estimated_Time_Sec_Baseline"]
        o_time = row["Estimated_Time_Sec_Optimized"]

        dist_saved = round(b_dist - o_dist, 2)
        pct_reduction = round((dist_saved / b_dist) * 100, 2) if b_dist > 0 else 0.0
        time_saved = round(b_time - o_time, 2)

        ro_dist = ro_map.get(oid, o_dist)
        so_dist = so_map.get(oid, o_dist)

        if dist_saved > 0:
            status = "IMPROVED"
            note = f"Combined slotting & routing reduced travel distance by {dist_saved:.2f} ({pct_reduction:.1f}%)"
        elif dist_saved < 0:
            status = "WORSE"
            worse_cases_count += 1
            note = (
                f"Nearest Neighbor heuristic performed WORSE than baseline by {abs(dist_saved):.2f} "
                f"({abs(pct_reduction):.1f}% longer) due to greedy local choice causing suboptimal return leg."
            )
        else:
            status = "IDENTICAL"
            note = "Route distance identical to baseline"

        comparison_rows.append(
            {
                "Order_ID": oid,
                "Baseline_Distance": b_dist,
                "Route_Only_Distance": ro_dist,
                "Slot_Only_Distance": so_dist,
                "Optimized_Distance": o_dist,
                "Distance_Saved": dist_saved,
                "Pct_Distance_Reduction": pct_reduction,
                "Baseline_Time_Sec": b_time,
                "Optimized_Time_Sec": o_time,
                "Time_Saved_Sec": time_saved,
                "Route_Status": status,
                "Notes": note,
            }
        )

    comparison_df = pd.DataFrame(comparison_rows)

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        comparison_df.to_csv(out_file, index=False)
        logger.info(f"Route comparison report saved to {out_file.resolve()}")

    avg_saved_pct = comparison_df["Pct_Distance_Reduction"].mean()
    logger.info(
        f"Route comparison complete: Average distance reduction = {avg_saved_pct:.2f}%. "
        f"Cases where NN was worse: {worse_cases_count}/{len(comparison_df)} orders."
    )

    return comparison_df

