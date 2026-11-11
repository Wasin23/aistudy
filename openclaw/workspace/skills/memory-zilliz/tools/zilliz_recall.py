#!/usr/bin/env python3
"""
Search vector memory for relevant context
"""
import os
import sys
import json
from pathlib import Path
from pymilvus import MilvusClient
from openai import OpenAI

# Load .env from workspace root
try:
    from dotenv import load_dotenv
    workspace_root = Path(__file__).parent.parent.parent.parent
    env_path = workspace_root / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, rely on system env vars

def memory_search(query: str, limit: int = 5) -> dict:
    """
    Search Zilliz for relevant memories
    
    Args:
        query: Search query (natural language)
        limit: Maximum results to return
        
    Returns:
        List of relevant memory chunks with metadata
    """
    try:
        # Initialize clients
        zilliz_endpoint = os.environ.get("ZILLIZ_ENDPOINT")
        zilliz_token = os.environ.get("ZILLIZ_TOKEN")
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        if not all([zilliz_endpoint, zilliz_token, openai_key]):
            return {
                "error": "Missing credentials",
                "message": "Set ZILLIZ_ENDPOINT, ZILLIZ_TOKEN, and OPENAI_API_KEY"
            }
        
        # Connect to Zilliz
        client = MilvusClient(
            uri=zilliz_endpoint,
            token=zilliz_token
        )
        
        # Generate query embedding
        openai_client = OpenAI(api_key=openai_key)
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_vector = embedding_response.data[0].embedding
        
        # Search collection
        collection_name = "openclaw_memory"
        
        # Check if collection exists
        collections = client.list_collections()
        if collection_name not in collections:
            return {
                "results": [],
                "message": f"Collection '{collection_name}' doesn't exist yet. Use ingest script to create it."
            }
        
        # Perform vector search
        results = client.search(
            collection_name=collection_name,
            data=[query_vector],
            limit=limit,
            output_fields=["content", "category", "importance", "timestamp", "user"]
        )
        
        # Format results
        memories = []
        for hits in results:
            for hit in hits:
                memories.append({
                    "content": hit["entity"].get("content", ""),
                    "category": hit["entity"].get("category", "unknown"),
                    "importance": hit["entity"].get("importance", 1),
                    "timestamp": hit["entity"].get("timestamp", ""),
                    "user": hit["entity"].get("user", ""),
                    "score": hit["distance"]
                })
        
        return {
            "results": memories,
            "count": len(memories),
            "query": query
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

if __name__ == "__main__":
    # CLI usage
    if len(sys.argv) < 2:
        print("Usage: memory_search.py <query> [limit]")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    result = memory_search(query, limit)
    print(json.dumps(result, indent=2))
