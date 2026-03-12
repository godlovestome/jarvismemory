# Jarvis Memory Bootstrap

Bootstrap repository for deploying the current working `Jarvis Memory + True Recall`
stack onto an existing OpenClaw host without depending on the retired SpeedyFox GitLab.

## What this repo does

- Stores the runtime-tested workspace files that are already running on the VPS.
- Adds a repeatable bootstrap script for new OpenClaw installs.
- Keeps deployment logic outside the OpenClaw app itself, so OpenClaw updates do not
  become the source of truth for this memory stack.
- Preserves the current live architecture:
  - OpenClaw sessions stay under `~/.openclaw/agents/main/sessions`
  - workspace integrations stay under `~/.openclaw/workspace`
  - Redis and Qdrant stay in Docker
  - True Recall stays under `~/.openclaw/workspace/.projects/true-recall`

## Quick start

On a new VPS where OpenClaw is already installed:

```bash
git clone https://github.com/godlovestome/jarvismemory.git
cd jarvismemory
sudo bash bootstrap/bootstrap.sh
```

The bootstrap script will:

- install missing host dependencies
- install or validate Docker and Ollama
- pull the required models
- deploy the workspace files
- generate `.memory_env`
- configure cron
- set the system timezone
- run a final audit

## Current defaults

- OpenClaw user: `openclaw`
- Timezone: `America/Los_Angeles`
- True Recall: `10:30`
- Jarvis Memory backup: `11:00`
- Sliding backup: `11:30`
- Compose project name: `jarvis-memory`
- Embedding model: `mxbai-embed-large`
- Curator model: `qwen3.5:35b-a3b`

These defaults match the currently deployed VPS more closely than the older manual guide.

## Audit notes

The full audit is in `docs/AUDIT.md`.

In short:

- the original SpeedyFox GitLab remotes are no longer a viable source of truth
- the live VPS contains runtime fixes that never made it back into the source repos
- the original guide is too manual to serve as a long-term deployment workflow

## Important

This repo is designed to adopt the current working deployment, not replace it with a new
architecture. The bootstrap flow copies managed files into the OpenClaw workspace and can
be re-run safely after updates.
