# Jarvis Memory v2.0.5

**Persistent Memory for OpenClaw**  
**面向 OpenClaw 的持久记忆层**

## Purpose / 目标

Jarvis Memory + True Recall is a persistent, cross-session memory stack for OpenClaw. It uses Redis for short-term staging, Qdrant for long-term vector storage, and Ollama for local embedding plus curation.

Jarvis Memory + True Recall 是一套面向 OpenClaw 的跨会话持久记忆栈。它使用 Redis 做短期暂存，使用 Qdrant 做长期向量存储，使用 Ollama 做本地 embedding 与记忆提炼。

## Version Focus / 版本重点

`v2.0.5` hardens CodeShield deployments in two ways:

- True Recall cron now follows the live `openclaw-svc` session runtime under CodeShield and falls back safely to `/home/openclaw` when no isolated runtime exists.
- Legacy curator defaults such as `qwen3.5:35b-a3b` are auto-migrated to the lighter `qwen3:14b`, avoiding out-of-memory failures on typical 32 GB hosts.
- README and changelog remain clean UTF-8 bilingual documents.

`v2.0.5` 进一步加固了 CodeShield 部署：

- True Recall 的 cron 现在会优先跟随 CodeShield 下真实运行的 `openclaw-svc` session 目录；如果没有隔离运行时，会安全回退到 `/home/openclaw`。
- 像 `qwen3.5:35b-a3b` 这样的旧 curator 默认值会自动迁移到更轻量的 `qwen3:14b`，避免在常见 32 GB 主机上出现内存不足。
- README 与 changelog 持续保持为干净的 UTF-8 双语文档。

## CodeShield Compatibility / 与 CodeShield 的兼容方式

This repository is designed to run **inside** the CodeShield security model, not around it.

- Secrets remain managed by CodeShield.
- OpenClaw can continue running as `openclaw-svc`.
- Jarvis Memory cron jobs only read the active session transcripts; they do not bypass CodeShield secret ownership or inject credentials into OpenClaw onboarding config.

本仓库的设计目标是在 **CodeShield 安全框架之内** 运行，而不是绕过它。

- 密钥继续由 CodeShield 接管。
- OpenClaw 可以继续以 `openclaw-svc` 身份运行。
- Jarvis Memory 的 cron 只读取当前活跃的 session transcript，不会绕过 CodeShield 的密钥托管，也不会把凭据重新写回 OpenClaw onboarding 配置。

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
- 现有由 CodeShield 托管的密钥
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

## Default Models / 默认模型

- Embedding: `mxbai-embed-large`
- Curator: `qwen3:14b`
- OpenClaw memorySearch: `qwen3-embedding:4b`

If an older deployment still carries the legacy curator default `qwen3.5:35b-a3b`, `bootstrap.sh` and `bootstrap/update.sh` will migrate it to `qwen3:14b` automatically unless you already set a different custom curator model.

- Embedding：`mxbai-embed-large`
- Curator：`qwen3:14b`
- OpenClaw memorySearch：`qwen3-embedding:4b`

如果旧部署仍保留 legacy curator 默认值 `qwen3.5:35b-a3b`，`bootstrap.sh` 与 `bootstrap/update.sh` 会自动把它迁移到 `qwen3:14b`；如果你已经显式指定了其他自定义 curator model，则不会覆盖。

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
