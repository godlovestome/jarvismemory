# Jarvis Memory v2.0.3

**Persistent Memory System for OpenClaw AI Agents**  
**面向 OpenClaw AI Agent 的持久记忆系统**

## Purpose / 目标

Jarvis Memory + True Recall is a persistent, cross-session memory layer that runs independently from OpenClaw built-in retrieval. It uses Qdrant for vector storage, Ollama for local embeddings and generation, and Redis for short-term buffering.

Jarvis Memory + True Recall 是独立于 OpenClaw 内置检索之外的跨会话持久记忆层。它使用 Qdrant 进行向量存储，使用 Ollama 提供本地 embedding 与生成，使用 Redis 做短期缓冲。

**Version focus / 版本重点：v2.0.3**

- Repairs README and changelog Chinese text as clean UTF-8 bilingual docs.
- Keeps the documented coexistence model with OpenClaw QMD retrieval.

- 修复 README 与 changelog 的中文乱码，统一为 UTF-8 双语文档。
- 保留并明确说明与 OpenClaw QMD 检索并存的运行方式。

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

This update path does not wipe existing memory data, Qdrant state, Redis state, `.memory_env`, or CODE SHIELD integration.

这条更新路径不会清空已有记忆数据、Qdrant 状态、Redis 状态、`.memory_env` 或 CODE SHIELD 集成。

## Coexistence with QMD / 与 QMD 的并存关系

Jarvis Memory and OpenClaw QMD retrieval can run together:

Jarvis Memory 与 OpenClaw 的 QMD 检索可以同时存在：

| Item / 项目 | OpenClaw built-in retrieval | Jarvis Memory + True Recall |
| --- | --- | --- |
| Backend / 后端 | `memory_search` or `memory.qmd` | Qdrant + Redis + managed workspace |
| Primary role / 主要职责 | session retrieval / 会话检索 | long-term memory / 长期记忆 |
| Storage / 存储 | SQLite or QMD index | Qdrant / Redis / workspace files |
| Update path / 更新路径 | OpenClaw or custom_qmd | `bootstrap/update.sh` |

QMD can serve OpenClaw built-in retrieval without replacing Jarvis Memory.

QMD 可以承担 OpenClaw 的内置检索，但不会替代 Jarvis Memory。

## What Bootstrap Does / Bootstrap 会做什么

1. Install host dependencies
2. Start Redis and Qdrant with Docker
3. Validate Ollama and pull required models
4. Sync managed workspace files
5. Write `.memory_env`
6. Configure cron jobs and maintenance tasks
7. Keep service runtime files aligned with OpenClaw / CODE SHIELD

1. 安装宿主机依赖
2. 通过 Docker 启动 Redis 和 Qdrant
3. 检查 Ollama 并拉取所需模型
4. 同步受管 workspace 文件
5. 写入 `.memory_env`
6. 配置 cron 任务与维护任务
7. 保持与 OpenClaw / CODE SHIELD 的运行时文件对齐

## Recommended Operations / 推荐操作

```bash
sudo bash bootstrap/bootstrap.sh
sudo bash bootstrap/update.sh
docker ps
redis-cli ping
curl http://127.0.0.1:6333/collections
```

## Notes / 说明

- Update OpenClaw independently when needed.
- Keep secrets under CODE SHIELD when CODE SHIELD is installed.
- Use `bootstrap/update.sh` for production-safe maintenance.

- 需要时可以独立升级 OpenClaw。
- 如果已经安装 CODE SHIELD，请继续让密钥由 CODE SHIELD 接管。
- 生产环境维护请优先使用 `bootstrap/update.sh`。
