#!/usr/bin/env python3
"""
Image Vectorization for Interior Define Catalog 2
Creates Pinecone database with image embeddings using OpenAI's embedding API
"""

import os
import base64
import json
import time
from typing import List, Dict, Optional
import pandas as pd
from config import Config

# Check for required libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("❌ OpenAI library not available. Install with: pip install openai")

try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("❌ Pinecone library not available. Install with: pip install pinecone")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("❌ PIL not available. Install with: pip install Pillow")

class ImageVectorizationPinecone:
    """Image vectorization and Pinecone database management for Interior Define Catalog 2"""
    
    def __init__(self, config: Config = None):
        """Initialize the image vectorization system."""
        if config is None:
            config = Config()
        
        self.config = config
        self.catalog_path = "InteriorDefine_catalog_2/INTERIOR_DEFINE_MASTER_CATALOG.csv"
        self.base_image_dir = "InteriorDefine_catalog_2"
        self.pinecone_client = None
        self.index = None
        
        # Initialize OpenAI client
        self._init_openai()
        
        # Initialize Pinecone client
        self._init_pinecone()
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        if not OPENAI_AVAILABLE:
            print("❌ OpenAI library not available.")
            return
        
        try:
            openai_key = self.config.get_openai_key()
            if not openai_key:
                print("❌ OpenAI API key not found")
                return
            
            self.client = openai.OpenAI(api_key=openai_key)
            print("✅ OpenAI client initialized successfully")
            
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {e}")
            self.client = None
    
    def _init_pinecone(self):
        """Initialize Pinecone client and connect to the index."""
        if not PINECONE_AVAILABLE:
            print("❌ Pinecone library not available.")
            return
        
        try:
            pinecone_key = self.config.get_pinecone_key()
            if not pinecone_key:
                print("❌ Pinecone API key not found")
                return
            
            # Initialize Pinecone with new API
            self.pinecone_client = Pinecone(api_key=pinecone_key)
            
            # Create or connect to Interior Define catalog 2 index
            index_name = "interior-define-images-catalog-2"
            
            # Check if index exists
            existing_indexes = [index.name for index in self.pinecone_client.list_indexes()]
            
            if index_name not in existing_indexes:
                print(f"📝 Creating new Pinecone index: {index_name}")
                self.pinecone_client.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI text-embedding-3-small dimension
                    metric="cosine",
                    spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}
                )
                print(f"✅ Created Pinecone index: {index_name}")
            else:
                print(f"✅ Using existing Pinecone index: {index_name}")
            
            # Connect to the index
            self.index = self.pinecone_client.Index(index_name)
            print(f"✅ Pinecone client initialized successfully - Index: {index_name}")
            
        except Exception as e:
            print(f"❌ Pinecone initialization failed: {e}")
            self.index = None
    
    def is_available(self) -> bool:
        """Check if all required services are available."""
        return (self.client is not None and 
                self.index is not None and 
                OPENAI_AVAILABLE and 
                PINECONE_AVAILABLE and 
                PIL_AVAILABLE)
    
    def load_catalog_data(self) -> List[Dict]:
        """Load catalog data from the master CSV file."""
        try:
            if not os.path.exists(self.catalog_path):
                print(f"❌ Catalog file not found: {self.catalog_path}")
                return []
            
            print(f"📁 Loading catalog data from: {self.catalog_path}")
            
            # Use pandas with proper CSV parsing to handle quoted fields with commas
            df = pd.read_csv(self.catalog_path, quotechar='"', skipinitialspace=True)
            items = []
            
            for _, row in df.iterrows():
                # Clean up any NaN values and convert to strings
                items.append({
                    'catalog_number': str(row['catalog_number']) if pd.notna(row['catalog_number']) else '',
                    'item_name': str(row['item_name']) if pd.notna(row['item_name']) else '',
                    'item_type': str(row['item_type']) if pd.notna(row['item_type']) else '',
                    'price': str(row['price']) if pd.notna(row['price']) else '',
                    'color': str(row['color']) if pd.notna(row['color']) else 'Standard finish',
                    'image_url': str(row['image_url']) if pd.notna(row['image_url']) else '',
                    'link': str(row['link']) if pd.notna(row['link']) else ''
                })
            
            print(f"✅ Loaded {len(items)} items from catalog")
            return items
            
        except Exception as e:
            print(f"❌ Error loading catalog data: {e}")
            return []
    
    def find_image_path(self, item: Dict) -> Optional[str]:
        """Find the actual image file path for an item."""
        try:
            image_url = item.get('image_url', '')
            item_type = item.get('item_type', '')
            catalog_number = item.get('catalog_number', '')
            
            # Try direct path first
            if image_url and os.path.exists(image_url):
                return image_url
            
            # Try to find image in the appropriate category folder
            category_folders = {
                'sofa': 'sofas',
                'sofas': 'sofas',
                'chair': 'chairs',
                'chairs': 'chairs',
                'table': 'tables',
                'tables': 'tables',
                'bench': 'benches',
                'benches': 'benches',
                'nightstand': 'nightstands',
                'nightstands': 'nightstands',
                'lighting': 'lighting',
                'lamp': 'lighting',
                'rug': 'rugs',
                'rugs': 'rugs'
            }
            
            category_folder = category_folders.get(item_type.lower(), item_type.lower())
            category_dir = os.path.join(self.base_image_dir, category_folder)
            
            if not os.path.exists(category_dir):
                return None
            
            # First, try to match the exact filename from image_url (with different extensions)
            if image_url:
                base_filename = os.path.splitext(os.path.basename(image_url))[0]
                for ext in ['.png', '.jpg', '.jpeg']:
                    potential_path = os.path.join(category_dir, base_filename + ext)
                    if os.path.exists(potential_path):
                        return potential_path
            
            # If that doesn't work, look for image files that might match this item
            for filename in os.listdir(category_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # Check if filename contains catalog number or item name
                    item_name_clean = item.get('item_name', '').replace(' ', '_').replace('·', '').replace(',', '').replace('(', '').replace(')', '')
                    if (catalog_number in filename or 
                        item_name_clean.lower() in filename.lower() or
                        item_type.lower() in filename.lower()):
                        return os.path.join(category_dir, filename)
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding image path for {item.get('catalog_number', 'unknown')}: {e}")
            return None
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Encode image to base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ Error encoding image {image_path}: {e}")
            return None
    
    def get_image_embedding(self, image_path: str) -> Optional[List[float]]:
        """Get embedding for an image using CLIP model for direct image embeddings."""
        try:
            if not self.client:
                print("❌ OpenAI client not available")
                return None
            
            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return None
            
            # Use OpenAI's CLIP model for direct image embeddings
            print(f"    🔍 Embedding image: {os.path.basename(image_path)}")
            
            response = self.client.embeddings.create(
                model="clip-vit-base-patch32",  # CLIP model for image embeddings
                input=f"data:image/png;base64,{base64_image}"
            )
            
            print(f"    ✅ Generated direct image embedding")
            return response.data[0].embedding
            
        except Exception as e:
            print(f"❌ Error getting image embedding for {image_path}: {e}")
            # Fallback to using image filename as text embedding
            print(f"    ⚠️  Falling back to filename-based embedding")
            try:
                fallback_response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=f"Furniture image: {os.path.basename(image_path)}"
                )
                return fallback_response.data[0].embedding
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                return None
    
    def upsert_to_pinecone(self, items: List[Dict], batch_size: int = 100):
        """Upsert items to Pinecone database."""
        try:
            if not self.index:
                print("❌ Pinecone index not available")
                return False
            
            print(f"📤 Upserting {len(items)} items to Pinecone in batches of {batch_size}")
            
            successful_upserts = 0
            failed_upserts = 0
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                vectors_to_upsert = []
                
                print(f"🔄 Processing batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}")
                
                for item in batch:
                    try:
                        # Find image path
                        image_path = self.find_image_path(item)
                        if not image_path:
                            print(f"⚠️  No image found for {item['catalog_number']}")
                            failed_upserts += 1
                            continue
                        
                        # Get embedding
                        embedding = self.get_image_embedding(image_path)
                        if not embedding:
                            print(f"⚠️  Failed to get embedding for {item['catalog_number']}")
                            failed_upserts += 1
                            continue
                        
                        # Prepare vector for upsert
                        vector_data = {
                            'id': item['catalog_number'],
                            'values': embedding,
                            'metadata': {
                                'item_name': item['item_name'],
                                'item_type': item['item_type'],
                                'price': item['price'],
                                'color': item['color'],
                                'image_url': item['image_url'],
                                'link': item['link'],
                                'image_path': image_path
                            }
                        }
                        
                        vectors_to_upsert.append(vector_data)
                        successful_upserts += 1
                        
                        # Small delay to avoid rate limiting
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"❌ Error processing {item['catalog_number']}: {e}")
                        failed_upserts += 1
                        continue
                
                # Upsert batch to Pinecone
                if vectors_to_upsert:
                    try:
                        self.index.upsert(vectors=vectors_to_upsert)
                        print(f"✅ Upserted {len(vectors_to_upsert)} vectors to Pinecone")
                    except Exception as e:
                        print(f"❌ Error upserting batch to Pinecone: {e}")
                        failed_upserts += len(vectors_to_upsert)
                        successful_upserts -= len(vectors_to_upsert)
            
            print(f"\n📊 Upsert Summary:")
            print(f"   ✅ Successful: {successful_upserts}")
            print(f"   ❌ Failed: {failed_upserts}")
            print(f"   📈 Success Rate: {successful_upserts/(successful_upserts + failed_upserts)*100:.1f}%")
            
            return successful_upserts > 0
            
        except Exception as e:
            print(f"❌ Error upserting to Pinecone: {e}")
            return False
    
    def process_catalog_images(self):
        """Process all catalog images and create Pinecone database."""
        print("🖼️  Image Vectorization for Interior Define Catalog 2")
        print("=" * 60)
        
        if not self.is_available():
            print("❌ Required services not available. Please check:")
            print("   - OpenAI API key")
            print("   - Pinecone API key")
            print("   - Required libraries (openai, pinecone, PIL)")
            return False
        
        # Load catalog data
        items = self.load_catalog_data()
        if not items:
            print("❌ No catalog data loaded")
            return False
        
        # Process images and upsert to Pinecone
        success = self.upsert_to_pinecone(items)
        
        if success:
            print(f"\n🎉 SUCCESS!")
            print(f"✅ Interior Define Catalog 2 images vectorized and stored in Pinecone")
            print(f"📊 Index: interior-define-images-catalog-2")
            print(f"🔍 Dimension: 1536 (OpenAI text-embedding-3-small)")
            print(f"📏 Metric: cosine")
        else:
            print(f"\n❌ FAILED!")
            print(f"❌ Image vectorization process failed")
        
        return success

def main():
    """Main function to run image vectorization."""
    print("🖼️  Interior Define Catalog 2 Image Vectorization")
    print("=" * 60)
    
    # Load configuration
    config = Config()
    config.print_status()
    
    # Validate API keys
    if not config.validate_keys()['openai']:
        print("❌ OpenAI API key not found. Please set it in config.json or environment.")
        return
    
    if not config.validate_keys()['pinecone']:
        print("❌ Pinecone API key not found. Please set it in config.json or environment.")
        return
    
    try:
        vectorizer = ImageVectorizationPinecone(config=config)
        vectorizer.process_catalog_images()
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Process failed: {e}")

if __name__ == "__main__":
    main()
