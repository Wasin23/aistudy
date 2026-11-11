#!/usr/bin/env python3
"""
Check how many memories are stored in Zilliz and preview them
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

from pymilvus import MilvusClient

client = MilvusClient(
    uri=os.environ["ZILLIZ_ENDPOINT"],
    token=os.environ["ZILLIZ_TOKEN"]
)

COLLECTION = "openclaw_memory"

stats = client.get_collection_stats(COLLECTION)
count = stats["row_count"]
print(f"Total memories: {count}")

if "--list" in sys.argv or "-l" in sys.argv:
    results = client.query(
        collection_name=COLLECTION,
        filter="id >= 0",
        output_fields=["id", "content", "source"],
        limit=count
    )
    print()
    for i, r in enumerate(results, 1):
        content = r.get("content", "")[:120].replace("\n", " ")
        source = r.get("source", "unknown")
        print(f"{i:3}. [{source}] {content}")
