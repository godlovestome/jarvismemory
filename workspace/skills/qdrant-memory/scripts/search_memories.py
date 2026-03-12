#!/usr/bin/env python3
"""
Search memories by semantic similarity in Qdrant.
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime
from typing import Any, Dict, List

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "kimi_memories")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")


def _ollama_embeddings_url() -> str:
    base = OLLAMA_URL.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/embeddings"
    return f"{base}/v1/embeddings"


def get_embedding(text: str) -> List[float] | None:
    data = json.dumps({"model": EMBEDDING_MODEL, "input": text[:8192]}).encode()
    req = urllib.request.Request(
        _ollama_embeddings_url(),
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
        return result["data"][0]["embedding"]
    except Exception as exc:
        print(f"Error generating embedding: {exc}", file=sys.stderr)
        return None


def update_access_stats(point_id: Any, current_payload: Dict[str, Any]) -> bool:
    update_body = {
        "points": [
            {
                "id": point_id,
                "payload": {
                    "access_count": current_payload.get("access_count", 0) + 1,
                    "last_accessed": datetime.now().isoformat(),
                },
            }
        ]
    }
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/payload?wait=true",
        data=json.dumps(update_body).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
        return result.get("status") == "ok"
    except Exception:
        return False


def search_memories(query_vector: List[float], limit: int = 5, tag_filter: str | None = None, track_access: bool = True):
    search_body: Dict[str, Any] = {
        "vector": query_vector,
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
    }
    if tag_filter:
        search_body["filter"] = {"must": [{"key": "tags", "match": {"value": tag_filter}}]}

    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
        data=json.dumps(search_body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
        results = result.get("result", [])
        if track_access:
            for item in results:
                point_id = item.get("id")
                if point_id is not None:
                    update_access_stats(point_id, item.get("payload", {}))
        return results
    except Exception as exc:
        print(f"Error searching memories: {exc}", file=sys.stderr)
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Search memories by semantic similarity")
    parser.add_argument("query", help="Search query text")
    parser.add_argument("--limit", type=int, default=5, help="Number of results")
    parser.add_argument("--filter-tag", help="Filter by tag")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--no-track", action="store_true", help="Do not update access stats")
    args = parser.parse_args()

    query_vector = get_embedding(args.query)
    if query_vector is None:
        raise SystemExit(1)

    results = search_memories(query_vector, args.limit, args.filter_tag, track_access=not args.no_track)
    if not results:
        print("No matching memories found.")
        return

    if args.json:
        output = []
        for item in results:
            payload = item.get("payload", {})
            output.append({
                "id": item.get("id"),
                "score": item.get("score"),
                "text": payload.get("text", ""),
                "date": payload.get("date", ""),
                "tags": payload.get("tags", []),
                "importance": payload.get("importance", "medium"),
                "confidence": payload.get("confidence", "medium"),
                "verified": payload.get("verified", False),
                "access_count": payload.get("access_count", 0),
                "last_accessed": payload.get("last_accessed", ""),
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print(f"Found {len(results)} similar memories.\n")
    for index, item in enumerate(results, start=1):
        payload = item.get("payload", {})
        text = payload.get("text", "")
        if len(text) > 200:
            text = text[:200] + "..."
        print(f"{index}. [{payload.get('date', 'unknown')}] score={item.get('score', 0):.3f}")
        print(f"   {text}")
        tags = payload.get("tags", [])
        if tags:
            print(f"   tags: {', '.join(tags)}")
        access_count = payload.get("access_count", 0)
        if access_count:
            print(f"   accessed: {access_count} times")
        print()


if __name__ == "__main__":
    main()
