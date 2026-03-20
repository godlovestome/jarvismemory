#!/usr/bin/env python3
"""
Search True-Recall contextual gems.
"""

import argparse
import json
import os
from typing import Any, Dict, List

import requests

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_COLLECTION = os.getenv("TR_COLLECTION", "true_recall")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
DEFAULT_USER_ID = os.getenv("USER_ID", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")


def _qdrant_headers() -> dict:
    h = {}
    if QDRANT_API_KEY:
        h["api-key"] = QDRANT_API_KEY
    return h


def get_embedding(text: str) -> List[float]:
    response = requests.post(
        f"{OLLAMA_URL.rstrip('/')}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["embedding"]


def search_memories(query: str, user_id: str, limit: int, min_score: float) -> List[Dict[str, Any]]:
    response = requests.post(
        f"{QDRANT_URL.rstrip('/')}/collections/{QDRANT_COLLECTION}/points/search",
        json={
            "vector": get_embedding(query),
            "limit": limit,
            "with_payload": True,
            "filter": {"must": [{"key": "user_id", "match": {"value": user_id}}]},
            "score_threshold": min_score,
        },
        headers=_qdrant_headers(),
        timeout=60,
    )
    response.raise_for_status()

    results = []
    for item in response.json().get("result", []):
        payload = item.get("payload", {})
        payload["score"] = item.get("score")
        results.append(payload)
    return results


def format_gem(gem: Dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Gem: {gem.get('gem', 'N/A')}",
            f"Context: {gem.get('context', 'N/A')}",
            f"Snippet: {gem.get('snippet', 'N/A')[:240]}",
            f"Categories: {', '.join(gem.get('categories', []))}",
            f"Importance: {gem.get('importance', 'N/A')}",
            f"Confidence: {gem.get('confidence', 'N/A')}",
            f"Date: {gem.get('date', 'N/A')} {gem.get('timestamp', '')}",
            f"Score: {gem.get('score', 0):.3f}",
            "---",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Search True-Recall gems")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help="User ID")
    parser.add_argument("--limit", type=int, default=5, help="Result limit")
    parser.add_argument("--min-score", type=float, default=0.5, help="Minimum score")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not args.user_id:
        raise SystemExit("--user-id is required when USER_ID is not set")

    gems = search_memories(args.query, args.user_id, args.limit, args.min_score)
    if args.json:
        print(json.dumps(gems, indent=2, ensure_ascii=False))
        return

    if not gems:
        print("No matching True-Recall gems found.")
        return

    print(f"Found {len(gems)} gem(s).")
    print()
    for gem in gems:
        print(format_gem(gem))


if __name__ == "__main__":
    main()
