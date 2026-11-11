#!/usr/bin/env python3
"""
search.py - WALL-E's Serper search tool
Usage: python3 search.py "your query here"
"""

import sys
import json
import http.client

SERPER_API_KEY = "2e1c97088736f926ced5d6f325f3095a4d0674dd"

def search(query: str, num: int = 5) -> dict:
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query, "num": num})
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search.py \"query\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    results = search(query)

    print(f"\nSearch: {query}\n{'='*50}")

    # Answer box
    if "answerBox" in results:
        ab = results["answerBox"]
        print(f"Answer: {ab.get('answer') or ab.get('snippet', '')}\n")

    # Organic results
    for i, r in enumerate(results.get("organic", []), 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['link']}")
        print(f"   {r.get('snippet', '')}\n")

if __name__ == "__main__":
    main()
