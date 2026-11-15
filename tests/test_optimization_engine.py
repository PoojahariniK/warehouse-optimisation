"""
Unit and Integration Tests for Python Optimization Engine (CAP-12).
Verifies:
- Demand classification thresholds
- Capacity validation
- Category compatibility
- Empty location filtering
- Unique location assignment
- Replenishment alerts
- Baseline route calculation
- Nearest Neighbor route calculation
- Route distance comparison (including proving a real case where NN is worse)
- Actual dataset verification
- Aisle-network graph construction (new — CAP-12 upgrade)
- Dijkstra's shortest-path correctness (new — CAP-12 upgrade)
- Slot recommendation uses aisle-network distance (new — CAP-12 upgrade)
- Pick-path uses aisle-network distance (new — CAP-12 upgrade)
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.optimization_engine.data_loader import load_clean_data
from src.optimization_engine.demand_classifier import classify_demand, classify_frequency
from src.optimization_engine.slot_recommender import recommend_slots
from src.optimization_engine.pick_path import (
    calculate_baseline_routes,
    calculate_optimized_routes,
    compare_routes,
    calculate_picking_time,
)
from src.optimization_engine.validation import (
    validate_slot_assignment,
    check_replenishment_alerts,
)
from src.optimization_engine.aisle_network import (
    build_warehouse_graph,
    get_dispatch_node,
    find_shortest_path,
    get_shortest_distance,
    validate_graph,
)


@pytest.fixture(scope="module")
def real_datasets():
    """Loads actual cleaned CSV datasets from datasets/cleaned."""
    return load_clean_data("datasets/cleaned")


# 1. Demand Classification Tests
def test_demand_classification_thresholds():
    assert classify_frequency(15) == "Fast"
    assert classify_frequency(10) == "Fast"
    assert classify_frequency(9) == "Medium"
    assert classify_frequency(4) == "Medium"
    assert classify_frequency(3) == "Slow"
    assert classify_frequency(0) == "Slow"


def test_demand_classification_on_actual_data(real_datasets):
    products, _, orders, _ = real_datasets
    demand_df = classify_demand(orders, products, output_path=None, summary_path=None)

    assert len(demand_df) == 30
    counts = demand_df["Demand_Class"].value_counts().to_dict()
    assert counts.get("Fast") == 10
    assert counts.get("Medium") == 10
    assert counts.get("Slow") == 10
    assert (demand_df[demand_df["Demand_Class"] == "Fast"]["Order_Frequency"] >= 10).all()
    assert (
        (demand_df[demand_df["Demand_Class"] == "Medium"]["Order_Frequency"] >= 4)
        & (demand_df[demand_df["Demand_Class"] == "Medium"]["Order_Frequency"] <= 9)
    ).all()
    assert (demand_df[demand_df["Demand_Class"] == "Slow"]["Order_Frequency"] < 4).all()


# 2. Validation Constraints Tests
def test_validate_slot_capacity_violation(real_datasets):
    products, locations, _, _ = real_datasets
    # Create test case where required capacity (50) exceeds location capacity (25 at A02)
    prods_copy = products.copy()
    prods_copy.loc[prods_copy["SKU_ID"] == "SKU001", "Required_Capacity"] = 50
    is_valid, msg = validate_slot_assignment("SKU001", "A02", prods_copy, locations)
    assert not is_valid
    assert "Capacity shortfall" in msg


def test_validate_slot_category_mismatch(real_datasets):
    products, locations, _, _ = real_datasets
    # SKU001 (Laptop, Category: Computing) -> E07 (Allowed_Category: ACCESSORIES, EMPTY)
    is_valid, msg = validate_slot_assignment("SKU001", "E07", products, locations)
    assert not is_valid
    assert "Category mismatch" in msg


def test_validate_occupied_location(real_datasets):
    products, locations, _, _ = real_datasets
    # A01 is already OCCUPIED
    is_valid, msg = validate_slot_assignment("SKU002", "A01", products, locations)
    assert not is_valid
    assert "already OCCUPIED" in msg


def test_validate_duplicate_location_assignment(real_datasets):
    products, locations, _, _ = real_datasets
    # A02 is empty, but marked as already assigned in this batch
    active_assignments = {"A02"}
    is_valid, msg = validate_slot_assignment(
        "SKU001", "A02", products, locations, active_assignments=active_assignments
    )
    assert not is_valid
    assert "already assigned to another SKU" in msg


def test_validate_valid_assignment(real_datasets):
    products, locations, _, _ = real_datasets
    # SKU006 (USB Hub, Accessories, Required_Capacity: 19) -> E07 (Capacity: 30, Allowed: ACCESSORIES, EMPTY)
    is_valid, msg = validate_slot_assignment("SKU006", "E07", products, locations)
    assert is_valid
    assert "Valid assignment" in msg


def test_validate_slot_hazard_violation(real_datasets):
    products, locations, _, _ = real_datasets
    # SKU011 (Power Bank, HAZMAT_BATTERY) -> A02 (Certified GENERAL only, EMPTY)
    is_valid, msg = validate_slot_assignment("SKU011", "A02", products, locations)
    assert not is_valid
    assert "Hazard mismatch" in msg


def test_four_way_route_comparison(real_datasets):
    products, locations, orders, _ = real_datasets
    graph = build_warehouse_graph(locations)
    dispatch_node = get_dispatch_node(graph, (0.0, 0.0), locations)

    # 1. Baseline Old
    baseline = calculate_baseline_routes(
        orders, products, locations, graph=graph, dispatch_node=dispatch_node, output_path=None
    )
    # 2. Route Only NN
    route_only = calculate_optimized_routes(
        orders, products, locations, graph=graph, dispatch_node=dispatch_node, output_path=None
    )

    demand = classify_demand(orders, products, output_path=None, summary_path=None)
    recs = recommend_slots(products, locations, demand, graph=graph, dispatch_node=dispatch_node, output_path=None)
    overrides = {
        r["SKU_ID"]: r["Recommended_Location"]
        for _, r in recs.iterrows()
        if r["Recommendation_Status"] == "RECOMMENDED"
    }

    # 3. Slot Only Naive
    slot_only = calculate_baseline_routes(
        orders, products, locations, location_overrides=overrides, graph=graph, dispatch_node=dispatch_node, output_path=None
    )
    # 4. Dual Opt NN
    dual_opt = calculate_optimized_routes(
        orders, products, locations, location_overrides=overrides, graph=graph, dispatch_node=dispatch_node, output_path=None
    )

    comp = compare_routes(
        baseline_df=baseline,
        optimized_df=dual_opt,
        route_only_df=route_only,
        slot_only_df=slot_only,
        output_path=None,
    )

    assert len(comp) == 50
    for col in ["Baseline_Distance", "Route_Only_Distance", "Slot_Only_Distance", "Optimized_Distance"]:
        assert col in comp.columns
        assert (comp[col] > 0).all()


# 3. Slot Recommendation Tests
def test_slot_recommendation_empty_filtering_and_uniqueness(real_datasets):
    products, locations, orders, _ = real_datasets
    demand_df = classify_demand(orders, products, output_path=None, summary_path=None)
    recs = recommend_slots(products, locations, demand_df, dispatch_point=(0.0, 0.0), output_path=None)

    assert len(recs) == 30
    recommended = recs[recs["Recommendation_Status"] == "RECOMMENDED"]
    # Only empty locations can be recommended
    empty_loc_ids = set(locations[locations["Status"] == "EMPTY"]["Location_ID"])
    for loc_id in recommended["Recommended_Location"]:
        assert loc_id in empty_loc_ids

    # Unique 1-to-1 location assignment
    assigned_locs = list(recommended["Recommended_Location"])
    assert len(assigned_locs) == len(set(assigned_locs))
    assert len(assigned_locs) <= len(empty_loc_ids)

    # Unassigned products must have NO_FEASIBLE_LOCATION with explicit reason
    no_locs = recs[recs["Recommendation_Status"] == "NO_FEASIBLE_LOCATION"]
    assert len(no_locs) > 0
    for _, r in no_locs.iterrows():
        assert r["Recommended_Location"] == "NONE"
        assert len(r["Reason"]) > 0


# 4. Replenishment Alert Tests
def test_replenishment_alerts(real_datasets):
    products, _, _, inventory = real_datasets
    alerts = check_replenishment_alerts(inventory, products, output_path=None)

    assert len(alerts) == 6
    for _, r in alerts.iterrows():
        assert r["Current_Stock"] <= r["Minimum_Stock"]
        assert r["Replenishment_Required"] == "YES"
        if r["Current_Stock"] == 0:
            assert r["Stock_Status"] == "OUT_OF_STOCK"
        else:
            assert r["Stock_Status"] == "LOW_STOCK"

    # SKU006 has Current_Stock=0, should be OUT_OF_STOCK
    sku6 = alerts[alerts["SKU_ID"] == "SKU006"].iloc[0]
    assert sku6["Stock_Status"] == "OUT_OF_STOCK"


# 5. Route Calculations and Honest Suboptimal Evaluation
def test_route_calculation_and_suboptimal_cases(real_datasets):
    products, locations, orders, _ = real_datasets

    baseline = calculate_baseline_routes(orders, products, locations, output_path=None)
    optimized = calculate_optimized_routes(orders, products, locations, output_path=None)
    comparison = compare_routes(baseline, optimized, output_path=None)

    assert len(baseline) == 50
    assert len(optimized) == 50
    assert len(comparison) == 50

    # Ensure overall average route distance improved
    mean_baseline = baseline["Total_Distance"].mean()
    mean_optimized = optimized["Total_Distance"].mean()
    assert mean_optimized < mean_baseline

    # MANDATORY CAP-12 TEST: Demonstrate a real case where Nearest Neighbor is WORSE than baseline
    worse_cases = comparison[comparison["Route_Status"] == "WORSE"]
    assert len(worse_cases) > 0, "Requirement failed: Must demonstrate cases where NN is worse than baseline!"

    # Verify that at least one order has NN worse (ORD012 or any other)
    # With aisle-network distances the specific order that is worst may shift;
    # we verify the structural property rather than pinning to a specific Order_ID.
    any_worse = comparison[comparison["Route_Status"] == "WORSE"].iloc[0]
    assert any_worse["Optimized_Distance"] > any_worse["Baseline_Distance"]
    assert any_worse["Distance_Saved"] < 0
    assert any_worse["Pct_Distance_Reduction"] < 0



# =============================================================================
# 6. Aisle Network Graph Tests (CAP-12 Upgrade — Dijkstra / Graph-Based Distance)
# =============================================================================

@pytest.fixture(scope="module")
def warehouse_graph_fixture(real_datasets):
    """Builds the warehouse graph from actual location data."""
    _, locations, _, _ = real_datasets
    return build_warehouse_graph(locations)


@pytest.fixture(scope="module")
def locations_df_fixture(real_datasets):
    _, locations, _, _ = real_datasets
    return locations


# Test 11: Graph has the correct number of nodes
def test_graph_has_40_nodes(warehouse_graph_fixture):
    """Graph must contain exactly 40 nodes (one per warehouse location)."""
    # Exclude any virtual DISPATCH node from count
    warehouse_nodes = {n for n in warehouse_graph_fixture if n != "DISPATCH"}
    assert len(warehouse_nodes) == 40, (
        f"Expected 40 nodes, got {len(warehouse_nodes)}"
    )


# Test 12: Same-aisle consecutive edges exist and have correct weight
def test_same_aisle_consecutive_edges(warehouse_graph_fixture):
    """A01 ↔ A02 must be a direct edge with weight = 5 (Y: 0→5)."""
    neighbors_of_a01 = {n: w for n, w in warehouse_graph_fixture["A01"]}
    assert "A02" in neighbors_of_a01, "A01 must have A02 as a neighbour"
    assert neighbors_of_a01["A02"] == pytest.approx(5.0), (
        "A01→A02 edge weight should be 5 (|Y=5 - Y=0|)"
    )


# Test 13: Cross-aisle edges exist between adjacent aisles at same Y
def test_cross_aisle_edges(warehouse_graph_fixture):
    """A01 ↔ B01 must be a direct edge with weight = 10 (X: 0→10)."""
    neighbors_of_a01 = {n: w for n, w in warehouse_graph_fixture["A01"]}
    assert "B01" in neighbors_of_a01, "A01 must have B01 as a cross-aisle neighbour"
    assert neighbors_of_a01["B01"] == pytest.approx(10.0), (
        "A01→B01 edge weight should be 10 (|X=10 - X=0|)"
    )


# Test 14: All edges are bidirectional
def test_bidirectional_edges(warehouse_graph_fixture):
    """Every edge A→B must also exist as B→A with the same weight."""
    for node, neighbors in warehouse_graph_fixture.items():
        for neighbor, weight in neighbors:
            reverse_neighbors = {n: w for n, w in warehouse_graph_fixture.get(neighbor, [])}
            assert node in reverse_neighbors, (
                f"Edge {node}→{neighbor} exists but reverse {neighbor}→{node} is missing"
            )
            assert reverse_neighbors[node] == pytest.approx(weight), (
                f"Reverse edge {neighbor}→{node} has different weight"
            )


# Test 15: No diagonal edges — A01 connects ONLY to A02 and B01
def test_no_diagonal_edges(warehouse_graph_fixture):
    """A01 must only connect to A02 (same aisle, next Y) and B01 (adjacent aisle, same Y).
    It must NOT connect to B02 or any diagonal."""
    neighbor_ids = {n for n, _ in warehouse_graph_fixture["A01"]}
    assert "A02" in neighbor_ids, "A01 must connect to A02"
    assert "B01" in neighbor_ids, "A01 must connect to B01"
    assert "B02" not in neighbor_ids, "A01 must NOT connect to B02 (diagonal)"
    assert "C01" not in neighbor_ids, "A01 must NOT connect to C01 (non-adjacent aisle)"


# Test 16: Edge weight calculated from actual coordinates
def test_edge_weight_from_coordinates(warehouse_graph_fixture):
    """
    A01→A02 = 5.0  (same aisle, Y diff = |5-0|)
    A01→B01 = 10.0 (cross aisle, X diff = |10-0|)
    B03→C03 = 10.0 (cross aisle, X diff = |20-10|)
    """
    a01_neighbors = {n: w for n, w in warehouse_graph_fixture["A01"]}
    assert a01_neighbors["A02"] == pytest.approx(5.0)
    assert a01_neighbors["B01"] == pytest.approx(10.0)

    b03_neighbors = {n: w for n, w in warehouse_graph_fixture["B03"]}
    assert "C03" in b03_neighbors
    assert b03_neighbors["C03"] == pytest.approx(10.0)


# Test 17: Dijkstra simple — adjacent same-aisle nodes
def test_dijkstra_simple_adjacent(warehouse_graph_fixture):
    """A01 → A02 shortest path distance must be exactly 5."""
    dist, path = find_shortest_path(warehouse_graph_fixture, "A01", "A02")
    assert dist == pytest.approx(5.0)
    assert path == ["A01", "A02"]


# Test 18: Dijkstra cross aisle — A01 to E01 travels 4 aisles = 40 units
def test_dijkstra_cross_aisle(warehouse_graph_fixture):
    """A01 → E01 shortest path: A01→B01→C01→D01→E01 = 10+10+10+10 = 40."""
    dist, path = find_shortest_path(warehouse_graph_fixture, "A01", "E01")
    assert dist == pytest.approx(40.0)
    assert path[0] == "A01"
    assert path[-1] == "E01"
    assert len(path) == 5  # A01, B01, C01, D01, E01


# Test 19: Dijkstra long path — A01 to E08 = 40 (horiz) + 35 (vert) = 75
def test_dijkstra_long_path(warehouse_graph_fixture):
    """A01 → E08: cross 4 aisles (40) + travel Y=0→35 within E (35) = 75."""
    dist, _ = find_shortest_path(warehouse_graph_fixture, "A01", "E08")
    assert dist == pytest.approx(75.0)


# Test 20: Dispatch node resolves to A01 when dispatch = (0, 0)
def test_dispatch_node_is_a01(warehouse_graph_fixture, locations_df_fixture):
    """Dispatch at (0.0, 0.0) must resolve to 'A01' (no virtual node needed)."""
    dispatch = get_dispatch_node(warehouse_graph_fixture, (0.0, 0.0), locations_df_fixture)
    assert dispatch == "A01"


# Test 21: Slot recommendation uses aisle-network distance (not Euclidean)
def test_slot_recommendation_uses_aisle_distance(real_datasets):
    """
    Distance values in slot_recommendations must equal aisle-network distances,
    not Euclidean straight-line distances.
    For A01 at (0,0): aisle dist to itself = 0; to B01 = 10 (not 10 either way, but
    to verify: pick a known recommendation and confirm the distance field matches Dijkstra.
    """
    products, locations, orders, _ = real_datasets
    demand_df = classify_demand(orders, products, output_path=None, summary_path=None)
    recs = recommend_slots(products, locations, demand_df, dispatch_point=(0.0, 0.0), output_path=None)

    graph = build_warehouse_graph(locations)
    dispatch_node = get_dispatch_node(graph, (0.0, 0.0), locations)

    recommended = recs[recs["Recommendation_Status"] == "RECOMMENDED"]
    assert len(recommended) > 0

    for _, row in recommended.iterrows():
        loc_id = row["Recommended_Location"]
        aisle_dist = get_shortest_distance(graph, dispatch_node, loc_id)
        assert row["Distance"] == pytest.approx(round(aisle_dist, 2)), (
            f"Recommendation for {loc_id}: expected aisle distance {round(aisle_dist,2)}, "
            f"got {row['Distance']}"
        )


# Test 22: Slot capacity restriction is preserved
def test_slot_capacity_restriction(real_datasets):
    """Recommended locations must have capacity >= product required capacity."""
    products, locations, orders, _ = real_datasets
    demand_df = classify_demand(orders, products, output_path=None, summary_path=None)
    recs = recommend_slots(products, locations, demand_df, dispatch_point=(0.0, 0.0), output_path=None)

    loc_capacity = locations.set_index("Location_ID")["Capacity"].to_dict()
    prod_req_cap = products.set_index("SKU_ID")["Required_Capacity"].to_dict()

    recommended = recs[recs["Recommendation_Status"] == "RECOMMENDED"]
    for _, row in recommended.iterrows():
        assert loc_capacity[row["Recommended_Location"]] >= prod_req_cap[row["SKU_ID"]], (
            f"Capacity violated for {row['SKU_ID']} → {row['Recommended_Location']}"
        )


# Test 23: Slot category restriction is preserved
def test_slot_category_restriction(real_datasets):
    """Recommended locations must have Allowed_Category == 'ALL' or matching product category."""
    products, locations, orders, _ = real_datasets
    demand_df = classify_demand(orders, products, output_path=None, summary_path=None)
    recs = recommend_slots(products, locations, demand_df, dispatch_point=(0.0, 0.0), output_path=None)

    loc_cat = {r["Location_ID"]: r["Allowed_Category"].strip().upper()
               for _, r in locations.iterrows()}
    prod_cat = {r["SKU_ID"]: r["Category"].strip().upper()
                for _, r in products.iterrows()}

    recommended = recs[recs["Recommendation_Status"] == "RECOMMENDED"]
    for _, row in recommended.iterrows():
        allowed = loc_cat[row["Recommended_Location"]]
        pcat = prod_cat[row["SKU_ID"]]
        assert allowed == "ALL" or allowed == pcat, (
            f"Category mismatch: {row['SKU_ID']} (cat={pcat}) → {row['Recommended_Location']} (allowed={allowed})"
        )


# Test 24: No duplicate slot assignments
def test_no_duplicate_slot_assignments(real_datasets):
    """Each recommended location must appear at most once in the recommendations."""
    products, locations, orders, _ = real_datasets
    demand_df = classify_demand(orders, products, output_path=None, summary_path=None)
    recs = recommend_slots(products, locations, demand_df, dispatch_point=(0.0, 0.0), output_path=None)

    recommended_locs = recs[recs["Recommendation_Status"] == "RECOMMENDED"]["Recommended_Location"].tolist()
    assert len(recommended_locs) == len(set(recommended_locs)), (
        "Duplicate location assignments found in slot recommendations!"
    )


# Test 25: Baseline route uses graph distance (aisle-network)
def test_baseline_route_uses_graph_distance(real_datasets):
    """
    Baseline route total_distance must equal the sum of sequential Dijkstra hops:
      dispatch → loc1 → loc2 → … → dispatch.
    We verify this for a small set of orders by recalculating manually.
    """
    products, locations, orders, _ = real_datasets
    graph = build_warehouse_graph(locations)
    dispatch_node = get_dispatch_node(graph, (0.0, 0.0), locations)

    baseline = calculate_baseline_routes(
        orders, products, locations,
        dispatch_point=(0.0, 0.0), output_path=None,
        graph=graph, dispatch_node=dispatch_node
    )

    assert len(baseline) == 50

    # Spot-check the first 5 orders: manually recalculate distance and compare
    sku_to_loc = {row["SKU_ID"]: row["Current_Location"] for _, row in products.iterrows()}

    for _, row in baseline.head(5).iterrows():
        order_id = row["Order_ID"]
        order_lines = orders[orders["Order_ID"] == order_id]

        visited: list = []
        for _, line in order_lines.iterrows():
            lid = sku_to_loc.get(line["SKU_ID"])
            if lid and lid not in visited:
                visited.append(lid)

        expected = 0.0
        current = dispatch_node
        for loc in visited:
            expected += get_shortest_distance(graph, current, loc)
            current = loc
        expected += get_shortest_distance(graph, current, dispatch_node)
        expected = round(expected, 2)

        assert row["Total_Distance"] == pytest.approx(expected), (
            f"Order {order_id}: expected aisle distance {expected}, got {row['Total_Distance']}"
        )


# Test 26: Optimized route uses graph distance (aisle-network)
def test_optimized_route_uses_graph_distance(real_datasets):
    """
    Optimized total_distance must be >= 0 and structurally consistent
    (stops count equals number of locations visited).
    """
    products, locations, orders, _ = real_datasets
    graph = build_warehouse_graph(locations)
    dispatch_node = get_dispatch_node(graph, (0.0, 0.0), locations)

    optimized = calculate_optimized_routes(
        orders, products, locations,
        dispatch_point=(0.0, 0.0), output_path=None,
        graph=graph, dispatch_node=dispatch_node
    )

    assert len(optimized) == 50
    assert (optimized["Total_Distance"] >= 0).all()

    # Stops_Count must match the number of locations in Locations_Visited
    for _, row in optimized.iterrows():
        if row["Stops_Count"] > 0:
            locs = row["Locations_Visited"].split(" -> ")
            assert len(locs) == row["Stops_Count"], (
                f"Order {row['Order_ID']}: stops_count={row['Stops_Count']} "
                f"but {len(locs)} locations in string"
            )


# Test 27: Route starts and ends at dispatch node
def test_return_to_dispatch_included(real_datasets):
    """Route_Sequence string must start with 'START(A01)' and end with 'END(A01)'."""
    products, locations, orders, _ = real_datasets
    graph = build_warehouse_graph(locations)
    dispatch_node = get_dispatch_node(graph, (0.0, 0.0), locations)

    baseline = calculate_baseline_routes(
        orders, products, locations,
        dispatch_point=(0.0, 0.0), output_path=None,
        graph=graph, dispatch_node=dispatch_node
    )

    for _, row in baseline.iterrows():
        seq = row["Route_Sequence"]
        assert seq.startswith(f"START({dispatch_node})"), (
            f"Route does not start at dispatch node: {seq[:40]}"
        )
        assert seq.endswith(f"END({dispatch_node})"), (
            f"Route does not end at dispatch node: {seq[-40:]}"
        )


# Test 28: Graph validation passes on real data (no isolated or unreachable nodes)
def test_graph_validation_passes(warehouse_graph_fixture, locations_df_fixture):
    """validate_graph must complete without raising any exception on real warehouse data."""
    try:
        validate_graph(warehouse_graph_fixture, locations_df_fixture)
    except ValueError as e:
        pytest.fail(f"validate_graph raised ValueError: {e}")
