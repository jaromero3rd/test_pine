#!/usr/bin/env python3
"""
Master Catalog Updater - Simplified Version
Compiles essential data from individual CSV files without AI descriptions
"""

import os
import csv
from typing import Dict, List, Optional
from config import Config

class MasterCatalogUpdater:
    def __init__(self, catalog_type: str = "interior_define", config: Config = None):
        """Initialize the master catalog updater."""
        if config is None:
            config = Config()
        
        self.config = config
        self.catalog_type = catalog_type.lower()
        
        # Set paths based on catalog type
        if self.catalog_type == "haverty":
            self.base_output_dir = "haverty_catalog"
            self.master_csv_path = os.path.join(self.base_output_dir, "HAVERTYS_MASTER_CATALOG.csv")
            self.categories = {
                'beds': {
                    'folder': 'beds',
                    'csv_file': 'havertys_beds_hybrid.csv',
                    'item_type': 'bed'
                },
                'dressers': {
                    'folder': 'dressers',
                    'csv_file': 'havertys_dressers_robust.csv',
                    'item_type': 'dresser'
                },
                'nightstands': {
                    'folder': 'nightstands',
                    'csv_file': 'havertys_nightstands_smart.csv',
                    'item_type': 'nightstand'
                },
                'chests': {
                    'folder': 'chests',
                    'csv_file': 'havertys_chests_smart.csv',
                    'item_type': 'chest'
                },
                'benches': {
                    'folder': 'benches',
                    'csv_file': 'havertys_benches_smart.csv',
                    'item_type': 'bench'
                },
                'sofas': {
                    'folder': 'sofas',
                    'csv_file': 'havertys_sofas_smart.csv',
                    'item_type': 'sofa'
                }
            }
        elif self.catalog_type == "boconcept":
            self.base_output_dir = "BoConcept_catalog"
            self.master_csv_path = os.path.join(self.base_output_dir, "BOCONCEPT_MASTER_CATALOG.csv")
            self.categories = {
                'sofas': {
                    'folder': 'sofas',
                    'csv_file': 'sofas.csv',
                    'item_type': 'sofa'
                },
                'chairs': {
                    'folder': 'chairs',
                    'csv_file': 'chairs.csv',
                    'item_type': 'chair'
                },
                'lamps': {
                    'folder': 'lamps',
                    'csv_file': 'lamps.csv',
                    'item_type': 'lamp'
                },
                'beds': {
                    'folder': 'beds',
                    'csv_file': 'beds.csv',
                    'item_type': 'bed'
                },
                'tables': {
                    'folder': 'tables',
                    'csv_file': 'tables.csv',
                    'item_type': 'table'
                },
                'rugs': {
                    'folder': 'rugs',
                    'csv_file': 'rugs.csv',
                    'item_type': 'rug'
                }
            }
        elif self.catalog_type == "interior_define":
            self.base_output_dir = "InteriorDefine_catalog"
            self.master_csv_path = os.path.join(self.base_output_dir, "INTERIOR_DEFINE_MASTER_CATALOG.csv")
            self.categories = {
                'sofas': {
                    'folder': 'sofas',
                    'csv_file': 'sofas.csv',
                    'item_type': 'sofa'
                },
                'chairs': {
                    'folder': 'chairs',
                    'csv_file': 'chairs.csv',
                    'item_type': 'chair'
                },
                'tables': {
                    'folder': 'tables',
                    'csv_file': 'tables.csv',
                    'item_type': 'table'
                },
                'benches': {
                    'folder': 'benches',
                    'csv_file': 'benches.csv',
                    'item_type': 'bench'
                },
                'nightstands': {
                    'folder': 'nightstands',
                    'csv_file': 'nightstands.csv',
                    'item_type': 'nightstand'
                },
                'lighting': {
                    'folder': 'lighting',
                    'csv_file': 'lighting.csv',
                    'item_type': 'lighting'
                },
                'rugs': {
                    'folder': 'rugs',
                    'csv_file': 'rugs.csv',
                    'item_type': 'rug'
                }
            }
        elif self.catalog_type == "interior_define_2":
            self.base_output_dir = "InteriorDefine_catalog_2"
            self.master_csv_path = os.path.join(self.base_output_dir, "INTERIOR_DEFINE_MASTER_CATALOG.csv")
            self.categories = {
                'sofas': {
                    'folder': 'sofas',
                    'csv_file': 'sofas.csv',
                    'item_type': 'sofa'
                },
                'chairs': {
                    'folder': 'chairs',
                    'csv_file': 'chairs.csv',
                    'item_type': 'chair'
                },
                'tables': {
                    'folder': 'tables',
                    'csv_file': 'tables.csv',
                    'item_type': 'table'
                },
                'benches': {
                    'folder': 'benches',
                    'csv_file': 'benches.csv',
                    'item_type': 'bench'
                },
                'nightstands': {
                    'folder': 'nightstands',
                    'csv_file': 'nightstands.csv',
                    'item_type': 'nightstand'
                },
                'lighting': {
                    'folder': 'lighting',
                    'csv_file': 'lighting.csv',
                    'item_type': 'lighting'
                },
                'rugs': {
                    'folder': 'rugs',
                    'csv_file': 'rugs.csv',
                    'item_type': 'rug'
                }
            }
        else:
            raise ValueError(f"Unknown catalog type: {catalog_type}. Use 'haverty', 'boconcept', or 'interior_define'")

    def load_category_data(self, category_name: str) -> List[Dict]:
        """Load data from a category CSV file."""
        category_info = self.categories[category_name]
        csv_path = os.path.join(self.base_output_dir, category_info['folder'], category_info['csv_file'])
        
        if not os.path.exists(csv_path):
            print(f"⚠️  Category CSV not found: {csv_path}")
            return []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                items = []
                for row in reader:
                    # Convert colors string back to list
                    colors_str = row.get('colors', '')
                    colors = [c.strip() for c in colors_str.split(',')] if colors_str else []
                    
                    items.append({
                        'catalog_number': row.get('catalog_number', ''),
                        'item_name': row.get('item_name', ''),
                        'item_type': row.get('item_type', ''),
                        'price': row.get('price', ''),
                        'colors': colors,
                        'image_url': row.get('image_url', ''),
                        'link': row.get('link', '')
                    })
                
                return items
                
        except Exception as e:
            print(f"❌ Error loading {category_name} data: {e}")
            return []

    def save_master_catalog(self, items: List[Dict]):
        """Save master catalog with the new simplified structure."""
        with open(self.master_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['catalog_number', 'item_name', 'item_type', 'price', 'color', 'image_url', 'link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in items:
                # Format colors as a single string
                color_str = ', '.join(item.get('colors', [])) if item.get('colors') else 'Standard finish'
                
                writer.writerow({
                    'catalog_number': item.get('catalog_number', ''),
                    'item_name': item.get('item_name', ''),
                    'item_type': item.get('item_type', ''),
                    'price': item.get('price', ''),
                    'color': color_str,
                    'image_url': item.get('image_url', ''),
                    'link': item.get('link', '')
                })

    def create_master_catalog(self):
        """Create master catalog from individual category CSV files."""
        print("Master Catalog Updater - Simplified Version")
        print("=" * 60)
        print("📋 Compiling essential data from individual CSV files")
        print("🚫 No AI descriptions - focusing on core data only")
        
        # Load fresh data from individual CSV files
        all_items = []
        total_categories = len(self.categories)
        
        for i, (category_name, category_info) in enumerate(self.categories.items(), 1):
            print(f"\n📁 Processing {category_name} ({i}/{total_categories})...")
            
            items = self.load_category_data(category_name)
            if items:
                print(f"   ✅ Loaded {len(items)} items")
                all_items.extend(items)
            else:
                print(f"   ⚠️  No items found")
        
        print(f"\n📊 Total items loaded: {len(all_items)}")
        
        if not all_items:
            print("❌ No items found to create master catalog")
            return
        
        # Save master catalog
        self.save_master_catalog(all_items)
        
        print(f"\n✅ Master catalog created successfully!")
        print(f"   📁 Saved to: {self.master_csv_path}")
        print(f"   📊 Total items: {len(all_items)}")
        print(f"   📋 Columns: catalog_number, item_name, item_type, price, color, image_url, link")
        
        # Print sample of the data
        print(f"\n📋 Sample data:")
        for i, item in enumerate(all_items[:3]):
            print(f"   {i+1}. {item['catalog_number']} - {item['item_name']} ({item['item_type']}) - {item['price']}")

def main():
    """Main function to run the master catalog updater."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create simplified master catalog from individual CSV files')
    parser.add_argument('--catalog-type', choices=['haverty', 'boconcept', 'interior_define', 'interior_define_2'], default='interior_define', 
                       help='Type of catalog to process (default: interior_define)')
    parser.add_argument('--config-file', default='config.json', help='Path to config file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config_file)
    config.print_status()
    
    try:
        updater = MasterCatalogUpdater(catalog_type=args.catalog_type, config=config)
        updater.create_master_catalog()
            
    except KeyboardInterrupt:
        print("\nUpdate interrupted by user")
    except Exception as e:
        print(f"Update failed: {e}")

if __name__ == "__main__":
    main()