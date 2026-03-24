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
        self.assertIn('TIMEZONE="${TIMEZONE:-America/Los_Angeles}"', text)
        self.assertIn('OPENCLAW_QMD_TIMEOUT_MS="${OPENCLAW_QMD_TIMEOUT_MS:-600000}"', text)
        self.assertIn('CRON_CAPTURE_SCHEDULE="${CRON_CAPTURE_SCHEDULE:-5 11 * * *}"', text)
        self.assertIn('TR_SCHEDULE="${TR_SCHEDULE:-30 11 * * *}"', text)
        self.assertIn('BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-0 12 * * *}"', text)
        self.assertIn('SLIDING_SCHEDULE="${SLIDING_SCHEDULE:-30 12 * * *}"', text)
        self.assertIn('DEFAULT_CURATION_MODEL="${DEFAULT_CURATION_MODEL:-qwen3.5:35b-a3b}"', text)
        self.assertIn('CURATION_MODEL="${CURATION_MODEL:-${DEFAULT_CURATION_MODEL}}"', text)
        self.assertIn('CURATION_TIMEOUT_SECONDS="${CURATION_TIMEOUT_SECONDS:-1200}"', text)
        self.assertIn('CURATION_NUM_PREDICT="${CURATION_NUM_PREDICT:-1200}"', text)
        self.assertIn('has_service_runtime()', text)
        self.assertIn('mem_env_service_workspace="${SERVICE_WORKSPACE_DIR}/.memory_env"', text)
        self.assertIn('export OPENCLAW_HOME_SESSIONS_DIR="${home_sessions_dir}"', text)
        self.assertIn('export OPENCLAW_SERVICE_SESSIONS_DIR="${service_sessions_dir}"', text)
        self.assertIn('configure_service_session_access()', text)
        self.assertIn('setfacl -m "u:${OPENCLAW_USER}:x"', text)
        self.assertIn('setfacl -d -m "u:${OPENCLAW_USER}:rx" "${SERVICE_SESSIONS_DIR}"', text)
        self.assertIn('setfacl -R -m "u:${OPENCLAW_USER}:rX" "${SERVICE_SESSIONS_DIR}"', text)
        self.assertIn('setfacl -R -d -m "u:${OPENCLAW_USER}:rX" "${SERVICE_SESSIONS_DIR}"', text)
        self.assertIn('capture_sessions_arg=" --sessions-dir ${SERVICE_SESSIONS_DIR}"', text)

    def test_audit_reports_home_and_service_session_dirs_and_uses_api_key(self) -> None:
        text = read_text(AUDIT)
        self.assertIn('CURATION_MODEL:-qwen3.5:35b-a3b', text)
        self.assertIn('CURATION_TIMEOUT_SECONDS=${CURATION_TIMEOUT_SECONDS:-1200}', text)
        self.assertIn('CURATION_NUM_PREDICT=${CURATION_NUM_PREDICT:-1200}', text)
        self.assertIn('OPENCLAW_HOME_SESSIONS_DIR', text)
        self.assertIn('OPENCLAW_SERVICE_SESSIONS_DIR', text)
        self.assertIn('headers["api-key"] = api_key', text)
        self.assertIn("find \"${dir}\" -maxdepth 1 -name '*.jsonl'", text)
        self.assertIn('cannot read service session directory', text)

    def test_docs_track_version_and_lossless_update(self) -> None:
        readme = read_text(README)
        changelog = read_text(CHANGELOG)
        update = read_text(UPDATE)
        self.assertIn('Jarvis Memory v2.0.23', readme)
        self.assertIn('2.0.23', changelog)
        self.assertIn('bootstrap/update.sh', readme)
        self.assertIn('configure_openclaw_qmd', update)
        self.assertIn('Persistent memory for OpenClaw.', readme)
        self.assertIn('一行代码无损更新', readme)
        self.assertIn('一行代码全新安装', readme)

    def test_curator_fallback_matches_bootstrap_default(self) -> None:
        text = read_text(CURATOR)
        self.assertIn('CURATION_MODEL = os.getenv("CURATION_MODEL", "qwen3.5:35b-a3b")', text)
        self.assertIn('CURATION_TIMEOUT_SECONDS = int(os.getenv("CURATION_TIMEOUT_SECONDS", "1200"))', text)
        self.assertIn('CURATION_NUM_PREDICT = int(os.getenv("CURATION_NUM_PREDICT", "1200"))', text)
        self.assertIn('"format": "json"', text)
        self.assertIn('def normalize_staged_turns(', text)
        self.assertIn('def normalize_gem_payload(', text)

    def test_curator_uses_codeshield_qdrant_api_key_when_storing_gems(self) -> None:
        text = read_text(CURATOR)
        self.assertIn('QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")', text)
        self.assertIn('def _qdrant_headers()', text)
        self.assertIn('headers=_qdrant_headers()', text)
        self.assertIn('points?wait=true', text)
        self.assertIn('Qdrant store failed:', text)

    def test_bootstrap_installs_and_configures_true_recall_plugin(self) -> None:
        text = read_text(BOOTSTRAP)
        self.assertIn('configure_openclaw_qmd()', text)
        self.assertIn('install_openclaw_true_recall_plugin()', text)
        self.assertIn('configure_openclaw_true_recall()', text)
        self.assertIn('plugins install', text)
        self.assertIn('plugins enable memory-qdrant', text)
        self.assertIn('plugin_install_dir="${runtime_home}/.openclaw/extensions/memory-qdrant"', text)
        self.assertIn('plugin already exists', text)
        self.assertIn('rsync -a --delete "${plugin_source}/" "${plugin_install_dir}/"', text)
        self.assertIn('chown -R root:root "${plugin_install_dir}"', text)
        self.assertIn("'apiKeyEnvVar': 'QDRANT_API_KEY'", text)

    def test_bootstrap_configures_qmd_separately_from_true_recall(self) -> None:
        text = read_text(BOOTSTRAP)
        self.assertIn('QMD bootstrap', text)
        self.assertIn('configure_openclaw_qmd()', text)
        self.assertIn('memory = cfg.setdefault("memory", {})', text)
        self.assertIn('memory["backend"] = "qmd"', text)
        self.assertIn('memory["citations"] = "auto"', text)
        self.assertIn('limits = qmd.setdefault("limits", {})', text)
        self.assertIn('limits["timeoutMs"] = max(', text)
        self.assertIn('qmd_timeout_ms = int(sys.argv[4])', text)
        self.assertIn('existing_paths = qmd.setdefault("paths", [])', text)
        self.assertIn('{"name": "docs", "path": f"{workspace_path}/docs", "pattern": "**/*.md"}', text)
        self.assertIn('{"name": "memory", "path": f"{workspace_path}/memory", "pattern": "**/*.md"}', text)
        self.assertIn("'collectionName': os.environ.get('TR_COLLECTION', 'true_recall')", text)
        self.assertIn("'qdrantUrl': os.environ.get('QDRANT_URL', 'http://127.0.0.1:6333')", text)
        self.assertIn('memory-qdrant', text)
        self.assertIn('true_recall', text)

    def test_plugin_package_exists_with_manifest_and_entrypoint(self) -> None:
        self.assertTrue(PLUGIN_PACKAGE.exists(), PLUGIN_PACKAGE)
        self.assertTrue(PLUGIN_MANIFEST.exists(), PLUGIN_MANIFEST)
        self.assertTrue(PLUGIN_INDEX.exists(), PLUGIN_INDEX)
        package = read_text(PLUGIN_PACKAGE)
        manifest = read_text(PLUGIN_MANIFEST)
        index = read_text(PLUGIN_INDEX)

        self.assertIn('"name": "@godlovestome/memory-qdrant"', package)
        self.assertIn('"version": "2.0.23"', package)
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
        self.assertIn('.memory_env', readme)
        self.assertIn('重建 True Recall gems', readme)
        self.assertIn('2.0.23', changelog)
        self.assertIn('CodeShield-managed secrets stay outside .memory_env', update)
        self.assertIn('SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"', update)
        self.assertIn('resolve_script_context()', update)
        self.assertIn('git clone --depth 1 "${JARVISMEMORY_REPO_URL}" "${REMOTE_REPO_DIR}"', update)
        self.assertIn('QDRANT_API_KEY managed by CodeShield - sourced from restricted path', template)

        rebuild = read_text(REBUILD)
        self.assertIn('curate_memories.py', rebuild)
        self.assertIn('cron_capture.py', rebuild)
        self.assertIn('true_recall', rebuild)
        self.assertIn('redis-cli', rebuild)
        self.assertIn('--hours 0', rebuild)
        self.assertIn('--sessions-dir', rebuild)
        self.assertIn('--all-transcripts', rebuild)
        self.assertIn('repair_service_session_access()', rebuild)
        self.assertIn('probe_transcript_visibility()', rebuild)
        self.assertIn("Visible transcripts for", rebuild)

    def test_audit_reports_qmd_and_true_recall_as_independent_chains(self) -> None:
        text = read_text(AUDIT)
        self.assertIn('--- 4. QMD chain ---', text)
        self.assertIn('--- 5. True Recall chain ---', text)
        self.assertIn('memory.backend', text)
        self.assertIn('citations=auto', text)
        self.assertIn('timeoutMs>=600000', text)
        self.assertIn('collection=true_recall', text)
        self.assertIn('OPENCLAW_SERVICE_SESSIONS_DIR', text)
        self.assertIn('OPENCLAW_HOME_SESSIONS_DIR', text)
        self.assertIn('memory-qdrant', text)
        self.assertIn('can list service session directory', text)


if __name__ == '__main__':
    unittest.main()
