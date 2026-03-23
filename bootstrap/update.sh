#!/usr/bin/env bash
# update.sh - Non-destructive in-place update of an existing Jarvis Memory deployment
#
# Preserves user settings and existing data while refreshing the managed workspace files,
# cron block, and generated .memory_env files.
#
# CodeShield-managed secrets stay outside .memory_env and continue to be sourced at runtime
# from the protected /run/openclaw-memory/secrets.env path.
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

if [[ ! -f "${ENV_FILE}" ]]; then
  die "No existing deployment found at ${ENV_FILE}.
       For a fresh install run: sudo bash bootstrap/bootstrap.sh"
fi

log "Found existing deployment: ${ENV_FILE}"

# Load current runtime values so the regenerated .memory_env keeps the same
# workspace, URLs, models, and user id. If CodeShield is present, the sourced
# file will continue to load protected secrets from /run/openclaw-memory/secrets.env.
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
  log "  QDRANT_API_KEY  = (available via runtime env)"
else
  log "  QDRANT_API_KEY  = (not set)"
fi

[[ -n "${USER_ID:-}" ]] || die "USER_ID is empty in ${ENV_FILE} - cannot update safely."

# shellcheck disable=SC1091
source "${SCRIPT_DIR}/bootstrap.sh"

log "Checking root"
require_root

log "Preparing paths"
prepare_paths

log "Syncing workspace scripts (backup created first)"
sync_workspace

log "Regenerating environment files (CodeShield secret source preserved)"
write_memory_env

log "Refreshing read-only access to CodeShield service sessions"
configure_service_session_access

log "Regenerating cron block"
configure_cron

log "Running audit"
OPENCLAW_USER="${OPENCLAW_USER}" \
OPENCLAW_HOME="${OPENCLAW_HOME}" \
WORKSPACE_DIR="${WORKSPACE_DIR}" \
  "${SCRIPT_DIR}/audit.sh"

echo
log "================================================================"
log "Update complete - no containers were restarted and no data was removed."
log "Scripts updated from: $(git -C "${SCRIPT_DIR}/.." log -1 --format='%h %s' 2>/dev/null || echo 'unknown')"
log "================================================================"
