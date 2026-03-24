#!/usr/bin/env python3
"""
True-Recall Curator: holistic gem extraction.

Reads recent conversation turns from Redis, extracts high-signal gems with an Ollama
curation model, and stores them in the `true_recall` Qdrant collection.

The Redis buffer is intentionally preserved so the Jarvis Memory backup job can flush the
same source turns into `kimi_memories` on its own schedule.
"""

import argparse
import json
import os
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis
import requests

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = 0
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_COLLECTION = os.getenv("TR_COLLECTION", "true_recall")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
CURATION_MODEL = os.getenv("CURATION_MODEL", "qwen3.5:35b-a3b")
CURATION_TIMEOUT_SECONDS = int(os.getenv("CURATION_TIMEOUT_SECONDS", "1200"))
CURATION_NUM_PREDICT = int(os.getenv("CURATION_NUM_PREDICT", "1200"))

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CURATOR_PROMPT_PATH = PROJECT_DIR / "curator_prompt.md"


def load_curator_prompt() -> str:
    return CURATOR_PROMPT_PATH.read_text(encoding="utf-8")


def _qdrant_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if QDRANT_API_KEY:
        headers["api-key"] = QDRANT_API_KEY
    return headers


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )


def get_staged_turns(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    items = get_redis_client().lrange(f"mem:{user_id}", 0, -1)
    staged_messages: List[Dict[str, Any]] = []

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

        staged_messages.append(turn)

    return normalize_staged_turns(staged_messages)


def _parse_timestamp(raw_value: Any) -> Optional[datetime]:
    if not raw_value or not isinstance(raw_value, str):
        return None
    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _iso_or_default(raw_value: Any) -> str:
    parsed = _parse_timestamp(raw_value)
    if parsed is not None:
        return parsed.isoformat()
    return datetime.utcnow().isoformat() + "+00:00"


def normalize_staged_turns(staged_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not staged_messages:
        return []

    if all("user_message" in item and "ai_response" in item for item in staged_messages):
        normalized = []
        for index, item in enumerate(staged_messages, start=1):
            timestamp = _iso_or_default(item.get("timestamp"))
            normalized.append(
                {
                    "user_id": item.get("user_id", ""),
                    "user_message": str(item.get("user_message", "")).strip(),
                    "ai_response": str(item.get("ai_response", "")).strip(),
                    "turn": int(item.get("turn", index)),
                    "timestamp": timestamp,
                    "date": item.get("date") or timestamp[:10],
                    "conversation_id": str(
                        item.get("conversation_id") or item.get("session") or "unknown-session"
                    ),
                }
            )
        normalized.sort(key=lambda value: value.get("turn", 0))
        return normalized

    def sort_key(value: Dict[str, Any]) -> tuple[str, str]:
        return (
            str(value.get("session") or "unknown-session"),
            _iso_or_default(value.get("timestamp")),
        )

    turns: List[Dict[str, Any]] = []
    pending_by_session: Dict[str, Dict[str, Any]] = {}
    next_turn_by_session: Dict[str, int] = {}

    for message in sorted(staged_messages, key=sort_key):
        role = str(message.get("role", "")).strip()
        if role not in {"user", "assistant"}:
            continue

        session_id = str(message.get("session") or "unknown-session")
        content = str(message.get("content", "")).strip()
        if not content:
            continue

        timestamp = _iso_or_default(message.get("timestamp"))
        user_id = str(message.get("user_id", "")).strip()
        turn_number = next_turn_by_session.setdefault(session_id, 1)
        pending = pending_by_session.get(session_id)

        if role == "user":
            if pending and pending.get("user_message") and not pending.get("ai_response"):
                pending["user_message"] = f"{pending['user_message']}\n{content}".strip()
                pending["timestamp"] = timestamp
                pending["date"] = timestamp[:10]
                continue

            if pending and pending.get("user_message") and pending.get("ai_response"):
                turns.append(pending)
                next_turn_by_session[session_id] = int(pending["turn"]) + 1
                turn_number = next_turn_by_session[session_id]

            pending_by_session[session_id] = {
                "user_id": user_id,
                "user_message": content,
                "ai_response": "",
                "turn": turn_number,
                "timestamp": timestamp,
                "date": timestamp[:10],
                "conversation_id": session_id,
            }
            continue

        if pending and pending.get("user_message"):
            pending["ai_response"] = f"{pending.get('ai_response', '')}\n{content}".strip()
            pending["timestamp"] = timestamp
            pending["date"] = timestamp[:10]
            turns.append(pending)
            next_turn_by_session[session_id] = int(pending["turn"]) + 1
            pending_by_session.pop(session_id, None)

    turns.sort(key=lambda value: (value.get("conversation_id", ""), value.get("turn", 0)))
    return turns


def _join_snippet(turns: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for turn in turns:
        user_message = str(turn.get("user_message", "")).strip()
        ai_response = str(turn.get("ai_response", "")).strip()
        if user_message:
            parts.append(f"User: {user_message}")
        if ai_response:
            parts.append(f"Assistant: {ai_response}")
    return "\n".join(parts)


def _first_nonempty_string(payload: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_categories(raw_categories: Any) -> List[str]:
    if isinstance(raw_categories, str):
        values = re.split(r"[,|/\n]+", raw_categories)
    elif isinstance(raw_categories, list):
        values = [str(value) for value in raw_categories]
    else:
        values = []

    normalized: List[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized[:5]


def _normalize_source_turns(raw_source_turns: Any) -> List[int]:
    values: List[int] = []

    if isinstance(raw_source_turns, int):
        return [raw_source_turns]

    if isinstance(raw_source_turns, str):
        raw_source_turns = raw_source_turns.strip()
        if not raw_source_turns:
            return []
        range_match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", raw_source_turns)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if start <= end:
                return list(range(start, end + 1))
            return list(range(end, start + 1))
        raw_source_turns = re.split(r"[,\s]+", raw_source_turns)

    if not isinstance(raw_source_turns, list):
        return []

    for value in raw_source_turns:
        if isinstance(value, int):
            values.append(value)
            continue
        if isinstance(value, str) and value.isdigit():
            values.append(int(value))
            continue
        if isinstance(value, dict):
            turn_value = value.get("turn")
            if isinstance(turn_value, int):
                values.append(turn_value)
            elif isinstance(turn_value, str) and turn_value.isdigit():
                values.append(int(turn_value))

    return sorted({value for value in values if value > 0})


def normalize_gem_payload(
    gem: Dict[str, Any],
    turns: List[Dict[str, Any]],
    user_id: str,
) -> Optional[Dict[str, Any]]:
    if not isinstance(gem, dict):
        return None

    gem_text = _first_nonempty_string(
        gem,
        ["gem", "memory", "summary", "fact", "insight", "title"],
    )
    if not gem_text:
        return None

    normalized_turns = [turn for turn in turns if isinstance(turn, dict)]
    if not normalized_turns:
        return None

    indexed_turns = {
        int(turn["turn"]): turn
        for turn in normalized_turns
        if str(turn.get("turn", "")).isdigit() or isinstance(turn.get("turn"), int)
    }

    source_turns = gem.get("source_turns")
    parsed_source_turns = _normalize_source_turns(source_turns)
    if not parsed_source_turns:
        parsed_source_turns = _normalize_source_turns(gem.get("turn_range"))
    if not parsed_source_turns and indexed_turns:
        parsed_source_turns = sorted(indexed_turns.keys())[:2]

    selected_turns = [indexed_turns[turn] for turn in parsed_source_turns if turn in indexed_turns]
    if not selected_turns:
        selected_turns = normalized_turns[: min(len(normalized_turns), 2)]
        parsed_source_turns = [int(turn["turn"]) for turn in selected_turns if "turn" in turn]

    last_turn = selected_turns[-1]
    first_turn = selected_turns[0]
    context = _first_nonempty_string(gem, ["context", "why", "reason", "rationale"])
    snippet = _first_nonempty_string(gem, ["snippet", "excerpt", "evidence"]) or _join_snippet(selected_turns)
    categories = _normalize_categories(gem.get("categories") or gem.get("tags") or gem.get("labels"))
    if not categories:
        categories = ["technical"]
    categories = categories[:5]

    importance = str(gem.get("importance", "medium")).strip().lower()
    if importance in {"critical", "urgent"}:
        importance = "high"
    elif importance == "low":
        importance = "medium"
    if importance not in {"medium", "high"}:
        importance = "medium"

    try:
        confidence = float(gem.get("confidence", 0.8))
    except (TypeError, ValueError):
        confidence = 0.8
    confidence = max(0.6, min(confidence, 1.0))

    timestamp = str(gem.get("timestamp") or last_turn.get("timestamp") or "").strip()
    timestamp = _iso_or_default(timestamp)
    date = str(gem.get("date") or timestamp[:10]).strip() or timestamp[:10]

    conversation_id = str(
        gem.get("conversation_id")
        or last_turn.get("conversation_id")
        or first_turn.get("conversation_id")
        or "unknown-session"
    ).strip()
    if not conversation_id:
        conversation_id = "unknown-session"

    if parsed_source_turns:
        turn_range = f"{parsed_source_turns[0]}-{parsed_source_turns[-1]}"
    else:
        turn_range = str(gem.get("turn_range", "")).strip() or "0-0"

    normalized = {
        "gem": gem_text,
        "context": context or gem_text,
        "snippet": snippet,
        "categories": categories,
        "importance": importance,
        "confidence": confidence,
        "timestamp": timestamp,
        "date": date,
        "conversation_id": conversation_id,
        "turn_range": turn_range,
        "source_turns": parsed_source_turns,
        "user_id": user_id,
    }
    return normalized


def build_qdrant_point_id(gem: Dict[str, Any], user_id: str) -> str:
    seed = "|".join(
        [
            str(user_id),
            str(gem.get("conversation_id", "")),
            str(gem.get("turn_range", "")),
            str(gem.get("gem", "")),
        ]
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


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
            "format": "json",
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
    except json.JSONDecodeError:
        start = min((idx for idx in (output.find("["), output.find("{")) if idx != -1), default=-1)
        end = max(output.rfind("]"), output.rfind("}"))
        if start != -1 and end != -1 and end > start:
            try:
                gems = json.loads(output[start : end + 1])
            except json.JSONDecodeError as exc:
                print(f"Error parsing curator output: {exc}")
                print(output[:500])
                return []
        else:
            print("Error parsing curator output: no JSON payload found")
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

    gem_id = build_qdrant_point_id(gem, user_id)

    response = requests.put(
        f"{QDRANT_URL.rstrip('/')}/collections/{QDRANT_COLLECTION}/points?wait=true",
        json={
            "points": [
                {
                    "id": gem_id,
                    "vector": vector,
                    "payload": {"user_id": user_id, **gem},
                }
            ]
        },
        headers=_qdrant_headers(),
        timeout=120,
    )
    if response.status_code not in (200, 202):
        print(f"Qdrant store failed: {response.status_code} {response.text[:1000]}")
    response.raise_for_status()
    return response.status_code in (200, 202)


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

    raw_gems = extract_gems_with_curator(turns)
    print(f"Gems extracted: {len(raw_gems)}")
    if not raw_gems:
        print("No gems extracted. Redis buffer preserved for Jarvis Memory.")
        return

    gems: List[Dict[str, Any]] = []
    for gem in raw_gems:
        normalized = normalize_gem_payload(gem, turns, args.user_id)
        if normalized is not None:
            gems.append(normalized)
        else:
            preview = json.dumps(gem, ensure_ascii=False)[:500]
            print(f"Skipped invalid gem payload: {preview}")

    if not gems:
        print("No valid gems after normalization. Redis buffer preserved for Jarvis Memory.")
        return

    for index, gem in enumerate(gems[:3], start=1):
        print(f"Gem {index}: {gem.get('gem', 'N/A')[:120]}")

    if args.dry_run:
        print("Dry run complete. Nothing stored.")
        return

    stored = 0
    for gem in gems:
        try:
            if store_gem_to_qdrant(gem, args.user_id):
                stored += 1
        except requests.RequestException as exc:
            print(f"Failed to store gem: {exc}")

    print(f"Stored {stored}/{len(gems)} gems")
    print("Redis buffer preserved for Jarvis Memory backup.")


if __name__ == "__main__":
    main()
