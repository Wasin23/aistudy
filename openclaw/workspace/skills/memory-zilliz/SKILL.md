# memory-zilliz

Vector-based memory system using Zilliz for scalable, searchable context retrieval.

## What it does

Replaces flat markdown memory files with vector embeddings for efficient context loading:
- Query relevant memories instead of loading everything
- Write new memories with semantic metadata
- Per-user collections for multi-tenant setups

## Tools

- `zilliz_recall(query, limit=5)` - Retrieve relevant memories from Zilliz
- `zilliz_store(content, category, importance)` - Store new memories in Zilliz

## Setup

Add to `.env`:
```
ZILLIZ_ENDPOINT=your-cluster-endpoint
ZILLIZ_TOKEN=your-api-token
OPENAI_API_KEY=your-key-for-embeddings
```

## Usage

The agent automatically queries memory at session start and writes important context during conversations.
