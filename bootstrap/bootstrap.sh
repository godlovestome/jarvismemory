#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

OPENCLAW_USER="${OPENCLAW_USER:-openclaw}"
TIMEZONE="${TIMEZONE:-America/Los_Angeles}"
USER_ID="${USER_ID:-}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-mxbai-embed-large}"
CURATION_MODEL="${CURATION_MODEL:-qwen3.5:35b-a3b}"
OPENCLAW_HOME="${OPENCLAW_HOME:-/home/${OPENCLAW_USER}}"
WORKSPACE_DIR="${WORKSPACE_DIR:-${OPENCLAW_HOME}/.openclaw/workspace}"
SESSIONS_DIR="${SESSIONS_DIR:-${OPENCLAW_HOME}/.openclaw/agents/main/sessions}"
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

log() { printf '[bootstrap] %s\n' "$*"; }
die() { printf '[bootstrap] ERROR: %s\n' "$*" >&2; exit 1; }

run_as_openclaw() {
  su - "${OPENCLAW_USER}" -c "$*"
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
  apt-get install -y ca-certificates curl gnupg lsb-release rsync redis-tools python3 python3-pip python3-venv

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
  env_body=$(cat <<EOF
export WORKSPACE_DIR="${WORKSPACE_DIR}"
export OPENCLAW_WORKSPACE="${WORKSPACE_DIR}"
export OPENCLAW_SESSIONS_DIR="${SESSIONS_DIR}"

export USER_ID="${USER_ID}"

export REDIS_HOST="127.0.0.1"
export REDIS_PORT="6379"

export QDRANT_URL="http://127.0.0.1:6333"
export QDRANT_COLLECTION="kimi_memories"
export TR_COLLECTION="true_recall"

export OLLAMA_URL="http://127.0.0.1:11434"
export EMBEDDING_MODEL="${EMBEDDING_MODEL}"
export CURATION_MODEL="${CURATION_MODEL}"

export MEMORY_INITIALIZED="true"
EOF
)

  printf '%s\n' "${env_body}" > "${MEM_ENV_HOME}"
  printf '%s\n' "${env_body}" > "${MEM_ENV_WORKSPACE}"
  chown "${OPENCLAW_USER}:${OPENCLAW_USER}" "${MEM_ENV_HOME}" "${MEM_ENV_WORKSPACE}"

  if ! grep -Fq 'source ~/.memory_env' "${OPENCLAW_HOME}/.bashrc"; then
    printf '\n# Jarvis Memory\nsource ~/.memory_env\n' >> "${OPENCLAW_HOME}/.bashrc"
  fi
}

sync_workspace() {
  backup_if_exists "${WORKSPACE_DIR}/skills/mem-redis"
  backup_if_exists "${WORKSPACE_DIR}/skills/qdrant-memory"
  backup_if_exists "${PROJECT_DIR}"
  backup_if_exists "${WORKSPACE_DIR}/HEARTBEAT.md"
  backup_if_exists "${WORKSPACE_DIR}/config/HEARTBEAT.md"
  backup_if_exists "${WORKSPACE_DIR}/docs/MEM_DIAGRAM.md"

  rsync -a "${REPO_ROOT}/workspace/skills/" "${WORKSPACE_DIR}/skills/"
  rsync -a "${REPO_ROOT}/workspace/docs/" "${WORKSPACE_DIR}/docs/"
  rsync -a "${REPO_ROOT}/workspace/config/" "${WORKSPACE_DIR}/config/"
  rsync -a "${REPO_ROOT}/workspace/.projects/true-recall/" "${WORKSPACE_DIR}/.projects/true-recall/"
  install -m 0644 "${REPO_ROOT}/workspace/HEARTBEAT.md" "${WORKSPACE_DIR}/HEARTBEAT.md"
  chmod +x "${WORKSPACE_DIR}/skills/qdrant-memory/scripts/sliding_backup.sh"
  chown -R "${OPENCLAW_USER}:${OPENCLAW_USER}" "${WORKSPACE_DIR}/skills" "${WORKSPACE_DIR}/docs" "${WORKSPACE_DIR}/config" "${WORKSPACE_DIR}/.projects" "${WORKSPACE_DIR}/HEARTBEAT.md"
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
    f"{sliding} source {home}/.memory_env && {workspace}/skills/qdrant-memory/scripts/sliding_backup.sh >> /var/log/memory-backup.log 2>&1",
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
  write_memory_env

  log "Ensuring Ollama models"
  ensure_models

  log "Initializing Qdrant collections"
  init_qdrant

  log "Configuring timezone"
  configure_timezone

  log "Configuring logs"
  configure_logs

  log "Configuring cron"
  configure_cron

  log "Running final audit"
  OPENCLAW_USER="${OPENCLAW_USER}" OPENCLAW_HOME="${OPENCLAW_HOME}" WORKSPACE_DIR="${WORKSPACE_DIR}" "${SCRIPT_DIR}/audit.sh"
}

main "$@"
