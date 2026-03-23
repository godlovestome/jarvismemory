# Jarvis Memory v2.0.14

**Persistent Memory for OpenClaw**  
**面向 OpenClaw 的持久记忆层**

## Purpose / 目标

Jarvis Memory + True Recall gives OpenClaw a persistent, cross-session memory stack. Redis stages fresh turns, Qdrant stores long-term vectors, Ollama handles local embeddings and curation, and a real OpenClaw `memory-qdrant` plugin injects relevant True Recall gems before replies.

Jarvis Memory + True Recall 为 OpenClaw 提供跨会话持久记忆能力。Redis 暂存新对话，Qdrant 保存长期向量，Ollama 负责本地 embedding 与 gems 提炼，真正安装到 OpenClaw 里的 `memory-qdrant` 插件会在回复前注入相关的 True Recall gems。

## Version Focus / 版本重点

`v2.0.14` hardens the True Recall recall path under CodeShield:

- `memory-qdrant` is now a real installable OpenClaw plugin, not just a stale config entry.
- `bootstrap.sh` and `bootstrap/update.sh` install and enable the plugin for both `openclaw` and `openclaw-svc` runtimes.
- Plugin recall is limited to local `127.0.0.1` Qdrant and Ollama endpoints, keeping retrieval inside the CodeShield boundary.
- Plugin config carries only non-secret runtime values; Qdrant credentials still come only from `/run/openclaw-memory/secrets.env`.
- OpenClaw runtime now pins `memory-qdrant` in `plugins.allow`, so the plugin is treated as an explicitly trusted CodeShield-managed component.
- The default curator model remains `qwen3.5:35b-a3b`, and legacy fallback `qwen3:14b` is still normalized back automatically.

`v2.0.14` 重点加固 CodeShield 框架下的 True Recall 召回链路：

- `memory-qdrant` 现在是真正可安装的 OpenClaw 插件，不再只是一个会被忽略的配置项。
- `bootstrap.sh` 与 `bootstrap/update.sh` 会为 `openclaw` 和 `openclaw-svc` 两套运行时安装并启用该插件。
- 插件召回只允许访问本机 `127.0.0.1` 的 Qdrant 与 Ollama，保证检索始终留在 CodeShield 边界内。
- 插件配置只写入非敏感运行参数；Qdrant 密钥仍然只从 `/run/openclaw-memory/secrets.env` 加载。
- OpenClaw 运行时现在会把 `memory-qdrant` 固定写入 `plugins.allow`，把它明确标记为受信任的 CodeShield 托管插件。
- 默认 curator 模型保持为 `qwen3.5:35b-a3b`，旧的临时回退模型 `qwen3:14b` 仍会自动纠正回来。

## CodeShield Compatibility / CodeShield 兼容性

This repository is designed to run inside the CodeShield security framework, not around it.

- Secrets remain managed by CodeShield.
- Runtime secrets are sourced only from `/run/openclaw-memory/secrets.env`.
- OpenClaw can continue running as `openclaw-svc`.
- The recall plugin only talks to local Qdrant and Ollama addresses.
- No Telegram token, Qdrant API key, or other protected secret is copied into `.memory_env`, README examples, or OpenClaw onboarding.

本仓库的设计目标是在 CodeShield 安全框架之内运行，而不是绕过它。

- 密钥继续由 CodeShield 接管。
- 运行时密钥只从 `/run/openclaw-memory/secrets.env` 加载。
- OpenClaw 可以继续以 `openclaw-svc` 身份运行。
- 召回插件只访问本机的 Qdrant 和 Ollama 地址。
- Telegram token、Qdrant API key 等受保护密钥都不会写入 `.memory_env`、README 示例或 OpenClaw onboarding。

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

1. `cron_capture.py` collects recent OpenClaw turns from the active runtime session directory.
2. Redis stages those turns under `mem:<user_id>`.
3. `curate_memories.py` extracts high-signal gems and stores them into `true_recall`.
4. The installed `memory-qdrant` plugin queries local Qdrant with local Ollama embeddings and prepends relevant gems before replies.
5. Jarvis Memory backup jobs can still flush the same Redis source turns into the long-term memory pipeline.

1. `cron_capture.py` 会从当前活跃运行时的 session 目录抓取最近对话。
2. Redis 会把这些 turn 暂存到 `mem:<user_id>`。
3. `curate_memories.py` 会提炼高价值 gems 并写入 `true_recall`。
4. 已安装的 `memory-qdrant` 插件会使用本地 Ollama embedding 查询本地 Qdrant，并在回复前注入相关 gems。
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
