#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_USER="${OPENCLAW_USER:-openclaw}"
OPENCLAW_HOME="${OPENCLAW_HOME:-/home/${OPENCLAW_USER}}"
ENV_FILE="${OPENCLAW_HOME}/.memory_env"
WORKSPACE_DIR="${WORKSPACE_DIR:-${OPENCLAW_HOME}/.openclaw/workspace}"
SERVICE_OPENCLAW_USER="${SERVICE_OPENCLAW_USER:-openclaw-svc}"
SERVICE_OPENCLAW_HOME="${SERVICE_OPENCLAW_HOME:-/var/lib/${SERVICE_OPENCLAW_USER}}"
SERVICE_WORKSPACE_DIR="${SERVICE_WORKSPACE_DIR:-${SERVICE_OPENCLAW_HOME}/.openclaw/workspace}"
PYTHON_BIN="${WORKSPACE_DIR}/.venv/bin/python"
CAPTURE_SCRIPT="${WORKSPACE_DIR}/skills/mem-redis/scripts/cron_capture.py"
CURATOR_SCRIPT="${WORKSPACE_DIR}/.projects/true-recall/tr-process/curate_memories.py"
STATE_FILE="${WORKSPACE_DIR}/.mem_capture_state.json"
SERVICE_STATE_FILE="${SERVICE_WORKSPACE_DIR}/.mem_capture_state.json"
USER_ID="${USER_ID:-${1:-}}"

log() { printf '[rebuild_true_recall] %s\n' "$*"; }
die() { printf '[rebuild_true_recall] ERROR: %s\n' "$*" >&2; exit 1; }

require_root() {
  [[ "$(id -u)" -eq 0 ]] || die "Please run this script as root or with sudo"
}

repair_service_session_access() {
  if [[ ! -d "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions" ]]; then
    return 0
  fi

  if ! command -v setfacl >/dev/null 2>&1; then
    return 0
  fi

  local traverse_paths=(
    "${SERVICE_OPENCLAW_HOME}"
    "${SERVICE_OPENCLAW_HOME}/.openclaw"
    "${SERVICE_OPENCLAW_HOME}/.openclaw/agents"
    "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main"
    "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions"
  )

  local path
  for path in "${traverse_paths[@]}"; do
    [[ -d "${path}" ]] || continue
    setfacl -m "u:${OPENCLAW_USER}:x" "${path}" || true
  done

  setfacl -m "u:${OPENCLAW_USER}:rx" "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions" || true
  setfacl -d -m "u:${OPENCLAW_USER}:rX" "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions" || true
  setfacl -R -m "u:${OPENCLAW_USER}:rX" "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions" || true
}

run_as_openclaw() {
  local command_text="$1"
  su -s /bin/bash "${OPENCLAW_USER}" -c "source '${ENV_FILE}' && ${command_text}"
}

capture_command() {
  local base_cmd="'${PYTHON_BIN}' '${CAPTURE_SCRIPT}' --user-id '${USER_ID}'"
  if [[ -d "${SERVICE_OPENCLAW_HOME}/.openclaw" && -d "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions" ]]; then
    printf "%s --sessions-dir '%s'" "${base_cmd}" "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions"
    return 0
  fi
  printf "%s" "${base_cmd}"
}

require_root
[[ -f "${ENV_FILE}" ]] || die "Missing ${ENV_FILE}. Run bootstrap/bootstrap.sh first."

export HOME="${OPENCLAW_HOME}"
# shellcheck disable=SC1090
source "${ENV_FILE}"

USER_ID="${USER_ID:-${USER_ID:-}}"
[[ -n "${USER_ID}" ]] || die "USER_ID is not set. Export it or pass it as the first argument."
[[ -x "${PYTHON_BIN}" ]] || die "Missing virtualenv python at ${PYTHON_BIN}"
[[ -f "${CAPTURE_SCRIPT}" ]] || die "Missing capture script at ${CAPTURE_SCRIPT}"
[[ -f "${CURATOR_SCRIPT}" ]] || die "Missing curator script at ${CURATOR_SCRIPT}"

log "User: ${USER_ID}"
log "Workspace: ${WORKSPACE_DIR}"
log "True Recall collection: ${TR_COLLECTION:-true_recall}"
log "Secrets source: /run/openclaw-memory/secrets.env (if present)"

log "Clearing staged Redis buffer"
redis-cli -h "${REDIS_HOST:-127.0.0.1}" -p "${REDIS_PORT:-6379}" DEL "mem:${USER_ID}" >/dev/null

log "Removing capture state files"
rm -f "${STATE_FILE}"
rm -f "${SERVICE_STATE_FILE}"

log "Repairing service session ACLs"
repair_service_session_access

log "Recreating true_recall collection"
"${PYTHON_BIN}" - <<'PY'
import json
import os
import urllib.error
import urllib.request

base = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
collection = os.environ.get("TR_COLLECTION", "true_recall")
api_key = os.environ.get("QDRANT_API_KEY", "")
headers = {"Content-Type": "application/json"}
if api_key:
    headers["api-key"] = api_key

delete_req = urllib.request.Request(
    f"{base}/collections/{collection}",
    headers=headers,
    method="DELETE",
)
try:
    with urllib.request.urlopen(delete_req, timeout=30) as resp:
        print(f"delete: HTTP {resp.status}")
except urllib.error.HTTPError as exc:
    if exc.code not in (404,):
        raise
    print("delete: collection already absent")

create_payload = json.dumps(
    {"vectors": {"size": 1024, "distance": "Cosine"}}
).encode("utf-8")
create_req = urllib.request.Request(
    f"{base}/collections/{collection}",
    data=create_payload,
    headers=headers,
    method="PUT",
)
with urllib.request.urlopen(create_req, timeout=30) as resp:
    print(f"create: HTTP {resp.status}")
PY

log "Re-running transcript capture"
run_as_openclaw "$(capture_command)"

log "Re-running gem curation"
run_as_openclaw "'${PYTHON_BIN}' '${CURATOR_SCRIPT}' --user-id '${USER_ID}' --hours 0"

log "Final point count"
"${PYTHON_BIN}" - <<'PY'
import json
import os
import urllib.request

base = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
collection = os.environ.get("TR_COLLECTION", "true_recall")
api_key = os.environ.get("QDRANT_API_KEY", "")
headers = {}
if api_key:
    headers["api-key"] = api_key

req = urllib.request.Request(f"{base}/collections/{collection}", headers=headers)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)
print(f"points_count={data.get('result', {}).get('points_count', 0)}")
PY

log "Redis buffer length after rebuild"
redis-cli -h "${REDIS_HOST:-127.0.0.1}" -p "${REDIS_PORT:-6379}" LLEN "mem:${USER_ID}"

log "Rebuild complete"
