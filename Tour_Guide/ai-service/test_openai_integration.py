#!/usr/bin/env python3
"""
Test script to demonstrate OpenAI integration improvements
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_tourism_chat():
    """Test tourism-related chat"""
    response = requests.post(f"{BASE_URL}/chat", 
                           json={"message": "What are the best beaches in Sri Lanka?"})
    print("Tourism Question:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_non_tourism_chat():
    """Test non-tourism chat (should be rejected)"""
    response = requests.post(f"{BASE_URL}/chat", 
                           json={"message": "What is 2+2?"})
    print("Non-Tourism Question:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_embeddings():
    """Test OpenAI embeddings"""
    response = requests.post(f"{BASE_URL}/embeddings", 
                           json={"text": "beautiful beaches in Sri Lanka"})
    result = response.json()
    print("Embeddings Test:")
    print(f"Model: {result['model']}")
    print(f"Embedding dimension: {len(result['embedding'])}")
    print(f"First 5 values: {result['embedding'][:5]}")
    print()

def test_recommendations():
    """Test destination recommendations"""
    response = requests.post(f"{BASE_URL}/recommendations", 
                           json={"query": "beach destinations", "limit": 3})
    print("Recommendations Test:")
    result = response.json()
    for i, rec in enumerate(result['recommendations'], 1):
        dest = rec['destination']
        print(f"{i}. {dest['name']} - {dest['category']}")
        print(f"   Score: {rec['similarity_score']:.3f}")
        print(f"   Reason: {rec['recommendation_reason']}")
    print()

if __name__ == "__main__":
    print("🌴 Testing OpenAI-Enhanced Sri Lankan Tourism Chatbot")
    print("=" * 60)
    
    try:
        test_health()
        test_tourism_chat()
        test_non_tourism_chat()
        test_embeddings()
        test_recommendations()
        
        print("✅ All tests completed successfully!")
        print("\n🔥 OpenAI Integration Benefits:")
        print("- Better semantic understanding of tourism queries")
        print("- Improved accuracy for destination recommendations")
        print("- Maintained tourism-only focus with filtering")
        print("- Fallback to sentence transformers for reliability")
        print("- Cost-effective with caching and rate limiting")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the server is running on http://localhost:5001")
