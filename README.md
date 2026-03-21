# Jarvis Memory v2.0.0

**Persistent Memory System for OpenClaw AI Agents / OpenClaw AI Agent 永续记忆系统**

Jarvis Memory + True Recall provides a persistent, cross-session memory system that operates independently from OpenClaw's built-in `memory_search`. It uses Qdrant (vector DB) + Ollama (local embeddings) + Redis (buffer), and survives OpenClaw upgrades without data loss. V2.0.0 adds CodeShield V3.0.11 integration, secure secret management, and automatic OpenClaw `memorySearch` configuration with local Ollama.

---

**Jarvis Memory v2.0.0 — OpenClaw AI Agent 永续记忆系统**

Jarvis Memory + True Recall 提供独立于 OpenClaw 内置 `memory_search` 的持久化跨会话记忆系统。使用 Qdrant（向量数据库）+ Ollama（本地嵌入）+ Redis（缓冲），OpenClaw 升级不影响记忆数据。V2.0.0 新增 CodeShield V3.0.11 集成、安全密钥管理、自动配置 OpenClaw `memorySearch` 使用本地 Ollama。

---

## Quick Start / 快速开始

### Fresh Install / 全新安装（一行命令）

```bash
git clone https://github.com/godlovestome/jarvismemory.git && cd jarvismemory && sudo bash bootstrap/bootstrap.sh
```

### Update Existing / 无损更新（一行命令）

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/update.sh
```

> **OpenClaw updates are safe / OpenClaw 更新安全：**
> ```bash
> curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard
> ```
> This only updates OpenClaw code. It does **NOT** touch:
> - Jarvis Memory data (Qdrant/Redis)
> - `openclaw.json` configuration (memorySearch settings preserved)
> - `.memory_env` / cron jobs / workspace scripts
> - CodeShield security framework
>
> After OpenClaw update, re-run `sudo bash bootstrap/update.sh` to re-sync scripts.
>
> 此命令仅更新 OpenClaw 代码，**不会**影响 Jarvis Memory 数据、配置、定时任务或 CodeShield 安全框架。更新后执行 `sudo bash bootstrap/update.sh` 重新同步脚本。

---

## Architecture / 架构

Two independent memory systems running side by side:

两套独立的记忆系统并行运行：

| | OpenClaw memory_search | Jarvis Memory + True Recall |
|---|---|---|
| **Storage / 存储** | SQLite + sqlite-vec | Qdrant vector DB |
| **Embedding** | Ollama `qwen3-embedding:4b` (2560d) | Ollama `mxbai-embed-large` (1024d) |
| **Data / 数据** | OpenClaw workspace memory files | Conversations, facts, curated gems |
| **Scope / 范围** | Current workspace context | Cross-session persistent memory |
| **Conflict / 冲突** | None — separate storage, models, config / 无——存储、模型、配置完全独立 |

---

## What's New in v2.0.0 / v2.0.0 更新内容

| Change / 变更 | Description / 说明 |
|---|---|
| CodeShield integration | `QDRANT_API_KEY` sourced from `/run/openclaw-memory/secrets.env` (CodeShield V3.0.11) instead of plaintext / 密钥从 CodeShield 安全路径加载，不再明文存储 |
| OpenClaw memorySearch config | Auto-configures `memorySearch.provider=ollama` + `model=qwen3-embedding:4b` / 自动配置 OpenClaw 使用本地 Ollama 做 embedding |
| `.memory_env` hardening | Permissions tightened to 600; QDRANT_API_KEY no longer stored in plaintext / 权限收紧为 600；密钥不再明文存储 |
| Diagnose: CodeShield checks | `diagnose.sh` now checks CodeShield interaction, proxy, and secret paths / 诊断脚本新增 CodeShield 检查项 |

---

## Usage / 使用说明

### 1. Fresh Install / 首次部署

On a VPS where OpenClaw is already installed:

在已安装 OpenClaw 的 VPS 上执行：

```bash
git clone https://github.com/godlovestome/jarvismemory.git
cd jarvismemory
sudo bash bootstrap/bootstrap.sh
```

The script will prompt for `USER_ID` on first run if not set in the environment.

首次运行时脚本会交互式询问 `USER_ID`（OpenClaw 的用户标识符）。

**What bootstrap.sh does / bootstrap.sh 做了什么：**

| Step | English | 中文 |
|------|---------|------|
| 1 | Install host dependencies (Docker, Python, etc.) | 安装宿主机依赖 |
| 2 | Start Redis and Qdrant via Docker | 启动 Redis 和 Qdrant 容器 |
| 3 | Validate Ollama and pull required models | 检查 Ollama 并拉取所需模型 |
| 4 | Sync workspace scripts to `~/.openclaw/workspace` | 同步脚本到 workspace |
| 5 | Write `.memory_env` configuration file | 生成 `.memory_env` 配置文件 |
| 6 | Configure system timezone and cron schedules | 设置时区和定时任务 |
| 7 | Configure OpenClaw memorySearch (local Ollama) | 配置 OpenClaw memorySearch 使用本地 Ollama |
| 8 | Run final audit | 执行最终检查 |

**Configurable defaults / 可配置默认值：**

| Variable | Default | Description / 说明 |
|----------|---------|---------------------|
| `OPENCLAW_USER` | `openclaw` | System user / 系统用户 |
| `TIMEZONE` | `America/Los_Angeles` | System timezone / 系统时区 |
| `EMBEDDING_MODEL` | `mxbai-embed-large` | Jarvis Memory embedding model / Jarvis 向量嵌入模型 |
| `CURATION_MODEL` | `qwen3.5:35b-a3b` | LLM for True Recall curation / True Recall 整理模型 |
| `OPENCLAW_MEMORYSEARCH_MODEL` | `qwen3-embedding:4b` | OpenClaw memory_search embedding / OpenClaw 搜索嵌入模型 |
| `TR_SCHEDULE` | `30 10 * * *` | True Recall daily run / True Recall 每日执行 |
| `BACKUP_SCHEDULE` | `0 11 * * *` | Daily backup / 每日备份 |
| `SLIDING_SCHEDULE` | `30 11 * * *` | Sliding backup / 滑动备份 |

Override any variable before running:

运行前可直接覆盖变量：

```bash
sudo TIMEZONE=Asia/Shanghai OPENCLAW_MEMORYSEARCH_MODEL=nomic-embed-text bash bootstrap/bootstrap.sh
```

---

### 2. Update an Existing Deployment / 更新现有部署

For deployments already running, use the non-destructive updater:

已部署的系统请使用无损更新脚本：

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/update.sh
```

This **preserves all secrets and running containers**. It only syncs scripts and
regenerates config/cron.

该脚本**不会触碰密钥、Docker 容器或数据库**，只同步脚本文件并重新生成配置和定时任务。

**What update.sh preserves vs updates / 保留 vs 更新对比：**

| Item / 内容 | Preserved / 保留 | Updated / 更新 |
|-------------|:---:|:---:|
| `USER_ID`, `QDRANT_API_KEY` | ✓ | |
| `OLLAMA_URL`, `QDRANT_URL`, `REDIS_*` | ✓ | |
| Qdrant vector data / 向量数据 | ✓ | |
| Redis buffer / Redis 缓存 | ✓ | |
| Running Docker containers / 运行中容器 | ✓ | |
| Ollama models / Ollama 模型 | ✓ | |
| OpenClaw `memorySearch` config | ✓ | |
| Python scripts in `workspace/skills/` | | ✓ |
| True Recall scripts in `workspace/.projects/` | | ✓ |
| `.memory_env` values | | ✓ (保留现有值重新写入) |
| Cron managed block / 定时任务块 | | ✓ |

> **When to use which / 如何选择：**
> - First time on a new server → `bootstrap.sh`
> - Pulling code updates on existing server → `update.sh`
>
> 新服务器首次部署用 `bootstrap.sh`；已有部署拉取更新用 `update.sh`。

---

### 3. Diagnose Errors / 故障排查

If you see embedding or memory search errors, run the diagnostic script:

遇到向量嵌入或记忆搜索报错时，执行诊断脚本：

```bash
sudo bash bootstrap/diagnose.sh
```

**What it checks / 检查项目：**

| Check / 检查 | Description / 说明 |
|-------------|---------------------|
| Proxy environment | HTTP_PROXY / HTTPS_PROXY / NO_PROXY 配置 |
| Local bypass | 确认 127.0.0.1 / localhost / 10.x 绕过代理 |
| Ollama availability | Ollama 服务是否可访问 |
| Embedding model | 所需嵌入模型是否已加载 |
| Qdrant connectivity | Qdrant 端口和 API key 是否正常 |
| Redis connectivity | Redis 连接是否正常 |
| CodeShield interaction | CodeShield 安全框架兼容性检查 |

Output uses `[PASS]` / `[FAIL]` / `[WARN]` indicators.

输出使用 `[PASS]` / `[FAIL]` / `[WARN]` 标识每项状态。

---

### 4. Environment Configuration / 环境配置

The deployment writes `~/.memory_env` (sourced by all scripts). Reference
template: `templates/.memory_env.example`.

所有脚本通过 `source ~/.memory_env` 读取配置。参考模板：`templates/.memory_env.example`。

| Variable | Description / 说明 |
|----------|---------------------|
| `WORKSPACE_DIR` | Main workspace path / 工作区路径 |
| `USER_ID` | OpenClaw user identifier / 用户标识符 |
| `REDIS_HOST` / `REDIS_PORT` | Redis connection / Redis 连接 |
| `QDRANT_URL` | Qdrant API endpoint / Qdrant 地址 |
| `QDRANT_COLLECTION` | Memory collection name (default: `kimi_memories`) |
| `TR_COLLECTION` | True Recall collection (default: `true_recall`) |
| `OLLAMA_URL` | Ollama API endpoint / Ollama 地址 |
| `EMBEDDING_MODEL` | Jarvis embedding model / Jarvis 嵌入模型名称 |
| `CURATION_MODEL` | LLM for memory curation / 记忆整理模型 |
| `QDRANT_API_KEY` | Loaded from CodeShield (auto) or set manually / 从 CodeShield 加载或手动设置 |
| `NO_PROXY` / `no_proxy` | Proxy bypass list / 代理绕过列表 |

---

### 5. Key Scripts / 核心脚本

**Qdrant memory scripts** (`workspace/skills/qdrant-memory/scripts/`):

| Script | Purpose / 用途 |
|--------|----------------|
| `store_memory.py` | Store a memory to Qdrant / 存储记忆 |
| `smart_search.py` | Hybrid semantic search / 混合语义搜索 |
| `search_memories.py` | Basic memory retrieval / 基础记忆检索 |
| `harvest_sessions.py` | Harvest sessions from OpenClaw / 采集会话数据 |
| `extract_facts.py` | Extract structured facts from text / 提取结构化事实 |
| `daily_backup.py` | Daily snapshot to disk / 每日快照备份 |
| `init_all_collections.py` | Initialize all Qdrant collections / 初始化集合 |
| `qd.py` | CLI for quick Qdrant operations / 命令行快速操作 |

**Redis memory scripts** (`workspace/skills/mem-redis/scripts/`):

| Script | Purpose / 用途 |
|--------|----------------|
| `cron_capture.py` | Periodic memory capture (every 5 min) / 定时采集记忆 |
| `save_mem.py` | Save a memory entry to Redis / 写入 Redis 记忆 |
| `mem_retrieve.py` | Retrieve memories from Redis / 读取 Redis 记忆 |
| `search_mem.py` | Search Redis memory store / 搜索 Redis 记忆 |
| `cron_backup.py` | Scheduled Redis backup / 定时备份 |

---

## CodeShield Integration / CodeShield 集成

When CODE SHIELD V3.0.11+ is installed, Jarvis Memory automatically:

安装 CODE SHIELD V3.0.11+ 后，Jarvis Memory 自动：

1. **Loads `QDRANT_API_KEY` from CodeShield-managed tmpfs** (`/run/openclaw-memory/secrets.env`) — no plaintext key in `~/.memory_env`
   从 CodeShield 管理的 tmpfs 加载密钥——`~/.memory_env` 不存储明文密钥

2. **Bypasses Squid proxy for local services** via `NO_PROXY=127.0.0.1,localhost` — Ollama, Qdrant, Redis connections go direct
   通过 `NO_PROXY` 绕过 Squid 代理——Ollama、Qdrant、Redis 直连

3. **Configures OpenClaw memorySearch** to use local Ollama (`qwen3-embedding:4b`) — avoids iptables blocking of external embedding APIs
   配置 OpenClaw memorySearch 使用本地 Ollama——避免 iptables 阻断外部嵌入 API

---

## Docs / 文档

- Deployment guide / 部署手册: `docs/DEPLOYMENT.md`
- Audit notes / 审计说明: `docs/AUDIT.md`

---

## Safety Goal / 安全目标

- OpenClaw can be updated independently / OpenClaw 可独立升级，不影响记忆系统
- This repo remains the source of truth for memory deployment / 本仓库是记忆部署的唯一可信来源
- Rerunning bootstrap or update restores managed files and schedules / 重跑脚本可恢复托管文件和定时任务

这意味着以后新装 OpenClaw 后，可以直接从这个 GitHub 仓库拉代码并执行 bootstrap，
而不是重新手工照旧文档逐条修改。
