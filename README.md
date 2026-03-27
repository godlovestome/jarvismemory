# Jarvis Memory + True Recall v2.1.0

Persistent memory for OpenClaw.
面向 OpenClaw 的持久记忆层。

---

## Table of Contents / 目录

- [English](#english)
  - [What is Jarvis Memory + True Recall](#what-is-jarvis-memory--true-recall)
  - [Version 2.1.0 Features](#version-210-features)
  - [Architecture: Three-Layer Memory System](#architecture-three-layer-memory-system)
  - [Capture Methods](#capture-methods)
  - [Integration: CODE SHIELD](#integration-code-shield)
  - [Integration: QMD Knowledge Base](#integration-qmd-knowledge-base)
  - [Fresh Install](#fresh-install)
  - [Lossless Update](#lossless-non-destructive-update)
  - [Debug and Troubleshooting](#debug-and-troubleshooting)
  - [Cron Schedule](#cron-schedule)
  - [Docker Services](#docker-services)
  - [Protected Data During Updates](#protected-data-during-updates)
  - [Configuration Files and Paths](#configuration-files-and-paths)
- [中文](#中文)
  - [Jarvis Memory + True Recall 简介](#jarvis-memory--true-recall-简介)
  - [2.1.0 版本特性](#210-版本特性)
  - [架构：三层记忆系统](#架构三层记忆系统)
  - [抓取方式](#抓取方式)
  - [集成：CODE SHIELD](#集成code-shield)
  - [集成：QMD 知识库](#集成qmd-知识库)
  - [全新安装](#全新安装)
  - [无损更新](#无损非破坏性更新)
  - [调试与排障](#调试与排障)
  - [Cron 调度](#cron-调度)
  - [Docker 服务](#docker-服务)
  - [更新时受保护的数据](#更新时受保护的数据)
  - [配置文件与路径](#配置文件与路径)

---

# English

## What is Jarvis Memory + True Recall

Jarvis Memory + True Recall is the persistent memory system for OpenClaw. It captures conversation data, extracts durable knowledge gems via LLM-powered curation, and stores them as searchable vectors. The `memory-qdrant` OpenClaw plugin recalls relevant gems before each reply, giving the assistant long-term context awareness.

## Version 2.1.0 Features

- QMD scope config fix: `scope: {"default": "allow"}` in openclaw.json so all channels access QMD search.
- TOOLS.md update: QMD knowledge base documented so TARS knows QMD is installed and available.
- exec-approval fix: `tools.exec.ask: "off"` disabled globally so new users skip manual approval.
- Service session ACL repair: recursive permission fix for openclaw-svc sessions.
- CodeShield plugin trust: root-owned plugin directories match OpenClaw expectations.
- Version bump to 2.1.0 across all artifacts.

## Architecture: Three-Layer Memory System

```
Conversation --> [Layer 1: Redis Buffer] --> [Layer 2: True Recall Curator] --> [Layer 3: Qdrant Vector DB]
                  real-time staging           LLM gem extraction                 semantic search
                  24h TTL                     qwen3.5:35b-a3b                    mxbai-embed-large (1024 dims)
```

### Layer 1: Redis Buffer

Real-time conversation staging. New conversation turns are pushed to a Redis list keyed by user ID (`mem:<user_id>`). Data has a 24-hour TTL and serves as the intake queue for the curator.

- Host: `127.0.0.1:6379`
- Container: `redis-memory`

### Layer 2: True Recall Curator

LLM-powered gem extraction. A scheduled Python process reads staged turns from Redis, feeds them to the curation model (`qwen3.5:35b-a3b` via Ollama), and extracts structured knowledge gems with importance scores, confidence levels, and contextual metadata.

- Model: `qwen3.5:35b-a3b` (configurable via `CURATION_MODEL`)
- Timeout: 1200s (configurable via `CURATION_TIMEOUT_SECONDS`)

### Layer 3: Qdrant Vector DB

Semantic search over long-term memory. Gems are embedded using `mxbai-embed-large` (1024 dimensions) and stored in the `true_recall` Qdrant collection. The `memory-qdrant` OpenClaw plugin queries this collection before each reply.

- Host: `127.0.0.1:6333` (HTTP) / `127.0.0.1:6334` (gRPC)
- Container: `qdrant-memory`
- Collection: `true_recall`

## Capture Methods

| Method | Description | Token Cost |
|--------|-------------|------------|
| **Heartbeat** | Real-time capture triggered by the HEARTBEAT.md skill during conversation | Normal |
| **Cron** | Scheduled daily capture via `cron_capture.py` (no active conversation needed) | Zero-token |
| **Manual** | On-demand full-history rebuild via `rebuild_true_recall.sh` | Zero-token |

## Integration: CODE SHIELD

Jarvis Memory operates within the CODE SHIELD security framework:

- **Secrets management**: Qdrant API keys and other protected credentials are managed by CODE SHIELD. Runtime secrets are read from `/run/openclaw-memory/secrets.env`. No secrets are written into `.memory_env`.
- **ACL enforcement**: Service session transcripts under `/var/lib/openclaw-svc/` are protected with POSIX ACLs. The `openclaw` user receives read-only access via `setfacl`.
- **Plugin trust**: Installed plugin directories are root-owned and world-readable, matching OpenClaw's trust model and avoiding suspicious-ownership blocks.
- **Network isolation**: The recall plugin communicates only with local `127.0.0.1` endpoints (Qdrant, Ollama, Redis).

## Integration: QMD Knowledge Base

QMD (Query Markdown) provides searchable knowledge bases from markdown files. Jarvis Memory configures OpenClaw to use QMD with:

- Backend: `qmd` with `citations: auto`
- Scope: `{"default": "allow"}` -- all channels can access QMD search
- Knowledge paths auto-discovered from `/home/openclaw/qmd-index/`
- Custom wrapper script: `/home/openclaw/scripts/qmd-openclaw-wrapper.sh`
- Timeout: 600000ms (configurable via `OPENCLAW_QMD_TIMEOUT_MS`)

## Fresh Install

Prerequisites: Ubuntu/Debian VDS with Docker, a system user `openclaw`, and Ollama installed (the bootstrap script installs missing dependencies automatically).

```bash
git clone https://github.com/godlovestome/jarvismemory.git && cd jarvismemory && sudo bash bootstrap/bootstrap.sh
```

## Lossless (Non-Destructive) Update

The `update.sh` script preserves all existing data while refreshing managed workspace files, cron blocks, and environment files.

```bash
curl -fsSL https://raw.githubusercontent.com/godlovestome/jarvismemory/main/bootstrap/update.sh | sudo bash
```

Protected during update: OpenClaw settings, CodeShield-managed secrets, Redis data, Qdrant data, cron schedules, and `.memory_env` runtime values.

## Debug and Troubleshooting

```bash
# Verify installation
bash bootstrap/audit.sh

# Troubleshooting diagnostics
bash bootstrap/diagnose.sh

# Full history rebuild (reprocesses all transcripts)
bash bootstrap/rebuild_true_recall.sh

# Check Redis buffer length
redis-cli LLEN mem:<user_id>

# Check Qdrant true_recall collection
curl http://127.0.0.1:6333/collections/true_recall

# Check cron schedule
crontab -l -u openclaw

# Qdrant container logs
docker logs qdrant-memory

# Redis container logs
docker logs redis-memory

# OpenClaw service logs
journalctl -u openclaw -f
```

## Cron Schedule

The VDS timezone remains `America/Los_Angeles`. The default daily cron window is pinned to Los Angeles times that correspond to China early morning:

| LA Time (America/Los_Angeles) | China Time | Task |
|-------------------------------|------------|------|
| 11:05 | 02:05 | Capture -- stage new conversation turns to Redis |
| 11:30 | 02:30 | Curation -- True Recall LLM gem extraction (last 24h) |
| 12:00 | 03:00 | Backup -- Redis and Qdrant backup |
| 12:30 | 03:30 | Sliding backup -- rolling Qdrant snapshot |

## Docker Services

| Container | Ports | Purpose |
|-----------|-------|---------|
| `qdrant-memory` | 6333 (HTTP), 6334 (gRPC) | Long-term vector storage |
| `redis-memory` | 6379 | Short-term conversation buffer |

Both containers are managed via `docker-compose.yml` under the `jarvis-memory` project name.

## Protected Data During Updates

The lossless update path (`update.sh`) preserves:

- Qdrant vector data and collections
- Redis buffered conversation turns
- OpenClaw configuration (`openclaw.json`)
- CodeShield-managed secrets (`/run/openclaw-memory/secrets.env`)
- Cron schedules (rewritten but functionally identical)
- `.memory_env` runtime values (USER_ID, model settings, URLs)
- Backup history under `.backups/`

## Configuration Files and Paths

| Path | Purpose |
|------|---------|
| `/home/openclaw/.memory_env` | Runtime environment (sourced by `.bashrc`) |
| `/home/openclaw/.openclaw/workspace/.memory_env` | Workspace copy of runtime environment |
| `/home/openclaw/.openclaw/openclaw.json` | OpenClaw config (interactive runtime) |
| `/var/lib/openclaw-svc/.openclaw/openclaw.json` | OpenClaw config (service runtime) |
| `/home/openclaw/.openclaw/workspace/` | Workspace root (skills, docs, plugins, projects) |
| `/var/lib/openclaw-svc/.openclaw/workspace/` | Service workspace root |
| `/home/openclaw/.openclaw/agents/main/sessions/` | Interactive session transcripts |
| `/var/lib/openclaw-svc/.openclaw/agents/main/sessions/` | Service session transcripts |
| `/home/openclaw/.openclaw/extensions/memory-qdrant/` | Installed plugin (interactive) |
| `/var/lib/openclaw-svc/.openclaw/extensions/memory-qdrant/` | Installed plugin (service) |
| `/run/openclaw-memory/secrets.env` | CodeShield-managed secrets |
| `/etc/openclaw-codeshield/` | CodeShield configuration |
| `/home/openclaw/qmd-index/` | QMD knowledge base index |
| `/home/openclaw/scripts/qmd-openclaw-wrapper.sh` | QMD wrapper script |

---

# 中文

## Jarvis Memory + True Recall 简介

Jarvis Memory + True Recall 是 OpenClaw 的持久记忆系统。它捕获对话数据，通过 LLM 驱动的 curator 提炼持久知识 gem，并将其存储为可搜索的向量。`memory-qdrant` OpenClaw 插件会在每次回复前召回相关 gem，赋予助手长期上下文感知能力。

## 2.1.0 版本特性

- QMD scope 配置修复：在 openclaw.json 中添加 `scope: {"default": "allow"}`，所有 channel 均可访问 QMD 搜索。
- TOOLS.md 更新：添加 QMD 知识库文档，使 TARS 知道 QMD 已安装并可用。
- exec-approval 修复：全局设置 `tools.exec.ask: "off"`，新用户不再需要手动审批。
- 服务会话 ACL 修复：对 openclaw-svc sessions 递归权限修复。
- CodeShield 插件信任：root-owned 插件目录符合 OpenClaw 预期。
- 版本号更新至 2.1.0。

## 架构：三层记忆系统

```
对话 --> [第一层：Redis 缓冲] --> [第二层：True Recall Curator] --> [第三层：Qdrant 向量库]
          实时暂存                  LLM gem 提炼                     语义搜索
          24 小时 TTL               qwen3.5:35b-a3b                  mxbai-embed-large (1024 维)
```

### 第一层：Redis 缓冲

实时对话暂存。新的对话 turn 被推入以用户 ID 为 key 的 Redis 列表（`mem:<user_id>`）。数据有 24 小时 TTL，作为 curator 的入队队列。

- 地址：`127.0.0.1:6379`
- 容器：`redis-memory`

### 第二层：True Recall Curator

LLM 驱动的 gem 提炼。定时 Python 进程从 Redis 读取暂存 turn，通过 Ollama 调用 curation 模型（`qwen3.5:35b-a3b`），提取带有重要性评分、置信度和上下文元数据的结构化知识 gem。

- 模型：`qwen3.5:35b-a3b`（可通过 `CURATION_MODEL` 配置）
- 超时：1200 秒（可通过 `CURATION_TIMEOUT_SECONDS` 配置）

### 第三层：Qdrant 向量库

长期记忆的语义搜索。Gem 使用 `mxbai-embed-large`（1024 维）嵌入，存储在 `true_recall` Qdrant collection 中。`memory-qdrant` OpenClaw 插件在每次回复前查询此 collection。

- 地址：`127.0.0.1:6333`（HTTP）/ `127.0.0.1:6334`（gRPC）
- 容器：`qdrant-memory`
- Collection：`true_recall`

## 抓取方式

| 方式 | 说明 | Token 消耗 |
|------|------|-----------|
| **Heartbeat（心跳）** | 对话过程中由 HEARTBEAT.md skill 实时触发抓取 | 正常消耗 |
| **Cron（定时）** | 通过 `cron_capture.py` 每日定时抓取（无需活跃对话） | 零 token |
| **Manual（手动）** | 通过 `rebuild_true_recall.sh` 按需全量历史重建 | 零 token |

## 集成：CODE SHIELD

Jarvis Memory 在 CODE SHIELD 安全框架内运行：

- **密钥管理**：Qdrant API key 等受保护凭据由 CODE SHIELD 托管。运行时密钥从 `/run/openclaw-memory/secrets.env` 读取，不会写入 `.memory_env`。
- **ACL 强制执行**：`/var/lib/openclaw-svc/` 下的服务会话 transcript 使用 POSIX ACL 保护。`openclaw` 用户通过 `setfacl` 获得只读访问权限。
- **插件信任**：已安装插件目录为 root-owned 且全局可读，符合 OpenClaw 信任模型，避免可疑 ownership 阻断。
- **网络隔离**：召回插件仅与本机 `127.0.0.1` 端点通信（Qdrant、Ollama、Redis）。

## 集成：QMD 知识库

QMD（Query Markdown）提供基于 markdown 文件的可搜索知识库。Jarvis Memory 配置 OpenClaw 使用 QMD：

- 后端：`qmd`，`citations: auto`
- 范围：`{"default": "allow"}` -- 所有 channel 均可访问 QMD 搜索
- 知识路径从 `/home/openclaw/qmd-index/` 自动发现
- 自定义包装脚本：`/home/openclaw/scripts/qmd-openclaw-wrapper.sh`
- 超时：600000ms（可通过 `OPENCLAW_QMD_TIMEOUT_MS` 配置）

## 全新安装 / 一行代码全新安装

前置条件：安装了 Docker 的 Ubuntu/Debian VDS，系统用户 `openclaw`，以及 Ollama（bootstrap 脚本会自动安装缺失依赖）。

```bash
git clone https://github.com/godlovestome/jarvismemory.git && cd jarvismemory && sudo bash bootstrap/bootstrap.sh
```

## 无损（非破坏性）更新 / 一行代码无损更新

`update.sh` 脚本在刷新托管的 workspace 文件、cron 块和环境文件的同时，保留所有现有数据。

```bash
curl -fsSL https://raw.githubusercontent.com/godlovestome/jarvismemory/main/bootstrap/update.sh | sudo bash
```

更新期间受保护的数据：OpenClaw 设置、CodeShield 托管密钥、Redis 数据、Qdrant 数据、cron 调度以及 `.memory_env` 运行时值。

## 调试与排障

```bash
# 验证安装
bash bootstrap/audit.sh

# 排障诊断
bash bootstrap/diagnose.sh

# 全量历史重建 -- 从现有 transcript 重建 True Recall gems
bash bootstrap/rebuild_true_recall.sh

# 检查 Redis 缓冲长度
redis-cli LLEN mem:<user_id>

# 检查 Qdrant true_recall collection
curl http://127.0.0.1:6333/collections/true_recall

# 检查 cron 调度
crontab -l -u openclaw

# Qdrant 容器日志
docker logs qdrant-memory

# Redis 容器日志
docker logs redis-memory

# OpenClaw 服务日志
journalctl -u openclaw -f
```

## Cron 调度

VDS 时区保持 `America/Los_Angeles`。默认每日 cron 时间窗对应中国凌晨：

| LA 时间（America/Los_Angeles） | 中国时间 | 任务 |
|-------------------------------|---------|------|
| 11:05 | 02:05 | 抓取 -- 将新对话 turn 暂存到 Redis |
| 11:30 | 02:30 | 提炼 -- True Recall LLM gem 提取（最近 24 小时） |
| 12:00 | 03:00 | 备份 -- Redis 和 Qdrant 备份 |
| 12:30 | 03:30 | 滚动备份 -- Qdrant 滚动快照 |

## Docker 服务

| 容器 | 端口 | 用途 |
|------|------|------|
| `qdrant-memory` | 6333（HTTP）、6334（gRPC） | 长期向量存储 |
| `redis-memory` | 6379 | 短期对话缓冲 |

两个容器通过 `docker-compose.yml` 在 `jarvis-memory` 项目名下管理。

## 更新时受保护的数据

无损更新路径（`update.sh`）保留以下数据：

- Qdrant 向量数据和 collection
- Redis 缓冲的对话 turn
- OpenClaw 配置（`openclaw.json`）
- CodeShield 托管密钥（`/run/openclaw-memory/secrets.env`）
- Cron 调度（会重写但功能等价）
- `.memory_env` 运行时值（USER_ID、模型设置、URL）
- `.backups/` 下的备份历史

## 配置文件与路径

| 路径 | 用途 |
|------|------|
| `/home/openclaw/.memory_env` | 运行时环境（由 `.bashrc` source） |
| `/home/openclaw/.openclaw/workspace/.memory_env` | workspace 运行时环境副本 |
| `/home/openclaw/.openclaw/openclaw.json` | OpenClaw 配置（交互式运行时） |
| `/var/lib/openclaw-svc/.openclaw/openclaw.json` | OpenClaw 配置（服务运行时） |
| `/home/openclaw/.openclaw/workspace/` | Workspace 根目录（skills、docs、plugins、projects） |
| `/var/lib/openclaw-svc/.openclaw/workspace/` | 服务 workspace 根目录 |
| `/home/openclaw/.openclaw/agents/main/sessions/` | 交互式会话 transcript |
| `/var/lib/openclaw-svc/.openclaw/agents/main/sessions/` | 服务会话 transcript |
| `/home/openclaw/.openclaw/extensions/memory-qdrant/` | 已安装插件（交互式） |
| `/var/lib/openclaw-svc/.openclaw/extensions/memory-qdrant/` | 已安装插件（服务） |
| `/run/openclaw-memory/secrets.env` | CodeShield 托管密钥 |
| `/etc/openclaw-codeshield/` | CodeShield 配置 |
| `/home/openclaw/qmd-index/` | QMD 知识库索引 |
| `/home/openclaw/scripts/qmd-openclaw-wrapper.sh` | QMD 包装脚本 |
