from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "bootstrap" / "bootstrap.sh"
README = REPO_ROOT / "README.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


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
        self.assertIn('build_memory_env "${SERVICE_WORKSPACE_DIR}" "${SERVICE_SESSIONS_DIR}"', text)

    def test_docs_track_version_and_lossless_update(self) -> None:
        self.assertIn('Jarvis Memory v2.0.2', read_text(README))
        self.assertIn('2.0.2', read_text(CHANGELOG))
        self.assertIn('bootstrap/update.sh', read_text(README))


if __name__ == '__main__':
    unittest.main()
