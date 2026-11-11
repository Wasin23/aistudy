#!/usr/bin/env python3
"""
memory_check.py - WALL-E's memory usage tracker
Scans workspace memory files and reports sizes + estimated token counts.
"""

import os
import json
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent

# Files to track
TRACKED_FILES = [
    "MEMORY.md",
    "SOUL.md",
    "USER.md",
    "IDENTITY.md",
    "AGENTS.md",
    "TOOLS.md",
    "HEARTBEAT.md",
]

MEMORY_DIR = WORKSPACE / "memory"

# Rough token estimate: ~4 chars per token
def estimate_tokens(text: str) -> int:
    return len(text) // 4

# Thresholds
WARN_TOKENS = 2000
HARD_LIMIT_TOKENS = 4000

def check_file(path: Path):
    if not path.exists():
        return None
    size = path.stat().st_size
    text = path.read_text(encoding="utf-8", errors="ignore")
    tokens = estimate_tokens(text)
    return {
        "path": str(path.relative_to(WORKSPACE)),
        "size_bytes": size,
        "size_kb": round(size / 1024, 1),
        "tokens": tokens,
        "status": "HARD LIMIT" if tokens >= HARD_LIMIT_TOKENS else "WARN" if tokens >= WARN_TOKENS else "OK"
    }

def main():
    results = []

    # Check tracked root files
    for filename in TRACKED_FILES:
        result = check_file(WORKSPACE / filename)
        if result:
            results.append(result)

    # Check memory/ daily files
    if MEMORY_DIR.exists():
        for f in sorted(MEMORY_DIR.glob("*.md"))[-7:]:  # last 7 days
            result = check_file(f)
            if result:
                results.append(result)
        for f in MEMORY_DIR.glob("*.json"):
            result = check_file(f)
            if result:
                results.append(result)

    # Print report
    print("=" * 52)
    print("  WALL-E Memory Usage Report")
    print("=" * 52)

    total_tokens = 0
    for r in results:
        flag = ""
        if r["status"] == "HARD LIMIT":
            flag = " ❌"
        elif r["status"] == "WARN":
            flag = " ⚠️"
        print(f"  {r['path']:<35} {r['size_kb']:>5}kb  ~{r['tokens']:>5} tokens{flag}")
        total_tokens += r["tokens"]

    print("-" * 52)
    total_status = "❌ OVER LIMIT" if total_tokens >= 10000 else "⚠️  GETTING HEAVY" if total_tokens >= 6000 else "✅ OK"
    print(f"  {'TOTAL':<35} {'':>5}    ~{total_tokens:>5} tokens  {total_status}")
    print("=" * 52)

    # Save state
    state_path = MEMORY_DIR / "memory-usage.json"
    MEMORY_DIR.mkdir(exist_ok=True)
    with open(state_path, "w") as f:
        json.dump({
            "total_tokens": total_tokens,
            "files": results
        }, f, indent=2)

    print(f"\n  State saved to memory/memory-usage.json")

if __name__ == "__main__":
    main()
