from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "bootstrap" / "bootstrap.sh"
README = REPO_ROOT / "README.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
AUDIT = REPO_ROOT / "bootstrap" / "audit.sh"
UPDATE = REPO_ROOT / "bootstrap" / "update.sh"
TEMPLATE_ENV = REPO_ROOT / "templates" / ".memory_env.example"
REBUILD = REPO_ROOT / "bootstrap" / "rebuild_true_recall.sh"
CURATOR = REPO_ROOT / "workspace" / ".projects" / "true-recall" / "tr-process" / "curate_memories.py"
PLUGIN_DIR = REPO_ROOT / "workspace" / "plugins" / "memory-qdrant"
PLUGIN_PACKAGE = PLUGIN_DIR / "package.json"
PLUGIN_MANIFEST = PLUGIN_DIR / "openclaw.plugin.json"
PLUGIN_INDEX = PLUGIN_DIR / "index.ts"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


class RuntimePathTests(unittest.TestCase):
    def test_bootstrap_syncs_workspace_for_service_runtime(self) -> None:
        text = read_text(BOOTSTRAP)
        self.assertIn('SERVICE_OPENCLAW_USER="${SERVICE_OPENCLAW_USER:-openclaw-svc}"', text)
        self.assertIn('SERVICE_WORKSPACE_DIR="${SERVICE_WORKSPACE_DIR:-${SERVICE_OPENCLAW_HOME}/.openclaw/workspace}"', text)
        self.assertIn('sync_repo_workspace "${SERVICE_WORKSPACE_DIR}" "${SERVICE_OPENCLAW_USER}"', text)
        self.assertIn('if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then', text)

    def test_bootstrap_writes_service_memory_env_when_runtime_exists(self) -> None:
        text = read_text(BOOTSTRAP)
        self.assertIn('DEFAULT_CURATION_MODEL="${DEFAULT_CURATION_MODEL:-qwen3.5:35b-a3b}"', text)
        self.assertIn('CURATION_MODEL="${CURATION_MODEL:-${DEFAULT_CURATION_MODEL}}"', text)
        self.assertIn('CURATION_TIMEOUT_SECONDS="${CURATION_TIMEOUT_SECONDS:-1200}"', text)
        self.assertIn('CURATION_NUM_PREDICT="${CURATION_NUM_PREDICT:-1200}"', text)
        self.assertIn('is_legacy_default_curation_model()', text)
        self.assertIn('qwen3:14b', text)
        self.assertIn('Replacing temporary curator fallback ${CURATION_MODEL} with ${DEFAULT_CURATION_MODEL}', text)
        self.assertIn('has_service_runtime()', text)
        self.assertIn('mem_env_service_workspace="${SERVICE_WORKSPACE_DIR}/.memory_env"', text)
        self.assertIn('export OPENCLAW_HOME_SESSIONS_DIR="${home_sessions_dir}"', text)
        self.assertIn('export OPENCLAW_SERVICE_SESSIONS_DIR="${service_sessions_dir}"', text)
        self.assertIn('build_memory_env "${SERVICE_WORKSPACE_DIR}" "${SERVICE_SESSIONS_DIR}" "${SESSIONS_DIR}" "${SERVICE_SESSIONS_DIR}"', text)
        self.assertIn('configure_service_session_access()', text)
        self.assertIn('setfacl -m "u:${OPENCLAW_USER}:x"', text)
        self.assertIn('setfacl -d -m "u:${OPENCLAW_USER}:rx" "${SERVICE_SESSIONS_DIR}"', text)
        self.assertIn('/bin/bash {workspace}/skills/qdrant-memory/scripts/sliding_backup.sh', text)

    def test_audit_reports_home_and_service_session_dirs(self) -> None:
        text = read_text(AUDIT)
        self.assertIn('CURATION_MODEL:-qwen3.5:35b-a3b', text)
        self.assertIn('CURATION_TIMEOUT_SECONDS=${CURATION_TIMEOUT_SECONDS:-1200}', text)
        self.assertIn('CURATION_NUM_PREDICT=${CURATION_NUM_PREDICT:-1200}', text)
        self.assertIn('OPENCLAW_HOME_SESSIONS_DIR', text)
        self.assertIn('OPENCLAW_SERVICE_SESSIONS_DIR', text)
        self.assertIn("find \"${dir}\" -maxdepth 1 -name '*.jsonl'", text)
        self.assertIn('cannot read service session directory', text)

    def test_docs_track_version_and_lossless_update(self) -> None:
        self.assertIn('Jarvis Memory v2.0.16', read_text(README))
        self.assertIn('2.0.16', read_text(CHANGELOG))
        self.assertIn('bootstrap/update.sh', read_text(README))
        self.assertIn('面向 OpenClaw 的持久记忆层', read_text(README))
        self.assertIn('一行代码无损更新', read_text(README))
        self.assertIn('一行代码全新安装', read_text(README))

    def test_curator_fallback_matches_bootstrap_default(self) -> None:
        text = read_text(CURATOR)
        self.assertIn('CURATION_MODEL = os.getenv("CURATION_MODEL", "qwen3.5:35b-a3b")', text)
        self.assertIn('CURATION_TIMEOUT_SECONDS = int(os.getenv("CURATION_TIMEOUT_SECONDS", "1200"))', text)
        self.assertIn('CURATION_NUM_PREDICT = int(os.getenv("CURATION_NUM_PREDICT", "1200"))', text)
        self.assertIn('"format": "json"', text)

    def test_curator_uses_codeshield_qdrant_api_key_when_storing_gems(self) -> None:
        text = read_text(CURATOR)
        self.assertIn('QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")', text)
        self.assertIn('def _qdrant_headers()', text)
        self.assertIn('headers=_qdrant_headers()', text)
        self.assertIn('points?wait=true', text)
        self.assertIn('response.raise_for_status()', text)
        self.assertIn('response.status_code in (200, 202)', text)

    def test_bootstrap_installs_and_configures_true_recall_plugin(self) -> None:
        text = read_text(BOOTSTRAP)
        self.assertIn('install_openclaw_true_recall_plugin()', text)
        self.assertIn('configure_openclaw_true_recall()', text)
        self.assertIn('plugins install', text)
        self.assertIn('plugins enable memory-qdrant', text)
        self.assertIn('plugins/memory-qdrant', text)
        self.assertIn('plugin_install_dir="${runtime_home}/.openclaw/extensions/memory-qdrant"', text)
        self.assertIn('plugin already exists', text)
        self.assertIn('rsync -a --delete "${plugin_source}/" "${plugin_install_dir}/"', text)
        self.assertIn("plugin_version=\"$(python3 -c ", text)
        self.assertIn("'collectionName': os.environ.get('TR_COLLECTION', 'true_recall')", text)
        self.assertIn("'embeddingModel': os.environ.get('EMBEDDING_MODEL', 'mxbai-embed-large')", text)
        self.assertIn("'autoRecall': True", text)
        self.assertIn("plugins = cfg.setdefault('plugins', {})", text)
        self.assertIn("allow = plugins.setdefault('allow', [])", text)
        self.assertIn("allow.append('memory-qdrant')", text)
        self.assertIn("installs = plugins.setdefault('installs', {})", text)
        self.assertIn("'installPath': f'{runtime_home}/.openclaw/extensions/memory-qdrant'", text)
        self.assertIn("'version': os.environ.get('OPENCLAW_PLUGIN_VERSION', '')", text)
        self.assertIn("'apiKeyEnvVar': 'QDRANT_API_KEY'", text)

    def test_plugin_package_exists_with_manifest_and_entrypoint(self) -> None:
        self.assertTrue(PLUGIN_PACKAGE.exists(), PLUGIN_PACKAGE)
        self.assertTrue(PLUGIN_MANIFEST.exists(), PLUGIN_MANIFEST)
        self.assertTrue(PLUGIN_INDEX.exists(), PLUGIN_INDEX)
        package = read_text(PLUGIN_PACKAGE)
        manifest = read_text(PLUGIN_MANIFEST)
        index = read_text(PLUGIN_INDEX)

        self.assertIn('"name": "@godlovestome/memory-qdrant"', package)
        self.assertIn('"version": "2.0.16"', package)
        self.assertIn('"./index.ts"', package)
        self.assertIn('"id": "memory-qdrant"', manifest)
        self.assertIn('"kind": "memory"', manifest)
        self.assertIn('before_agent_start', index)
        self.assertIn('true_recall', index)
        self.assertIn('127.0.0.1:6333', index)
        self.assertIn('/run/openclaw-memory/secrets.env', index)
        self.assertIn('resolveQdrantApiKey', index)

    def test_codeshield_secret_handling_and_rebuild_workflow_are_documented(self) -> None:
        readme = read_text(README)
        changelog = read_text(CHANGELOG)
        update = read_text(UPDATE)
        template = read_text(TEMPLATE_ENV)

        self.assertIn('/run/openclaw-memory/secrets.env', readme)
        self.assertIn('不会写入 `.memory_env`', readme)
        self.assertIn('重建 True Recall gems', readme)
        self.assertIn('2.0.16', changelog)
        self.assertIn('CodeShield-managed secrets stay outside .memory_env', update)
        self.assertIn('QDRANT_API_KEY managed by CodeShield - sourced from restricted path', template)

        rebuild = read_text(REBUILD)
        self.assertIn('curate_memories.py', rebuild)
        self.assertIn('cron_capture.py', rebuild)
        self.assertIn('true_recall', rebuild)
        self.assertIn('redis-cli', rebuild)


if __name__ == '__main__':
    unittest.main()
