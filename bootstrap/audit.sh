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
  "${PROJECT_DIR}/tr-process/curate_memories.py"; do
  if [[ -e "${path}" ]]; then
    echo "OK   ${path}"
  else
    echo "MISS ${path}"
  fi
done
echo

echo "--- 7. Cron ---"
crontab -l -u "${OPENCLAW_USER}" 2>/dev/null | grep -E 'cron_capture|cron_backup|sliding_backup|curate_memories' || true
echo

echo "=============================================="
echo " Audit complete"
echo "=============================================="
