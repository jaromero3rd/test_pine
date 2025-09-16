#!/usr/bin/env python3
"""
Test script for Pinecone Vector Database Integration

This script demonstrates how to use the Pinecone integration
with sample data and search queries.
"""

import os
import sys
from pinecone_vector_database import PineconeVectorDatabase


def test_pinecone_integration():
    """Test the Pinecone integration with sample data."""
    
    # You'll need to provide your own API keys
    openai_api_key = os.getenv('OPENAI_API_KEY', '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')
    
    # You'll need to get a Pinecone API key from https://www.pinecone.io/
    pinecone_api_key = os.getenv('PINECONE_API_KEY', 'your-pinecone-api-key-here')
    
    if pinecone_api_key == 'your-pinecone-api-key-here':
        print("❌ Please set your Pinecone API key:")
        print("   1. Go to https://www.pinecone.io/")
        print("   2. Create an account and get your API key")
        print("   3. Set environment variable: export PINECONE_API_KEY='your-key'")
        print("   4. Or modify this script with your key")
        return
    
    print("🧪 Testing Pinecone Vector Database Integration")
    print("=" * 50)
    
    try:
        # Initialize database
        db = PineconeVectorDatabase(
            openai_api_key=openai_api_key,
            pinecone_api_key=pinecone_api_key
        )
        print("✅ Database initialized successfully")
        
        # Test embedding generation
        print("\n🔄 Testing embedding generation...")
        test_text = "Modern leather sofa with tufted backrest"
        embedding = db.generate_embedding(test_text)
        
        if embedding:
            print(f"✅ Embedding generated (dimension: {len(embedding)})")
        else:
            print("❌ Failed to generate embedding")
            return
        
        # Test index creation
        print("\n🏗️  Testing index creation...")
        if db.create_index(force_recreate=True):
            print("✅ Index created successfully")
        else:
            print("❌ Failed to create index")
            return
        
        # Test with sample catalog data
        print("\n📚 Testing with sample catalog data...")
        sample_items = [
            {
                'catalog_number': 'TEST-001',
                'item_name': 'Modern Leather Sofa',
                'item_type': 'sofa',
                'master_description': 'Item_type: sofa, Style_of_furniture: contemporary, Material: leather, Color: brown, Dimensions: W: 90", H: 38", D: 39", Description: A luxurious leather sofa with tufted backrest and modern design.'
            },
            {
                'catalog_number': 'TEST-002',
                'item_name': 'Traditional Wooden Bed',
                'item_type': 'bed',
                'master_description': 'Item_type: bed, Style_of_furniture: traditional, Material: solid wood, Color: oak, Dimensions: W: 80", H: 60", D: 87", Description: A classic wooden bed frame with headboard and footboard.'
            }
        ]
        
        # Prepare vector data
        vector_data = db.prepare_vector_data(sample_items)
        
        if vector_data:
            print(f"✅ Prepared {len(vector_data)} vectors")
            
            # Upload vectors
            if db.upload_vectors(vector_data):
                print("✅ Vectors uploaded successfully")
                
                # Test search
                print("\n🔍 Testing similarity search...")
                search_queries = [
                    "comfortable leather seating",
                    "wooden bedroom furniture",
                    "modern contemporary design"
                ]
                
                for query in search_queries:
                    print(f"\n   Query: '{query}'")
                    results = db.search_similar_items(query, top_k=2)
                    
                    if results:
                        for i, item in enumerate(results, 1):
                            print(f"      {i}. {item['item_name']} (score: {item['similarity_score']:.3f})")
                    else:
                        print("      No results found")
                
                # Show stats
                print("\n📊 Index Statistics:")
                stats = db.get_index_stats()
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                
            else:
                print("❌ Failed to upload vectors")
        else:
            print("❌ Failed to prepare vector data")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_pinecone_integration()
