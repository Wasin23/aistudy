#!/usr/bin/env python3
"""
Ingest WALL-E conversation history into Zilliz

Reads the session JSONL file and extracts key memories:
- User info (name, preferences, context)
- Important discussions (RAG, crypto trading, autonomous agents)
- Personality traits (sarcasm, no unnecessary emojis)
- Technical context (Zilliz usage, ClawHub, paper trading plans)
"""
import os
import sys
import json
from datetime import datetime

# Add tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../skills/memory-zilliz/tools'))
from memory_write import memory_write

def extract_memories_from_session(session_file):
    """Parse JSONL session and extract memorable content"""
    memories = []
    
    with open(session_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                entry = json.loads(line)
                
                # Extract user messages
                if entry.get('type') == 'message' and entry.get('message', {}).get('role') == 'user':
                    msg = entry['message']
                    content_parts = msg.get('content', [])
                    
                    for part in content_parts:
                        if part.get('type') == 'text':
                            text = part.get('text', '')
                            
                            # Filter out metadata
                            if 'Conversation info (untrusted metadata)' in text:
                                continue
                            if 'Sender (untrusted metadata)' in text:
                                continue
                            
                            # Store actual user messages
                            if text.strip():
                                memories.append({
                                    'content': f"User said: {text}",
                                    'category': 'conversation',
                                    'importance': 2,
                                    'timestamp': entry.get('timestamp', '')
                                })
                
                # Extract assistant responses with important context
                if entry.get('type') == 'message' and entry.get('message', {}).get('role') == 'assistant':
                    msg = entry['message']
                    content_parts = msg.get('content', [])
                    
                    for part in content_parts:
                        if part.get('type') == 'text':
                            text = part.get('text', '')
                            
                            # Filter for important topics
                            if any(keyword in text.lower() for keyword in ['zilliz', 'rag', 'clawhub', 'paper trading', 'autonomous', 'emoji']):
                                memories.append({
                                    'content': f"Assistant discussed: {text[:500]}",
                                    'category': 'discussion',
                                    'importance': 3,
                                    'timestamp': entry.get('timestamp', '')
                                })
                
            except json.JSONDecodeError:
                continue
    
    return memories

def main():
    # Set up environment
    os.environ['ZILLIZ_ENDPOINT'] = 'https://in03-6c238263815f091.serverless.gcp-us-west1.cloud.zilliz.com'
    os.environ['ZILLIZ_TOKEN'] = '0dc117d66370e26d6e0f29ef4e58efdc9012e6d94286ee084e5447e4ac63b04562eb6eafbb8b761e789525553efe24d472f37214'
    
    # Check for OpenAI key
    if not os.environ.get('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY=your-key")
        sys.exit(1)
    
    # Session file location
    session_file = os.path.join(
        os.path.dirname(__file__),
        '../../session-backup.jsonl'
    )
    
    if not os.path.exists(session_file):
        print(f"ERROR: Session file not found at {session_file}")
        sys.exit(1)
    
    print("Extracting memories from conversation...")
    memories = extract_memories_from_session(session_file)
    
    print(f"Found {len(memories)} memory candidates")
    
    # Add key facts manually for better context
    key_facts = [
        {
            'content': "User's name is Cole (username: colefidelman). UCLA sophomore, has TTM internship lined up. Building AI assistant setups for wealthy clients as a business ($150-300/hr consulting).",
            'category': 'user_info',
            'importance': 5
        },
        {
            'content': "Named the assistant WALL-E after the Pixar trash robot. User appreciates sarcasm and direct communication. Dislikes unnecessary emojis (called out trained emoji usage).",
            'category': 'personality',
            'importance': 5
        },
        {
            'content': "Uses Zilliz for vector storage. Plans to migrate all memory from flat markdown to Zilliz for scalability.",
            'category': 'technical',
            'importance': 4
        },
        {
            'content': "Wants to build: (1) RAG system with Zilliz per-client, (2) Paper trading bot for crypto analysis, (3) Autonomous agent with ReAct loop that self-codes instructions",
            'category': 'plans',
            'importance': 5
        },
        {
            'content': "Discovered ClawHub (clawhub.ai) - marketplace for OpenClaw skills. Plans to publish custom tools there. Business model: build integrations, sell them.",
            'category': 'business',
            'importance': 4
        },
        {
            'content': "Testing OpenClaw capabilities. Gave access to write/execute code on filesystem. Workspace: C:\\Users\\colto\\OneDrive\\aistudy\\openclaw\\workspace",
            'category': 'technical',
            'importance': 3
        }
    ]
    
    all_memories = key_facts + memories[:20]  # Limit conversation memories to avoid spam
    
    print(f"\nIngesting {len(all_memories)} memories to Zilliz...")
    
    success_count = 0
    for i, mem in enumerate(all_memories):
        result = memory_write(
            content=mem['content'],
            category=mem['category'],
            importance=mem['importance'],
            user='cole'
        )
        
        if result.get('success'):
            success_count += 1
            print(f"  [{i+1}/{len(all_memories)}] ✓ {mem['category']}: {mem['content'][:60]}...")
        else:
            print(f"  [{i+1}/{len(all_memories)}] ✗ Error: {result.get('error', 'Unknown')}")
    
    print(f"\n✓ Ingested {success_count}/{len(all_memories)} memories to Zilliz")
    print("Memory system ready! Test with: python3 scripts/test_memory_search.py")

if __name__ == "__main__":
    main()
