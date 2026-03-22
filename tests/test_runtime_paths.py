from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "bootstrap" / "bootstrap.sh"
README = REPO_ROOT / "README.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
AUDIT = REPO_ROOT / "bootstrap" / "audit.sh"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


class RuntimePathTests(unittest.TestCase):
    def test_bootstrap_syncs_workspace_for_service_runtime(self) -> None:
        text = read_text(BOOTSTRAP)
        self.assertIn('SERVICE_OPENCLAW_USER="${SERVICE_OPENCLAW_USER:-openclaw-svc}"', text)
        self.assertIn('SERVICE_WORKSPACE_DIR="${SERVICE_WORKSPACE_DIR:-${SERVICE_OPENCLAW_HOME}/.openclaw/workspace}"', text)
        self.assertIn('sync_repo_workspace "${SERVICE_WORKSPACE_DIR}" "${SERVICE_OPENCLAW_USER}"', text)

    def test_bootstrap_writes_service_memory_env_when_runtime_exists(self) -> None:
        text = read_text(BOOTSTRAP)
        self.assertIn('has_service_runtime()', text)
        self.assertIn('mem_env_service_workspace="${SERVICE_WORKSPACE_DIR}/.memory_env"', text)
        self.assertIn('export OPENCLAW_HOME_SESSIONS_DIR="${home_sessions_dir}"', text)
        self.assertIn('export OPENCLAW_SERVICE_SESSIONS_DIR="${service_sessions_dir}"', text)
        self.assertIn('build_memory_env "${SERVICE_WORKSPACE_DIR}" "${SERVICE_SESSIONS_DIR}" "${SESSIONS_DIR}" "${SERVICE_SESSIONS_DIR}"', text)

    def test_audit_reports_home_and_service_session_dirs(self) -> None:
        text = read_text(AUDIT)
        self.assertIn('OPENCLAW_HOME_SESSIONS_DIR', text)
        self.assertIn('OPENCLAW_SERVICE_SESSIONS_DIR', text)
        self.assertIn("find \"${dir}\" -maxdepth 1 -name '*.jsonl'", text)

    def test_docs_track_version_and_lossless_update(self) -> None:
        self.assertIn('Jarvis Memory v2.0.4', read_text(README))
        self.assertIn('2.0.4', read_text(CHANGELOG))
        self.assertIn('bootstrap/update.sh', read_text(README))


if __name__ == '__main__':
    unittest.main()
