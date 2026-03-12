# Jarvis Memory Bootstrap

`Jarvis Memory + True Recall` 的 GitHub 部署仓库。

This repository turns the currently working VPS deployment into a repeatable
bootstrap flow for future OpenClaw installs.

## What This Repo Is For

- Rebuild deployment from GitHub instead of the retired SpeedyFox GitLab.
- Keep Jarvis Memory and True Recall outside the OpenClaw app codebase.
- Re-sync managed files after OpenClaw updates without rebuilding everything by hand.
- Preserve the current live architecture instead of replacing it with a new one.

## Quick Start

On a VPS where OpenClaw is already installed:

```bash
git clone https://github.com/godlovestome/jarvismemory.git
cd jarvismemory
sudo bash bootstrap/bootstrap.sh
```

在已经安装好 OpenClaw 的 VPS 上，执行上面三条命令即可开始接管式部署。

## Docs

- Deployment guide / 部署手册: `docs/DEPLOYMENT.md`
- Audit notes / 审计说明: `docs/AUDIT.md`

## What The Bootstrap Script Does

- installs or validates host dependencies
- starts Redis and Qdrant via Docker
- validates Ollama and required models
- syncs managed workspace files into `~/.openclaw/workspace`
- writes `.memory_env`
- configures timezone and cron
- runs a final audit

## Current Defaults

- OpenClaw user: `openclaw`
- Timezone: `America/Los_Angeles`
- True Recall: `10:30`
- Jarvis Memory backup: `11:00`
- Sliding backup: `11:30`
- Embedding model: `mxbai-embed-large`
- Curator model: `qwen3.5:35b-a3b`

## Safety Goal

The goal is:

- OpenClaw can be updated independently
- this repo remains the source of truth for memory deployment
- rerunning bootstrap restores managed files and schedules

这意味着以后新装 OpenClaw 后，可以直接从这个 GitHub 仓库拉代码并执行 bootstrap，
而不是重新手工照旧文档逐条修改。
