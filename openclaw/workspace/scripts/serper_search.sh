#!/bin/bash
# Serper search wrapper
# Usage: ./serper_search.sh "your query here"

SERPER_KEY="2e1c97088736f926ced5d6f325f3095a4d0674dd"
QUERY="${1:-test}"

curl -s -X POST "https://google.serper.dev/search" \
  -H "X-API-KEY: $SERPER_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"q\": \"$QUERY\", \"num\": 5}" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
results = data.get('organic', [])
for i, r in enumerate(results, 1):
    print(f'{i}. {r[\"title\"]}')
    print(f'   {r[\"link\"]}')
    print(f'   {r.get(\"snippet\", \"\")}')
    print()
"
