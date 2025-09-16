#!/usr/bin/env python3
"""
Demo script for Pinecone Vector Database Integration

This script demonstrates how to use the Pinecone integration
with the actual Havertys Master Catalog.
"""

import os
import sys
from pinecone_vector_database import PineconeVectorDatabase


def demo_with_real_catalog():
    """Demo the Pinecone integration with the real master catalog."""
    
    # Use the provided OpenAI API key
    openai_api_key = "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"
    
    # You'll need to get a Pinecone API key from https://www.pinecone.io/
    pinecone_api_key = os.getenv('PINECONE_API_KEY', 'your-pinecone-api-key-here')
    
    if pinecone_api_key == 'your-pinecone-api-key-here':
        print("❌ Please set your Pinecone API key:")
        print("   1. Go to https://www.pinecone.io/")
        print("   2. Create an account and get your API key")
        print("   3. Set environment variable: export PINECONE_API_KEY='your-key'")
        print("   4. Or modify this script with your key")
        return
    
    print("🎯 Demo: Pinecone Vector Database Integration with Real Catalog")
    print("=" * 70)
    
    try:
        # Initialize database
        db = PineconeVectorDatabase(
            openai_api_key=openai_api_key,
            pinecone_api_key=pinecone_api_key
        )
        print("✅ Database initialized successfully")
        
        # Create index
        print("\n🏗️  Creating Pinecone index...")
        if not db.create_index(force_recreate=True):
            print("❌ Failed to create index")
            return
        
        # Load real master catalog
        print("\n📚 Loading Havertys Master Catalog...")
        catalog_items = db.load_master_catalog("Catalog/HAVERTYS_MASTER_CATALOG.csv")
        
        if not catalog_items:
            print("❌ No catalog items loaded")
            return
        
        print(f"✅ Loaded {len(catalog_items)} items from master catalog")
        
        # Show sample items
        print("\n📋 Sample catalog items:")
        for i, item in enumerate(catalog_items[:3], 1):
            print(f"   {i}. {item['item_name']} ({item['item_type']})")
            print(f"      Catalog: {item['catalog_number']}")
            print(f"      Description: {item['master_description'][:100]}...")
            print()
        
        # Prepare and upload vectors
        print("🔄 Preparing vector data...")
        vector_data = db.prepare_vector_data(catalog_items)
        
        if vector_data:
            print(f"✅ Prepared {len(vector_data)} vectors")
            
            # Upload vectors
            print("\n📤 Uploading vectors to Pinecone...")
            if db.upload_vectors(vector_data):
                print("✅ Vectors uploaded successfully!")
                
                # Show statistics
                print("\n📊 Index Statistics:")
                stats = db.get_index_stats()
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                
                # Test various search queries
                print("\n🔍 Testing Semantic Search:")
                search_queries = [
                    "comfortable leather sofa for living room",
                    "wooden bed frame with headboard",
                    "modern contemporary furniture",
                    "storage furniture for bedroom",
                    "upholstered seating with arms"
                ]
                
                for query in search_queries:
                    print(f"\n   🔎 Query: '{query}'")
                    results = db.search_similar_items(query, top_k=3)
                    
                    if results:
                        for i, item in enumerate(results, 1):
                            print(f"      {i}. {item['item_name']} ({item['item_type']})")
                            print(f"         Similarity: {item['similarity_score']:.3f}")
                            print(f"         Catalog: {item['catalog_number']}")
                    else:
                        print("      No results found")
                
                print("\n🎉 Demo completed successfully!")
                print("\n💡 You can now use the Pinecone index for semantic search!")
                print("   Try queries like:")
                print("   - 'comfortable seating'")
                print("   - 'wooden furniture'")
                print("   - 'modern design'")
                print("   - 'bedroom storage'")
                
            else:
                print("❌ Failed to upload vectors")
        else:
            print("❌ Failed to prepare vector data")
            
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_with_real_catalog()
