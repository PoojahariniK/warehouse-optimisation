"""
Dataset Enhancement Script for CAP-12 Warehouse Slotting & Pick-Path Optimization.

Generates realistic initial warehouse friction:
1. Misplaces several Fast Movers into Aisles D and E (far from dispatch).
2. Places Slow Movers in prime Aisle A locations.
3. Provides prime EMPTY locations in Aisles A & B for the slot recommender to discover.
4. Adds Hazard_Class to products and Hazard_Allowed to warehouse locations.
5. Keeps historical orders and dates so volatility and routes can be computed.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def generate_enhanced_datasets():
    repo_root = Path(__file__).resolve().parent.parent
    clean_dir = repo_root / "datasets" / "cleaned"
    orig_dir = repo_root / "datasets" / "original"
    clean_dir.mkdir(parents=True, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. Warehouse Locations (40 bins across 5 aisles)
    # -------------------------------------------------------------
    # Coordinates: Aisle X: A=0, B=10, C=20, D=30, E=40; Y: 0, 5, 10, 15, 20, 25, 30, 35
    # Empty slots: A02, A06, B02, B06, C04, C08, D07, D08, E07, E08 (10 empty bins, including prime bins in A & B!)
    # Hazard_Allowed: E01-E04 allow HAZMAT_BATTERY, E05-E06 allow HAZMAT_FLAMMABLE, others GENERAL or ALL.
    
    locations = []
    aisles = ['A', 'B', 'C', 'D', 'E']
    aisle_x = {'A': 0, 'B': 10, 'C': 20, 'D': 30, 'E': 40}
    empty_loc_ids = {'A02', 'A06', 'B02', 'B06', 'C04', 'C08', 'D07', 'D08', 'E07', 'E08'}
    
    capacities = {
        'A': [28, 25, 23, 29, 34, 22, 34, 33],
        'B': [25, 30, 24, 32, 31, 26, 22, 35],
        'C': [28, 34, 31, 32, 32, 24, 27, 28],
        'D': [28, 22, 29, 24, 32, 31, 30, 25],
        'E': [20, 40, 15, 30, 25, 50, 30, 20]
    }
    
    allowed_categories = {
        'E01': 'ACCESSORIES', 'E02': 'ALL', 'E03': 'ELECTRONICS', 'E04': 'ALL',
        'E05': 'ALL', 'E06': 'ALL', 'E07': 'ACCESSORIES', 'E08': 'ALL'
    }
    
    for a in aisles:
        for idx in range(1, 9):
            loc_id = f"{a}{idx:02d}"
            y = (idx - 1) * 5
            x = aisle_x[a]
            cap = capacities[a][idx - 1]
            status = 'EMPTY' if loc_id in empty_loc_ids else 'OCCUPIED'
            cat = allowed_categories.get(loc_id, 'ALL')
            
            # Hazard zone assignment
            if loc_id in ['E01', 'E02', 'E03', 'E04']:
                hazard_allowed = 'HAZMAT_BATTERY'
            elif loc_id in ['E05', 'E06']:
                hazard_allowed = 'HAZMAT_FLAMMABLE'
            else:
                hazard_allowed = 'GENERAL'
                
            locations.append({
                'Location_ID': loc_id,
                'Aisle': a,
                'X': x,
                'Y': y,
                'Capacity': cap,
                'Status': status,
                'Allowed_Category': cat,
                'Hazard_Allowed': hazard_allowed
            })
            
    locations_df = pd.DataFrame(locations)
    
    # -------------------------------------------------------------
    # 2. Products Master (30 SKUs) with Realistic Initial Friction
    # -------------------------------------------------------------
    # Notice: Occupied bins = 30 locations (40 total - 10 empty)
    occupied_bins = [l['Location_ID'] for l in locations if l['Status'] == 'OCCUPIED']
    # 30 occupied locations:
    # Aisle A: A01, A03, A04, A05, A07, A08 (6 bins)
    # Aisle B: B01, B03, B04, B05, B07, B08 (6 bins)
    # Aisle C: C01, C02, C03, C05, C06, C07 (6 bins)
    # Aisle D: D01, D02, D03, D04, D05, D06 (6 bins)
    # Aisle E: E01, E02, E03, E04, E05, E06 (6 bins)
    
    # Intentionally misplace Fast Movers into D & E, and Slow Movers into A!
    # Fast Movers: SKU001..SKU010
    # Medium Movers: SKU011..SKU020
    # Slow Movers: SKU021..SKU030
    
    initial_slotting = {
        # 10 Fast Movers (Ordered 12x): Some in C, D, E (misplaced far away!)
        'SKU001': 'D04',  # Laptop (Fast Mover stuck at D04, Distance = 45!)
        'SKU002': 'D05',  # Tablet (Fast Mover stuck at D05, Distance = 50!)
        'SKU003': 'E03',  # Smartphone (Fast Mover at E03, Distance = 50!)
        'SKU004': 'C02',  # Monitor (Fast Mover at C02, Distance = 25)
        'SKU005': 'D06',  # Webcam (Fast Mover at D06, Distance = 55!)
        'SKU006': 'C03',  # USB Hub (Fast Mover at C03, Distance = 30)
        'SKU007': 'B03',  # Wireless Mouse (Fast Mover at B03, Distance = 20)
        'SKU008': 'D01',  # Keyboard (Fast Mover at D01, Distance = 30)
        'SKU009': 'B04',  # Laptop Stand (Fast Mover at B04, Distance = 25)
        'SKU010': 'C05',  # Mouse Pad (Fast Mover at C05, Distance = 40)
        
        # 10 Medium Movers (Ordered 6x):
        'SKU011': 'E01',  # Power Bank (HAZMAT_BATTERY -> placed in compliant E01)
        'SKU012': 'E02',  # AA Battery Pack (HAZMAT_BATTERY -> placed in compliant E02)
        'SKU013': 'E04',  # Rechargeable Battery (HAZMAT_BATTERY -> placed in compliant E04)
        'SKU014': 'B05',  # Bluetooth Speaker (Audio)
        'SKU015': 'B07',  # Headphones (Audio)
        'SKU016': 'B08',  # Earbuds (Audio)
        'SKU017': 'C01',  # Microphone (Audio)
        'SKU018': 'C06',  # HDMI Cable (Accessories)
        'SKU019': 'C07',  # USB-C Cable (Accessories)
        'SKU020': 'D02',  # Ethernet Cable (Accessories)
        
        # 10 Slow Movers (Ordered 2x): Wastefully occupying prime slots in Aisle A & B!
        'SKU021': 'A01',  # External SSD (Slow Mover wastefully at A01, Distance = 0!)
        'SKU022': 'A03',  # Flash Drive (Slow Mover wastefully at A03, Distance = 10!)
        'SKU023': 'A04',  # Router (Slow Mover wastefully at A04, Distance = 15!)
        'SKU024': 'A05',  # Wi-Fi Adapter (Slow Mover wastefully at A05, Distance = 20!)
        'SKU025': 'E05',  # Laptop Charger (HAZMAT_FLAMMABLE -> in compliant E05)
        'SKU026': 'A07',  # Phone Charger (Slow Mover wastefully at A07, Distance = 30!)
        'SKU027': 'D03',  # Smartwatch (Slow Mover at D03)
        'SKU028': 'A08',  # Graphics Tablet (Slow Mover wastefully at A08, Distance = 35!)
        'SKU029': 'B01',  # Docking Station (Slow Mover wastefully at B01, Distance = 10!)
        'SKU030': 'E06',  # Portable SSD (Slow Mover at E06)
    }
    
    products_raw = [
        ('SKU001', 'Laptop', 'Computing', 9, 'GENERAL'),
        ('SKU002', 'Tablet', 'Computing', 18, 'GENERAL'),
        ('SKU003', 'Smartphone', 'Electronics', 16, 'GENERAL'),
        ('SKU004', 'Monitor', 'Electronics', 13, 'GENERAL'),
        ('SKU005', 'Webcam', 'Electronics', 13, 'GENERAL'),
        ('SKU006', 'USB Hub', 'Accessories', 19, 'GENERAL'),
        ('SKU007', 'Wireless Mouse', 'Accessories', 9, 'GENERAL'),
        ('SKU008', 'Keyboard', 'Accessories', 17, 'GENERAL'),
        ('SKU009', 'Laptop Stand', 'Accessories', 10, 'GENERAL'),
        ('SKU010', 'Mouse Pad', 'Accessories', 9, 'GENERAL'),
        ('SKU011', 'Power Bank', 'Battery', 14, 'HAZMAT_BATTERY'),
        ('SKU012', 'AA Battery Pack', 'Battery', 20, 'HAZMAT_BATTERY'),
        ('SKU013', 'Rechargeable Battery', 'Battery', 17, 'HAZMAT_BATTERY'),
        ('SKU014', 'Bluetooth Speaker', 'Audio', 17, 'GENERAL'),
        ('SKU015', 'Headphones', 'Audio', 17, 'GENERAL'),
        ('SKU016', 'Earbuds', 'Audio', 18, 'GENERAL'),
        ('SKU017', 'Microphone', 'Audio', 14, 'GENERAL'),
        ('SKU018', 'HDMI Cable', 'Accessories', 9, 'GENERAL'),
        ('SKU019', 'USB-C Cable', 'Accessories', 18, 'GENERAL'),
        ('SKU020', 'Ethernet Cable', 'Accessories', 13, 'GENERAL'),
        ('SKU021', 'External SSD', 'Computing', 14, 'GENERAL'),
        ('SKU022', 'Flash Drive', 'Computing', 12, 'GENERAL'),
        ('SKU023', 'Router', 'Electronics', 10, 'GENERAL'),
        ('SKU024', 'Wi-Fi Adapter', 'Electronics', 20, 'GENERAL'),
        ('SKU025', 'Laptop Charger', 'Electronics', 18, 'HAZMAT_FLAMMABLE'),
        ('SKU026', 'Phone Charger', 'Electronics', 16, 'GENERAL'),
        ('SKU027', 'Smartwatch', 'Electronics', 13, 'GENERAL'),
        ('SKU028', 'Graphics Tablet', 'Computing', 18, 'GENERAL'),
        ('SKU029', 'Docking Station', 'Computing', 15, 'GENERAL'),
        ('SKU030', 'Portable SSD', 'Computing', 13, 'GENERAL'),
    ]
    
    products = []
    for sku, name, cat, req_cap, hazard in products_raw:
        curr_loc = initial_slotting[sku]
        products.append({
            'SKU_ID': sku,
            'Product_Name': name,
            'Category': cat,
            'Required_Capacity': req_cap,
            'Current_Location': curr_loc,
            'Hazard_Class': hazard
        })
    products_df = pd.DataFrame(products)
    
    # -------------------------------------------------------------
    # 3. Order Lines (Keep existing order structure with dates)
    # -------------------------------------------------------------
    old_orders = pd.read_csv(orig_dir / "order_lines.csv")
    
    # -------------------------------------------------------------
    # 4. Inventory Clean (Keep existing or verify)
    # -------------------------------------------------------------
    old_inv = pd.read_csv(orig_dir / "inventory.csv")
    
    # Save all 4 clean files
    products_df.to_csv(clean_dir / "products_clean.csv", index=False)
    locations_df.to_csv(clean_dir / "warehouse_locations_clean.csv", index=False)
    old_orders.to_csv(clean_dir / "order_lines_clean.csv", index=False)
    old_inv.to_csv(clean_dir / "inventory_clean.csv", index=False)
    
    print(f"Enhanced datasets successfully written to {clean_dir.resolve()}")
    print(f"Products: {len(products_df)}, Locations: {len(locations_df)}, Orders: {len(old_orders)}, Inventory: {len(old_inv)}")

if __name__ == "__main__":
    generate_enhanced_datasets()
