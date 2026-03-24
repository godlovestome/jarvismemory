from __future__ import annotations

import contextlib
import io
import importlib.util
import os
import shutil
import unittest
import uuid
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "workspace"
    / "skills"
    / "mem-redis"
    / "scripts"
    / "session_runtime.py"
)
CRON_MODULE_PATH = (
    REPO_ROOT
    / "workspace"
    / "skills"
    / "mem-redis"
    / "scripts"
    / "cron_capture.py"
)
REBUILD_SCRIPT_PATH = REPO_ROOT / "bootstrap" / "rebuild_true_recall.sh"


def load_module():
    spec = importlib.util.spec_from_file_location("session_runtime", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cron_module():
    spec = importlib.util.spec_from_file_location("cron_capture", CRON_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {CRON_MODULE_PATH}")
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

    def test_prefers_service_runtime_even_when_home_transcript_is_newer(self) -> None:
        module = load_module()

        root = self.make_sandbox()
        home_dir = root / "home-sessions"
        service_dir = root / "service-sessions"
        home_dir.mkdir()
        service_dir.mkdir()

        home_file = home_dir / "newer-home.jsonl"
        home_file.write_text('{"type":"message"}\n', encoding="utf-8")
        service_file = service_dir / "older-service.jsonl"
        service_file.write_text('{"type":"message"}\n', encoding="utf-8")

        os.utime(home_file, (3000, 3000))
        os.utime(service_file, (2000, 2000))

        os.environ["OPENCLAW_HOME_SESSIONS_DIR"] = str(home_dir)
        os.environ["OPENCLAW_SERVICE_SESSIONS_DIR"] = str(service_dir)
        os.environ["OPENCLAW_SESSIONS_DIR"] = str(home_dir)

        selected = module.find_latest_transcript(module.discover_session_dirs())

        self.assertEqual(selected, service_file)

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

    def test_find_all_transcripts_returns_every_readable_file_in_priority_order(self) -> None:
        module = load_module()

        root = self.make_sandbox()
        home_dir = root / "home-sessions"
        service_dir = root / "service-sessions"
        home_dir.mkdir()
        service_dir.mkdir()

        service_old = service_dir / "service-old.jsonl"
        service_new = service_dir / "service-new.jsonl"
        home_only = home_dir / "home-only.jsonl"

        service_old.write_text('{"type":"message"}\n', encoding="utf-8")
        service_new.write_text('{"type":"message"}\n', encoding="utf-8")
        home_only.write_text('{"type":"message"}\n', encoding="utf-8")

        os.utime(service_old, (1000, 1000))
        os.utime(service_new, (2000, 2000))
        os.utime(home_only, (3000, 3000))

        os.environ["OPENCLAW_HOME_SESSIONS_DIR"] = str(home_dir)
        os.environ["OPENCLAW_SERVICE_SESSIONS_DIR"] = str(service_dir)
        os.environ["OPENCLAW_SESSIONS_DIR"] = str(home_dir)

        transcripts = module.find_all_transcripts(module.discover_session_dirs())

        self.assertEqual(transcripts, [service_old, service_new, home_only])

    def test_ignores_unreadable_service_runtime_and_keeps_readable_home_dir(self) -> None:
        module = load_module()

        root = self.make_sandbox()
        home_dir = root / "home-sessions"
        service_dir = root / "service-sessions"
        home_dir.mkdir()
        service_dir.mkdir()

        home_file = home_dir / "current.jsonl"
        home_file.write_text('{"type":"message"}\n', encoding="utf-8")

        os.environ["OPENCLAW_HOME_SESSIONS_DIR"] = str(home_dir)
        os.environ["OPENCLAW_SERVICE_SESSIONS_DIR"] = str(service_dir)
        os.environ["OPENCLAW_SESSIONS_DIR"] = str(home_dir)

        original_is_dir = module.Path.is_dir

        def fake_is_dir(path_obj):
            if str(path_obj) == str(service_dir):
                raise PermissionError("service runtime is not readable")
            return original_is_dir(path_obj)

        with mock.patch.object(module.Path, "is_dir", autospec=True, side_effect=fake_is_dir):
            discovered = module.discover_session_dirs()

        self.assertEqual(discovered, [home_dir])

    def test_discover_session_dirs_skips_directories_that_cannot_be_listed(self) -> None:
        module = load_module()

        root = self.make_sandbox()
        readable_dir = root / "readable"
        blocked_dir = root / "blocked"
        readable_dir.mkdir()
        blocked_dir.mkdir()

        os.environ["OPENCLAW_HOME_SESSIONS_DIR"] = str(readable_dir)
        os.environ["OPENCLAW_SERVICE_SESSIONS_DIR"] = str(blocked_dir)
        os.environ["OPENCLAW_SESSIONS_DIR"] = str(readable_dir)

        original_iterdir = module.Path.iterdir

        def fake_iterdir(path_obj):
            if str(path_obj) == str(blocked_dir):
                raise PermissionError("blocked session directory")
            return original_iterdir(path_obj)

        with mock.patch.object(module.Path, "iterdir", autospec=True, side_effect=fake_iterdir):
            discovered = module.discover_session_dirs()

        self.assertEqual(discovered, [readable_dir])

    def test_find_all_transcripts_keeps_readable_files_when_metadata_refresh_fails(self) -> None:
        module = load_module()

        root = self.make_sandbox()
        session_dir = root / "sessions"
        session_dir.mkdir()

        first = session_dir / "first.jsonl"
        second = session_dir / "second.jsonl"
        third = session_dir / "third.jsonl"

        first.write_text('{"type":"message"}\n', encoding="utf-8")
        second.write_text('{"type":"message"}\n', encoding="utf-8")
        third.write_text('{"type":"message"}\n', encoding="utf-8")

        os.utime(first, (1000, 1000))
        os.utime(second, (2000, 2000))
        os.utime(third, (3000, 3000))

        original_stat = module.Path.stat
        stat_calls: dict[str, int] = {}

        def fake_stat(path_obj, *args, **kwargs):
            path_str = str(path_obj)
            stat_calls[path_str] = stat_calls.get(path_str, 0) + 1
            if path_obj == second and stat_calls[path_str] > 1:
                raise OSError("metadata disappeared during sort")
            return original_stat(path_obj, *args, **kwargs)

        with mock.patch.object(module.Path, "stat", autospec=True, side_effect=fake_stat):
            transcripts = module.find_all_transcripts([session_dir])

        self.assertEqual(transcripts, [first, second, third])

    def test_cron_capture_reports_no_transcript_diagnostics(self) -> None:
        module = load_cron_module()

        stdout = io.StringIO()
        with (
            mock.patch.object(module, "discover_session_dirs", return_value=[]),
            mock.patch.object(module.Path, "is_dir", autospec=True, return_value=False),
            contextlib.redirect_stdout(stdout),
        ):
            with mock.patch.object(module.sys, "argv", ["cron_capture.py"]):
                module.main()

        output = stdout.getvalue()
        self.assertIn("No session transcripts found", output)
        self.assertIn("OPENCLAW_SERVICE_SESSIONS_DIR", output)
        self.assertIn("--sessions-dir", output)

    def test_cron_capture_dry_run_reports_source_visibility(self) -> None:
        module = load_cron_module()

        root = self.make_sandbox()
        session_dir = root / "sessions"
        session_dir.mkdir()
        transcript = session_dir / "session.jsonl"
        transcript.write_text(
            '{"type":"message","message":{"role":"user","content":"hello"}}\n',
            encoding="utf-8",
        )

        stdout = io.StringIO()
        with (
            mock.patch.object(module, "discover_session_dirs", return_value=[session_dir]),
            mock.patch.object(module, "find_all_transcripts", return_value=[transcript]),
            mock.patch.object(module, "append_to_redis", return_value=1),
            mock.patch.object(module, "load_state", return_value={}),
            mock.patch.object(module, "save_state"),
            contextlib.redirect_stdout(stdout),
        ):
            with mock.patch.object(module.sys, "argv", ["cron_capture.py", "--dry-run"]):
                module.main()

        output = stdout.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn(str(session_dir), output)
        self.assertIn("would append", output)

    def test_rebuild_script_logs_capture_command_for_visibility(self) -> None:
        text = REBUILD_SCRIPT_PATH.read_text(encoding="utf-8", errors="replace")
        self.assertIn('log "Capture command:', text)


if __name__ == "__main__":
    unittest.main()
