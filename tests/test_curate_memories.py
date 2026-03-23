from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "workspace"
    / ".projects"
    / "true-recall"
    / "tr-process"
    / "curate_memories.py"
)
PROMPT_PATH = (
    REPO_ROOT
    / "workspace"
    / ".projects"
    / "true-recall"
    / "curator_prompt.md"
)


def load_module():
    spec = importlib.util.spec_from_file_location("curate_memories", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CurateMemoriesTests(unittest.TestCase):
    def test_curator_prompt_matches_current_true_recall_contract(self) -> None:
        prompt = PROMPT_PATH.read_text(encoding="utf-8")

        self.assertIn("The input is a JSON array of normalized turns.", prompt)
        self.assertIn("Return a JSON array only.", prompt)
        self.assertIn("conversation_id", prompt)
        self.assertNotIn("kimi_memories", prompt)
        self.assertNotIn("snowflake-arctic-embed2", prompt)

    def test_normalize_staged_turns_builds_turns_from_message_pairs(self) -> None:
        module = load_module()

        staged_messages = [
            {
                "role": "user",
                "content": "QMD retriever is timing out.",
                "timestamp": "2026-03-23T07:00:00+00:00",
                "user_id": "tars",
                "session": "telegram-session",
            },
            {
                "role": "assistant",
                "content": "Let's raise the timeout and confirm the logs.",
                "timestamp": "2026-03-23T07:01:00+00:00",
                "user_id": "tars",
                "session": "telegram-session",
            },
            {
                "role": "user",
                "content": "True Recall still is not storing gems.",
                "timestamp": "2026-03-23T07:02:00+00:00",
                "user_id": "tars",
                "session": "telegram-session",
            },
            {
                "role": "assistant",
                "content": "We should validate the gem payload before writing to Qdrant.",
                "timestamp": "2026-03-23T07:03:00+00:00",
                "user_id": "tars",
                "session": "telegram-session",
            },
        ]

        turns = module.normalize_staged_turns(staged_messages)

        self.assertEqual(len(turns), 2)
        self.assertEqual(turns[0]["turn"], 1)
        self.assertEqual(turns[0]["user_message"], "QMD retriever is timing out.")
        self.assertEqual(turns[0]["ai_response"], "Let's raise the timeout and confirm the logs.")
        self.assertEqual(turns[0]["conversation_id"], "telegram-session")
        self.assertEqual(turns[0]["date"], "2026-03-23")
        self.assertEqual(turns[1]["turn"], 2)
        self.assertEqual(
            turns[1]["ai_response"],
            "We should validate the gem payload before writing to Qdrant.",
        )

    def test_normalize_gem_payload_fills_required_fields_from_turns(self) -> None:
        module = load_module()

        turns = [
            {
                "turn": 1,
                "user_message": "QMD retriever is timing out.",
                "ai_response": "Let's raise the timeout and confirm the logs.",
                "timestamp": "2026-03-23T07:01:00+00:00",
                "date": "2026-03-23",
                "conversation_id": "telegram-session",
                "user_id": "tars",
            },
            {
                "turn": 2,
                "user_message": "True Recall still is not storing gems.",
                "ai_response": "We should validate the gem payload before writing to Qdrant.",
                "timestamp": "2026-03-23T07:03:00+00:00",
                "date": "2026-03-23",
                "conversation_id": "telegram-session",
                "user_id": "tars",
            },
        ]

        gem = module.normalize_gem_payload(
            {
                "gem": "Raise QMD timeout and harden True Recall gem validation.",
                "context": "The current retrieval path times out too early and malformed gems fail to store.",
                "categories": ["technical", "memory"],
                "source_turns": [1, 2],
            },
            turns,
            "tars",
        )

        self.assertIsNotNone(gem)
        self.assertEqual(gem["conversation_id"], "telegram-session")
        self.assertEqual(gem["turn_range"], "1-2")
        self.assertEqual(gem["source_turns"], [1, 2])
        self.assertEqual(gem["date"], "2026-03-23")
        self.assertEqual(gem["timestamp"], "2026-03-23T07:03:00+00:00")
        self.assertIn("QMD retriever is timing out.", gem["snippet"])
        self.assertEqual(gem["importance"], "medium")
        self.assertGreaterEqual(gem["confidence"], 0.6)

    def test_normalize_gem_payload_rejects_missing_gem_text(self) -> None:
        module = load_module()

        turns = [
            {
                "turn": 7,
                "user_message": "hello",
                "ai_response": "hi",
                "timestamp": "2026-03-23T07:03:00+00:00",
                "date": "2026-03-23",
                "conversation_id": "telegram-session",
                "user_id": "tars",
            }
        ]

        gem = module.normalize_gem_payload(
            {
                "context": "This object is malformed and should never be written.",
                "categories": ["technical"],
                "source_turns": [7],
            },
            turns,
            "tars",
        )

        self.assertIsNone(gem)


if __name__ == "__main__":
    unittest.main()
