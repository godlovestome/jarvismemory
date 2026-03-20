# Jarvis Memory Bootstrap

`Jarvis Memory + True Recall` 的 GitHub 部署仓库。

This repository turns the currently working VPS deployment into a repeatable
bootstrap flow for future OpenClaw installs.

---

## What This Repo Is For / 仓库用途

- Rebuild deployment from GitHub instead of the retired SpeedyFox GitLab.
- Keep Jarvis Memory and True Recall outside the OpenClaw app codebase.
- Re-sync managed files after OpenClaw updates without rebuilding everything by hand.
- Preserve the current live architecture instead of replacing it with a new one.

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
| 7 | Run final audit | 执行最终检查 |

**Configurable defaults / 可配置默认值：**

| Variable | Default | Description / 说明 |
|----------|---------|---------------------|
| `OPENCLAW_USER` | `openclaw` | System user / 系统用户 |
| `TIMEZONE` | `America/Los_Angeles` | System timezone / 系统时区 |
| `EMBEDDING_MODEL` | `mxbai-embed-large` | Embedding model / 向量嵌入模型 |
| `CURATION_MODEL` | `qwen3.5:35b-a3b` | LLM for curation / 记忆整理模型 |
| `TR_SCHEDULE` | `30 10 * * *` | True Recall daily run / True Recall 每日执行 |
| `BACKUP_SCHEDULE` | `0 11 * * *` | Daily backup / 每日备份 |
| `SLIDING_SCHEDULE` | `30 11 * * *` | Sliding backup / 滑动备份 |

Override any variable before running:

运行前可直接覆盖变量：

```bash
sudo TIMEZONE=Asia/Shanghai EMBEDDING_MODEL=nomic-embed-text bash bootstrap/bootstrap.sh
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

Output uses `[PASS]` / `[FAIL]` / `[WARN]` indicators.

输出使用 `[PASS]` / `[FAIL]` / `[WARN]` 标识每项状态。

**Common fix for proxy environments / 代理环境常见修复：**

If running behind CodeShield or a corporate proxy, ensure `.memory_env` contains:

在 CodeShield 或企业代理环境下，确保 `.memory_env` 包含：

```bash
export NO_PROXY=127.0.0.1,localhost,10.0.0.0/8,::1
export no_proxy=127.0.0.1,localhost,10.0.0.0/8,::1
```

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
| `EMBEDDING_MODEL` | Embedding model name / 嵌入模型名称 |
| `CURATION_MODEL` | LLM for memory curation / 记忆整理模型 |
| `QDRANT_API_KEY` | Optional Qdrant auth key / 可选认证密钥 |
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
