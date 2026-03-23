# Jarvis Memory v2.0.9

**Persistent Memory for OpenClaw**  
**面向 OpenClaw 的持久记忆层**

## Purpose / 目标

Jarvis Memory + True Recall is a persistent cross-session memory stack for OpenClaw. It uses Redis for short-term staging, Qdrant for long-term vector storage, and Ollama for local embedding plus gem curation.

Jarvis Memory + True Recall 是一套面向 OpenClaw 的跨会话持久记忆栈。它使用 Redis 做短期暂存，使用 Qdrant 做长期向量存储，使用 Ollama 做本地 embedding 与 gems 提炼。

## Version Focus / 版本重点

`v2.0.9` focuses on secure CodeShield operation and safe True Recall rebuilding:

- CodeShield-managed secrets stay outside `.memory_env`; runtime only sources them from `/run/openclaw-memory/secrets.env`.
- The regular True Recall curator model is restored to `qwen3.5:35b-a3b`.
- A new rebuild helper resets the `true_recall` collection, clears staged pickup state, and re-runs capture plus gem curation without moving secrets out of CodeShield.
- README and changelog are refreshed as clean UTF-8 bilingual documents.

`v2.0.9` 重点放在 CodeShield 安全运行与 True Recall 安全重建：

- CodeShield 托管的密钥不会写入 `.memory_env`，运行时只会从 `/run/openclaw-memory/secrets.env` 读取。
- True Recall 的常规 curator 模型恢复为 `qwen3.5:35b-a3b`。
- 新增安全重建脚本，可重置 `true_recall` collection、清空拾取状态，并重新执行 capture 与 gem 提炼，全程不把密钥移出 CodeShield。
- README 与 changelog 已刷新为干净的 UTF-8 双语文档。

## CodeShield Compatibility / CodeShield 兼容性

This repository is designed to run **inside** the CodeShield security model, not around it.

- Secrets remain managed by CodeShield.
- OpenClaw can continue running as `openclaw-svc`.
- Jarvis Memory cron jobs only read active session transcripts.
- No Telegram token, Qdrant API key, or other protected secret needs to be copied into OpenClaw onboarding or plaintext repo config.

本仓库的设计目标是在 **CodeShield 安全框架之内** 运行，而不是绕过它。

- 密钥继续由 CodeShield 接管。
- OpenClaw 可以继续以 `openclaw-svc` 身份运行。
- Jarvis Memory 的 cron 只读取当前活跃的 session transcript。
- Telegram token、Qdrant API key 等受保护密钥都不需要回填到 OpenClaw onboarding 或仓库明文配置里。

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

1. `cron_capture.py` 将新的 session turns 暂存到 Redis。
2. `curate_memories.py` 读取暂存 turns，并把高价值 gems 提炼进 `true_recall`。
3. `cron_backup.py` 将暂存 turns 刷入 `kimi_memories`。
4. `sliding_backup.sh` 负责滚动文件备份。

## Default Models / 默认模型

- Embedding: `mxbai-embed-large`
- Curator: `qwen3.5:35b-a3b`
- OpenClaw memorySearch: `qwen3-embedding:4b`
- Curator timeout: `1200`
- Curator max tokens: `1200`

If a deployment still carries the temporary curator fallback `qwen3:14b`, `bootstrap.sh` and `bootstrap/update.sh` normalize it back to `qwen3.5:35b-a3b`.

- Embedding：`mxbai-embed-large`
- Curator：`qwen3.5:35b-a3b`
- OpenClaw memorySearch：`qwen3-embedding:4b`
- Curator 超时：`1200`
- Curator 最大生成 tokens：`1200`

如果部署仍保留临时回退模型 `qwen3:14b`，`bootstrap.sh` 与 `bootstrap/update.sh` 会将其恢复到 `qwen3.5:35b-a3b`。

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

## Rebuild True Recall Gems / 重建 True Recall gems

When you need to clear existing True Recall vectors and rebuild them under CodeShield, use:

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/rebuild_true_recall.sh
```

This helper will:

- keep CodeShield-managed secrets outside `.memory_env`
- clear the staged Redis pickup buffer for the current `USER_ID`
- remove old capture state files
- recreate the `true_recall` collection
- re-run `cron_capture.py`
- re-run `curate_memories.py`

当你需要在 CodeShield 框架下清空旧的 True Recall 向量并重新拾取 gems 时，使用：

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/rebuild_true_recall.sh
```

该脚本会：

- 保持 CodeShield 托管密钥继续留在 `.memory_env` 之外
- 清空当前 `USER_ID` 的 Redis 暂存拾取缓冲
- 删除旧的 capture 状态文件
- 重建 `true_recall` collection
- 重新执行 `cron_capture.py`
- 重新执行 `curate_memories.py`

## Useful Commands / 常用命令

```bash
sudo bash bootstrap/audit.sh
sudo bash bootstrap/rebuild_true_recall.sh
redis-cli LLEN mem:$USER_ID
tail -f /var/log/memory-capture.log
tail -f /var/log/true-recall-curator.log
```

## Changelog / 更新记录

See [CHANGELOG.md](/D:/23_QMD/jarvismemory/CHANGELOG.md).
