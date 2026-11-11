#!/usr/bin/env python3
"""
Write new memories to Zilliz
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
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

def memory_write(content: str, category: str = "general", importance: int = 1, user: str = "default") -> dict:
    """
    Store a new memory in Zilliz
    
    Args:
        content: The memory text to store
        category: Memory category (e.g., "user_info", "preferences", "facts")
        importance: 1-5 scale (5 = critical, always retrieve)
        user: User identifier for multi-tenant setups
        
    Returns:
        Confirmation with memory ID
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
        
        # Generate embedding
        openai_client = OpenAI(api_key=openai_key)
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        vector = embedding_response.data[0].embedding
        
        collection_name = "openclaw_memory"
        
        # Check if collection exists, create if not
        collections = client.list_collections()
        if collection_name not in collections:
            from pymilvus import DataType
            
            schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=True
            )
            
            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=1536)
            schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=10000)
            schema.add_field(field_name="category", datatype=DataType.VARCHAR, max_length=100)
            schema.add_field(field_name="importance", datatype=DataType.INT64)
            schema.add_field(field_name="timestamp", datatype=DataType.VARCHAR, max_length=100)
            schema.add_field(field_name="user", datatype=DataType.VARCHAR, max_length=100)
            
            index_params = client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="AUTOINDEX",
                metric_type="COSINE"
            )
            
            client.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params
            )
        
        # Insert memory
        data = [{
            "vector": vector,
            "content": content,
            "category": category,
            "importance": importance,
            "timestamp": datetime.utcnow().isoformat(),
            "user": user
        }]
        
        result = client.insert(
            collection_name=collection_name,
            data=data
        )
        
        return {
            "success": True,
            "inserted_count": result["insert_count"],
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "category": category,
            "importance": importance
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

if __name__ == "__main__":
    # CLI usage
    if len(sys.argv) < 2:
        print("Usage: memory_write.py <content> [category] [importance] [user]")
        sys.exit(1)
    
    content = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else "general"
    importance = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    user = sys.argv[4] if len(sys.argv) > 4 else "default"
    
    result = memory_write(content, category, importance, user)
    print(json.dumps(result, indent=2))
