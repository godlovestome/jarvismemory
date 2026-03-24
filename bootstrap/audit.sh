#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_USER="${OPENCLAW_USER:-openclaw}"
OPENCLAW_HOME="${OPENCLAW_HOME:-/home/${OPENCLAW_USER}}"
SERVICE_OPENCLAW_USER="${SERVICE_OPENCLAW_USER:-openclaw-svc}"
SERVICE_OPENCLAW_HOME="${SERVICE_OPENCLAW_HOME:-/var/lib/${SERVICE_OPENCLAW_USER}}"
WORKSPACE_DIR="${WORKSPACE_DIR:-${OPENCLAW_HOME}/.openclaw/workspace}"
PROJECT_DIR="${WORKSPACE_DIR}/.projects/true-recall"
ENV_FILE="${OPENCLAW_HOME}/.memory_env"

if [[ -f "${ENV_FILE}" ]]; then
  export HOME="${OPENCLAW_HOME}"
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

WORKSPACE_DIR="${WORKSPACE_DIR:-${OPENCLAW_HOME}/.openclaw/workspace}"
PROJECT_DIR="${WORKSPACE_DIR}/.projects/true-recall"

echo "=============================================="
echo " Jarvis Memory + True Recall audit"
echo "=============================================="
echo "OpenClaw user: ${OPENCLAW_USER}"
echo "Workspace: ${WORKSPACE_DIR}"
echo

echo "--- 1. Services ---"
systemctl is-active docker ollama 2>/dev/null || true
echo

echo "--- 2. Docker containers ---"
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' 2>/dev/null || true
echo

echo "--- 3. Ollama models ---"
for model in "${EMBEDDING_MODEL:-mxbai-embed-large}" "${CURATION_MODEL:-qwen3.5:35b-a3b}"; do
  if ollama list 2>/dev/null | awk '{print $1}' | grep -Eq "^${model}(:latest)?$"; then
    echo "OK   ${model}"
  else
    echo "MISS ${model}"
  fi
done
echo "CURATION_TIMEOUT_SECONDS=${CURATION_TIMEOUT_SECONDS:-1200}"
echo "CURATION_NUM_PREDICT=${CURATION_NUM_PREDICT:-1200}"
echo

echo "--- 4. QMD chain ---"
# memory.backend=qmd citations=auto timeoutMs>=600000
python3 - <<'PY'
import json
import os
from pathlib import Path

runtimes = [
    ("openclaw", Path(os.getenv("OPENCLAW_HOME", "/home/openclaw")) / ".openclaw" / "openclaw.json"),
    ("openclaw-svc", Path(os.getenv("SERVICE_OPENCLAW_HOME", "/var/lib/openclaw-svc")) / ".openclaw" / "openclaw.json"),
]

for runtime, path in runtimes:
    if not path.exists():
        print(f"MISS {runtime} memory.backend=<missing> citations=<missing> timeoutMs=<missing>")
        continue
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MISS {runtime} memory.backend=<unreadable> citations=<unreadable> timeoutMs=<unreadable>: {exc}")
        continue

    memory = cfg.get("memory", {})
    qmd = memory.get("qmd", {})
    limits = qmd.get("limits", {})
    print(
        f"OK   {runtime} memory.backend={memory.get('backend', '<missing>')} "
        f"citations={memory.get('citations', '<missing>')} timeoutMs={limits.get('timeoutMs', '<missing>')} "
        f"paths={len(qmd.get('paths', []))}"
    )
PY
echo

echo "--- 5. True Recall chain ---"
# collection=true_recall
python3 - <<'PY'
import json
import os
import urllib.request
from pathlib import Path

base = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
headers = {}
api_key = os.getenv("QDRANT_API_KEY", "")
if api_key:
    headers["api-key"] = api_key
for name in [os.getenv("QDRANT_COLLECTION", "kimi_memories"), os.getenv("TR_COLLECTION", "true_recall")]:
    try:
        req = urllib.request.Request(f"{base}/collections/{name}", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
        result = data["result"]
        print(f"OK   {name}: points={result.get('points_count', 0)}")
    except Exception as exc:
        print(f"MISS {name}: {exc}")

runtimes = [
    ("openclaw", Path(os.getenv("OPENCLAW_HOME", "/home/openclaw")) / ".openclaw" / "openclaw.json"),
    ("openclaw-svc", Path(os.getenv("SERVICE_OPENCLAW_HOME", "/var/lib/openclaw-svc")) / ".openclaw" / "openclaw.json"),
]

for runtime, path in runtimes:
    if not path.exists():
        print(f"MISS {runtime} plugin=memory-qdrant enabled=<missing> collection=<missing>")
        continue
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MISS {runtime} plugin=memory-qdrant enabled=<unreadable> collection=<unreadable>: {exc}")
        continue

    plugin = cfg.get("plugins", {}).get("entries", {}).get("memory-qdrant", {})
    collection = plugin.get("config", {}).get("collectionName", "<missing>")
    enabled = plugin.get("enabled", False)
    print(f"OK   {runtime} plugin=memory-qdrant enabled={enabled} collection={collection}")
PY
echo

echo "--- 6. Redis buffer ---"
redis-cli -h "${REDIS_HOST:-127.0.0.1}" -p "${REDIS_PORT:-6379}" LLEN "mem:${USER_ID:-unknown}" 2>/dev/null || true
echo

echo "--- 7. Managed files ---"
for path in \
  "${WORKSPACE_DIR}/HEARTBEAT.md" \
  "${WORKSPACE_DIR}/.memory_env" \
  "${WORKSPACE_DIR}/skills/mem-redis/scripts/cron_capture.py" \
  "${WORKSPACE_DIR}/skills/mem-redis/scripts/cron_backup.py" \
  "${WORKSPACE_DIR}/skills/qdrant-memory/scripts/auto_store.py" \
  "${WORKSPACE_DIR}/plugins/memory-qdrant/package.json" \
  "${PROJECT_DIR}/tr-process/curate_memories.py"; do
  if [[ -e "${path}" ]]; then
    echo "OK   ${path}"
  else
    echo "MISS ${path}"
  fi
done
echo

echo "--- 8. Session runtime ---"
echo "OPENCLAW_SESSIONS_DIR=${OPENCLAW_SESSIONS_DIR:-<not set>}"
echo "OPENCLAW_HOME_SESSIONS_DIR=${OPENCLAW_HOME_SESSIONS_DIR:-<not set>}"
echo "OPENCLAW_SERVICE_SESSIONS_DIR=${OPENCLAW_SERVICE_SESSIONS_DIR:-<not set>}"

for dir in "${OPENCLAW_SERVICE_SESSIONS_DIR:-}" "${OPENCLAW_HOME_SESSIONS_DIR:-}" "${OPENCLAW_SESSIONS_DIR:-}"; do
  [[ -n "${dir}" ]] || continue
  if [[ -d "${dir}" ]]; then
    latest="$(find "${dir}" -maxdepth 1 -name '*.jsonl' -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-)"
    if [[ -n "${latest}" ]]; then
      echo "OK   ${dir} -> latest $(basename "${latest}")"
    else
      echo "WARN ${dir} -> no .jsonl transcripts"
    fi
  else
    echo "MISS ${dir}"
  fi
done
if [[ -n "${OPENCLAW_SERVICE_SESSIONS_DIR:-}" ]] && [[ -d "${OPENCLAW_SERVICE_SESSIONS_DIR}" ]]; then
  if visible_count="$(sudo -u "${OPENCLAW_USER}" find "${OPENCLAW_SERVICE_SESSIONS_DIR}" -maxdepth 1 -name '*.jsonl' -type f 2>/dev/null | wc -l)"; then
    echo "OK   ${OPENCLAW_USER} can list service session directory (${visible_count} visible .jsonl files)"
  else
    echo "WARN ${OPENCLAW_USER} cannot read service session directory"
  fi
fi
echo

echo "--- 9. Cron ---"
crontab -l -u "${OPENCLAW_USER}" 2>/dev/null | grep -E 'cron_capture|cron_backup|sliding_backup|curate_memories' || true
echo

echo "--- 10. OpenClaw plugin ---"
if command -v openclaw >/dev/null 2>&1; then
  HOME="${OPENCLAW_HOME}" XDG_CONFIG_HOME="${OPENCLAW_HOME}/.config" openclaw plugins info memory-qdrant 2>/dev/null || echo "WARN memory-qdrant plugin not installed for ${OPENCLAW_USER}"
else
  echo "WARN openclaw binary not found for plugin audit"
fi
echo

echo "=============================================="
echo " Audit complete"
echo "=============================================="
