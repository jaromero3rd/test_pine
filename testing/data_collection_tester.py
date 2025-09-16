#!/usr/bin/env python3
"""
Data Collection Verification Script
Tests the master catalog updater to ensure all columns are correctly collected and reports failures
"""

import os
import csv
import json
import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class DataCollectionTester:
    def __init__(self):
        """Initialize the data collection tester."""
        self.base_output_dir = "haverty_catalog"
        self.master_csv_path = os.path.join(self.base_output_dir, "HAVERTYS_MASTER_CATALOG.csv")
        
        # Create timestamped report directory inside data_collection_report folder
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = os.path.join("data_collection_report", f"data_collection_report_{timestamp}")
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Define categories
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
        
        self.test_results = {
            'total_items': 0,
            'missing_dimensions': [],
            'missing_colors': [],
            'missing_images': [],
            'missing_links': [],
            'missing_prices': [],
            'dimension_format_issues': [],
            'color_format_issues': [],
            'master_catalog_issues': [],
            'category_stats': defaultdict(lambda: {
                'total_items': 0,
                'missing_dimensions': 0,
                'missing_colors': 0,
                'missing_images': 0,
                'missing_links': 0,
                'missing_prices': 0
            })
        }

    def parse_dimensions(self, dimensions_str: str) -> str:
        """Parse dimensions string and return formatted string."""
        try:
            if not dimensions_str or dimensions_str == '{}':
                return "Dimensions not available"
            
            # Handle both string and dict formats
            if isinstance(dimensions_str, str):
                dimensions = eval(dimensions_str)
            else:
                dimensions = dimensions_str
            
            if not isinstance(dimensions, dict):
                return "Dimensions not available"
            
            parts = []
            if 'width' in dimensions:
                parts.append(f"Width: {dimensions['width']}")
            if 'height' in dimensions:
                parts.append(f"Height: {dimensions['height']}")
            if 'depth' in dimensions:
                parts.append(f"Depth: {dimensions['depth']}")
            if 'weight' in dimensions:
                parts.append(f"Weight: {dimensions['weight']}")
            
            return ", ".join(parts) if parts else "Dimensions not available"
            
        except Exception as e:
            return f"Dimensions parsing error: {str(e)}"

    def load_category_data(self, category_name: str) -> List[Dict]:
        """Load data from a category CSV file."""
        category_info = self.categories[category_name]
        csv_path = os.path.join(self.base_output_dir, category_info['folder'], category_info['csv_file'])
        
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                items = []
                for row in reader:
                    # Convert dimensions string back to dict
                    dimensions_str = row.get('dimensions', '{}')
                    if dimensions_str and dimensions_str != '{}':
                        try:
                            dimensions = eval(dimensions_str)
                        except:
                            dimensions = {}
                    else:
                        dimensions = {}
                    
                    # Convert colors string back to list
                    colors_str = row.get('colors', '')
                    colors = [c.strip() for c in colors_str.split(',')] if colors_str else []
                    
                    items.append({
                        'catalog_number': row.get('catalog_number', ''),
                        'item_name': row.get('item_name', ''),
                        'price': row.get('price', ''),
                        'link': row.get('link', ''),
                        'image_url': row.get('image_url', ''),
                        'colors': colors,
                        'dimensions': dimensions,
                        'dimensions_str': dimensions_str,
                        'item_type': row.get('item_type', '')
                    })
                
                return items
                
        except Exception as e:
            print(f"❌ Error loading {category_name} data: {e}")
            return []

    def check_image_exists(self, item: Dict, category_folder: str) -> bool:
        """Check if image file exists for an item."""
        item_name = item.get('item_name', '')
        catalog_number = item.get('catalog_number', '')
        item_type = item.get('item_type', '')
        
        category_dir = os.path.join(self.base_output_dir, category_folder)
        
        if not os.path.exists(category_dir):
            return False
        
        # Look for image files that match the item
        for filename in os.listdir(category_dir):
            if filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png'):
                # Check if filename contains item name or catalog number
                if (item_name.lower() in filename.lower() or 
                    catalog_number in filename or
                    item_type in filename.lower()):
                    return True
        
        return False

    def test_category_data(self, category_name: str) -> Dict:
        """Test data collection for a specific category."""
        print(f"\n🔍 Testing {category_name.upper()} category...")
        
        category_info = self.categories[category_name]
        items = self.load_category_data(category_name)
        
        if not items:
            print(f"❌ No items found in {category_name}")
            return {}
        
        print(f"✓ Found {len(items)} items in {category_name}")
        
        category_results = {
            'total_items': len(items),
            'missing_dimensions': [],
            'missing_colors': [],
            'missing_images': [],
            'missing_links': [],
            'missing_prices': [],
            'dimension_format_issues': [],
            'color_format_issues': []
        }
        
        for item in items:
            item_name = item.get('item_name', 'Unknown')
            catalog_number = item.get('catalog_number', 'Unknown')
            
            # Check dimensions
            dimensions = item.get('dimensions', {})
            dimensions_str = item.get('dimensions_str', '{}')
            
            if not dimensions or dimensions == {} or dimensions_str == '{}':
                category_results['missing_dimensions'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name,
                    'issue': 'No dimensions data'
                })
            else:
                # Check if dimensions are properly formatted
                formatted_dims = self.parse_dimensions(dimensions_str)
                if "error" in formatted_dims.lower():
                    category_results['dimension_format_issues'].append({
                        'catalog_number': catalog_number,
                        'item_name': item_name,
                        'issue': formatted_dims,
                        'raw_data': dimensions_str
                    })
            
            # Check colors
            colors = item.get('colors', [])
            if not colors:
                category_results['missing_colors'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name,
                    'issue': 'No colors data'
                })
            
            # Check image
            if not self.check_image_exists(item, category_info['folder']):
                category_results['missing_images'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name,
                    'issue': 'Image file not found'
                })
            
            # Check link
            link = item.get('link', '')
            if not link:
                category_results['missing_links'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name,
                    'issue': 'No product link'
                })
            
            # Check price
            price = item.get('price', '')
            if not price:
                category_results['missing_prices'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name,
                    'issue': 'No price data'
                })
        
        # Print summary for this category
        print(f"  📊 {category_name.upper()} Summary:")
        print(f"    Total items: {category_results['total_items']}")
        print(f"    Missing dimensions: {len(category_results['missing_dimensions'])}")
        print(f"    Missing colors: {len(category_results['missing_colors'])}")
        print(f"    Missing images: {len(category_results['missing_images'])}")
        print(f"    Missing links: {len(category_results['missing_links'])}")
        print(f"    Missing prices: {len(category_results['missing_prices'])}")
        print(f"    Dimension format issues: {len(category_results['dimension_format_issues'])}")
        
        return category_results

    def test_master_catalog(self) -> Dict:
        """Test the master catalog for data consistency."""
        print(f"\n🔍 Testing MASTER CATALOG...")
        
        if not os.path.exists(self.master_csv_path):
            print("❌ Master catalog file not found!")
            return {}
        
        try:
            with open(self.master_csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                master_items = list(reader)
        except Exception as e:
            print(f"❌ Error reading master catalog: {e}")
            return {}
        
        print(f"✓ Found {len(master_items)} items in master catalog")
        
        master_results = {
            'total_items': len(master_items),
            'missing_dimensions_in_description': [],
            'dimension_format_issues': [],
            'missing_colors_in_description': [],
            'template_descriptions': [],
            'ai_descriptions': []
        }
        
        for item in master_items:
            catalog_number = item.get('catalog_number', 'Unknown')
            item_name = item.get('item_name', 'Unknown')
            master_description = item.get('master_description', '')
            
            # Check if dimensions are in the description
            if "Dimensions not available" in master_description:
                master_results['missing_dimensions_in_description'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name,
                    'issue': 'Dimensions not available in master description'
                })
            
            # Check if colors are in the description
            if "Standard finish" in master_description and "Color:" in master_description:
                master_results['missing_colors_in_description'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name,
                    'issue': 'Using generic color description'
                })
            
            # Check description type
            if "This " in master_description and " features " in master_description:
                master_results['template_descriptions'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name
                })
            elif "Description: " in master_description and "Feel_to_the_touch: " in master_description:
                master_results['ai_descriptions'].append({
                    'catalog_number': catalog_number,
                    'item_name': item_name
                })
        
        # Print summary
        print(f"  📊 MASTER CATALOG Summary:")
        print(f"    Total items: {master_results['total_items']}")
        print(f"    Missing dimensions in descriptions: {len(master_results['missing_dimensions_in_description'])}")
        print(f"    Missing colors in descriptions: {len(master_results['missing_colors_in_description'])}")
        print(f"    Template descriptions: {len(master_results['template_descriptions'])}")
        print(f"    AI descriptions: {len(master_results['ai_descriptions'])}")
        
        return master_results

    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive data collection test."""
        print("=" * 80)
        print("🔍 DATA COLLECTION VERIFICATION TEST")
        print("=" * 80)
        
        # Test each category
        category_results = {}
        for category_name in self.categories.keys():
            category_results[category_name] = self.test_category_data(category_name)
        
        # Test master catalog
        master_results = self.test_master_catalog()
        
        # Compile overall results
        overall_results = {
            'category_results': category_results,
            'master_results': master_results,
            'summary': self.generate_summary(category_results, master_results)
        }
        
        return overall_results

    def generate_summary(self, category_results: Dict, master_results: Dict) -> Dict:
        """Generate overall summary statistics."""
        total_items = sum(cat['total_items'] for cat in category_results.values())
        total_missing_dimensions = sum(len(cat['missing_dimensions']) for cat in category_results.values())
        total_missing_colors = sum(len(cat['missing_colors']) for cat in category_results.values())
        total_missing_images = sum(len(cat['missing_images']) for cat in category_results.values())
        total_missing_links = sum(len(cat['missing_links']) for cat in category_results.values())
        total_missing_prices = sum(len(cat['missing_prices']) for cat in category_results.values())
        
        summary = {
            'total_items_tested': total_items,
            'total_missing_dimensions': total_missing_dimensions,
            'total_missing_colors': total_missing_colors,
            'total_missing_images': total_missing_images,
            'total_missing_links': total_missing_links,
            'total_missing_prices': total_missing_prices,
            'dimension_collection_rate': ((total_items - total_missing_dimensions) / total_items * 100) if total_items > 0 else 0,
            'color_collection_rate': ((total_items - total_missing_colors) / total_items * 100) if total_items > 0 else 0,
            'image_collection_rate': ((total_items - total_missing_images) / total_items * 100) if total_items > 0 else 0,
            'link_collection_rate': ((total_items - total_missing_links) / total_items * 100) if total_items > 0 else 0,
            'price_collection_rate': ((total_items - total_missing_prices) / total_items * 100) if total_items > 0 else 0
        }
        
        return summary

    def print_detailed_report(self, results: Dict):
        """Print detailed report of all issues found."""
        print("\n" + "=" * 80)
        print("📋 DETAILED ISSUE REPORT")
        print("=" * 80)
        
        summary = results['summary']
        print(f"\n📊 OVERALL SUMMARY:")
        print(f"  Total items tested: {summary['total_items_tested']}")
        print(f"  Dimension collection rate: {summary['dimension_collection_rate']:.1f}%")
        print(f"  Color collection rate: {summary['color_collection_rate']:.1f}%")
        print(f"  Image collection rate: {summary['image_collection_rate']:.1f}%")
        print(f"  Link collection rate: {summary['link_collection_rate']:.1f}%")
        print(f"  Price collection rate: {summary['price_collection_rate']:.1f}%")
        
        # Print detailed issues by category
        for category_name, category_data in results['category_results'].items():
            if not category_data:
                continue
                
            print(f"\n🔍 {category_name.upper()} DETAILED ISSUES:")
            
            if category_data['missing_dimensions']:
                print(f"  ❌ Missing Dimensions ({len(category_data['missing_dimensions'])}):")
                for issue in category_data['missing_dimensions'][:5]:  # Show first 5
                    print(f"    - {issue['catalog_number']}: {issue['item_name']}")
                if len(category_data['missing_dimensions']) > 5:
                    print(f"    ... and {len(category_data['missing_dimensions']) - 5} more")
            
            if category_data['missing_colors']:
                print(f"  ❌ Missing Colors ({len(category_data['missing_colors'])}):")
                for issue in category_data['missing_colors'][:5]:  # Show first 5
                    print(f"    - {issue['catalog_number']}: {issue['item_name']}")
                if len(category_data['missing_colors']) > 5:
                    print(f"    ... and {len(category_data['missing_colors']) - 5} more")
            
            if category_data['missing_images']:
                print(f"  ❌ Missing Images ({len(category_data['missing_images'])}):")
                for issue in category_data['missing_images'][:5]:  # Show first 5
                    print(f"    - {issue['catalog_number']}: {issue['item_name']}")
                if len(category_data['missing_images']) > 5:
                    print(f"    ... and {len(category_data['missing_images']) - 5} more")
            
            if category_data['missing_links']:
                print(f"  ❌ Missing Links ({len(category_data['missing_links'])}):")
                for issue in category_data['missing_links'][:5]:  # Show first 5
                    print(f"    - {issue['catalog_number']}: {issue['item_name']}")
                if len(category_data['missing_links']) > 5:
                    print(f"    ... and {len(category_data['missing_links']) - 5} more")
            
            if category_data['missing_prices']:
                print(f"  ❌ Missing Prices ({len(category_data['missing_prices'])}):")
                for issue in category_data['missing_prices'][:5]:  # Show first 5
                    print(f"    - {issue['catalog_number']}: {issue['item_name']}")
                if len(category_data['missing_prices']) > 5:
                    print(f"    ... and {len(category_data['missing_prices']) - 5} more")
        
        # Print master catalog issues
        master_results = results['master_results']
        if master_results:
            print(f"\n🔍 MASTER CATALOG ISSUES:")
            
            if master_results['missing_dimensions_in_description']:
                print(f"  ❌ Missing Dimensions in Descriptions ({len(master_results['missing_dimensions_in_description'])}):")
                for issue in master_results['missing_dimensions_in_description'][:5]:
                    print(f"    - {issue['catalog_number']}: {issue['item_name']}")
                if len(master_results['missing_dimensions_in_description']) > 5:
                    print(f"    ... and {len(master_results['missing_dimensions_in_description']) - 5} more")
            
            if master_results['missing_colors_in_description']:
                print(f"  ❌ Generic Colors in Descriptions ({len(master_results['missing_colors_in_description'])}):")
                for issue in master_results['missing_colors_in_description'][:5]:
                    print(f"    - {issue['catalog_number']}: {issue['item_name']}")
                if len(master_results['missing_colors_in_description']) > 5:
                    print(f"    ... and {len(master_results['missing_colors_in_description']) - 5} more")

    def save_report(self, results: Dict, filename: str = "data_collection_report.json"):
        """Save detailed report to JSON file in timestamped directory."""
        try:
            report_path = os.path.join(self.report_dir, filename)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Detailed report saved to: {report_path}")
            
            # Also save a summary text report
            summary_path = os.path.join(self.report_dir, "summary_report.txt")
            self.save_summary_report(results, summary_path)
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    def save_summary_report(self, results: Dict, filename: str):
        """Save a human-readable summary report."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("DATA COLLECTION REPORT SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                # Get summary data
                summary = results.get('summary', {})
                category_results = results.get('category_results', {})
                
                # Overall statistics
                f.write("OVERALL STATISTICS:\n")
                f.write(f"Total Items Tested: {summary.get('total_items_tested', 0)}\n")
                f.write(f"Missing Images: {summary.get('total_missing_images', 0)}\n")
                f.write(f"Missing Colors: {summary.get('total_missing_colors', 0)}\n")
                f.write(f"Missing Dimensions: {summary.get('total_missing_dimensions', 0)}\n")
                f.write(f"Missing Links: {summary.get('total_missing_links', 0)}\n")
                f.write(f"Missing Prices: {summary.get('total_missing_prices', 0)}\n")
                f.write(f"Image Collection Rate: {summary.get('image_collection_rate', 0):.1f}%\n")
                f.write(f"Color Collection Rate: {summary.get('color_collection_rate', 0):.1f}%\n")
                f.write(f"Dimension Collection Rate: {summary.get('dimension_collection_rate', 0):.1f}%\n\n")
                
                # Category breakdown
                f.write("CATEGORY BREAKDOWN:\n")
                for category, data in category_results.items():
                    f.write(f"{category.upper()}:\n")
                    f.write(f"  Total Items: {data.get('total_items', 0)}\n")
                    f.write(f"  Missing Images: {len(data.get('missing_images', []))}\n")
                    f.write(f"  Missing Colors: {len(data.get('missing_colors', []))}\n")
                    f.write(f"  Missing Dimensions: {len(data.get('missing_dimensions', []))}\n")
                    f.write(f"  Missing Links: {len(data.get('missing_links', []))}\n")
                    f.write(f"  Missing Prices: {len(data.get('missing_prices', []))}\n\n")
                
                # Major issues
                f.write("MAJOR ISSUES IDENTIFIED:\n")
                issues = summary.get('major_issues', [])
                if issues:
                    for issue in issues:
                        f.write(f"- {issue}\n")
                else:
                    f.write("- No major issues identified\n")
                
                f.write(f"\nReport generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            print(f"📄 Summary report saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error saving summary report: {e}")

def main():
    """Main function to run the data collection test."""
    tester = DataCollectionTester()
    results = tester.run_comprehensive_test()
    tester.print_detailed_report(results)
    tester.save_report(results)
    
    print("\n" + "=" * 80)
    print("✅ DATA COLLECTION TEST COMPLETE")
    print(f"📁 Reports saved to: {tester.report_dir}/")
    print("=" * 80)

if __name__ == "__main__":
    main()
