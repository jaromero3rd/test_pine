#!/usr/bin/env python3
"""
GPT Furniture Extractor
Uses GPT-Image-1 to extract furniture from images with clean backgrounds
"""

import os
import base64
import csv
import datetime
import pandas as pd
from typing import Optional, List, Tuple
from config import Config
from openai import OpenAI

# PIL imports for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL library not installed. Install with: pip install Pillow")

# OpenCV imports for grayscale conversion
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV library not installed. Install with: pip install opencv-python")

class GPTFurnitureExtractor:
    """GPT-Image-1 based furniture extractor"""
    
    def __init__(self):
        """Initialize the GPT furniture extractor."""
        self.client = None
        self._init_openai()
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            config = Config()
            api_key = config.get_openai_key()
            
            if not api_key:
                print("❌ OpenAI API key not found")
                return
            
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized successfully")
            
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {e}")
            self.client = None
    
    def check_master_query_log(self) -> Optional[int]:
        """Check master query log for queries that need extraction."""
        try:
            master_log_path = "querries/master_querry_log.csv"
            
            if not os.path.exists(master_log_path):
                print(f"❌ Master query log not found: {master_log_path}")
                return None
            
            # Read the master query log
            df = pd.read_csv(master_log_path)
            
            # Find queries where extraction_sufficed is "no"
            pending_extractions = df[df['extraction_sufficed'] == 'no']
            
            if pending_extractions.empty:
                print("✅ No queries pending extraction")
                return None
            
            # Get the latest query number that needs extraction
            latest_query = pending_extractions['request_number'].max()
            print(f"🔍 Found query {latest_query} pending extraction")
            
            return latest_query
            
        except Exception as e:
            print(f"❌ Error checking master query log: {e}")
            return None
    
    def find_designed_room_image(self, query_number: int) -> Optional[str]:
        """Find the designed room image for a query."""
        try:
            designed_room_path = f"querries/query_{query_number}/generated_images/designed_room"
            
            if not os.path.exists(designed_room_path):
                print(f"❌ Designed room folder not found: {designed_room_path}")
                return None
            
            # Look for image files in the designed room folder
            image_files = []
            for file in os.listdir(designed_room_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_files.append(os.path.join(designed_room_path, file))
            
            if not image_files:
                print(f"❌ No images found in designed room folder: {designed_room_path}")
                return None
            
            # Use the first image found
            image_path = image_files[0]
            print(f"✅ Found designed room image: {os.path.basename(image_path)}")
            return image_path
            
        except Exception as e:
            print(f"❌ Error finding designed room image: {e}")
            return None
    
    def update_extraction_status(self, query_number: int, status: str = "yes"):
        """Update the extraction_sufficed status in master query log."""
        try:
            master_log_path = "querries/master_querry_log.csv"
            
            # Read the CSV
            df = pd.read_csv(master_log_path)
            
            # Update the extraction_sufficed status for the specific query
            df.loc[df['request_number'] == query_number, 'extraction_sufficed'] = status
            
            # Save back to CSV
            df.to_csv(master_log_path, index=False)
            
            print(f"✅ Updated extraction_sufficed to '{status}' for query {query_number}")
            
        except Exception as e:
            print(f"❌ Error updating extraction status: {e}")
    
    def is_available(self) -> bool:
        """Check if GPT-Image-1 is available."""
        return self.client is not None
    
    def create_folder_structure(self, query_number: int) -> str:
        """Create the new folder structure for organized output."""
        try:
            # Create main query folder
            query_folder = f"reference_query_{query_number}"
            os.makedirs(query_folder, exist_ok=True)
            
            # Create generated_images folder with subfolders
            generated_images_folder = os.path.join(query_folder, "generated_images")
            os.makedirs(generated_images_folder, exist_ok=True)
            
            # Create subfolders
            subfolders = ["empty_room", "designed_room", "generated_furniture", "generated_furniture_gray"]
            for subfolder in subfolders:
                os.makedirs(os.path.join(generated_images_folder, subfolder), exist_ok=True)
            
            print(f"✅ Created folder structure: {query_folder}")
            return query_folder
            
        except Exception as e:
            print(f"❌ Error creating folder structure: {e}")
            return ""
    
    def create_query_csv(self, query_folder: str, query_number: int, room_type: str = "living_room", 
                        style_type: str = "modern", color_pallet: str = "neutral", budget: str = "medium") -> str:
        """Create CSV file with query information."""
        try:
            csv_path = os.path.join(query_folder, "query_info.csv")
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['request_number', 'room_type', 'style_type', 'color_pallet', 'budget']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerow({
                    'request_number': query_number,
                    'room_type': room_type,
                    'style_type': style_type,
                    'color_pallet': color_pallet,
                    'budget': budget
                })
            
            print(f"✅ Query CSV created: {csv_path}")
            return csv_path
            
        except Exception as e:
            print(f"❌ Error creating query CSV: {e}")
            return ""
    
    def convert_to_grayscale_opencv(self, input_path: str, output_path: str) -> bool:
        """Convert image to grayscale using OpenCV."""
        if not OPENCV_AVAILABLE:
            print("❌ OpenCV not available for grayscale conversion")
            return False
            
        try:
            print(f"🔄 Converting to grayscale: {os.path.basename(input_path)}")
            
            # Read the image
            img = cv2.imread(input_path)
            if img is None:
                print(f"❌ Could not read image: {input_path}")
                return False
            
            # Convert to grayscale
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Save the grayscale image
            cv2.imwrite(output_path, gray_img)
            
            print(f"✅ Grayscale image saved: {os.path.basename(output_path)}")
            return True
            
        except Exception as e:
            print(f"❌ Error converting to grayscale: {e}")
            return False
    
    def process_generated_images_to_grayscale(self, query_number: int) -> List[str]:
        """Process all generated furniture images and create grayscale versions."""
        try:
            generated_furniture_folder = f"querries/query_{query_number}/generated_images/generated_furniture"
            grayscale_folder = f"querries/query_{query_number}/generated_images/generated_furniture_gray"
            
            if not os.path.exists(generated_furniture_folder):
                print(f"❌ Generated furniture folder not found: {generated_furniture_folder}")
                return []
            
            grayscale_images = []
            
            # Process all images in the generated_furniture folder
            for filename in os.listdir(generated_furniture_folder):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    input_path = os.path.join(generated_furniture_folder, filename)
                    
                    # Create grayscale filename
                    name, ext = os.path.splitext(filename)
                    grayscale_filename = f"{name}_grayscale{ext}"
                    output_path = os.path.join(grayscale_folder, grayscale_filename)
                    
                    # Convert to grayscale
                    if self.convert_to_grayscale_opencv(input_path, output_path):
                        grayscale_images.append(output_path)
            
            print(f"✅ Created {len(grayscale_images)} grayscale images")
            return grayscale_images
            
        except Exception as e:
            print(f"❌ Error processing images to grayscale: {e}")
            return []
    
    def convert_avif_to_png(self, avif_path: str, png_path: str) -> bool:
        """Convert AVIF image to PNG format."""
        if not PIL_AVAILABLE:
            print("❌ PIL not available for image conversion")
            return False
            
        try:
            print(f"🔄 Converting {os.path.basename(avif_path)} to PNG...")
            
            with Image.open(avif_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as PNG
                img.save(png_path, 'PNG')
                print(f"✅ Converted to: {os.path.basename(png_path)}")
                return True
                
        except Exception as e:
            print(f"❌ Error converting image: {e}")
            return False
    
    def generate_with_reference_images(self, reference_images: List[str], prompt: str, output_path: str) -> Optional[str]:
        """Generate image using GPT-Image-1 with reference images."""
        try:
            print(f"🎨 Generating image with GPT-Image-1 using {len(reference_images)} reference images...")
            
            # Open all reference images
            image_files = []
            for img_path in reference_images:
                if os.path.exists(img_path):
                    image_files.append(open(img_path, "rb"))
                    print(f"📁 Loaded reference: {os.path.basename(img_path)}")
                else:
                    print(f"❌ Reference image not found: {img_path}")
                    return None
            
            try:
                # Generate image using GPT-Image-1 with reference images
                result = self.client.images.edit(
                    model="gpt-image-1",
                    image=image_files[0],  # Use first image only
                    prompt=prompt,
                    quality="low"
                )
                
                # Get the generated image
                image_base64 = result.data[0].b64_json
                image_bytes = base64.b64decode(image_base64)
                
                # Save the image to file
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                
                print(f"✅ Image generated and saved to: {os.path.basename(output_path)}")
                return output_path
                
            finally:
                # Close all image files
                for img_file in image_files:
                    img_file.close()
                
        except Exception as e:
            print(f"❌ Error generating image with GPT-Image-1: {e}")
            return None
    
    def detect_furniture_items_and_colors(self, image_path: str) -> Tuple[List[str], List[str]]:
        """Use GPT-4 Vision to detect furniture items and their colors in the image."""
        try:
            print(f"🔍 Detecting furniture items and colors in: {os.path.basename(image_path)}")
            
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create the detection prompt
            detection_prompt = """
Look at this image and identify which of these furniture types are present:
- benches
- chairs  
- lamps
- nightstands
- rugs
- sofas
- tables

For each furniture item you detect, also identify its primary color/material.

Respond with ONLY two lists in this exact format:
Items: [item1, item2, item3]
Colors: [color1, color2, color3]

Where color1 corresponds to item1, color2 to item2, etc.

For example, if you see a gray sofa and a wooden table, respond:
Items: [sofa, table]
Colors: [gray, wooden]

If you see nothing, respond:
Items: []
Colors: []
"""
            
            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": detection_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            print(f"📋 GPT-4 Vision detected: {response_text}")
            
            # Extract items and colors from the response
            items = []
            colors = []
            
            try:
                lines = response_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Items:'):
                        items_text = line.replace('Items:', '').strip()
                        if items_text.startswith('[') and items_text.endswith(']'):
                            items_content = items_text[1:-1]
                            if items_content.strip():
                                items = [item.strip() for item in items_content.split(',')]
                    elif line.startswith('Colors:'):
                        colors_text = line.replace('Colors:', '').strip()
                        if colors_text.startswith('[') and colors_text.endswith(']'):
                            colors_content = colors_text[1:-1]
                            if colors_content.strip():
                                colors = [color.strip() for color in colors_content.split(',')]
                
                # Validate that items and colors match
                if len(items) != len(colors):
                    print(f"⚠️ Mismatch: {len(items)} items but {len(colors)} colors")
                    # Pad with "unknown" if colors are missing
                    while len(colors) < len(items):
                        colors.append("unknown")
                    # Truncate if too many colors
                    colors = colors[:len(items)]
                
                print(f"✅ Detected furniture items: {items}")
                print(f"✅ Detected colors: {colors}")
                return items, colors
                
            except Exception as parse_error:
                print(f"⚠️ Error parsing response: {parse_error}")
                return [], []
                
        except Exception as e:
            print(f"❌ Error detecting furniture items and colors: {e}")
            return [], []
    
    def save_detection_results_to_csv(self, query_number: int, items: List[str], colors: List[str], image_path: str) -> str:
        """Save detection results to CSV file."""
        try:
            csv_path = "generated_images/furniture_detection_results.csv"
            
            # Check if CSV file exists to determine if we need headers
            file_exists = os.path.exists(csv_path)
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['query_number', 'timestamp', 'image_path', 'items', 'colors']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Write the data
                writer.writerow({
                    'query_number': query_number,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'image_path': image_path,
                    'items': ','.join(items),
                    'colors': ','.join(colors)
                })
            
            print(f"✅ Detection results saved to CSV: {csv_path}")
            return csv_path
            
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
            return ""
    
    def extract_furniture_item(self, reference_image: str, item_type: str, query_number: int) -> Optional[str]:
        """Extract a specific furniture item using GPT-Image-1."""
        try:
            # Set output path for the new folder structure
            output_path = f"querries/query_{query_number}/generated_images/generated_furniture/{item_type}_extracted.png"
            
            print(f"🎨 Extracting {item_type} with GPT-Image-1...")
            
            # Create item-specific prompt
            prompt = f"Extract the {item_type} and put it in the center of the image and head on. Make all background around the {item_type} white."
            
            # Call GPT-Image-1 with reference image
            response = self.client.images.edit(
                model="gpt-image-1",
                image=open(reference_image, "rb"),
                prompt=prompt,
                quality="low"
            )
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the result
            if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
                # GPT-Image-1 returns base64 data
                import base64
                image_data = base64.b64decode(response.data[0].b64_json)
                with open(output_path, "wb") as f:
                    f.write(image_data)
            elif hasattr(response.data[0], 'url') and response.data[0].url:
                # DALL-E returns URL
                image_url = response.data[0].url
                import requests
                response_img = requests.get(image_url)
                with open(output_path, "wb") as f:
                    f.write(response_img.content)
            else:
                print(f"❌ No image data received from API")
                return None
            
            print(f"✅ {item_type.title()} extraction completed: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error extracting {item_type}: {e}")
            return None
    
    def convert_to_png_if_needed(self, image_path: str) -> Optional[str]:
        """Convert image to PNG format if needed and resize if too large."""
        try:
            if not PIL_AVAILABLE:
                print("❌ PIL not available for image conversion")
                return None
            
            # Check if already PNG
            if image_path.lower().endswith('.png'):
                # Check file size
                file_size = os.path.getsize(image_path)
                if file_size < 4 * 1024 * 1024:  # Less than 4MB
                    return image_path
                else:
                    print(f"⚠️ PNG file is {file_size / (1024*1024):.1f}MB, resizing...")
            
            # Convert to PNG and resize if needed
            img = Image.open(image_path)
            
            # Resize if image is too large (keep aspect ratio)
            max_size = 1024  # Maximum dimension
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                print(f"✅ Resized image to {img.width}x{img.height}")
            
            png_path = image_path.rsplit('.', 1)[0] + '.png'
            img.save(png_path, 'PNG', optimize=True)
            
            # Check final size
            final_size = os.path.getsize(png_path)
            print(f"✅ Converted to PNG: {os.path.basename(png_path)} ({final_size / (1024*1024):.1f}MB)")
            
            return png_path
            
        except Exception as e:
            print(f"❌ Error converting image to PNG: {e}")
            return None
    
    def process_all_furniture(self, reference_image: str, query_number: int) -> Tuple[List[str], List[str], List[str]]:
        """Process all furniture items detected in the image."""
        try:
            print(f"🏠 Processing all furniture in: {os.path.basename(reference_image)}")
            
            # Convert image to PNG once at the beginning
            png_image_path = self.convert_to_png_if_needed(reference_image)
            if not png_image_path:
                print(f"❌ Failed to convert image to PNG format")
                return [], [], []
            
            # Detect furniture items and colors using the PNG image
            items, colors = self.detect_furniture_items_and_colors(png_image_path)
            
            if not items:
                print("❌ No furniture items detected")
                return [], [], []
            
            # Save detection results to CSV
            csv_path = self.save_detection_results_to_csv(query_number, items, colors, reference_image)
            
            # Extract each detected item using the PNG image
            extracted_images = []
            for i, item in enumerate(items):
                color = colors[i] if i < len(colors) else "unknown"
                print(f"\n🔄 Processing {item} (color: {color})...")
                extracted_path = self.extract_furniture_item(png_image_path, item, query_number)
                if extracted_path:
                    extracted_images.append(extracted_path)
            
            # Create grayscale versions
            print(f"\n🔄 Creating grayscale versions...")
            grayscale_images = self.process_generated_images_to_grayscale(query_number)
            
            return extracted_images, items, colors
            
        except Exception as e:
            print(f"❌ Error processing all furniture: {e}")
            return [], [], []

def main():
    """Main function to automatically process queries that need extraction."""
    print("🎨 GPT Furniture Extractor - Master Query Log Integration")
    print("=" * 60)
    
    # Initialize
    extractor = GPTFurnitureExtractor()
    
    if not extractor.is_available():
        print("❌ GPT furniture extractor not available. Please check API key.")
        return
    
    if not PIL_AVAILABLE:
        print("❌ PIL not available. Please install Pillow.")
        return
    
    if not OPENCV_AVAILABLE:
        print("❌ OpenCV not available. Please install opencv-python.")
        return
    
    # Check master query log for queries that need extraction
    query_number = extractor.check_master_query_log()
    
    if query_number is None:
        print("✅ No queries pending extraction")
        return
    
    # Find the designed room image for this query
    designed_room_image = extractor.find_designed_room_image(query_number)
    
    if designed_room_image is None:
        print(f"❌ No designed room image found for query {query_number}")
        return
    
    print(f"🔄 Processing query {query_number} with image: {os.path.basename(designed_room_image)}")
    
    # Process all furniture items
    extracted_images, detected_items, detected_colors = extractor.process_all_furniture(designed_room_image, query_number)
    
    if extracted_images:
        # Update extraction status to "yes"
        extractor.update_extraction_status(query_number, "yes")
        
        print(f"\n🎉 SUCCESS!")
        print(f"📊 Processed {len(detected_items)} furniture items:")
        for i, item in enumerate(detected_items):
            color = detected_colors[i] if i < len(detected_colors) else "unknown"
            print(f"   • {item} ({color})")
        
        print(f"📁 Extracted images saved to: querries/query_{query_number}/generated_images/generated_furniture/")
        print(f"📁 Grayscale images saved to: querries/query_{query_number}/generated_images/generated_furniture_gray/")
        print(f"✅ Extraction status updated to 'yes' for query {query_number}")
        
    else:
        print(f"❌ Failed to extract furniture items for query {query_number}")
        extractor.update_extraction_status(query_number, "no")

if __name__ == "__main__":
    main()
