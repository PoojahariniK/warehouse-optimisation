"""
Interactive CLI Script: Inventory & Slot Operations
Demonstrates:
1. Adding / Restocking SKU inventory (clearing alerts when stock rises > minimum)
2. Removing / Consuming SKU inventory (triggering alerts when stock drops <= minimum)
3. Vacating an existing occupied location to EMPTY so slot recommendations can use it!
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.optimization_engine.data_loader import load_clean_data

def inspect_sku_stock(sku_id):
    sku_id = sku_id.strip().upper()
    products_df, locations_df, _, inventory_df = load_clean_data()
    
    prod = products_df[products_df['SKU_ID'] == sku_id]
    inv = inventory_df[inventory_df['SKU_ID'] == sku_id]
    
    if prod.empty:
        print(f"[ERROR] SKU '{sku_id}' not found.")
        return
        
    p_row = prod.iloc[0]
    curr_stock = int(inv.iloc[0]['Current_Stock']) if not inv.empty else 0
    min_stock = int(inv.iloc[0]['Minimum_Stock']) if not inv.empty else 0
    
    status = "OUT_OF_STOCK" if curr_stock == 0 else ("LOW_STOCK" if curr_stock <= min_stock else "HEALTHY")
    
    print("\n" + "=" * 60)
    print(f"SKU INVENTORY & STORAGE STATUS: {sku_id}")
    print("=" * 60)
    print(f"Product Name:       {p_row['Product_Name']}")
    print(f"Category:           {p_row['Category']}")
    print(f"Current Bin:        {p_row['Current_Location']}")
    print(f"Current Stock:      {curr_stock} units")
    print(f"Minimum Threshold:  {min_stock} units")
    print(f"Stock Status:       {status}")
    print(f"Alert Active:       {'YES (Replenishment Required)' if curr_stock <= min_stock else 'NO (Sufficient Stock)'}")
    print("=" * 60 + "\n")

def simulate_stock_change(sku_id, delta_qty):
    sku_id = sku_id.strip().upper()
    products_df, _, _, inventory_df = load_clean_data()
    
    inv = inventory_df[inventory_df['SKU_ID'] == sku_id]
    if inv.empty:
        print(f"[ERROR] SKU '{sku_id}' not found in inventory.")
        return
        
    old_stock = int(inv.iloc[0]['Current_Stock'])
    min_stock = int(inv.iloc[0]['Minimum_Stock'])
    new_stock = max(0, old_stock + delta_qty)
    
    old_status = "OUT_OF_STOCK" if old_stock == 0 else ("LOW_STOCK" if old_stock <= min_stock else "HEALTHY")
    new_status = "OUT_OF_STOCK" if new_stock == 0 else ("LOW_STOCK" if new_stock <= min_stock else "HEALTHY")
    
    print("\n" + "=" * 65)
    print(f"SIMULATING STOCK ADJUSTMENT FOR {sku_id}")
    print("=" * 65)
    print(f"Action:             {'RESTOCK (+)' if delta_qty > 0 else 'DISPATCH / REMOVE (-)'} {abs(delta_qty)} units")
    print(f"Previous Stock:     {old_stock} (Status: {old_status})")
    print(f"New Stock:          {new_stock} (Status: {new_status})")
    print(f"Minimum Threshold:  {min_stock} units")
    
    if old_stock <= min_stock and new_stock > min_stock:
        print("  🎉 REPLENISHMENT RESOLVED: Stock is now above minimum threshold! Alert cleared.")
    elif old_stock > min_stock and new_stock <= min_stock:
        print("  ⚠️ REPLENISHMENT ALERT TRIGGERED: Stock fell to or below minimum threshold!")
    print("=" * 65 + "\n")

def simulate_vacate_location(location_id):
    location_id = location_id.strip().upper()
    products_df, locations_df, _, _ = load_clean_data()
    
    loc = locations_df[locations_df['Location_ID'] == location_id]
    if loc.empty:
        print(f"[ERROR] Location '{location_id}' not found.")
        return
        
    occupied_by = products_df[products_df['Current_Location'] == location_id]
    loc_row = loc.iloc[0]
    
    print("\n" + "=" * 65)
    print(f"SIMULATING BIN VACATE / PRODUCT REMOVAL: {location_id}")
    print("=" * 65)
    print(f"Aisle:              {loc_row['Aisle']} (X={loc_row['X']}, Y={loc_row['Y']})")
    print(f"Capacity:           {loc_row['Capacity']} units")
    print(f"Previous Status:    {loc_row['Status']}")
    if not occupied_by.empty:
        p = occupied_by.iloc[0]
        print(f"Occupant Evacuated: {p['SKU_ID']} ({p['Product_Name']}, Category: {p['Category']})")
    print("New Status:         EMPTY (Now immediately available for candidate slotting!)")
    print("=" * 65 + "\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/manage_inventory.py inspect <SKU_ID>")
        print("  python scripts/manage_inventory.py restock <SKU_ID> <QTY>")
        print("  python scripts/manage_inventory.py pick <SKU_ID> <QTY>")
        print("  python scripts/manage_inventory.py vacate <LOCATION_ID>")
        print("\nRunning demonstration defaults:")
        simulate_stock_change("SKU006", +25) # Restocking USB Hub from 0 to 25
        simulate_stock_change("SKU001", -45) # Consuming Laptop from 50 to 5
        simulate_vacate_location("A01")     # Vacating A01
    else:
        cmd = sys.argv[1].lower()
        if cmd == 'inspect' and len(sys.argv) > 2:
            inspect_sku_stock(sys.argv[2])
        elif cmd == 'restock' and len(sys.argv) > 3:
            simulate_stock_change(sys.argv[2], int(sys.argv[3]))
        elif cmd == 'pick' and len(sys.argv) > 3:
            simulate_stock_change(sys.argv[2], -int(sys.argv[3]))
        elif cmd == 'vacate' and len(sys.argv) > 2:
            simulate_vacate_location(sys.argv[2])

