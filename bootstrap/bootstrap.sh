#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

OPENCLAW_USER="${OPENCLAW_USER:-openclaw}"
TIMEZONE="${TIMEZONE:-America/Los_Angeles}"
USER_ID="${USER_ID:-}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-mxbai-embed-large}"
DEFAULT_CURATION_MODEL="${DEFAULT_CURATION_MODEL:-qwen3.5:35b-a3b}"
CURATION_MODEL="${CURATION_MODEL:-${DEFAULT_CURATION_MODEL}}"
CURATION_TIMEOUT_SECONDS="${CURATION_TIMEOUT_SECONDS:-1200}"
CURATION_NUM_PREDICT="${CURATION_NUM_PREDICT:-1200}"
OPENCLAW_MEMORYSEARCH_MODEL="${OPENCLAW_MEMORYSEARCH_MODEL:-qwen3-embedding:4b}"
OPENCLAW_HOME="${OPENCLAW_HOME:-/home/${OPENCLAW_USER}}"
SERVICE_OPENCLAW_USER="${SERVICE_OPENCLAW_USER:-openclaw-svc}"
SERVICE_OPENCLAW_HOME="${SERVICE_OPENCLAW_HOME:-/var/lib/${SERVICE_OPENCLAW_USER}}"
WORKSPACE_DIR="${WORKSPACE_DIR:-${OPENCLAW_HOME}/.openclaw/workspace}"
SESSIONS_DIR="${SESSIONS_DIR:-${OPENCLAW_HOME}/.openclaw/agents/main/sessions}"
SERVICE_WORKSPACE_DIR="${SERVICE_WORKSPACE_DIR:-${SERVICE_OPENCLAW_HOME}/.openclaw/workspace}"
SERVICE_SESSIONS_DIR="${SERVICE_SESSIONS_DIR:-${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main/sessions}"
PROJECT_DIR="${WORKSPACE_DIR}/.projects/true-recall"
MEM_ENV_HOME="${OPENCLAW_HOME}/.memory_env"
MEM_ENV_WORKSPACE="${WORKSPACE_DIR}/.memory_env"
BACKUP_DIR="${WORKSPACE_DIR}/.backups/bootstrap_$(date +%Y%m%d_%H%M%S)"
PYTHON_BIN="${WORKSPACE_DIR}/.venv/bin/python"
PIP_BIN="${WORKSPACE_DIR}/.venv/bin/pip"
CRON_CAPTURE_SCHEDULE="${CRON_CAPTURE_SCHEDULE:-*/5 * * * *}"
TR_SCHEDULE="${TR_SCHEDULE:-30 10 * * *}"
BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-0 11 * * *}"
SLIDING_SCHEDULE="${SLIDING_SCHEDULE:-30 11 * * *}"
OPENCLAW_PLUGIN_SOURCE_REL="${OPENCLAW_PLUGIN_SOURCE_REL:-plugins/memory-qdrant}"

log() { printf '[bootstrap] %s\n' "$*"; }
die() { printf '[bootstrap] ERROR: %s\n' "$*" >&2; exit 1; }

run_as_openclaw() {
  su - "${OPENCLAW_USER}" -c "$*"
}

resolve_openclaw_bin() {
  if command -v openclaw >/dev/null 2>&1; then
    command -v openclaw
    return 0
  fi
  if [[ -x "${OPENCLAW_HOME}/.npm-global/bin/openclaw" ]]; then
    printf '%s\n' "${OPENCLAW_HOME}/.npm-global/bin/openclaw"
    return 0
  fi
  return 1
}

run_openclaw_cli_for_runtime() {
  local runtime_user="$1"
  local runtime_home="$2"
  local runtime_workspace="$3"
  local cli_args="$4"
  local openclaw_bin

  openclaw_bin="$(resolve_openclaw_bin)" || die "openclaw binary not found"
  su -s /bin/bash "${runtime_user}" -c \
    "env HOME='${runtime_home}' XDG_CONFIG_HOME='${runtime_home}/.config' OPENCLAW_WORKSPACE='${runtime_workspace}' '${openclaw_bin}' ${cli_args}"
}

has_service_runtime() {
  id "${SERVICE_OPENCLAW_USER}" >/dev/null 2>&1 && [[ -d "${SERVICE_OPENCLAW_HOME}/.openclaw" ]]
}

is_legacy_default_curation_model() {
  case "${1:-}" in
    qwen3:14b)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

normalize_curation_model() {
  if [[ -z "${CURATION_MODEL:-}" ]]; then
    CURATION_MODEL="${DEFAULT_CURATION_MODEL}"
    return 0
  fi

  if is_legacy_default_curation_model "${CURATION_MODEL}"; then
    log "Replacing temporary curator fallback ${CURATION_MODEL} with ${DEFAULT_CURATION_MODEL}"
    CURATION_MODEL="${DEFAULT_CURATION_MODEL}"
  fi
}

build_memory_env() {
  local workspace_dir="$1"
  local sessions_dir="$2"
  local home_sessions_dir="${3:-$2}"
  local service_sessions_dir="${4:-}"
  local preferred_sessions_dir="${sessions_dir}"

  if [[ -n "${service_sessions_dir}" ]]; then
    preferred_sessions_dir="${service_sessions_dir}"
  fi
  cat <<EOF
export WORKSPACE_DIR="${workspace_dir}"
export OPENCLAW_WORKSPACE="${workspace_dir}"
export OPENCLAW_SESSIONS_DIR="${preferred_sessions_dir}"
export OPENCLAW_HOME_SESSIONS_DIR="${home_sessions_dir}"
export OPENCLAW_SERVICE_SESSIONS_DIR="${service_sessions_dir}"

export USER_ID="${USER_ID}"

export REDIS_HOST="127.0.0.1"
export REDIS_PORT="6379"

export QDRANT_URL="http://127.0.0.1:6333"
export QDRANT_COLLECTION="kimi_memories"
export TR_COLLECTION="true_recall"

export OLLAMA_URL="http://127.0.0.1:11434"
export EMBEDDING_MODEL="${EMBEDDING_MODEL}"
export CURATION_MODEL="${CURATION_MODEL}"
export CURATION_TIMEOUT_SECONDS="${CURATION_TIMEOUT_SECONDS}"
export CURATION_NUM_PREDICT="${CURATION_NUM_PREDICT}"

export MEMORY_INITIALIZED="true"
export NO_PROXY="127.0.0.1,localhost,10.0.0.0/8"
export no_proxy="127.0.0.1,localhost,10.0.0.0/8"

if [ -f /run/openclaw-memory/secrets.env ]; then
  . /run/openclaw-memory/secrets.env
  export QDRANT_API_KEY
fi
EOF
}

sync_repo_workspace() {
  local target_workspace="$1"
  local owner="$2"

  install -d -o "$owner" -g "$owner" "$target_workspace"
  install -d -o "$owner" -g "$owner" "$target_workspace/skills"
  install -d -o "$owner" -g "$owner" "$target_workspace/docs"
  install -d -o "$owner" -g "$owner" "$target_workspace/config"
  install -d -o "$owner" -g "$owner" "$target_workspace/.projects"
  install -d -o "$owner" -g "$owner" "$target_workspace/memory"
  install -d -o "$owner" -g "$owner" "$target_workspace/plugins"

  rsync -a "${REPO_ROOT}/workspace/skills/" "$target_workspace/skills/"
  rsync -a "${REPO_ROOT}/workspace/docs/" "$target_workspace/docs/"
  rsync -a "${REPO_ROOT}/workspace/config/" "$target_workspace/config/"
  rsync -a "${REPO_ROOT}/workspace/.projects/true-recall/" "$target_workspace/.projects/true-recall/"
  rsync -a "${REPO_ROOT}/workspace/plugins/" "$target_workspace/plugins/"
  install -m 0644 "${REPO_ROOT}/workspace/HEARTBEAT.md" "$target_workspace/HEARTBEAT.md"
  chmod +x "$target_workspace/skills/qdrant-memory/scripts/sliding_backup.sh"
  chown -R "$owner:$owner" "$target_workspace/skills" "$target_workspace/docs" "$target_workspace/config" "$target_workspace/.projects" "$target_workspace/plugins" "$target_workspace/HEARTBEAT.md"
}

prompt_if_missing() {
  local var_name="$1"
  local prompt_text="$2"
  local default_value="${3:-}"
  local current_value="${!var_name:-}"

  if [[ -n "${current_value}" ]]; then
    return 0
  fi

  if [[ ! -t 0 ]]; then
    die "${var_name} is required in non-interactive mode"
  fi

  if [[ -n "${default_value}" ]]; then
    read -r -p "${prompt_text} [${default_value}]: " current_value
    current_value="${current_value:-${default_value}}"
  else
    read -r -p "${prompt_text}: " current_value
  fi

  [[ -n "${current_value}" ]] || die "${var_name} cannot be empty"
  printf -v "${var_name}" '%s' "${current_value}"
}

require_root() {
  [[ "$(id -u)" -eq 0 ]] || die "Please run this script as root or with sudo"
}

install_host_deps() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg lsb-release rsync redis-tools python3 python3-pip python3-venv acl

  if ! command -v docker >/dev/null 2>&1; then
    apt-get install -y docker.io docker-compose-v2 || apt-get install -y docker.io docker-compose-plugin
  fi

  systemctl enable --now docker
  usermod -aG docker "${OPENCLAW_USER}" || true

  if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
  fi

  systemctl enable --now ollama
}

prepare_paths() {
  id "${OPENCLAW_USER}" >/dev/null 2>&1 || die "User ${OPENCLAW_USER} does not exist"
  [[ -d "${OPENCLAW_HOME}/.openclaw" ]] || die "OpenClaw home not found at ${OPENCLAW_HOME}/.openclaw"
  [[ -d "${SESSIONS_DIR}" ]] || die "OpenClaw sessions dir not found at ${SESSIONS_DIR}"

  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${WORKSPACE_DIR}"
  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${WORKSPACE_DIR}/skills"
  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${WORKSPACE_DIR}/docs"
  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${WORKSPACE_DIR}/config"
  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${WORKSPACE_DIR}/memory"
  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${WORKSPACE_DIR}/.projects"
  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${WORKSPACE_DIR}/.backups"
  install -d -o "${OPENCLAW_USER}" -g "${OPENCLAW_USER}" "${BACKUP_DIR}"
}

backup_if_exists() {
  local target="$1"
  if [[ -e "${target}" ]]; then
    local rel="${target#/}"
    local dest="${BACKUP_DIR}/${rel//\//__}"
    cp -a "${target}" "${dest}"
  fi
}

write_memory_env() {
  local env_body
  local service_sessions_dir=""
  if has_service_runtime; then
    service_sessions_dir="${SERVICE_SESSIONS_DIR}"
  fi
  env_body=$(build_memory_env "${WORKSPACE_DIR}" "${SESSIONS_DIR}" "${SESSIONS_DIR}" "${service_sessions_dir}")

  printf '%s\n' "${env_body}" > "${MEM_ENV_HOME}"
  printf '%s\n' "${env_body}" > "${MEM_ENV_WORKSPACE}"
  chown "${OPENCLAW_USER}:${OPENCLAW_USER}" "${MEM_ENV_HOME}" "${MEM_ENV_WORKSPACE}"
  chmod 600 "${MEM_ENV_HOME}" "${MEM_ENV_WORKSPACE}"

  if has_service_runtime; then
    local mem_env_service_workspace="${SERVICE_WORKSPACE_DIR}/.memory_env"
    local svc_env_body
    svc_env_body=$(build_memory_env "${SERVICE_WORKSPACE_DIR}" "${SERVICE_SESSIONS_DIR}" "${SESSIONS_DIR}" "${SERVICE_SESSIONS_DIR}")
    printf '%s\n' "${svc_env_body}" > "${mem_env_service_workspace}"
    chown "${SERVICE_OPENCLAW_USER}:${SERVICE_OPENCLAW_USER}" "${mem_env_service_workspace}"
    chmod 600 "${mem_env_service_workspace}"
  fi

  if ! grep -Fq 'source ~/.memory_env' "${OPENCLAW_HOME}/.bashrc"; then
    printf '\n# Jarvis Memory\nsource ~/.memory_env\n' >> "${OPENCLAW_HOME}/.bashrc"
  fi
}

# Configure OpenClaw's built-in memory_search to use local Ollama.
# This avoids iptables/proxy conflicts under CodeShield (external APIs
# are blocked by iptables for openclaw-svc; SSRF guard bypasses proxy).
configure_openclaw_memorysearch() {
  local OPENCLAW_MEMORYSEARCH_MODEL="${OPENCLAW_MEMORYSEARCH_MODEL:-qwen3-embedding:4b}"
  local openclaw_bin

  # Find openclaw binary
  openclaw_bin="$(su - "${OPENCLAW_USER}" -c 'which openclaw' 2>/dev/null || true)"
  if [[ -z "${openclaw_bin}" ]]; then
    log "WARN: openclaw binary not found; skipping memorySearch config"
    return 0
  fi

  # Pull embedding model if not present
  if ! ollama list 2>/dev/null | grep -q "${OPENCLAW_MEMORYSEARCH_MODEL}"; then
    log "Pulling Ollama model: ${OPENCLAW_MEMORYSEARCH_MODEL}"
    ollama pull "${OPENCLAW_MEMORYSEARCH_MODEL}" || {
      log "WARN: failed to pull ${OPENCLAW_MEMORYSEARCH_MODEL}; skipping memorySearch config"
      return 0
    }
  fi

  # Set memorySearch provider and model for the interactive user
  su - "${OPENCLAW_USER}" -c "openclaw config set agents.defaults.memorySearch.provider ollama" 2>/dev/null || true
  su - "${OPENCLAW_USER}" -c "openclaw config set agents.defaults.memorySearch.model '${OPENCLAW_MEMORYSEARCH_MODEL}'" 2>/dev/null || true

  # Also set for the service user if it exists
  local svc_user="openclaw-svc"
  if id "${svc_user}" >/dev/null 2>&1; then
    su -s /bin/bash "${svc_user}" -c "openclaw config set agents.defaults.memorySearch.provider ollama" 2>/dev/null || true
    su -s /bin/bash "${svc_user}" -c "openclaw config set agents.defaults.memorySearch.model '${OPENCLAW_MEMORYSEARCH_MODEL}'" 2>/dev/null || true
  fi

  log "OpenClaw memorySearch configured: provider=ollama model=${OPENCLAW_MEMORYSEARCH_MODEL}"
}

openclaw_json_paths() {
  printf '%s\n' "${OPENCLAW_HOME}/.openclaw/openclaw.json"
  if has_service_runtime; then
    printf '%s\n' "${SERVICE_OPENCLAW_HOME}/.openclaw/openclaw.json"
  fi
}

install_openclaw_true_recall_plugin() {
  local runtime_user="$1"
  local runtime_home="$2"
  local runtime_workspace="$3"
  local plugin_source="${runtime_workspace}/${OPENCLAW_PLUGIN_SOURCE_REL}"
  local output

  [[ -d "${plugin_source}" ]] || die "Plugin source not found at ${plugin_source}"

  if ! output="$(run_openclaw_cli_for_runtime "${runtime_user}" "${runtime_home}" "${runtime_workspace}" "plugins install '${plugin_source}'" 2>&1)"; then
    case "${output}" in
      *"already installed"*|*"is already installed"*)
        log "OpenClaw plugin memory-qdrant already installed for ${runtime_user}"
        ;;
      *)
        printf '%s\n' "${output}" >&2
        die "Failed to install memory-qdrant plugin for ${runtime_user}"
        ;;
    esac
  fi

  run_openclaw_cli_for_runtime "${runtime_user}" "${runtime_home}" "${runtime_workspace}" "plugins enable memory-qdrant" >/dev/null 2>&1 || true
}

install_openclaw_true_recall_plugins() {
  install_openclaw_true_recall_plugin "${OPENCLAW_USER}" "${OPENCLAW_HOME}" "${WORKSPACE_DIR}"
  if has_service_runtime; then
    install_openclaw_true_recall_plugin "${SERVICE_OPENCLAW_USER}" "${SERVICE_OPENCLAW_HOME}" "${SERVICE_WORKSPACE_DIR}"
  fi
}

configure_openclaw_true_recall() {
  local json_file owner workspace_path
  while IFS= read -r json_file; do
    [ -n "${json_file}" ] || continue
    owner="${OPENCLAW_USER}"
    workspace_path="${WORKSPACE_DIR}"
    if [[ "${json_file}" == "${SERVICE_OPENCLAW_HOME}/.openclaw/openclaw.json" ]]; then
      owner="${SERVICE_OPENCLAW_USER}"
      workspace_path="${SERVICE_WORKSPACE_DIR}"
    fi

    install -d -o "${owner}" -g "${owner}" "$(dirname "${json_file}")"

    EMBEDDING_MODEL="${EMBEDDING_MODEL}" \
    OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}" \
    QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}" \
    TR_COLLECTION="${TR_COLLECTION:-true_recall}" \
    python3 - "${json_file}" "${workspace_path}" <<'PY'
import json
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
workspace_path = sys.argv[2]
cfg = {}
if path.exists():
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cfg = {}

agents = cfg.setdefault("agents", {}).setdefault("defaults", {})
agents["workspace"] = workspace_path

plugins = cfg.setdefault('plugins', {})
entries = plugins.setdefault('entries', {})
plugin = entries.setdefault('memory-qdrant', {})
plugin['enabled'] = True
plugin['config'] = {
    'qdrantUrl': os.environ.get('QDRANT_URL', 'http://127.0.0.1:6333'),
    'collectionName': os.environ.get('TR_COLLECTION', 'true_recall'),
    'ollamaUrl': os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434'),
    'embeddingModel': os.environ.get('EMBEDDING_MODEL', 'mxbai-embed-large'),
    'userId': os.environ.get('USER_ID', ''),
    'autoRecall': True,
    'autoCapture': False,
    'maxRecallResults': 3,
    'minRecallScore': 0.5,
}

path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

    chown "${owner}:${owner}" "${json_file}"
    chmod 0600 "${json_file}"
  done < <(openclaw_json_paths)

  log "OpenClaw True Recall auto-recall configured: collection=${TR_COLLECTION:-true_recall} model=${EMBEDDING_MODEL}"
}

sync_workspace() {
  backup_if_exists "${WORKSPACE_DIR}/skills/mem-redis"
  backup_if_exists "${WORKSPACE_DIR}/skills/qdrant-memory"
  backup_if_exists "${WORKSPACE_DIR}/plugins/memory-qdrant"
  backup_if_exists "${PROJECT_DIR}"
  backup_if_exists "${WORKSPACE_DIR}/HEARTBEAT.md"
  backup_if_exists "${WORKSPACE_DIR}/config/HEARTBEAT.md"
  backup_if_exists "${WORKSPACE_DIR}/docs/MEM_DIAGRAM.md"

  sync_repo_workspace "${WORKSPACE_DIR}" "${OPENCLAW_USER}"

  if has_service_runtime; then
    sync_repo_workspace "${SERVICE_WORKSPACE_DIR}" "${SERVICE_OPENCLAW_USER}"
  fi
}

setup_python() {
  if [[ ! -x "${PYTHON_BIN}" ]]; then
    run_as_openclaw "python3 -m venv '${WORKSPACE_DIR}/.venv'"
  fi
  run_as_openclaw "\"${PIP_BIN}\" install --upgrade pip setuptools wheel"
  run_as_openclaw "\"${PIP_BIN}\" install -r \"${REPO_ROOT}/requirements.txt\" pyyaml"
}

ensure_models() {
  local model
  for model in "${EMBEDDING_MODEL}" "${CURATION_MODEL}"; do
    if ! ollama list 2>/dev/null | awk '{print $1}' | grep -Eq "^${model}(:latest)?$"; then
      log "Pulling Ollama model ${model}"
      ollama pull "${model}"
    fi
  done
}

start_stack() {
  docker compose -p jarvis-memory -f "${REPO_ROOT}/docker-compose.yml" up -d
}

init_qdrant() {
  export QDRANT_URL="http://127.0.0.1:6333"
  export QDRANT_COLLECTION="kimi_memories"
  export TR_COLLECTION="true_recall"

  "${PYTHON_BIN}" - <<'PY'
import os
import requests

base = os.environ["QDRANT_URL"]
collections = [
    os.environ.get("QDRANT_COLLECTION", "kimi_memories"),
    os.environ.get("TR_COLLECTION", "true_recall"),
]

for name in collections:
    check = requests.get(f"{base}/collections/{name}", timeout=10)
    if check.status_code == 200:
        print(f"collection ready: {name}")
        continue
    response = requests.put(
        f"{base}/collections/{name}",
        json={"vectors": {"size": 1024, "distance": "Cosine"}},
        timeout=15,
    )
    response.raise_for_status()
    print(f"collection created: {name}")
PY
}

configure_timezone() {
  timedatectl set-timezone "${TIMEZONE}"
}

configure_logs() {
  touch /var/log/memory-capture.log /var/log/memory-backup.log /var/log/true-recall-curator.log /var/log/qdrant-daily-backup.log
  chown "${OPENCLAW_USER}:${OPENCLAW_USER}" /var/log/memory-capture.log /var/log/memory-backup.log /var/log/true-recall-curator.log /var/log/qdrant-daily-backup.log
}

configure_service_session_access() {
  has_service_runtime || return 0

  if ! command -v setfacl >/dev/null 2>&1; then
    log "WARN: setfacl not available; cannot grant ${OPENCLAW_USER} read-only access to service sessions"
    return 0
  fi

  local traverse_paths=(
    "${SERVICE_OPENCLAW_HOME}"
    "${SERVICE_OPENCLAW_HOME}/.openclaw"
    "${SERVICE_OPENCLAW_HOME}/.openclaw/agents"
    "${SERVICE_OPENCLAW_HOME}/.openclaw/agents/main"
  )

  local path
  for path in "${traverse_paths[@]}"; do
    [[ -d "${path}" ]] || continue
    setfacl -m "u:${OPENCLAW_USER}:x" "${path}"
  done

  if [[ -d "${SERVICE_SESSIONS_DIR}" ]]; then
    setfacl -m "u:${OPENCLAW_USER}:rx" "${SERVICE_SESSIONS_DIR}"
    setfacl -d -m "u:${OPENCLAW_USER}:rx" "${SERVICE_SESSIONS_DIR}"
    find "${SERVICE_SESSIONS_DIR}" -maxdepth 1 -type f \( -name '*.jsonl' -o -name 'sessions.json' \) -exec setfacl -m "u:${OPENCLAW_USER}:r" {} +
  fi
}

configure_cron() {
  local tmpfile
  tmpfile="$(mktemp)"
  crontab -l -u "${OPENCLAW_USER}" > "${tmpfile}" 2>/dev/null || true

  python3 - "${tmpfile}" "${OPENCLAW_HOME}" "${WORKSPACE_DIR}" "${PYTHON_BIN}" "${CRON_CAPTURE_SCHEDULE}" "${TR_SCHEDULE}" "${BACKUP_SCHEDULE}" "${SLIDING_SCHEDULE}" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
home = sys.argv[2]
workspace = sys.argv[3]
python_bin = sys.argv[4]
capture = sys.argv[5]
curate = sys.argv[6]
backup = sys.argv[7]
sliding = sys.argv[8]
start = "# >>> jarvismemory managed block >>>"
end = "# <<< jarvismemory managed block <<<"

existing = path.read_text() if path.exists() else ""
lines = existing.splitlines()
kept = []
inside = False
legacy_tokens = ("cron_capture.py", "cron_backup.py", "sliding_backup.sh", "curate_memories.py")
for line in lines:
    stripped = line.strip()
    if stripped == start:
        inside = True
        continue
    if stripped == end:
        inside = False
        continue
    if inside:
        continue
    if any(token in line for token in legacy_tokens):
        continue
    kept.append(line)

block = [
    start,
    "SHELL=/bin/bash",
    f"{capture} source {home}/.memory_env && cd {workspace} && {python_bin} {workspace}/skills/mem-redis/scripts/cron_capture.py --user-id $USER_ID >> /var/log/memory-capture.log 2>&1",
    f"{curate} source {home}/.memory_env && cd {workspace}/.projects/true-recall && {python_bin} {workspace}/.projects/true-recall/tr-process/curate_memories.py --user-id $USER_ID >> /var/log/true-recall-curator.log 2>&1",
    f"{backup} source {home}/.memory_env && cd {workspace} && {python_bin} {workspace}/skills/mem-redis/scripts/cron_backup.py --user-id $USER_ID >> /var/log/memory-backup.log 2>&1",
    f"{sliding} source {home}/.memory_env && /bin/bash {workspace}/skills/qdrant-memory/scripts/sliding_backup.sh >> /var/log/memory-backup.log 2>&1",
    end,
]

new_text = "\n".join([line for line in kept if line.strip()] + [""] + block + [""])
path.write_text(new_text)
PY

  crontab -u "${OPENCLAW_USER}" "${tmpfile}"
  rm -f "${tmpfile}"
}

main() {
  require_root
  prompt_if_missing USER_ID "Enter the memory USER_ID"
  prompt_if_missing TIMEZONE "Enter the system timezone" "${TIMEZONE}"

  log "Installing host dependencies"
  install_host_deps

  log "Preparing target paths"
  prepare_paths

  log "Starting Docker stack"
  start_stack

  log "Syncing workspace files"
  sync_workspace

  log "Installing Python dependencies"
  setup_python

  log "Writing environment files"
  normalize_curation_model
  write_memory_env

  log "Ensuring Ollama models"
  ensure_models

  log "Initializing Qdrant collections"
  init_qdrant

  log "Configuring timezone"
  configure_timezone

  log "Configuring logs"
  configure_logs

  log "Granting read-only access to service sessions"
  configure_service_session_access

  log "Configuring cron"
  configure_cron

  log "Configuring OpenClaw memorySearch (local Ollama)"
  configure_openclaw_memorysearch

  log "Installing OpenClaw True Recall plugin"
  install_openclaw_true_recall_plugins

  log "Configuring OpenClaw True Recall auto-recall"
  configure_openclaw_true_recall

  log "Running final audit"
  OPENCLAW_USER="${OPENCLAW_USER}" OPENCLAW_HOME="${OPENCLAW_HOME}" WORKSPACE_DIR="${WORKSPACE_DIR}" "${SCRIPT_DIR}/audit.sh"
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
