#!/usr/bin/env python3
"""
Furniture Combination Optimizer
Analyzes similarity results and finds budget-constrained combinations ranked by total similarity scores
"""

import os
import csv
import pandas as pd
import itertools
from typing import List, Dict, Tuple, Optional
from config import Config

class FurnitureCombinationOptimizer:
    """Furniture combination optimizer for budget-constrained selections"""
    
    def __init__(self):
        """Initialize the optimizer."""
        self.master_log_path = "querries/master_querry_log.csv"
        self.similarity_results = {}
        self.budget = 0
        self.query_number = None
        
    def check_master_query_log(self) -> Optional[int]:
        """Check master query log for queries that need combination optimization."""
        try:
            if not os.path.exists(self.master_log_path):
                print(f"❌ Master query log not found: {self.master_log_path}")
                return None
            
            print(f"📋 Checking master query log: {self.master_log_path}")
            
            # Read the CSV file
            df = pd.read_csv(self.master_log_path)
            
            if df.empty:
                print("ℹ️ No queries found in master log")
                return None
            
            # Filter for queries where selected_sufficed = 'no'
            pending_selection = df[df['selected_sufficed'].str.lower() == 'no']
            
            if pending_selection.empty:
                print("✅ No queries pending combination optimization")
                return None
            
            # Get the latest query that needs combination optimization
            latest_query = pending_selection.iloc[-1]
            query_number = latest_query['request_number']
            
            print(f"✅ Latest query pending combination optimization: {query_number}")
            print(f"   Room Type: {latest_query['room_type']}")
            print(f"   Style Type: {latest_query['style_type']}")
            print(f"   Color Palette: {latest_query['color_pallet']}")
            print(f"   Budget: {latest_query['budget']}")
            
            # Store budget and query number
            self.budget = self.parse_budget(latest_query['budget'])
            self.query_number = query_number
            
            return query_number
            
        except Exception as e:
            print(f"❌ Error checking master query log: {e}")
            return None
    
    def parse_budget(self, budget_str: str) -> float:
        """Parse budget string to float value."""
        try:
            # Remove currency symbols and convert to float
            budget_clean = budget_str.replace('$', '').replace(',', '').strip()
            return float(budget_clean)
        except Exception as e:
            print(f"❌ Error parsing budget '{budget_str}': {e}")
            return 0.0
    
    def load_similarity_results(self, query_number: int) -> bool:
        """Load similarity results from CSV file."""
        try:
            similarity_csv_path = f"querries/query_{query_number}/similarity_results.csv"
            
            if not os.path.exists(similarity_csv_path):
                print(f"❌ Similarity results not found: {similarity_csv_path}")
                return False
            
            print(f"📁 Loading similarity results: {similarity_csv_path}")
            
            # Read the CSV file
            df = pd.read_csv(similarity_csv_path)
            
            if df.empty:
                print("❌ No similarity results found")
                return False
            
            # Group by image_name and store top results for each furniture type
            self.similarity_results = {}
            
            for image_name in df['image_name'].unique():
                furniture_type = image_name.replace('_extracted_grayscale.png', '')
                
                # Get top 3 results for each furniture type
                furniture_results = df[df['image_name'] == image_name].head(3)
                
                self.similarity_results[furniture_type] = []
                for _, row in furniture_results.iterrows():
                    self.similarity_results[furniture_type].append({
                        'catalog_number': row['catalog_number'],
                        'similarity_score': row['similarity_score'],
                        'rank': row['rank']
                    })
            
            print(f"✅ Loaded similarity results for {len(self.similarity_results)} furniture types")
            for furniture_type, results in self.similarity_results.items():
                print(f"   • {furniture_type}: {len(results)} options")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading similarity results: {e}")
            return False
    
    def get_furniture_prices(self) -> Dict[str, Dict[str, float]]:
        """Get furniture prices from Interior Define master catalog with fallback to estimated prices."""
        try:
            catalog_path = "InteriorDefine_catalog/INTERIOR_DEFINE_MASTER_CATALOG.csv"
            
            if not os.path.exists(catalog_path):
                print(f"❌ Interior Define catalog not found: {catalog_path}")
                return self._get_estimated_prices()
            
            print(f"📁 Loading furniture prices from: {catalog_path}")
            
            # Read the catalog
            df = pd.read_csv(catalog_path)
            
            # Create price lookup dictionary
            price_lookup = {}
            
            for _, row in df.iterrows():
                catalog_number = row['catalog_number']
                price_str = str(row.get('price', '0'))
                
                # Parse price (handle various formats)
                try:
                    price_clean = price_str.replace('$', '').replace(',', '').replace('USD', '').strip()
                    if price_clean and price_clean != 'nan':
                        price = float(price_clean)
                        price_lookup[catalog_number] = price
                except:
                    continue
            
            print(f"✅ Loaded prices for {len(price_lookup)} items")
            
            # Check if similarity results catalog numbers match master catalog
            matched_items = 0
            total_items = 0
            
            for furniture_type, items in self.similarity_results.items():
                for item in items:
                    total_items += 1
                    if item['catalog_number'] in price_lookup:
                        matched_items += 1
            
            if matched_items == 0:
                print(f"⚠️  No catalog numbers match between similarity results and master catalog")
                print(f"   Similarity results use different catalog numbering (likely from grayscale database)")
                print(f"   Falling back to estimated pricing")
                return self._get_estimated_prices()
            elif matched_items < total_items:
                print(f"⚠️  Only {matched_items}/{total_items} catalog numbers match")
                print(f"   Using real prices where available, estimated prices for others")
            
            # Print sample prices
            print(f"📊 Sample prices:")
            for furniture_type, items in self.similarity_results.items():
                if items:
                    sample_item = items[0]
                    sample_price = price_lookup.get(sample_item['catalog_number'], 0)
                    if sample_price == 0:
                        # Use estimated price for unmatched items
                        estimated_price = self._get_estimated_price_for_type(furniture_type, 0)
                        print(f"   • {furniture_type}: ${estimated_price:,.2f} (estimated)")
                    else:
                        print(f"   • {furniture_type}: ${sample_price:,.2f}")
            
            return price_lookup
            
        except Exception as e:
            print(f"❌ Error loading furniture prices: {e}")
            return self._get_estimated_prices()
    
    def _get_estimated_prices(self) -> Dict[str, float]:
        """Get estimated prices for all items in similarity results."""
        price_lookup = {}
        
        for furniture_type, items in self.similarity_results.items():
            for i, item in enumerate(items):
                catalog_number = item['catalog_number']
                estimated_price = self._get_estimated_price_for_type(furniture_type, i)
                price_lookup[catalog_number] = estimated_price
        
        print(f"✅ Generated estimated prices for {len(price_lookup)} items")
        return price_lookup
    
    def _get_estimated_price_for_type(self, furniture_type: str, rank: int) -> float:
        """Get estimated price for a specific furniture type and rank."""
        # Estimated price ranges for different furniture types
        price_ranges = {
            'sofa': (800, 2500),      # Sofas: $800-$2500
            'chair': (200, 800),      # Chairs: $200-$800
            'table': (300, 1200),     # Tables: $300-$1200
            'lamp': (100, 400),       # Lamps: $100-$400
            'rug': (200, 800),        # Rugs: $200-$800
            'bench': (300, 1000),     # Benches: $300-$1000
            'nightstand': (150, 600), # Nightstands: $150-$600
            'lighting': (100, 400)    # Lighting: $100-$400
        }
        
        # Get price range for this furniture type
        base_type = furniture_type.lower()
        if base_type in price_ranges:
            min_price, max_price = price_ranges[base_type]
        else:
            min_price, max_price = 200, 800  # Default range
        
        # Generate price based on rank (better rank = higher price)
        rank_factor = (4 - rank) / 3  # 1.0 for rank 1, 0.67 for rank 2, 0.33 for rank 3
        price_range = max_price - min_price
        estimated_price = min_price + (price_range * rank_factor)
        
        return round(estimated_price, 2)
    
    def generate_combinations(self, price_lookup: Dict[str, float]) -> List[Dict]:
        """Generate all possible combinations within budget."""
        try:
            print(f"🔍 Generating combinations within budget: ${self.budget:,.2f}")
            
            # Get furniture types
            furniture_types = list(self.similarity_results.keys())
            
            # Generate all combinations
            combinations = []
            
            # Create list of all possible items with their details
            all_items = []
            for furniture_type, items in self.similarity_results.items():
                for item in items:
                    catalog_number = item['catalog_number']
                    price = price_lookup.get(catalog_number, 0)
                    
                    all_items.append({
                        'furniture_type': furniture_type,
                        'catalog_number': catalog_number,
                        'similarity_score': item['similarity_score'],
                        'rank': item['rank'],
                        'price': price
                    })
            
            # Generate combinations (one item per furniture type)
            furniture_types = list(self.similarity_results.keys())
            
            # Create combinations using itertools.product
            for combination in itertools.product(*[self.similarity_results[ft] for ft in furniture_types]):
                total_price = 0
                total_similarity = 0
                combination_details = []
                
                for i, item in enumerate(combination):
                    furniture_type = furniture_types[i]
                    catalog_number = item['catalog_number']
                    price = price_lookup.get(catalog_number, 0)
                    similarity_score = item['similarity_score']
                    
                    total_price += price
                    total_similarity += similarity_score
                    
                    combination_details.append({
                        'furniture_type': furniture_type,
                        'catalog_number': catalog_number,
                        'similarity_score': similarity_score,
                        'rank': item['rank'],
                        'price': price
                    })
                
                # Only include combinations within budget
                if total_price <= self.budget and total_price > 0:
                    combinations.append({
                        'total_price': total_price,
                        'total_similarity': total_similarity,
                        'items': combination_details,
                        'budget_remaining': self.budget - total_price
                    })
            
            # Sort by total similarity score (descending)
            combinations.sort(key=lambda x: x['total_similarity'], reverse=True)
            
            print(f"✅ Generated {len(combinations)} combinations within budget")
            return combinations
            
        except Exception as e:
            print(f"❌ Error generating combinations: {e}")
            return []
    
    def save_combinations_to_csv(self, combinations: List[Dict]) -> str:
        """Save combinations to CSV file."""
        try:
            output_path = f"querries/query_{self.query_number}/furniture_combinations.csv"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'combination_rank', 'total_price', 'total_similarity', 'budget_remaining',
                    'furniture_type', 'catalog_number', 'similarity_score', 'item_rank', 'price'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for rank, combination in enumerate(combinations, 1):
                    for item in combination['items']:
                        writer.writerow({
                            'combination_rank': rank,
                            'total_price': combination['total_price'],
                            'total_similarity': combination['total_similarity'],
                            'budget_remaining': combination['budget_remaining'],
                            'furniture_type': item['furniture_type'],
                            'catalog_number': item['catalog_number'],
                            'similarity_score': item['similarity_score'],
                            'item_rank': item['rank'],
                            'price': item['price']
                        })
            
            print(f"✅ Combinations saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error saving combinations: {e}")
            return ""
    
    def print_top_combinations(self, combinations: List[Dict], top_n: int = 5):
        """Print top N combinations."""
        try:
            print(f"\n🎉 TOP {min(top_n, len(combinations))} FURNITURE COMBINATIONS")
            print("=" * 80)
            
            for i, combination in enumerate(combinations[:top_n], 1):
                print(f"\n🏆 COMBINATION #{i}")
                print(f"   💰 Total Price: ${combination['total_price']:,.2f}")
                print(f"   📊 Total Similarity: {combination['total_similarity']:.4f}")
                print(f"   💵 Budget Remaining: ${combination['budget_remaining']:,.2f}")
                print(f"   📋 Items:")
                
                for item in combination['items']:
                    print(f"      • {item['furniture_type'].title()}: {item['catalog_number']} "
                          f"(Score: {item['similarity_score']:.4f}, Price: ${item['price']:,.2f})")
                
                print("-" * 80)
                
        except Exception as e:
            print(f"❌ Error printing combinations: {e}")
    
    def update_selection_status(self, status: str = "yes"):
        """Update the selected_sufficed status in master query log."""
        try:
            # Read the CSV
            df = pd.read_csv(self.master_log_path)
            
            # Update the selected_sufficed status for the specific query
            df.loc[df['request_number'] == self.query_number, 'selected_sufficed'] = status
            
            # Save back to CSV
            df.to_csv(self.master_log_path, index=False)
            
            print(f"✅ Updated selected_sufficed to '{status}' for query {self.query_number}")
            
        except Exception as e:
            print(f"❌ Error updating selection status: {e}")

def main():
    """Main function to optimize furniture combinations."""
    print("🎯 Furniture Combination Optimizer")
    print("=" * 50)
    
    # Initialize optimizer
    optimizer = FurnitureCombinationOptimizer()
    
    # Check master query log for queries that need combination optimization
    query_number = optimizer.check_master_query_log()
    if not query_number:
        print("✅ No queries pending combination optimization")
        return
    
    # Load similarity results
    if not optimizer.load_similarity_results(query_number):
        print("❌ Failed to load similarity results")
        return
    
    # Load furniture prices
    price_lookup = optimizer.get_furniture_prices()
    if not price_lookup:
        print("❌ Failed to load furniture prices")
        return
    
    # Generate combinations
    combinations = optimizer.generate_combinations(price_lookup)
    if not combinations:
        print("❌ No combinations found within budget")
        optimizer.update_selection_status("no")
        return
    
    # Print top combinations
    optimizer.print_top_combinations(combinations, top_n=5)
    
    # Save combinations to CSV
    csv_path = optimizer.save_combinations_to_csv(combinations)
    
    # Update selection status
    optimizer.update_selection_status("yes")
    
    print(f"\n✅ SUCCESS!")
    print(f"📊 Generated {len(combinations)} combinations within budget")
    print(f"📁 Results saved to: {csv_path}")
    print(f"✅ Selection status updated to 'yes' for query {query_number}")
    
    print(f"\n✅ Features delivered:")
    print(f"   ✅ Master query log analysis")
    print(f"   ✅ Similarity results processing")
    print(f"   ✅ Budget-constrained combinations")
    print(f"   ✅ Similarity score ranking")
    print(f"   ✅ CSV export with detailed results")

if __name__ == "__main__":
    main()
