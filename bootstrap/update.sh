#!/usr/bin/env bash
# update.sh — Non-destructive in-place update of an existing Jarvis Memory deployment
#
# Preserves all secrets and custom settings (USER_ID, QDRANT_API_KEY, OLLAMA_URL, etc.)
# Only updates: Python scripts, config files, .memory_env content, cron block
# Does NOT touch: Docker containers, Qdrant data, Redis data, system packages, Ollama models
#
# One-liner usage:
#   cd ~/jarvismemory && git pull && sudo bash bootstrap/update.sh
#
# With custom user/path:
#   OPENCLAW_USER=myuser sudo bash bootstrap/update.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OPENCLAW_USER="${OPENCLAW_USER:-openclaw}"
OPENCLAW_HOME="${OPENCLAW_HOME:-/home/${OPENCLAW_USER}}"
ENV_FILE="${OPENCLAW_HOME}/.memory_env"

log()  { printf '[update] %s\n' "$*"; }
die()  { printf '[update] ERROR: %s\n' "$*" >&2; exit 1; }

# ── Guard: existing deployment must be present ────────────────────────────
if [[ ! -f "${ENV_FILE}" ]]; then
  die "No existing deployment found at ${ENV_FILE}.
       For a fresh install run: sudo bash bootstrap/bootstrap.sh"
fi

log "Found existing deployment: ${ENV_FILE}"

# ── Load all current settings to preserve them ───────────────────────────
# set -a exports every variable that gets defined/set, so sourcing .memory_env
# exports USER_ID, QDRANT_API_KEY, OLLAMA_URL, etc. into the environment.
# bootstrap.sh reads all of these from env vars, so write_memory_env() will
# write them back unchanged.
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

log "Loaded settings from ${ENV_FILE}"
log "  USER_ID         = ${USER_ID:-<not set>}"
log "  QDRANT_URL      = ${QDRANT_URL:-<not set>}"
log "  OLLAMA_URL      = ${OLLAMA_URL:-<not set>}"
log "  EMBEDDING_MODEL = ${EMBEDDING_MODEL:-<not set>}"
if [[ -n "${QDRANT_API_KEY:-}" ]]; then
  log "  QDRANT_API_KEY  = (set)"
else
  log "  QDRANT_API_KEY  = (not set)"
fi

[[ -n "${USER_ID:-}" ]] || die "USER_ID is empty in ${ENV_FILE} — cannot update safely."

# ── Source bootstrap.sh to load function definitions ─────────────────────
# The BASH_SOURCE guard at the bottom of bootstrap.sh prevents main() from
# running when the file is sourced rather than executed directly.
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/bootstrap.sh"

# ── Run only the safe update steps ───────────────────────────────────────
log "Checking root"
require_root

log "Preparing paths"
prepare_paths

log "Syncing workspace scripts (backup created first)"
sync_workspace

log "Regenerating environment files (secrets preserved)"
write_memory_env

log "Regenerating cron block"
configure_cron

log "Running audit"
OPENCLAW_USER="${OPENCLAW_USER}" \
OPENCLAW_HOME="${OPENCLAW_HOME}" \
WORKSPACE_DIR="${WORKSPACE_DIR}" \
  "${SCRIPT_DIR}/audit.sh"

echo
log "================================================================"
log " Update complete — no containers were restarted, no data lost."
log " Scripts updated from: $(git -C "${SCRIPT_DIR}/.." log -1 --format='%h %s' 2>/dev/null || echo 'unknown')"
log "================================================================"
