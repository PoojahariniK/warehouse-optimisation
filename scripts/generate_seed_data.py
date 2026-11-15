"""
Generate frontend/public/seed_data.js and backend/src/main/resources/data.sql
containing the project's enhanced cleaned datasets and 4-way optimization results.
This keeps Python, Spring Boot H2, and React UI 100% in sync.
"""
import json
import os
import pandas as pd

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cleaned_dir = os.path.join(base_dir, 'datasets', 'cleaned')
outputs_dir = os.path.join(base_dir, 'outputs')
public_dir = os.path.join(base_dir, 'frontend', 'public')
backend_resources_dir = os.path.join(base_dir, 'backend', 'src', 'main', 'resources')

os.makedirs(public_dir, exist_ok=True)
os.makedirs(backend_resources_dir, exist_ok=True)

# 1. Products
df_prod = pd.read_csv(os.path.join(cleaned_dir, 'products_clean.csv'))
products = []
for _, row in df_prod.iterrows():
    products.append({
        "skuId": str(row['SKU_ID']),
        "productName": str(row['Product_Name']),
        "category": str(row['Category']),
        "requiredCapacity": int(row['Required_Capacity']),
        "currentLocation": str(row['Current_Location']),
        "hazardClass": str(row.get('Hazard_Class', 'GENERAL'))
    })

# 2. Locations
df_loc = pd.read_csv(os.path.join(cleaned_dir, 'warehouse_locations_clean.csv'))
locations = []
for _, row in df_loc.iterrows():
    locations.append({
        "locationId": str(row['Location_ID']),
        "aisle": str(row['Aisle']),
        "x": float(row['X']),
        "y": float(row['Y']),
        "capacity": int(row['Capacity']),
        "status": str(row['Status']),
        "allowedCategory": str(row['Allowed_Category']),
        "hazardAllowed": str(row.get('Hazard_Allowed', 'GENERAL'))
    })

# 3. Demand
df_dem = pd.read_csv(os.path.join(outputs_dir, 'demand_analysis.csv'))
demand = []
for _, row in df_dem.iterrows():
    demand.append({
        "skuId": str(row['SKU_ID']),
        "productName": str(row['Product_Name']),
        "category": str(row['Category']),
        "currentLocation": str(row.get('Current_Location', '')),
        "orderFrequency": int(row['Order_Frequency']),
        "totalQuantity": int(row['Total_Quantity']),
        "demandClass": str(row['Demand_Class']),
        "demandCv": float(row.get('Demand_CV', 0.0)),
        "volatilityClass": str(row.get('Volatility_Class', 'STABLE'))
    })

# 4. Slot recommendations
df_recs = pd.read_csv(os.path.join(outputs_dir, 'slot_recommendations.csv'))
recs = []
for _, row in df_recs.iterrows():
    recs.append({
        "recommendationId": str(row['Recommendation_ID']),
        "skuId": str(row['SKU_ID']),
        "productName": str(row['Product_Name']),
        "demandClass": str(row['Demand_Class']),
        "currentLocation": str(row['Current_Location']),
        "recommendedLocation": str(row['Recommended_Location']),
        "distance": float(row['Distance']),
        "distanceSaved": float(row.get('Distance_Saved', 0.0)),
        "recommendationStatus": str(row['Recommendation_Status']),
        "reason": str(row['Reason'])
    })

# 5. Routes (4-way operational matrix)
df_routes = pd.read_csv(os.path.join(outputs_dir, 'route_comparison.csv'))
df_base = pd.read_csv(os.path.join(outputs_dir, 'baseline_routes.csv')).set_index('Order_ID')
df_opt = pd.read_csv(os.path.join(outputs_dir, 'optimized_routes.csv')).set_index('Order_ID')

routes = []
for _, row in df_routes.iterrows():
    oid = str(row['Order_ID'])
    base_seq = str(df_base.loc[oid, 'Route_Sequence']) if oid in df_base.index else ''
    opt_seq = str(df_opt.loc[oid, 'Route_Sequence']) if oid in df_opt.index else ''
    routes.append({
        "orderId": oid,
        "baselineRouteSequence": base_seq,
        "optimizedRouteSequence": opt_seq,
        "baselineDistance": float(row['Baseline_Distance']),
        "routeOnlyDistance": float(row.get('Route_Only_Distance', row['Optimized_Distance'])),
        "slotOnlyDistance": float(row.get('Slot_Only_Distance', row['Baseline_Distance'])),
        "optimizedDistance": float(row['Optimized_Distance']),
        "distanceSaved": float(row['Distance_Saved']),
        "pctDistanceReduction": float(row['Pct_Distance_Reduction']),
        "baselineTimeSec": float(row['Baseline_Time_Sec']),
        "optimizedTimeSec": float(row['Optimized_Time_Sec']),
        "timeSavedSec": float(row['Time_Saved_Sec']),
        "routeStatus": str(row['Route_Status']),
        "notes": str(row['Notes'])
    })

# 6. Replenishment
df_rep = pd.read_csv(os.path.join(outputs_dir, 'replenishment_alerts.csv'))
replenishment = []
for _, row in df_rep.iterrows():
    replenishment.append({
        "skuId": str(row['SKU_ID']),
        "productName": str(row['Product_Name']),
        "currentStock": int(row['Current_Stock']),
        "minimumStock": int(row['Minimum_Stock']),
        "stockStatus": str(row['Stock_Status']),
        "replenishmentRequired": str(row['Replenishment_Required'])
    })

# 6b. Order Affinity (Market Basket Co-Occurrence)
affinity_pairs = []
aff_csv = os.path.join(outputs_dir, 'affinity_pairs.csv')
if os.path.exists(aff_csv):
    df_aff = pd.read_csv(aff_csv)
    for p_idx, row in df_aff.iterrows():
        affinity_pairs.append({
            "pairId": p_idx + 1,
            "skuA": str(row['SKU_A']),
            "productA": str(row['Product_A']),
            "categoryA": str(row['Category_A']),
            "skuB": str(row['SKU_B']),
            "productB": str(row['Product_B']),
            "categoryB": str(row['Category_B']),
            "coOccurrenceCount": int(row['Co_Occurrence_Count']),
            "ordersA": int(row['Orders_A']),
            "ordersB": int(row['Orders_B']),
            "affinityScore": float(row['Affinity_Score']),
            "jaccardIndex": float(row['Jaccard_Index']),
            "pairLabel": str(row['Pair_Label'])
        })

# 7. Inventory & Order Lines (for SQL seeding)
df_inv = pd.read_csv(os.path.join(cleaned_dir, 'inventory_clean.csv'))
df_ol = pd.read_csv(os.path.join(cleaned_dir, 'order_lines_clean.csv'))

# 8. Analytics
total_products = len(products)
total_locations = len(locations)
occupied = sum(1 for l in locations if l['status'] == 'OCCUPIED')
empty = sum(1 for l in locations if l['status'] == 'EMPTY')
fast = sum(1 for d in demand if d['demandClass'].upper() == 'FAST')
med = sum(1 for d in demand if d['demandClass'].upper() == 'MEDIUM')
slow = sum(1 for d in demand if d['demandClass'].upper() == 'SLOW')
total_orders = len(routes)
avg_base_dist = round(sum(r['baselineDistance'] for r in routes) / total_orders, 2)
avg_ro_dist = round(sum(r['routeOnlyDistance'] for r in routes) / total_orders, 2)
avg_so_dist = round(sum(r['slotOnlyDistance'] for r in routes) / total_orders, 2)
avg_opt_dist = round(sum(r['optimizedDistance'] for r in routes) / total_orders, 2)
total_saved = round(sum(r['distanceSaved'] for r in routes), 2)
avg_pct_reduction = round(sum(r['pctDistanceReduction'] for r in routes) / total_orders, 2)
improved_cnt = sum(1 for r in routes if r['routeStatus'] == 'IMPROVED')
worse_cnt = sum(1 for r in routes if r['routeStatus'] == 'WORSE')
ident_cnt = sum(1 for r in routes if r['routeStatus'] == 'IDENTICAL')
rec_cnt = sum(1 for r in recs if r['recommendationStatus'] == 'RECOMMENDED')
app_cnt = sum(1 for r in recs if r['recommendationStatus'] == 'APPROVED')
rej_cnt = sum(1 for r in recs if r['recommendationStatus'] == 'REJECTED')

analytics = {
    "totalProducts": total_products,
    "totalLocations": total_locations,
    "occupiedLocations": occupied,
    "emptyLocations": empty,
    "fastProducts": fast,
    "mediumProducts": med,
    "slowProducts": slow,
    "totalOrders": total_orders,
    "averageBaselineDistance": avg_base_dist,
    "averageRouteOnlyDistance": avg_ro_dist,
    "averageSlotOnlyDistance": avg_so_dist,
    "averageOptimizedDistance": avg_opt_dist,
    "totalDistanceSaved": total_saved,
    "averageDistanceReductionPct": avg_pct_reduction,
    "improvedOrdersCount": improved_cnt,
    "worseOrdersCount": worse_cnt,
    "identicalOrdersCount": ident_cnt,
    "replenishmentAlertsCount": len(replenishment),
    "recommendedSlotsCount": rec_cnt,
    "approvedSlotsCount": app_cnt,
    "rejectedSlotsCount": rej_cnt
}

seed_data = {
    "products": products,
    "locations": locations,
    "demand": demand,
    "affinityPairs": affinity_pairs,
    "recommendations": recs,
    "routes": routes,
    "replenishment": replenishment,
    "analytics": analytics
}

# Write frontend/public/seed_data.js and frontend/seed_data.js
out_file_js = os.path.join(public_dir, 'seed_data.js')
with open(out_file_js, 'w', encoding='utf-8') as f:
    f.write('window.__SEED_DATA__ = ' + json.dumps(seed_data, indent=2) + ';\n')

out_file_root_js = os.path.join(base_dir, 'frontend', 'seed_data.js')
with open(out_file_root_js, 'w', encoding='utf-8') as f:
    f.write('window.__SEED_DATA__ = ' + json.dumps(seed_data, indent=2) + ';\n')

# Write backend/src/main/resources/data.sql
out_file_sql = os.path.join(backend_resources_dir, 'data.sql')
with open(out_file_sql, 'w', encoding='utf-8') as f:
    f.write('-- Synchronized Seed Data for CAP-12 Warehouse Management\n\n')

    # Warehouse locations
    f.write('-- 1. WAREHOUSE LOCATIONS\n')
    for loc in locations:
        f.write(
            f"INSERT INTO WAREHOUSE_LOCATIONS (LOCATION_ID, AISLE, X, Y, CAPACITY, STATUS, ALLOWED_CATEGORY, HAZARD_ALLOWED) "
            f"VALUES ('{loc['locationId']}', '{loc['aisle']}', {int(loc['x'])}, {int(loc['y'])}, {loc['capacity']}, '{loc['status']}', '{loc['allowedCategory']}', '{loc['hazardAllowed']}');\n"
        )
    f.write('\n')

    # Products
    f.write('-- 2. PRODUCTS\n')
    for prod in products:
        pname = prod['productName'].replace("'", "''")
        f.write(
            f"INSERT INTO PRODUCTS (SKU_ID, PRODUCT_NAME, CATEGORY, REQUIRED_CAPACITY, CURRENT_LOCATION, HAZARD_CLASS) "
            f"VALUES ('{prod['skuId']}', '{pname}', '{prod['category']}', {prod['requiredCapacity']}, '{prod['currentLocation']}', '{prod['hazardClass']}');\n"
        )
    f.write('\n')

    # Inventory
    f.write('-- 3. INVENTORY\n')
    for _, row in df_inv.iterrows():
        f.write(
            f"INSERT INTO INVENTORY (SKU_ID, CURRENT_STOCK, MINIMUM_STOCK) "
            f"VALUES ('{row['SKU_ID']}', {int(row['Current_Stock'])}, {int(row['Minimum_Stock'])});\n"
        )
    f.write('\n')

    # Order Lines
    f.write('-- 4. ORDER LINES\n')
    for _, row in df_ol.iterrows():
        f.write(
            f"INSERT INTO ORDER_LINES (ORDER_LINE_ID, ORDER_ID, ORDER_DATE, SKU_ID, QUANTITY) "
            f"VALUES ('{row['Order_Line_ID']}', '{row['Order_ID']}', '{row['Order_Date']}', '{row['SKU_ID']}', {int(row['Quantity'])});\n"
        )
    f.write('\n')

    # Slot Recommendations
    f.write('-- 5. SLOT RECOMMENDATIONS\n')
    for r in recs:
        pname = r['productName'].replace("'", "''")
        reason_clean = r['reason'].replace("'", "''")
        f.write(
            f"INSERT INTO SLOT_RECOMMENDATIONS (RECOMMENDATION_ID, SKU_ID, PRODUCT_NAME, DEMAND_CLASS, CURRENT_LOCATION, RECOMMENDED_LOCATION, DISTANCE, DISTANCE_SAVED, RECOMMENDATION_STATUS, REASON) "
            f"VALUES ('{r['recommendationId']}', '{r['skuId']}', '{pname}', '{r['demandClass']}', '{r['currentLocation']}', '{r['recommendedLocation']}', {r['distance']}, {r['distanceSaved']}, '{r['recommendationStatus']}', '{reason_clean}');\n"
        )
    f.write('\n')

    # Route Results (4-Way Matrix)
    f.write('-- 6. ROUTE RESULTS\n')
    for rt in routes:
        notes_clean = rt['notes'].replace("'", "''")
        f.write(
            f"INSERT INTO ROUTE_RESULTS (ORDER_ID, BASELINE_ROUTE_SEQUENCE, OPTIMIZED_ROUTE_SEQUENCE, BASELINE_DISTANCE, ROUTE_ONLY_DISTANCE, SLOT_ONLY_DISTANCE, OPTIMIZED_DISTANCE, DISTANCE_SAVED, PCT_DISTANCE_REDUCTION, BASELINE_TIME_SEC, OPTIMIZED_TIME_SEC, TIME_SAVED_SEC, ROUTE_STATUS, NOTES) "
            f"VALUES ('{rt['orderId']}', '{rt['baselineRouteSequence']}', '{rt['optimizedRouteSequence']}', {rt['baselineDistance']}, {rt['routeOnlyDistance']}, {rt['slotOnlyDistance']}, {rt['optimizedDistance']}, {rt['distanceSaved']}, {rt['pctDistanceReduction']}, {rt['baselineTimeSec']}, {rt['optimizedTimeSec']}, {rt['timeSavedSec']}, '{rt['routeStatus']}', '{notes_clean}');\n"
        )
    f.write('\n')

    # Replenishment Alerts
    f.write('-- 7. REPLENISHMENT ALERTS\n')
    for rep in replenishment:
        pname = rep['productName'].replace("'", "''")
        f.write(
            f"INSERT INTO REPLENISHMENT_ALERTS (SKU_ID, PRODUCT_NAME, CURRENT_STOCK, MINIMUM_STOCK, STOCK_STATUS, REPLENISHMENT_REQUIRED) "
            f"VALUES ('{rep['skuId']}', '{pname}', {rep['currentStock']}, {rep['minimumStock']}, '{rep['stockStatus']}', '{rep['replenishmentRequired']}');\n"
        )
    f.write('\n')

    # Demand Analysis (includes Demand_CV and Volatility_Class)
    f.write('-- 8. DEMAND ANALYSIS\n')
    for d in demand:
        pname = d['productName'].replace("'", "''")
        f.write(
            f"INSERT INTO DEMAND_ANALYSIS (SKU_ID, PRODUCT_NAME, CATEGORY, CURRENT_LOCATION, ORDER_FREQUENCY, TOTAL_QUANTITY, DEMAND_CLASS, DEMAND_CV, VOLATILITY_CLASS) "
            f"VALUES ('{d['skuId']}', '{pname}', '{d['category']}', '{d['currentLocation']}', {d['orderFrequency']}, {d['totalQuantity']}, '{d['demandClass']}', {d['demandCv']}, '{d['volatilityClass']}');\n"
        )
    f.write('\n')

    # Order Affinity (Market Basket Analysis)
    f.write('-- 9. ORDER AFFINITY\n')
    for aff in affinity_pairs:
        pna = aff['productA'].replace("'", "''")
        pnb = aff['productB'].replace("'", "''")
        plab = aff['pairLabel'].replace("'", "''")
        f.write(
            f"INSERT INTO ORDER_AFFINITY (SKU_A, PRODUCT_A, CATEGORY_A, SKU_B, PRODUCT_B, CATEGORY_B, CO_OCCURRENCE_COUNT, ORDERS_A, ORDERS_B, AFFINITY_SCORE, JACCARD_INDEX, PAIR_LABEL) "
            f"VALUES ('{aff['skuA']}', '{pna}', '{aff['categoryA']}', '{aff['skuB']}', '{pnb}', '{aff['categoryB']}', {aff['coOccurrenceCount']}, {aff['ordersA']}, {aff['ordersB']}, {aff['affinityScore']}, {aff['jaccardIndex']}, '{plab}');\n"
        )
    f.write('\n')

print(f"Successfully generated {out_file_js}")
print(f"Successfully generated {out_file_sql}")
