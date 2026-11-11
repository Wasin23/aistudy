#!/usr/bin/env python3
"""
Test Zilliz memory search
"""
import os
import sys
import json

# Add tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../skills/memory-zilliz/tools'))
from memory_search import memory_search

def main():
    # Set up environment
    os.environ['ZILLIZ_ENDPOINT'] = 'https://in03-6c238263815f091.serverless.gcp-us-west1.cloud.zilliz.com'
    os.environ['ZILLIZ_TOKEN'] = '0dc117d66370e26d6e0f29ef4e58efdc9012e6d94286ee084e5447e4ac63b04562eb6eafbb8b761e789525553efe24d472f37214'
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Test queries
    test_queries = [
        "What is the user's name and background?",
        "What does Cole want to build?",
        "What is the personality of this assistant?",
        "Tell me about Zilliz and RAG plans"
    ]
    
    print("Testing Zilliz Memory Search\n" + "="*50)
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        result = memory_search(query, limit=3)
        
        if result.get('error'):
            print(f"   ✗ Error: {result['error']}")
        else:
            print(f"   Found {result['count']} results:")
            for i, mem in enumerate(result['results']):
                print(f"\n   [{i+1}] {mem['category'].upper()} (importance: {mem['importance']}, score: {mem['score']:.3f})")
                print(f"       {mem['content'][:150]}...")

if __name__ == "__main__":
    main()
