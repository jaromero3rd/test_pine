#!/usr/bin/env python3
"""
Example: How to use Pinecone Vector Database programmatically

This script shows how to integrate Pinecone search into your own applications.
"""

import os
from pinecone_vector_database import PineconeVectorDatabase


def example_usage():
    """Example of how to use the Pinecone integration in your own code."""
    
    # Initialize with your API keys
    openai_api_key = "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"
    pinecone_api_key = os.getenv('PINECONE_API_KEY', 'your-pinecone-api-key')
    
    if pinecone_api_key == 'your-pinecone-api-key':
        print("Please set your Pinecone API key first!")
        return
    
    # Create database instance
    db = PineconeVectorDatabase(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key
    )
    
    # Example 1: Search for furniture by style
    print("🔍 Example 1: Search by style")
    results = db.search_similar_items("modern contemporary furniture", top_k=5)
    
    print("Modern furniture found:")
    for item in results:
        print(f"  - {item['item_name']} ({item['item_type']}) - Score: {item['similarity_score']:.3f}")
    
    # Example 2: Search for furniture by material
    print("\n🔍 Example 2: Search by material")
    results = db.search_similar_items("leather upholstered seating", top_k=3)
    
    print("Leather furniture found:")
    for item in results:
        print(f"  - {item['item_name']} ({item['item_type']}) - Score: {item['similarity_score']:.3f}")
    
    # Example 3: Search for furniture by function
    print("\n🔍 Example 3: Search by function")
    results = db.search_similar_items("bedroom storage furniture", top_k=4)
    
    print("Storage furniture found:")
    for item in results:
        print(f"  - {item['item_name']} ({item['item_type']}) - Score: {item['similarity_score']:.3f}")
    
    # Example 4: Search for furniture by size
    print("\n🔍 Example 4: Search by size")
    results = db.search_similar_items("large comfortable seating", top_k=3)
    
    print("Large seating found:")
    for item in results:
        print(f"  - {item['item_name']} ({item['item_type']}) - Score: {item['similarity_score']:.3f}")
    
    # Example 5: Get index statistics
    print("\n📊 Example 5: Index statistics")
    stats = db.get_index_stats()
    print(f"Total vectors: {stats.get('total_vector_count', 'Unknown')}")
    print(f"Dimension: {stats.get('dimension', 'Unknown')}")
    print(f"Index fullness: {stats.get('index_fullness', 'Unknown')}")


def example_recommendation_system():
    """Example of building a recommendation system."""
    
    openai_api_key = "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"
    pinecone_api_key = os.getenv('PINECONE_API_KEY', 'your-pinecone-api-key')
    
    if pinecone_api_key == 'your-pinecone-api-key':
        print("Please set your Pinecone API key first!")
        return
    
    db = PineconeVectorDatabase(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key
    )
    
    print("\n🎯 Example: Recommendation System")
    print("=" * 40)
    
    # Simulate a customer looking for bedroom furniture
    customer_preferences = [
        "modern bedroom furniture",
        "wooden bed frame",
        "storage solutions",
        "contemporary design"
    ]
    
    print("Customer preferences:")
    for pref in customer_preferences:
        print(f"  - {pref}")
    
    print("\nRecommended items:")
    
    # Get recommendations for each preference
    all_recommendations = {}
    
    for preference in customer_preferences:
        results = db.search_similar_items(preference, top_k=3)
        all_recommendations[preference] = results
    
    # Show top recommendations
    for preference, results in all_recommendations.items():
        print(f"\n  For '{preference}':")
        for item in results:
            print(f"    - {item['item_name']} ({item['item_type']}) - Score: {item['similarity_score']:.3f}")


if __name__ == "__main__":
    print("🚀 Pinecone Vector Database Usage Examples")
    print("=" * 50)
    
    # Run basic examples
    example_usage()
    
    # Run recommendation system example
    example_recommendation_system()
    
    print("\n✅ Examples completed!")
    print("\n💡 You can now integrate these patterns into your own applications!")
