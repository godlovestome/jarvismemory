#!/usr/bin/env bash
# diagnose.sh — Troubleshoot memory_search / embedding provider fetch errors
#
# Run this when the Jarvis agent reports:
#   "memory_search failed: embedding/provider fetch error"
#   "memory semantic recall unavailable"
#
# Usage: bash bootstrap/diagnose.sh

set -uo pipefail

OPENCLAW_USER="${OPENCLAW_USER:-openclaw}"
OPENCLAW_HOME="${OPENCLAW_HOME:-/home/${OPENCLAW_USER}}"
ENV_FILE="${OPENCLAW_HOME}/.memory_env"

if [[ -f "${ENV_FILE}" ]]; then
  export HOME="${OPENCLAW_HOME}"
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-mxbai-embed-large}"
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"

PASS="[PASS]"
FAIL="[FAIL]"
WARN="[WARN]"

echo "=============================================="
echo " Jarvis Memory — Embedding/Provider Diagnosis"
echo "=============================================="
echo "Date: $(date)"
echo

# ── 1. Proxy environment ───────────────────────────────────────────────────
echo "--- 1. Proxy environment ---"

http_proxy_val="${HTTP_PROXY:-${http_proxy:-}}"
https_proxy_val="${HTTPS_PROXY:-${https_proxy:-}}"
no_proxy_val="${NO_PROXY:-${no_proxy:-}}"

if [[ -n "${http_proxy_val}" ]] || [[ -n "${https_proxy_val}" ]]; then
  echo "${WARN} Proxy is active: HTTP_PROXY='${http_proxy_val}' HTTPS_PROXY='${https_proxy_val}'"
  if [[ -z "${no_proxy_val}" ]]; then
    echo "${FAIL} NO_PROXY is not set — Ollama/Qdrant calls will go through the proxy."
    echo "      Fix: add to .memory_env:"
    echo "        export NO_PROXY='127.0.0.1,localhost,10.0.0.0/8'"
    echo "        export no_proxy='127.0.0.1,localhost,10.0.0.0/8'"
  else
    echo "${PASS} NO_PROXY='${no_proxy_val}'"
    # Check that Ollama/Qdrant hosts are covered
    ollama_host="$(echo "${OLLAMA_URL}" | sed 's|https\?://||;s|/.*||;s|:.*||')"
    qdrant_host="$(echo "${QDRANT_URL}" | sed 's|https\?://||;s|/.*||;s|:.*||')"
    for host in "${ollama_host}" "${qdrant_host}"; do
      if echo "${no_proxy_val}" | grep -qE "(^|,)\s*${host}\s*(,|$)|10\.0\.0\.0/8|0\.0\.0\.0/0"; then
        echo "${PASS} Host ${host} is covered by NO_PROXY"
      else
        echo "${FAIL} Host ${host} is NOT covered by NO_PROXY — calls will go through proxy"
        echo "      Fix: add ${host} to NO_PROXY in .memory_env"
      fi
    done
  fi
else
  echo "${PASS} No proxy configured (HTTP_PROXY / HTTPS_PROXY not set)"
fi
echo

# ── 2. Ollama service ──────────────────────────────────────────────────────
echo "--- 2. Ollama service (${OLLAMA_URL}) ---"

ollama_embed_url="${OLLAMA_URL%/}/v1/embeddings"
if [[ "${OLLAMA_URL}" == *"/v1" ]]; then
  ollama_embed_url="${OLLAMA_URL%/}/embeddings"
fi

if curl -sf --max-time 5 "${OLLAMA_URL}/api/tags" -o /dev/null 2>/dev/null; then
  echo "${PASS} Ollama is reachable at ${OLLAMA_URL}"
else
  echo "${FAIL} Cannot reach Ollama at ${OLLAMA_URL}"
  echo "      Check: systemctl status ollama  (or: ollama serve)"
  echo "      If Ollama is on a remote host, verify OLLAMA_URL env var in .memory_env"
  echo
fi

# Check model availability
echo "      Checking model: ${EMBEDDING_MODEL}"
if curl -sf --max-time 5 "${OLLAMA_URL}/api/tags" 2>/dev/null | grep -q "\"${EMBEDDING_MODEL}\""; then
  echo "${PASS} Model '${EMBEDDING_MODEL}' is available in Ollama"
else
  echo "${WARN} Model '${EMBEDDING_MODEL}' not found in Ollama tag list"
  echo "      Fix: ollama pull ${EMBEDDING_MODEL}"
fi
echo

# ── 3. Embedding generation test ──────────────────────────────────────────
echo "--- 3. Embedding generation test ---"
embed_result=$(python3 - <<PYEOF 2>&1
import json, os, urllib.request, sys

ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
model = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")

if ollama_url.endswith("/v1"):
    url = f"{ollama_url}/embeddings"
else:
    url = f"{ollama_url}/v1/embeddings"

data = json.dumps({"model": model, "input": "test"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read().decode())
    vec = result.get("data", [{}])[0].get("embedding", [])
    if vec:
        print(f"OK dims={len(vec)}")
    else:
        print(f"FAIL no embedding in response: {result}")
except Exception as e:
    print(f"FAIL {e}")
PYEOF
)

if echo "${embed_result}" | grep -q "^OK"; then
  echo "${PASS} Embedding generation works — ${embed_result}"
else
  echo "${FAIL} Embedding generation failed: ${embed_result}"
  echo
  echo "      Common causes:"
  echo "      a) Ollama not running → start with: ollama serve"
  echo "      b) Model not pulled  → run: ollama pull ${EMBEDDING_MODEL}"
  echo "      c) Proxy blocking    → set NO_PROXY to include Ollama host"
  echo "         (Squid blocks non-standard ports like 11434 by default)"
  echo "      d) OLLAMA_URL wrong  → current: ${OLLAMA_URL}"
fi
echo

# ── 4. Qdrant service ─────────────────────────────────────────────────────
echo "--- 4. Qdrant service (${QDRANT_URL}) ---"

qdrant_curl_args=()
if [[ -n "${QDRANT_API_KEY}" ]]; then
  qdrant_curl_args+=(-H "api-key: ${QDRANT_API_KEY}")
fi

if curl -sf --max-time 5 "${qdrant_curl_args[@]}" "${QDRANT_URL}/collections" -o /dev/null 2>/dev/null; then
  echo "${PASS} Qdrant is reachable at ${QDRANT_URL}"
else
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${QDRANT_URL}/collections" 2>/dev/null || echo "000")
  if [[ "${http_code}" == "401" || "${http_code}" == "403" ]]; then
    echo "${FAIL} Qdrant returned HTTP ${http_code} — authentication required"
    if [[ -z "${QDRANT_API_KEY}" ]]; then
      echo "      QDRANT_API_KEY is not set in .memory_env"
      echo "      Fix: set QDRANT_API_KEY to the value from CodeShield's secrets.env"
      echo "           (grep QDRANT_API_KEY /etc/openclaw-codeshield/secrets.env)"
    else
      echo "      QDRANT_API_KEY is set but Qdrant rejected it — verify the key"
    fi
  else
    echo "${FAIL} Cannot reach Qdrant at ${QDRANT_URL} (HTTP ${http_code})"
    echo "      Check: docker ps | grep qdrant"
    echo "      Start: docker compose -f /path/to/jarvismemory/docker-compose.yml up -d qdrant"
    echo "      If Qdrant is on a remote host, verify QDRANT_URL env var in .memory_env"
    echo "      Also check NO_PROXY covers the Qdrant host"
  fi
fi
echo

# ── 5. Qdrant collections ─────────────────────────────────────────────────
echo "--- 5. Qdrant collections ---"
python3 - <<PYEOF 2>&1
import json, os, urllib.request

base = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
api_key = os.getenv("QDRANT_API_KEY", "")
headers = {}
if api_key:
    headers["api-key"] = api_key

for name in [
    os.getenv("QDRANT_COLLECTION", "kimi_memories"),
    os.getenv("TR_COLLECTION", "true_recall"),
]:
    req = urllib.request.Request(f"{base}/collections/{name}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        pts = data.get("result", {}).get("points_count", "?")
        print(f"[PASS] {name}: points={pts}")
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
PYEOF
echo

# ── 6. Redis service ───────────────────────────────────────────────────────
echo "--- 6. Redis service (${REDIS_HOST}:${REDIS_PORT}) ---"
if redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping 2>/dev/null | grep -q PONG; then
  echo "${PASS} Redis is reachable"
else
  echo "${FAIL} Cannot reach Redis at ${REDIS_HOST}:${REDIS_PORT}"
  echo "      Check: docker ps | grep redis"
  echo "      Start: docker compose -f /path/to/jarvismemory/docker-compose.yml up -d redis"
fi
echo

# ── 7. CodeShield interaction check ──────────────────────────────────────
echo "--- 7. CodeShield interaction ---"
if systemctl is-active --quiet codeshield-guardian 2>/dev/null || \
   [[ -f /etc/openclaw-codeshield/secrets.env ]]; then
  echo "${WARN} CodeShield appears to be installed"
  echo "      Verify that NO_PROXY covers internal service hosts:"
  echo "        Ollama: $(echo "${OLLAMA_URL}" | sed 's|https\?://||;s|/.*||')"
  echo "        Qdrant: $(echo "${QDRANT_URL}" | sed 's|https\?://||;s|/.*||')"
  echo "        Redis:  ${REDIS_HOST}:${REDIS_PORT}"
  echo
  echo "      If any of these are NOT 127.0.0.1/localhost, add them to:"
  echo "        NO_PROXY in ${ENV_FILE}"
  echo "        no_proxy in ${ENV_FILE}"
  echo
  if [[ -f /etc/openclaw-codeshield/secrets.env ]]; then
    if grep -q "QDRANT_API_KEY" /etc/openclaw-codeshield/secrets.env 2>/dev/null; then
      echo "${WARN} QDRANT_API_KEY found in CodeShield secrets — copy it to .memory_env:"
      echo "        grep QDRANT_API_KEY /etc/openclaw-codeshield/secrets.env"
    fi
  fi
else
  echo "${PASS} CodeShield not detected"
fi
echo

echo "=============================================="
echo " Diagnosis complete"
echo "=============================================="
