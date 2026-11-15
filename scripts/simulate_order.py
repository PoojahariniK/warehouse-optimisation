"""
Interactive CLI Script: Simulate Custom / New Order Pick Path
Allows adding an ad-hoc customer order with arbitrary SKUs, calculating both
Baseline (sequential) and Nearest Neighbor routing on the fly.
"""

import sys
import os
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.optimization_engine.data_loader import load_clean_data
from src.optimization_engine.pick_path import euclidean_dist, calculate_picking_time

def simulate_new_order(sku_list, dispatch_point=(0.0, 0.0), walking_speed=1.2, pick_time=15.0):
    products_df, locations_df, order_lines_df, inventory_df = load_clean_data()

    # Map product to location coordinates
    prod_loc = products_df.merge(
        locations_df[['Location_ID', 'X', 'Y']],
        left_on='Current_Location',
        right_on='Location_ID',
        how='left'
    )
    sku_map = {
        r['SKU_ID']: {
            'name': r['Product_Name'],
            'loc': r['Current_Location'],
            'coord': (float(r['X']), float(r['Y']))
        }
        for _, r in prod_loc.iterrows()
    }

    # Validate requested SKUs
    valid_skus = []
    seen_locs = []
    required_stops = {}
    for sku in sku_list:
        sku = sku.strip().upper()
        if sku in sku_map:
            valid_skus.append(sku)
            lid = sku_map[sku]['loc']
            coord = sku_map[sku]['coord']
            if lid not in required_stops:
                required_stops[lid] = coord
                seen_locs.append(lid)
        else:
            print(f"[WARNING] SKU '{sku}' not found in product catalog. Skipping.")

    if not required_stops:
        print("[ERROR] No valid SKUs provided.")
        return

    # 1. Baseline sequential tour (visiting distinct stops in order given)
    base_dist = 0.0
    current_pt = dispatch_point
    for lid in seen_locs:
        coord = required_stops[lid]
        base_dist += euclidean_dist(current_pt, coord)
        current_pt = coord
    base_dist += euclidean_dist(current_pt, dispatch_point)
    base_time = calculate_picking_time(base_dist, len(seen_locs), walking_speed, pick_time)
    base_seq = f"START({dispatch_point[0]}, {dispatch_point[1]}) -> " + " -> ".join(seen_locs) + f" -> END({dispatch_point[0]}, {dispatch_point[1]})"

    # 2. Nearest Neighbor tour
    unvisited = dict(required_stops)
    current_pt = dispatch_point
    visited_sequence = []
    nn_dist = 0.0

    while unvisited:
        nearest_loc = None
        min_d = float('inf')
        for loc_id, coord in unvisited.items():
            d = euclidean_dist(current_pt, coord)
            if d < min_d:
                min_d = d
                nearest_loc = loc_id
        if nearest_loc is not None:
            nn_dist += min_d
            current_pt = unvisited[nearest_loc]
            visited_sequence.append(nearest_loc)
            del unvisited[nearest_loc]

    nn_dist += euclidean_dist(current_pt, dispatch_point)
    nn_time = calculate_picking_time(nn_dist, len(visited_sequence), walking_speed, pick_time)
    nn_seq = f"START({dispatch_point[0]}, {dispatch_point[1]}) -> " + " -> ".join(visited_sequence) + f" -> END({dispatch_point[0]}, {dispatch_point[1]})"

    dist_saved = round(base_dist - nn_dist, 2)
    pct_reduction = round((dist_saved / base_dist) * 100, 2) if base_dist > 0 else 0.0
    time_saved = round(base_time - nn_time, 2)

    status = "IMPROVED" if dist_saved > 0 else ("WORSE" if dist_saved < 0 else "IDENTICAL")

    print("\n" + "=" * 75)
    print(f"AD-HOC CUSTOM ORDER PICK-PATH SIMULATION ({len(valid_skus)} SKUs, {len(seen_locs)} Bins)")
    print("=" * 75)
    print("Items Ordered:")
    for s in valid_skus:
        print(f"  - {s:6s}: {sku_map[s]['name']:<18s} @ Bin {sku_map[s]['loc']} (X={sku_map[s]['coord'][0]}, Y={sku_map[s]['coord'][1]})")

    print("\n--- BASELINE ROUTE (Sequential) ---")
    print(f"  Sequence: {base_seq}")
    print(f"  Distance: {base_dist:.2f} units | Est. Time: {base_time:.2f}s")

    print("\n--- OPTIMIZED ROUTE (Nearest Neighbor) ---")
    print(f"  Sequence: {nn_seq}")
    print(f"  Distance: {nn_dist:.2f} units | Est. Time: {nn_time:.2f}s")

    print("\n--- PERFORMANCE COMPARISON ---")
    print(f"  Outcome Status:      {status}")
    print(f"  Distance Variance:   {dist_saved:+.2f} units ({pct_reduction:+.2f}%)")
    print(f"  Picking Time Saved:  {time_saved:+.2f} seconds")
    if status == "WORSE":
        print("  ⚠️ NOTE: Nearest Neighbor produced a longer route due to greedy early selection!")
    elif status == "IMPROVED":
        print(f"  ✅ Nearest Neighbor successfully reduced travel distance by {dist_saved:.2f} units!")
    print("=" * 75 + "\n")

if __name__ == '__main__':
    test_skus = ['SKU001', 'SKU014', 'SKU025', 'SKU009']
    if len(sys.argv) > 1:
        test_skus = sys.argv[1:]
    simulate_new_order(test_skus)
