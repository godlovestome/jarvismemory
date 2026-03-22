# Jarvis Memory v2.0.1

**Persistent Memory System for OpenClaw AI Agents**  
**面向 OpenClaw AI Agent 的持久化记忆系统**

Jarvis Memory + True Recall is a persistent, cross-session memory layer that runs independently from OpenClaw's built-in `memory_search`. It uses Qdrant for vector storage, Ollama for local embeddings and generation, and Redis for short-term buffering.

Jarvis Memory + True Recall 是独立于 OpenClaw 内置 `memory_search` 的持久化跨会话记忆层，使用 Qdrant 作为向量存储、Ollama 作为本地嵌入与生成能力、Redis 作为短期缓冲。

**Version focus / 本版重点：v2.0.1**  
Adds Codeshield runtime workspace sync so the isolated `openclaw-svc` runtime receives the same managed memory workspace and `.memory_env` as the interactive user.  
新增 Codeshield 运行时工作区同步能力，使隔离运行用户 `openclaw-svc` 能拿到与交互用户相同的托管 workspace 和 `.memory_env`。

---

## Quick Start / 快速开始

### Fresh Install / 全新安装

```bash
git clone https://github.com/godlovestome/jarvismemory.git
cd jarvismemory
sudo bash bootstrap/bootstrap.sh
```

### Lossless Update / 无损更新

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/update.sh
```

### OpenClaw Upgrade Safety / OpenClaw 升级安全说明

```bash
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard
```

This updates OpenClaw code only. It does not wipe Jarvis Memory data, Qdrant/Redis state, `.memory_env`, or Codeshield integration.  
这条命令只更新 OpenClaw 代码，不会清空 Jarvis Memory 数据、Qdrant/Redis 状态、`.memory_env`，也不会破坏 Codeshield 集成。

After upgrading OpenClaw, run:
升级 OpenClaw 后建议执行：

```bash
sudo bash bootstrap/update.sh
```

---

## What's New in v2.0.1 / v2.0.1 更新内容

- Service-runtime workspace sync
- Service-runtime `.memory_env` sync
- Better compatibility with Codeshield-isolated OpenClaw runtime
- Regression coverage for service-runtime paths and docs

- 新增 service 运行时 workspace 同步
- 新增 service 运行时 `.memory_env` 同步
- 改善与 Codeshield 隔离运行态的兼容性
- 增加覆盖 service 运行路径与文档的回归测试

---

## Architecture / 架构

Two memory systems can coexist:
两套记忆系统可以并行共存：

| Item / 项目 | OpenClaw `memory_search` | Jarvis Memory + True Recall |
|---|---|---|
| Storage / 存储 | SQLite + sqlite-vec | Qdrant |
| Embedding / 嵌入 | Ollama `qwen3-embedding:4b` | Ollama `mxbai-embed-large` |
| Scope / 范围 | 当前工作区上下文 | 跨会话长期记忆 |
| Data / 数据 | OpenClaw 原生记忆 | 对话、事实、整理后的知识 |
| Isolation / 隔离 | 跟随 OpenClaw | 独立维护，可单独更新 |

---

## Bootstrap / 首次部署

Run `bootstrap/bootstrap.sh` on a server where OpenClaw is already installed.  
在已经安装好 OpenClaw 的服务器上运行 `bootstrap/bootstrap.sh`。

### What it does / 它会做什么

1. Install host dependencies
2. Start Redis and Qdrant with Docker
3. Validate Ollama and pull required models
4. Sync managed workspace files
5. Write `.memory_env`
6. Configure timezone and cron jobs
7. Configure OpenClaw `memorySearch` for local Ollama
8. Run a final audit

1. 安装宿主机依赖
2. 通过 Docker 启动 Redis 和 Qdrant
3. 检查 Ollama 并拉取所需模型
4. 同步托管 workspace 文件
5. 写入 `.memory_env`
6. 配置时区和定时任务
7. 把 OpenClaw `memorySearch` 配到本地 Ollama
8. 执行最终审计

### Key Defaults / 关键默认值

- `OPENCLAW_USER=openclaw`
- `TIMEZONE=America/Los_Angeles`
- `EMBEDDING_MODEL=mxbai-embed-large`
- `CURATION_MODEL=qwen3.5:35b-a3b`
- `OPENCLAW_MEMORYSEARCH_MODEL=qwen3-embedding:4b`

Override example / 覆盖示例：

```bash
sudo TIMEZONE=Asia/Shanghai OPENCLAW_MEMORYSEARCH_MODEL=nomic-embed-text bash bootstrap/bootstrap.sh
```

---

## Lossless Update / 无损更新说明

`bootstrap/update.sh` is intended for existing deployments. It refreshes managed scripts and config while preserving runtime data and secrets.

`bootstrap/update.sh` 用于已有部署，会刷新托管脚本和配置，同时保留运行中的数据与密钥。

### Preserved / 会保留

- `USER_ID`
- `QDRANT_API_KEY`
- `QDRANT_URL`
- `OLLAMA_URL`
- Redis and Qdrant data
- Running containers
- Ollama models
- Existing OpenClaw memorySearch settings

### Updated / 会更新

- Workspace scripts under `workspace/skills/`
- True Recall project files under `workspace/.projects/`
- Managed `.memory_env`
- Managed cron block
- Service-runtime mirrored workspace when `openclaw-svc` exists

---

## Diagnose / 故障诊断

If embedding or memory retrieval fails:
如果 embedding 或记忆检索异常：

```bash
sudo bash bootstrap/diagnose.sh
```

It checks:
它会检查：

- proxy environment
- `NO_PROXY` coverage
- Ollama availability
- embedding model readiness
- Qdrant connectivity
- Redis connectivity
- Codeshield interaction

- 代理环境
- `NO_PROXY` 是否覆盖本地服务
- Ollama 是否可用
- embedding 模型是否就绪
- Qdrant 连接是否正常
- Redis 连接是否正常
- Codeshield 交互是否异常

---

## Environment File / 环境文件

The deployment writes `~/.memory_env`, which is sourced by scheduled jobs and helper scripts.  
部署会写入 `~/.memory_env`，供定时任务和辅助脚本统一读取。

Important variables / 关键变量：

- `WORKSPACE_DIR`
- `OPENCLAW_WORKSPACE`
- `OPENCLAW_SESSIONS_DIR`
- `USER_ID`
- `REDIS_HOST`
- `REDIS_PORT`
- `QDRANT_URL`
- `QDRANT_COLLECTION`
- `TR_COLLECTION`
- `OLLAMA_URL`
- `EMBEDDING_MODEL`
- `CURATION_MODEL`
- `NO_PROXY`
- `no_proxy`

When Codeshield is installed, `QDRANT_API_KEY` is sourced from `/run/openclaw-memory/secrets.env` instead of being stored in plaintext.  
当 Codeshield 已安装时，`QDRANT_API_KEY` 会从 `/run/openclaw-memory/secrets.env` 加载，而不是明文写入环境文件。

---

## Codeshield Integration / Codeshield 集成

When CODE SHIELD is present, Jarvis Memory automatically:
在已安装 CODE SHIELD 的环境中，Jarvis Memory 会自动：

1. Load `QDRANT_API_KEY` from Codeshield-managed tmpfs
2. Bypass Squid for local services with `NO_PROXY`
3. Configure OpenClaw `memorySearch` to use local Ollama
4. Mirror managed workspace content into the isolated `openclaw-svc` runtime when available

1. 从 Codeshield 管理的 tmpfs 中加载 `QDRANT_API_KEY`
2. 通过 `NO_PROXY` 绕过本地服务的代理
3. 自动把 OpenClaw `memorySearch` 配置为本地 Ollama
4. 在存在 `openclaw-svc` 时，把托管 workspace 同步到隔离运行时

---

## Key Scripts / 关键脚本

### Qdrant memory scripts / Qdrant 记忆脚本

- `store_memory.py`
- `smart_search.py`
- `search_memories.py`
- `harvest_sessions.py`
- `extract_facts.py`
- `daily_backup.py`
- `init_all_collections.py`
- `qd.py`

### Redis memory scripts / Redis 记忆脚本

- `cron_capture.py`
- `save_mem.py`
- `mem_retrieve.py`
- `search_mem.py`
- `cron_backup.py`

---

## File Layout / 文件结构

```text
jarvismemory/
├─ bootstrap/
│  ├─ bootstrap.sh
│  ├─ update.sh
│  ├─ diagnose.sh
│  └─ audit.sh
├─ workspace/
│  ├─ skills/
│  ├─ docs/
│  ├─ config/
│  └─ .projects/
├─ docs/
├─ templates/
├─ docker-compose.yml
├─ CHANGELOG.md
└─ README.md
```

---

## Safety Goal / 安全目标

- OpenClaw can be updated independently without destroying memory data
- This repo remains the source of truth for memory deployment
- Re-running bootstrap or update restores managed files and schedules

- OpenClaw 可以独立升级而不破坏记忆数据
- 本仓库是记忆部署的可信来源
- 重新执行 bootstrap 或 update 可以恢复托管文件和定时任务
