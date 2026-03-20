# Deployment Audit

Date audited: 2026-03-12

## Summary

The manual deployment guide was good enough to get one VPS working, but it is not a safe
or repeatable long-term deployment process. The live VPS contains a working composite of:

- original `jarvis-memory` source from SpeedyFox GitLab
- original `true-recall` source from SpeedyFox GitLab
- direct runtime edits inside `~/.openclaw/workspace`
- cron and timezone changes applied manually on-host

This repo rebuilds the deployment flow around the live working state instead of the dead
GitLab sources.

## What was audited

- local deployment guide from `C:\Users\iok\Downloads`
- live VPS `152.53.54.30`
- live OpenClaw workspace under `/home/openclaw/.openclaw/workspace`
- source directories `/home/openclaw/jarvis-memory` and `/home/openclaw/true-recall`
- Docker, Ollama, Qdrant, Redis, cron, and current collection state

## Findings

### 1. The guide depends on retired remotes

The guide still clones from:

- `https://speedyfox.app/SpeedyFoxAi/jarvis-memory.git`
- `https://speedyfox.app/SpeedyFoxAi/true-recall.git`

Those should not remain in the bootstrap path.

### 2. The working VPS has source/runtime drift

The live runtime differs from the original source in important ways:

- `true-recall/tr-process/curate_memories.py`
  - curator model changed from `qwen3:4b-instruct` to `qwen3.5:35b-a3b`
  - `think: false` was added to the Ollama request
  - `<think>...</think>` stripping was added
  - Redis clearing was disabled so Jarvis Memory can clear the buffer later
- `qdrant-memory/scripts/auto_store.py`
  - embedding model changed from `snowflake-arctic-embed2` to `mxbai-embed-large`
  - embedding endpoint was hard-fixed to `/v1/embeddings`

If we bootstrap from the old source repos alone, we would reintroduce broken behavior.

### 3. The guide is too manual for GitHub-based reuse

The guide includes one-off manual steps such as:

- deleting and recreating `docker-compose.yml`
- multiple `nano` edits
- hand-editing cron
- hand-editing `HEARTBEAT.md`
- patching runtime scripts directly in `~/.openclaw/workspace`

That is not suitable for a future one-command deployment.

### 4. The current live deployment is not tracked to GitHub

The live workspace has a git repo but no remote configured.

That means the working runtime state is not yet recoverable from GitHub.

### 5. The current working schedule is host-timezone based

The live cron on the VPS runs at:

- `10:30` True Recall
- `11:00` Jarvis Memory backup
- `11:30` sliding backup

This relies on the host timezone being set to `America/Los_Angeles`, which matches the
later part of the deployment guide but not the earlier raw 2:30/3:00 examples.

## Audit decision

Yes, the requirements are implementable, but not by following the old guide literally.

The safe path is:

1. use the live VPS state as the canonical working baseline
2. store that state in GitHub
3. add a bootstrap layer that replays the managed files and system config
4. keep that bootstrap layer outside the OpenClaw install itself

## Repository design chosen here

- `workspace/` contains the runtime-tested files to deploy into OpenClaw
- `docker-compose.yml` is the canonical Redis + Qdrant stack
- `bootstrap/bootstrap.sh` performs install, sync, config, and audit
- `bootstrap/audit.sh` verifies the deployment after install or after OpenClaw updates

## OpenClaw update safety

This repo avoids storing the source of truth inside OpenClaw application code.

That reduces update risk because:

- the repo can live anywhere on disk
- Docker, cron, and Ollama are managed independently
- workspace files can be re-synced by rerunning bootstrap
- the deployment does not require patching the OpenClaw binary or package files
