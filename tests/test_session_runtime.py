from __future__ import annotations

import importlib.util
import os
import shutil
import unittest
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "workspace"
    / "skills"
    / "mem-redis"
    / "scripts"
    / "session_runtime.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("session_runtime", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SessionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._original_env)

    def make_sandbox(self) -> Path:
        root = REPO_ROOT / "tests" / f"runtime-sandbox-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        return root

    def test_prefers_service_runtime_when_it_has_newer_session_activity(self) -> None:
        module = load_module()

        root = self.make_sandbox()
        home_dir = root / "home-sessions"
        service_dir = root / "service-sessions"
        home_dir.mkdir()
        service_dir.mkdir()

        old_file = home_dir / "older.jsonl"
        old_file.write_text('{"type":"message"}\n', encoding="utf-8")

        newer_file = service_dir / "newer.jsonl"
        newer_file.write_text('{"type":"message"}\n', encoding="utf-8")

        os.utime(old_file, (1000, 1000))
        os.utime(newer_file, (2000, 2000))

        os.environ["OPENCLAW_HOME_SESSIONS_DIR"] = str(home_dir)
        os.environ["OPENCLAW_SERVICE_SESSIONS_DIR"] = str(service_dir)
        os.environ["OPENCLAW_SESSIONS_DIR"] = str(home_dir)

        selected = module.find_latest_transcript(module.discover_session_dirs())

        self.assertEqual(selected, newer_file)

    def test_falls_back_to_home_runtime_when_service_runtime_is_missing(self) -> None:
        module = load_module()

        root = self.make_sandbox()
        home_dir = root / "home-sessions"
        home_dir.mkdir()

        home_file = home_dir / "current.jsonl"
        home_file.write_text('{"type":"message"}\n', encoding="utf-8")

        os.environ["OPENCLAW_HOME_SESSIONS_DIR"] = str(home_dir)
        os.environ["OPENCLAW_SERVICE_SESSIONS_DIR"] = str(root / "missing-service")
        os.environ["OPENCLAW_SESSIONS_DIR"] = str(home_dir)

        selected = module.find_latest_transcript(module.discover_session_dirs())

        self.assertEqual(selected, home_file)


if __name__ == "__main__":
    unittest.main()
