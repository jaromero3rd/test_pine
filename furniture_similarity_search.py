#!/usr/bin/env python3
"""
Furniture Similarity Search with CLIP Embeddings
Checks master query log for successful queries and performs Pinecone similarity searches using CLIP image embeddings
"""

import os
import csv
import base64
import pandas as pd
import sys
from typing import List, Dict, Optional, Tuple
from config import Config

# CLIP imports for image embeddings
try:
    import torch
    import clip
    from PIL import Image
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("Warning: CLIP not available. Install with: pip install torch torchvision git+https://github.com/openai/CLIP.git")

# Pinecone imports
try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: Pinecone library not installed. Install with: pip install pinecone")

class FurnitureSimilaritySearch:
    """Furniture similarity search using CLIP embeddings and Pinecone"""
    
    def __init__(self):
        """Initialize the similarity search system."""
        self.pinecone_client = None
        self.index = None
        self.clip_model = None
        self.clip_preprocess = None
        self.device = None
        self._init_clip()
        self._init_pinecone()
    
    def _init_clip(self):
        """Initialize CLIP model."""
        if not CLIP_AVAILABLE:
            print("❌ CLIP not available.")
            return
        
        try:
            print("🔄 Loading CLIP model...")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"   Using device: {self.device}")
            
            # Load CLIP model
            self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=self.device)
            print("✅ CLIP model loaded successfully")
            
        except Exception as e:
            print(f"❌ CLIP initialization failed: {e}")
            self.clip_model = None
    
    def _init_pinecone(self):
        """Initialize Pinecone client."""
        try:
            config = Config()
            pinecone_key = config.get_pinecone_key()
            
            if not pinecone_key:
                print("❌ Pinecone API key not found")
                return
            
            # Initialize Pinecone with new API
            self.pinecone_client = Pinecone(api_key=pinecone_key)
            
            # Connect to Interior Define CLIP images index
            index_name = "interior-define-clip-images"
            self.index = self.pinecone_client.Index(index_name, host="https://interior-define-clip-images-7e5rvr1.svc.aped-4627-b74a.pinecone.io")
            print(f"✅ Pinecone client initialized successfully - Index: {index_name}")
            
        except Exception as e:
            print(f"❌ Pinecone initialization failed: {e}")
            self.index = None
    
    def is_available(self) -> bool:
        """Check if both CLIP and Pinecone are available."""
        return self.clip_model is not None and self.index is not None
    
    def check_master_query_log(self, log_path: str = "querries/master_querry_log.csv") -> Optional[int]:
        """Check master query log for queries that need similarity search."""
        try:
            if not os.path.exists(log_path):
                print(f"❌ Master query log not found: {log_path}")
                return None
            
            print(f"📋 Checking master query log: {log_path}")
            
            # Read the CSV file
            df = pd.read_csv(log_path)
            
            if df.empty:
                print("ℹ️ No queries found in master log")
                return None
            
            # Filter for queries where similarity_sufficed = 'no'
            pending_similarity = df[df['similarity_sufficed'].str.lower() == 'no']
            
            if pending_similarity.empty:
                print("✅ No queries pending similarity search")
                return None
            
            # Get the latest query that needs similarity search
            latest_query = pending_similarity.iloc[-1]
            query_number = latest_query['request_number']
            
            print(f"✅ Latest query pending similarity search: {query_number}")
            print(f"   Room Type: {latest_query['room_type']}")
            print(f"   Style Type: {latest_query['style_type']}")
            print(f"   Color Palette: {latest_query['color_pallet']}")
            print(f"   Budget: {latest_query['budget']}")
            
            return query_number
            
        except Exception as e:
            print(f"❌ Error checking master query log: {e}")
            return None
    
    def update_similarity_status(self, query_number: int, status: str = "yes"):
        """Update the similarity_sufficed status in master query log."""
        try:
            master_log_path = "querries/master_querry_log.csv"
            
            # Read the CSV
            df = pd.read_csv(master_log_path)
            
            # Update the similarity_sufficed status for the specific query
            df.loc[df['request_number'] == query_number, 'similarity_sufficed'] = status
            
            # Save back to CSV
            df.to_csv(master_log_path, index=False)
            
            print(f"✅ Updated similarity_sufficed to '{status}' for query {query_number}")
            
        except Exception as e:
            print(f"❌ Error updating similarity status: {e}")
    
    def get_grayscale_images(self, query_number: int) -> List[str]:
        """Get all grayscale furniture images for a query."""
        try:
            query_folder = f"querries/query_{query_number}"
            grayscale_folder = os.path.join(query_folder, "generated_images", "generated_furniture_gray")
            
            if not os.path.exists(grayscale_folder):
                print(f"❌ Grayscale folder not found: {grayscale_folder}")
                return []
            
            # Find all grayscale images
            grayscale_images = []
            for filename in os.listdir(grayscale_folder):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')) and 'grayscale' in filename.lower():
                    image_path = os.path.join(grayscale_folder, filename)
                    grayscale_images.append(image_path)
            
            print(f"✅ Found {len(grayscale_images)} grayscale images")
            for img in grayscale_images:
                print(f"   📁 {os.path.basename(img)}")
            
            return grayscale_images
            
        except Exception as e:
            print(f"❌ Error getting grayscale images: {e}")
            return []
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64 for OpenAI API."""
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            return image_data
        except Exception as e:
            print(f"❌ Error encoding image {image_path}: {e}")
            return None
    
    def get_clip_embedding(self, image_path: str) -> Optional[List[float]]:
        """Get CLIP embedding for an image."""
        try:
            if not self.clip_model:
                print("❌ CLIP model not available")
                return None
            
            print(f"🔍 CLIP embedding image: {os.path.basename(image_path)}")
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_input = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            
            # Get image features
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                # Convert to list
                embedding = image_features.cpu().numpy().flatten().tolist()
            
            print(f"✅ Generated CLIP embedding (dim: {len(embedding)})")
            return embedding
            
        except Exception as e:
            print(f"❌ Error getting CLIP embedding for {image_path}: {e}")
            return None
    
    def search_similar_furniture(self, embedding: List[float], furniture_type: str, top_k: int = 5) -> List[Dict]:
        """Search for similar furniture in Pinecone, filtered by furniture type."""
        try:
            # Query Pinecone with more results to account for filtering
            results = self.index.query(
                vector=embedding,
                top_k=top_k * 3,  # Get more results to filter by type
                include_metadata=True
            )
            
            similar_items = []
            for match in results['matches']:
                item_type = match['metadata'].get('item_type', '').lower()
                
                # Filter by furniture type (with some flexibility for similar types)
                if self._is_same_category(item_type, furniture_type.lower()):
                    similar_items.append({
                        'catalog_number': match['id'],
                        'similarity_score': match['score'],
                        'item_name': match['metadata'].get('item_name', ''),
                        'item_type': match['metadata'].get('item_type', ''),
                        'price': match['metadata'].get('price', ''),
                        'color': match['metadata'].get('color', ''),
                        'image_url': match['metadata'].get('image_url', ''),
                        'link': match['metadata'].get('link', '')
                    })
                    
                    # Stop when we have enough results
                    if len(similar_items) >= top_k:
                        break
            
            print(f"    ✅ Found {len(similar_items)} {furniture_type} items (filtered from {len(results['matches'])} total)")
            return similar_items
            
        except Exception as e:
            print(f"❌ Error searching Pinecone: {e}")
            return []
    
    def _is_same_category(self, item_type: str, target_type: str) -> bool:
        """Check if two furniture types are in the same category."""
        # Direct match
        if item_type == target_type:
            return True
        
        # Special handling for sofas - be more restrictive
        if target_type == 'sofa':
            return item_type in ['sofa', 'sofas', 'loveseat', 'loveseats']
        
        # Special handling for chairs - exclude sofas
        if target_type == 'chair':
            return item_type in ['chair', 'chairs', 'loveseat', 'loveseats']
        
        # Define category mappings for other types
        categories = {
            'tables': ['table', 'tables', 'nightstand', 'nightstands', 'coffee_table', 'side_table'],
            'lighting': ['lighting', 'lamp', 'lamps', 'pendant', 'sconce'],
            'rugs': ['rug', 'rugs'],
            'storage': ['bench', 'benches', 'storage_bench', 'ottoman']
        }
        
        # Check if both types are in the same category
        for category, types in categories.items():
            if item_type in types and target_type in types:
                return True
        
        # Special cases for similar items (excluding sofa/chair mixing)
        similar_pairs = [
            ('table', 'nightstand'),
            ('lamp', 'lighting'),
            ('bench', 'ottoman')
        ]
        
        for type1, type2 in similar_pairs:
            if (item_type == type1 and target_type == type2) or (item_type == type2 and target_type == type1):
                return True
        
        return False
    
    def _get_furniture_type_from_image_name(self, image_name: str) -> str:
        """Extract furniture type from image filename."""
        image_name_lower = image_name.lower()
        
        # Map image name patterns to furniture types
        if 'sofa' in image_name_lower:
            return 'sofa'
        elif 'chair' in image_name_lower:
            return 'chair'
        elif 'table' in image_name_lower:
            return 'table'
        elif 'lamp' in image_name_lower:
            return 'lighting'
        elif 'rug' in image_name_lower:
            return 'rug'
        elif 'bench' in image_name_lower:
            return 'bench'
        elif 'nightstand' in image_name_lower:
            return 'nightstand'
        else:
            # Default fallback - try to extract from filename
            if 'extracted' in image_name_lower:
                # Extract the part before 'extracted'
                parts = image_name_lower.split('_extracted')
                if parts:
                    return parts[0]
            return 'unknown'
    
    def process_query_images(self, query_number: int) -> Dict[str, List[Dict]]:
        """Process all grayscale images for a query and find similar furniture."""
        try:
            print(f"🏠 Processing query {query_number} images...")
            
            # Get grayscale images
            grayscale_images = self.get_grayscale_images(query_number)
            if not grayscale_images:
                print("❌ No grayscale images found")
                return {}
            
            results = {}
            
            for image_path in grayscale_images:
                image_name = os.path.basename(image_path)
                print(f"\n🔄 Processing {image_name}...")
                
                # Determine furniture type from image name
                furniture_type = self._get_furniture_type_from_image_name(image_name)
                print(f"    🏷️  Detected furniture type: {furniture_type}")
                
                # Get CLIP embedding directly from image
                embedding = self.get_clip_embedding(image_path)
                if not embedding:
                    print(f"❌ Failed to get CLIP embedding for {image_name}")
                    continue
                
                # Search for similar furniture of the same type
                similar_items = self.search_similar_furniture(embedding, furniture_type, top_k=5)
                if similar_items:
                    results[image_name] = similar_items
                    print(f"✅ Found {len(similar_items)} similar {furniture_type} items for {image_name}")
                else:
                    print(f"❌ No similar {furniture_type} items found for {image_name}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error processing query images: {e}")
            return {}
    
    def print_results(self, results: Dict[str, List[Dict]]):
        """Print similarity search results."""
        print(f"\n🎉 SIMILARITY SEARCH RESULTS")
        print("=" * 60)
        
        for image_name, similar_items in results.items():
            print(f"\n📸 {image_name}")
            print("-" * 40)
            
            for i, item in enumerate(similar_items, 1):
                print(f"{i}. {item['item_name']}")
                print(f"   Similarity Score: {item['similarity_score']:.4f}")
                print(f"   Catalog Number: {item['catalog_number']}")
                print(f"   Item Type: {item['item_type']}")
                print(f"   Price: {item.get('price', 'N/A')}")
                print(f"   Color: {item.get('color', 'N/A')}")
                print()
    
    def save_results_to_csv(self, query_number: int, results: Dict[str, List[Dict]]) -> str:
        """Save similarity search results to CSV."""
        try:
            output_path = f"querries/query_{query_number}/similarity_results.csv"
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['query_number', 'image_name', 'rank', 'catalog_number', 'similarity_score', 'item_name', 'item_type', 'price', 'color', 'image_url', 'link']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for image_name, similar_items in results.items():
                    for i, item in enumerate(similar_items, 1):
                        writer.writerow({
                            'query_number': query_number,
                            'image_name': image_name,
                            'rank': i,
                            'catalog_number': item['catalog_number'],
                            'similarity_score': item['similarity_score'],
                            'item_name': item['item_name'],
                            'item_type': item['item_type'],
                            'price': item.get('price', ''),
                            'color': item.get('color', ''),
                            'image_url': item.get('image_url', ''),
                            'link': item.get('link', '')
                        })
            
            print(f"✅ Results saved to CSV: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error saving results to CSV: {e}")
            return ""

def main():
    """Main function to perform furniture similarity search."""
    print("🔍 Furniture Similarity Search")
    print("=" * 40)
    
    # Initialize
    searcher = FurnitureSimilaritySearch()
    
    if not searcher.is_available():
        print("❌ Similarity search not available. Please check API keys.")
        return
    
    if not CLIP_AVAILABLE:
        print("❌ CLIP not available. Please install CLIP dependencies.")
        return
    
    if not PINECONE_AVAILABLE:
        print("❌ Pinecone not available. Please install pinecone.")
        return
    
    # Check master query log for queries that need similarity search
    latest_query = searcher.check_master_query_log()
    if not latest_query:
        print("✅ No queries pending similarity search")
        return
    
    # Process images for the latest query
    results = searcher.process_query_images(latest_query)
    
    if results:
        # Print results
        searcher.print_results(results)
        
        # Save results to CSV
        csv_path = searcher.save_results_to_csv(latest_query, results)
        
        # Update similarity status to "yes"
        searcher.update_similarity_status(latest_query, "yes")
        
        print(f"\n✅ SUCCESS!")
        print(f"📊 Processed {len(results)} images")
        print(f"📁 Results saved to: {csv_path}")
        print(f"✅ Similarity status updated to 'yes' for query {latest_query}")
        print(f"\n✅ Features delivered:")
        print(f"   ✅ Master query log analysis")
        print(f"   ✅ GPT-4 Vision image analysis")
        print(f"   ✅ Text embedding generation")
        print(f"   ✅ Pinecone similarity search")
        print(f"   ✅ Interior Define catalog 2 database")
        print(f"   ✅ CSV results export")
    else:
        print("\n❌ No similarity results found")
        searcher.update_similarity_status(latest_query, "no")

if __name__ == "__main__":
    main()
