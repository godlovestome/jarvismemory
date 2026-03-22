#!/usr/bin/env python3
"""
True-Recall Curator: holistic gem extraction.

Reads recent conversation turns from Redis, extracts high-signal gems with an Ollama
curation model, and stores them in the `true_recall` Qdrant collection.

The Redis buffer is intentionally preserved so the Jarvis Memory backup job can flush the
same source turns into `kimi_memories` on its own schedule.
"""

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import redis
import requests

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = 0
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_COLLECTION = os.getenv("TR_COLLECTION", "true_recall")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
CURATION_MODEL = os.getenv("CURATION_MODEL", "qwen3:14b")
CURATION_TIMEOUT_SECONDS = int(os.getenv("CURATION_TIMEOUT_SECONDS", "1200"))
CURATION_NUM_PREDICT = int(os.getenv("CURATION_NUM_PREDICT", "1200"))

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CURATOR_PROMPT_PATH = PROJECT_DIR / "curator_prompt.md"


def load_curator_prompt() -> str:
    return CURATOR_PROMPT_PATH.read_text(encoding="utf-8")


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )


def get_staged_turns(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    items = get_redis_client().lrange(f"mem:{user_id}", 0, -1)
    turns: List[Dict[str, Any]] = []

    for item in items:
        try:
            turn = json.loads(item)
        except json.JSONDecodeError as exc:
            print(f"Warning: skipping invalid turn: {exc}")
            continue

        if hours:
            try:
                turn_time = datetime.fromisoformat(turn.get("timestamp", "").replace("Z", "+00:00"))
            except ValueError:
                continue
            cutoff = datetime.now(turn_time.tzinfo) - timedelta(hours=hours)
            if turn_time < cutoff:
                continue

        turns.append(turn)

    turns.sort(key=lambda value: value.get("turn", 0))
    return turns


def extract_gems_with_curator(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not turns:
        return []

    response = requests.post(
        f"{OLLAMA_URL.rstrip('/')}/api/generate",
        json={
            "model": CURATION_MODEL,
            "think": False,
            "system": load_curator_prompt(),
            "prompt": (
                "## Input Conversation\n\n```json\n"
                f"{json.dumps(turns, indent=2)}\n"
                "```\n\n## Output\n"
            ),
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": CURATION_NUM_PREDICT},
        },
        timeout=CURATION_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    output = response.json().get("response", "").strip()
    output = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()

    if "```json" in output:
        output = output.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in output:
        output = output.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        gems = json.loads(output)
    except json.JSONDecodeError as exc:
        print(f"Error parsing curator output: {exc}")
        print(output[:500])
        return []

    if isinstance(gems, list):
        return gems
    if not gems:
        return []
    return [gems]


def get_embedding(text: str) -> List[float]:
    response = requests.post(
        f"{OLLAMA_URL.rstrip('/')}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["embedding"]


def store_gem_to_qdrant(gem: Dict[str, Any], user_id: str) -> bool:
    embedding_text = " ".join(
        [gem.get("gem", ""), gem.get("context", ""), gem.get("snippet", "")]
    ).strip()
    vector = get_embedding(embedding_text)

    hash_bytes = hashlib.sha256(
        f"{user_id}:{gem.get('conversation_id', '')}:{gem.get('turn_range', '')}".encode("utf-8")
    ).digest()[:8]
    gem_id = int.from_bytes(hash_bytes, byteorder="big") % (2**63)

    response = requests.put(
        f"{QDRANT_URL.rstrip('/')}/collections/{QDRANT_COLLECTION}/points",
        json={
            "points": [
                {
                    "id": gem_id,
                    "vector": vector,
                    "payload": {"user_id": user_id, **gem},
                }
            ]
        },
        timeout=120,
    )
    return response.status_code == 200


def main() -> None:
    parser = argparse.ArgumentParser(description="True-Recall Curator")
    parser.add_argument("--user-id", required=True, help="User ID to process")
    parser.add_argument("--hours", type=int, default=24, help="Hours of history to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without storing")
    args = parser.parse_args()

    print(f"True-Recall Curator for {args.user_id}")
    print(f"Hours: {args.hours}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Curator model: {CURATION_MODEL}")
    print(f"Curator timeout seconds: {CURATION_TIMEOUT_SECONDS}")
    print(f"Curator max tokens: {CURATION_NUM_PREDICT}")
    print(f"Collection: {QDRANT_COLLECTION}")
    print()

    turns = get_staged_turns(args.user_id, args.hours)
    print(f"Turns found: {len(turns)}")
    if not turns:
        print("No turns to process.")
        return

    gems = extract_gems_with_curator(turns)
    print(f"Gems extracted: {len(gems)}")
    if not gems:
        print("No gems extracted. Redis buffer preserved for Jarvis Memory.")
        return

    for index, gem in enumerate(gems[:3], start=1):
        print(f"Gem {index}: {gem.get('gem', 'N/A')[:120]}")

    if args.dry_run:
        print("Dry run complete. Nothing stored.")
        return

    stored = 0
    for gem in gems:
        if store_gem_to_qdrant(gem, args.user_id):
            stored += 1

    print(f"Stored {stored}/{len(gems)} gems")
    print("Redis buffer preserved for Jarvis Memory backup.")


if __name__ == "__main__":
    main()
