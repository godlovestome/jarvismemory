# Jarvis Memory v2.0.4

**Persistent Memory for OpenClaw**  
**面向 OpenClaw 的持久记忆层**

## Purpose / 目标

Jarvis Memory + True Recall is a persistent, cross-session memory stack for OpenClaw. It uses Redis for short-term staging, Qdrant for long-term vector storage, and Ollama for local embedding plus curation.

Jarvis Memory + True Recall 是一套面向 OpenClaw 的跨会话持久记忆栈。它使用 Redis 做短期暂存，使用 Qdrant 做长期向量存储，使用 Ollama 做本地 embedding 与记忆提炼。

## Version Focus / 版本重点

`v2.0.4` fixes True Recall cron pickup under CodeShield-managed deployments:

- Cron and heartbeat jobs now prefer the live `openclaw-svc` session runtime when CodeShield isolates OpenClaw.
- Session discovery falls back safely to the classic `/home/openclaw` runtime when no service runtime exists.
- Audit output now shows which session source is active, making cron troubleshooting easier.
- README and changelog are kept as clean UTF-8 bilingual documents.

`v2.0.4` 重点修复了 CodeShield 托管部署下 True Recall 的 cron 拾取问题：

- 当 CodeShield 让 OpenClaw 运行在 `openclaw-svc` 隔离运行时中时，cron 与 heartbeat 会优先跟随该实时 session 源。
- 如果不存在 service runtime，会安全回退到传统的 `/home/openclaw` 运行时。
- `audit.sh` 现在会直接显示当前采用的 session 来源，便于排查 cron 与 gems 拾取问题。
- README 与 changelog 继续保持为干净的 UTF-8 双语文档。

## CodeShield Compatibility / 与 CodeShield 的兼容方式

This repository is designed to run **inside** the CodeShield security model, not around it.

- Secrets remain managed by CodeShield.
- OpenClaw can continue running as `openclaw-svc`.
- Jarvis Memory cron jobs only read the active session transcripts; they do not bypass CodeShield secret ownership or inject credentials into OpenClaw onboarding config.

本仓库的设计目标是在 **CodeShield 安全框架之内** 运行，而不是绕过它。

- 密钥继续由 CodeShield 接管。
- OpenClaw 仍可继续以 `openclaw-svc` 运行。
- Jarvis Memory 的 cron 任务只读取当前活跃 session transcript，不会绕过 CodeShield 的密钥托管，也不会把凭据重新写回 OpenClaw onboarding 配置。

## Quick Start / 快速开始

### Fresh Install / 一行代码全新安装

```bash
git clone https://github.com/godlovestome/jarvismemory.git && cd jarvismemory && sudo bash bootstrap/bootstrap.sh
```

### Lossless Update / 一行代码无损更新

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/update.sh
```

The lossless update path keeps:

- existing Redis data
- existing Qdrant collections and vectors
- existing `.memory_env`
- existing CodeShield-managed secrets
- existing OpenClaw / QMD coexistence

无损更新路径会保留：

- 现有 Redis 数据
- 现有 Qdrant collection 与向量数据
- 现有 `.memory_env`
- 现有由 CodeShield 接管的密钥
- 现有 OpenClaw / QMD 并存关系

## How It Works / 工作方式

1. `cron_capture.py` stages new session turns into Redis.
2. `curate_memories.py` reads staged turns and extracts higher-value gems into `true_recall`.
3. `cron_backup.py` flushes staged turns into `kimi_memories`.
4. `sliding_backup.sh` keeps rolling file backups.

1. `cron_capture.py` 将新的 session turn 暂存到 Redis。
2. `curate_memories.py` 读取暂存 turn，并把高价值 gems 提炼进 `true_recall`。
3. `cron_backup.py` 将暂存 turn 刷入 `kimi_memories`。
4. `sliding_backup.sh` 负责滚动文件备份。

## Default Schedule / 默认调度

- Every 5 minutes: `cron_capture.py`
- `10:30`: `curate_memories.py`
- `11:00`: `cron_backup.py`
- `11:30`: `sliding_backup.sh`

- 每 5 分钟：`cron_capture.py`
- `10:30`：`curate_memories.py`
- `11:00`：`cron_backup.py`
- `11:30`：`sliding_backup.sh`

All times are based on the host timezone configured during bootstrap.

以上时间均以 bootstrap 配置的宿主机时区为准。

## QMD Coexistence / 与 QMD 并存

Jarvis Memory and OpenClaw QMD retrieval are complementary:

- QMD serves document and knowledge-base retrieval for OpenClaw.
- Jarvis Memory + True Recall preserves cross-session memory and curated gems.

Jarvis Memory 与 OpenClaw QMD 检索是互补关系：

- QMD 负责文档与知识库检索。
- Jarvis Memory + True Recall 负责跨会话记忆与 gems 提炼。

## Useful Commands / 常用命令

```bash
sudo bash bootstrap/audit.sh
redis-cli LLEN mem:$USER_ID
tail -f /var/log/memory-capture.log
tail -f /var/log/true-recall-curator.log
```

## Changelog / 更新记录

See [CHANGELOG.md](/D:/23_QMD/jarvismemory/CHANGELOG.md).
