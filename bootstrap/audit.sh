#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_USER="${OPENCLAW_USER:-openclaw}"
OPENCLAW_HOME="${OPENCLAW_HOME:-/home/${OPENCLAW_USER}}"
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

echo "--- 4. Qdrant collections ---"
python3 - <<'PY'
import json
import os
import urllib.request

base = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
for name in [os.getenv("QDRANT_COLLECTION", "kimi_memories"), os.getenv("TR_COLLECTION", "true_recall")]:
    try:
        with urllib.request.urlopen(f"{base}/collections/{name}", timeout=10) as resp:
            data = json.load(resp)
        result = data["result"]
        print(f"OK   {name}: points={result.get('points_count', 0)}")
    except Exception as exc:
        print(f"MISS {name}: {exc}")
PY
echo

echo "--- 5. Redis buffer ---"
redis-cli -h "${REDIS_HOST:-127.0.0.1}" -p "${REDIS_PORT:-6379}" LLEN "mem:${USER_ID:-unknown}" 2>/dev/null || true
echo

echo "--- 6. Managed files ---"
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

echo "--- 7. Session runtime ---"
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
  if sudo -u "${OPENCLAW_USER}" test -r "${OPENCLAW_SERVICE_SESSIONS_DIR}" 2>/dev/null; then
    echo "OK   ${OPENCLAW_USER} can read service session directory"
  else
    echo "WARN ${OPENCLAW_USER} cannot read service session directory"
  fi
fi
echo

echo "--- 8. Cron ---"
crontab -l -u "${OPENCLAW_USER}" 2>/dev/null | grep -E 'cron_capture|cron_backup|sliding_backup|curate_memories' || true
echo

echo "--- 9. OpenClaw plugin ---"
if command -v openclaw >/dev/null 2>&1; then
  HOME="${OPENCLAW_HOME}" XDG_CONFIG_HOME="${OPENCLAW_HOME}/.config" openclaw plugins info memory-qdrant 2>/dev/null || echo "WARN memory-qdrant plugin not installed for ${OPENCLAW_USER}"
else
  echo "WARN openclaw binary not found for plugin audit"
fi
echo

echo "=============================================="
echo " Audit complete"
echo "=============================================="
