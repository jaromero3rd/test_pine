#!/usr/bin/env python3
"""
Test Similarity Visualization
Creates side-by-side comparison images showing generated furniture next to similar catalog items
"""

import os
import csv
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from typing import List, Dict, Tuple
import argparse

class SimilarityVisualizer:
    """Creates visual comparisons between generated and similar furniture images"""
    
    def __init__(self):
        """Initialize the similarity visualizer."""
        self.base_query_dir = "querries"
        self.catalog_image_dir = "InteriorDefine_catalog_2"
        
    def load_similarity_results(self, query_number: int) -> Dict[str, List[Dict]]:
        """Load similarity results from CSV file."""
        try:
            csv_path = f"{self.base_query_dir}/query_{query_number}/similarity_results.csv"
            
            if not os.path.exists(csv_path):
                print(f"❌ Similarity results not found: {csv_path}")
                return {}
            
            print(f"📁 Loading similarity results from: {csv_path}")
            
            # Group results by image name
            results = {}
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                image_name = row['image_name']
                if image_name not in results:
                    results[image_name] = []
                
                results[image_name].append({
                    'rank': row['rank'],
                    'catalog_number': row['catalog_number'],
                    'similarity_score': row['similarity_score'],
                    'item_name': row['item_name'],
                    'item_type': row['item_type'],
                    'price': row['price'],
                    'color': row['color'],
                    'image_url': row['image_url'],
                    'link': row['link']
                })
            
            print(f"✅ Loaded similarity results for {len(results)} images")
            return results
            
        except Exception as e:
            print(f"❌ Error loading similarity results: {e}")
            return {}
    
    def find_catalog_image(self, catalog_number: str, item_type: str, image_url: str = None) -> str:
        """Find the catalog image file for a given catalog number."""
        try:
            # Map item types to folder names
            type_to_folder = {
                'sofa': 'sofas',
                'chair': 'chairs', 
                'table': 'tables',
                'bench': 'benches',
                'nightstand': 'nightstands',
                'lighting': 'lighting',
                'lamp': 'lighting',
                'rug': 'rugs'
            }
            
            folder = type_to_folder.get(item_type.lower(), item_type.lower())
            category_dir = os.path.join(self.catalog_image_dir, folder)
            
            if not os.path.exists(category_dir):
                print(f"⚠️  Category directory not found: {category_dir}")
                return None
            
            # First try to use the image_url if provided
            if image_url:
                # Convert .jpg to .png if needed
                base_name = os.path.splitext(image_url)[0]
                for ext in ['.png', '.jpg', '.jpeg']:
                    potential_path = os.path.join(category_dir, base_name + ext)
                    if os.path.exists(potential_path):
                        return potential_path
            
            # Look for image files that might match this catalog number
            for filename in os.listdir(category_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # Check if filename contains catalog number or similar pattern
                    if (catalog_number.lower() in filename.lower() or 
                        catalog_number.replace('-', '_').lower() in filename.lower()):
                        return os.path.join(category_dir, filename)
            
            # If no exact match, try to find by item name pattern
            print(f"⚠️  No exact match found for {catalog_number}, searching by pattern...")
            return None
            
        except Exception as e:
            print(f"❌ Error finding catalog image for {catalog_number}: {e}")
            return None
    
    def load_image_safely(self, image_path: str, max_size: Tuple[int, int] = (300, 300)) -> Image.Image:
        """Load and resize an image safely."""
        try:
            if not os.path.exists(image_path):
                print(f"⚠️  Image not found: {image_path}")
                return self.create_placeholder_image(max_size, "Image Not Found")
            
            image = Image.open(image_path).convert('RGB')
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Create a new image with exact size and paste the thumbnail
            new_image = Image.new('RGB', max_size, (240, 240, 240))
            paste_x = (max_size[0] - image.width) // 2
            paste_y = (max_size[1] - image.height) // 2
            new_image.paste(image, (paste_x, paste_y))
            
            return new_image
            
        except Exception as e:
            print(f"❌ Error loading image {image_path}: {e}")
            return self.create_placeholder_image(max_size, "Error Loading")
    
    def create_placeholder_image(self, size: Tuple[int, int], text: str) -> Image.Image:
        """Create a placeholder image when the original can't be loaded."""
        image = Image.new('RGB', size, (200, 200, 200))
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Draw text in the center
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), text, fill=(100, 100, 100), font=font)
        
        return image
    
    def create_comparison_image(self, generated_image_path: str, similar_items: List[Dict], 
                              output_path: str) -> bool:
        """Create a side-by-side comparison image."""
        try:
            print(f"🖼️  Creating comparison for: {os.path.basename(generated_image_path)}")
            
            # Load the generated image
            generated_img = self.load_image_safely(generated_image_path, (300, 300))
            
            # Load similar item images
            similar_images = []
            for item in similar_items:
                catalog_image_path = self.find_catalog_image(
                    item['catalog_number'], 
                    item['item_type'],
                    item.get('image_url', '')
                )
                
                if catalog_image_path:
                    similar_img = self.load_image_safely(catalog_image_path, (300, 300))
                else:
                    similar_img = self.create_placeholder_image(
                        (300, 300), 
                        f"{item['catalog_number']}\nNot Found"
                    )
                
                similar_images.append((similar_img, item))
            
            # Calculate layout
            num_similar = len(similar_images)
            if num_similar == 0:
                print("❌ No similar images to display")
                return False
            
            # Create the comparison image
            # Layout: Generated image on left, similar images in a grid on right
            img_width = 300
            img_height = 300
            
            # Calculate grid dimensions for similar images
            if num_similar <= 2:
                grid_cols = num_similar
                grid_rows = 1
            elif num_similar <= 4:
                grid_cols = 2
                grid_rows = 2
            else:
                grid_cols = 3
                grid_rows = (num_similar + 2) // 3
            
            # Calculate total dimensions
            total_width = img_width + (grid_cols * img_width) + 20  # 20px spacing
            total_height = max(img_height, grid_rows * img_height) + 100  # Extra space for labels
            
            # Create the main comparison image
            comparison_img = Image.new('RGB', (total_width, total_height), (255, 255, 255))
            draw = ImageDraw.Draw(comparison_img)
            
            try:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            except:
                font_large = None
                font_small = None
            
            # Add title
            title = f"Similarity Comparison: {os.path.basename(generated_image_path)}"
            draw.text((10, 10), title, fill=(0, 0, 0), font=font_large)
            
            # Place generated image on the left
            comparison_img.paste(generated_img, (10, 50))
            draw.text((10, 360), "Generated Image", fill=(0, 0, 0), font=font_small)
            
            # Place similar images in a grid
            x_offset = img_width + 30
            y_offset = 50
            
            for i, (similar_img, item) in enumerate(similar_images):
                row = i // grid_cols
                col = i % grid_cols
                
                x = x_offset + (col * img_width)
                y = y_offset + (row * img_height)
                
                comparison_img.paste(similar_img, (x, y))
                
                # Add labels
                label_y = y + img_height + 5
                
                # Item name (truncated)
                item_name = item['item_name'][:30] + "..." if len(item['item_name']) > 30 else item['item_name']
                draw.text((x, label_y), item_name, fill=(0, 0, 0), font=font_small)
                
                # Similarity score and price
                score_text = f"Score: {item['similarity_score']:.3f}"
                price_text = f"Price: ${item['price']}"
                
                draw.text((x, label_y + 15), score_text, fill=(0, 100, 0), font=font_small)
                draw.text((x, label_y + 30), price_text, fill=(0, 0, 150), font=font_small)
            
            # Save the comparison image
            comparison_img.save(output_path, 'PNG', quality=95)
            print(f"✅ Comparison image saved: {output_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating comparison image: {e}")
            return False
    
    def process_query(self, query_number: int) -> bool:
        """Process all images for a query and create comparison images."""
        try:
            print(f"🔍 Processing Query {query_number} Similarity Comparisons")
            print("=" * 60)
            
            # Load similarity results
            results = self.load_similarity_results(query_number)
            if not results:
                print("❌ No similarity results found")
                return False
            
            # Create output directory
            output_dir = f"{self.base_query_dir}/query_{query_number}/similarity_comparisons"
            os.makedirs(output_dir, exist_ok=True)
            
            success_count = 0
            total_count = len(results)
            
            for image_name, similar_items in results.items():
                print(f"\n🔄 Processing {image_name}...")
                
                # Find the generated image
                generated_image_path = f"{self.base_query_dir}/query_{query_number}/generated_images/generated_furniture_gray/{image_name}"
                
                if not os.path.exists(generated_image_path):
                    print(f"⚠️  Generated image not found: {generated_image_path}")
                    continue
                
                # Create comparison image
                output_filename = f"comparison_{os.path.splitext(image_name)[0]}.png"
                output_path = os.path.join(output_dir, output_filename)
                
                if self.create_comparison_image(generated_image_path, similar_items, output_path):
                    success_count += 1
                    print(f"✅ Created comparison for {image_name}")
                else:
                    print(f"❌ Failed to create comparison for {image_name}")
            
            print(f"\n📊 Summary:")
            print(f"   ✅ Successful: {success_count}/{total_count}")
            print(f"   📁 Output directory: {output_dir}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Error processing query {query_number}: {e}")
            return False

def main():
    """Main function to create similarity comparison images."""
    parser = argparse.ArgumentParser(description='Create similarity comparison images')
    parser.add_argument('--query', type=int, default=3, 
                       help='Query number to process (default: 3)')
    
    args = parser.parse_args()
    
    print("🖼️  Similarity Comparison Image Generator")
    print("=" * 50)
    
    visualizer = SimilarityVisualizer()
    success = visualizer.process_query(args.query)
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Similarity comparison images created for query {args.query}")
    else:
        print(f"\n❌ FAILED!")
        print(f"❌ Could not create similarity comparison images")

if __name__ == "__main__":
    main()
