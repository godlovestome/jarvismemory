# Jarvis Memory v2.0.12

**Persistent Memory for OpenClaw**  
**面向 OpenClaw 的持久记忆层**

## Purpose / 目标

Jarvis Memory + True Recall is a persistent cross-session memory stack for OpenClaw. It uses Redis for short-term staging, Qdrant for long-term vector storage, and Ollama for local embedding plus gem curation.

Jarvis Memory + True Recall 是一套面向 OpenClaw 的跨会话持久记忆栈。它使用 Redis 做短期暂存，使用 Qdrant 做长期向量存储，并使用 Ollama 负责本地 embedding 与 gems 提炼。

## Version Focus / 版本重点

`v2.0.12` focuses on reliable True Recall storage and retrieval under CodeShield:

- `curate_memories.py` now treats Qdrant `202 Accepted` as a successful write, so gems acknowledged asynchronously are no longer reported as failed.
- True Recall gem storage sends the CodeShield-managed `QDRANT_API_KEY` and waits for Qdrant acknowledgement.
- `bootstrap.sh` and `bootstrap/update.sh` write the `memory-qdrant` auto-recall plugin config into both OpenClaw runtimes, pointing recall at `true_recall` with `mxbai-embed-large`.
- The default curator model remains `qwen3.5:35b-a3b`, and legacy temporary fallback `qwen3:14b` is normalized back during bootstrap or update.
- CodeShield-managed secrets stay outside `.memory_env` and continue to load only from `/run/openclaw-memory/secrets.env`.

`v2.0.12` 重点修复 CodeShield 框架下 True Recall 的存储与检索链路：

- `curate_memories.py` 现在会把 Qdrant 返回的 `202 Accepted` 视为成功写入，避免 gems 已被异步确认却仍显示 `Stored 0/x`。
- True Recall 的 gems 写入会携带 CodeShield 托管的 `QDRANT_API_KEY`，并等待 Qdrant 明确确认。
- `bootstrap.sh` 与 `bootstrap/update.sh` 会把 `memory-qdrant` auto-recall 插件配置写入两份 OpenClaw 运行时配置，使检索直接指向 `true_recall`，并使用 `mxbai-embed-large` 做查询 embedding。
- 默认 curator 模型继续保持为 `qwen3.5:35b-a3b`，旧的临时回退模型 `qwen3:14b` 会在安装或更新时自动纠正回来。
- CodeShield 托管的密钥不会写入 `.memory_env`，运行时仍只从 `/run/openclaw-memory/secrets.env` 加载。

## CodeShield Compatibility / CodeShield 兼容性

This repository is designed to run inside the CodeShield security model, not around it.

- Secrets remain managed by CodeShield.
- Runtime secrets are sourced only from `/run/openclaw-memory/secrets.env`.
- OpenClaw can continue running as `openclaw-svc`.
- Jarvis Memory cron jobs only read active session transcripts.
- No Telegram token, Qdrant API key, or other protected secret needs to be copied into OpenClaw onboarding or plaintext repo config.

本仓库的设计目标是在 CodeShield 安全框架之内运行，而不是绕过它。

- 密钥继续由 CodeShield 接管。
- 运行时密钥只从 `/run/openclaw-memory/secrets.env` 加载。
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
curl -fsSL https://raw.githubusercontent.com/godlovestome/jarvismemory/main/bootstrap/update.sh | sudo bash
```

The lossless update path keeps:

- existing OpenClaw user parameters
- existing CodeShield-managed secrets
- existing Redis / Qdrant data
- existing cron schedule

无损更新路径会保留：

- 现有 OpenClaw 用户参数
- 现有 CodeShield 托管密钥
- 现有 Redis / Qdrant 数据
- 现有 cron 调度

## Runtime Behavior / 运行时行为

1. `cron_capture.py` captures recent OpenClaw turns from the active runtime session directory.
2. The Redis buffer stores staged turns under `mem:<user_id>`.
3. `curate_memories.py` extracts high-signal gems and stores them into `true_recall`.
4. `memory-qdrant` auto-recall injects relevant gems from `true_recall` before replies.
5. Jarvis Memory backup jobs can still flush the same Redis source turns into the long-term memory pipeline.

1. `cron_capture.py` 会从当前活跃运行时的 session 目录抓取最近对话。
2. Redis 会把这些 turn 暂存到 `mem:<user_id>`。
3. `curate_memories.py` 会提炼高价值 gems 并写入 `true_recall`。
4. `memory-qdrant` auto-recall 会在回复前从 `true_recall` 注入相关 gems。
5. Jarvis Memory 备份任务仍可继续把同一份 Redis 源 turn 刷入长期记忆流水线。

## Operations / 运维命令

### Rebuild True Recall Gems / 重建 True Recall gems

```bash
sudo bash bootstrap/rebuild_true_recall.sh
```

### Manual Curator Run / 手动运行 curator

```bash
sudo -u openclaw bash -lc 'source ~/.memory_env && cd /home/openclaw/.openclaw/workspace/.projects/true-recall && python3 tr-process/curate_memories.py --user-id "$USER_ID"'
```

### Inspect Redis Backlog / 查看 Redis 暂存队列

```bash
sudo -u openclaw bash -lc 'source ~/.memory_env && redis-cli LLEN mem:$USER_ID'
```
