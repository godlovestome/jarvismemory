# Jarvis Memory v2.0.23

Persistent memory for OpenClaw.
面向 OpenClaw 的持久记忆层。

## Overview / 概览

Jarvis Memory + True Recall gives OpenClaw a CodeShield-safe memory stack:

- Redis stages recent conversation data.
- True Recall extracts durable gems.
- Qdrant stores long-term vectors.
- The `memory-qdrant` OpenClaw plugin recalls relevant gems before replies.

Jarvis Memory + True Recall 为 OpenClaw 提供在 CodeShield 框架内运行的记忆链路：

- Redis 暂存最近对话。
- True Recall 提炼长期有效的 gems。
- Qdrant 保存长期向量。
- `memory-qdrant` 插件会在回复前召回相关 gems。

## Version Focus / 本版重点

`v2.0.23` adds a real one-time full-history rebuild path while keeping daily cron runs aligned to China early morning without changing the VDS timezone:

- `bootstrap/rebuild_true_recall.sh` now passes `--all-transcripts`, so rebuild mode sweeps every readable historical session transcript instead of only the latest `.jsonl`.
- Normal cron remains incremental, but the default schedule is now once per day at Los Angeles times that map to China early morning.
- Default cron window is now `11:05 / 11:30 / 12:00 / 12:30` in `America/Los_Angeles`, which corresponds to `02:05 / 02:30 / 03:00 / 03:30` in China during March 2026 daylight-saving time.

`v2.0.22` fixes the final Qdrant point-id write failure:

- Redis message items are now normalized into real conversation turns before curation.
- The curator prompt now matches the current True Recall turn schema.
- Gems are validated and normalized before Qdrant writes.
- Qdrant write failures now print the response body instead of failing as a black-box `400`.
- Invalid gems are skipped safely instead of crashing the whole run.
- Transcript capture and cron rebuild now explicitly pass `--sessions-dir /var/lib/openclaw-svc/...` when the CodeShield service runtime exists.
- `bootstrap/rebuild_true_recall.sh` now forces curator execution with `--hours 0`, so rebuild mode no longer drops staged turns because of the default 24-hour filter.
- Service session ACL repair is now recursive for existing and future transcript files.
- Installed OpenClaw plugin directories are now root-owned so OpenClaw no longer flags them as suspicious local ownership.
- Audit checks now use the CodeShield-managed Qdrant API key when available.
- True Recall gems now use stable UUIDv5 point IDs, which satisfies Qdrant's point-id format requirements.

`v2.0.22` 修复了最后一个 Qdrant point-id 写入失败问题：

- Redis 原始消息会先标准化成真正的 turn，再交给 curator。
- curator 提示词已对齐当前 True Recall 的 turn 结构。
- gem 在写入 Qdrant 前会先做校验与规范化。
- Qdrant 写入失败时会打印响应体，不再只是黑盒 `400`。
- 非法 gem 会被安全跳过，不会让整次任务崩掉。
- 在检测到 CodeShield service runtime 存在时，transcript 抓取和 cron 重建都会显式传入 `--sessions-dir /var/lib/openclaw-svc/...`。
- `bootstrap/rebuild_true_recall.sh` 现在会强制用 `--hours 0` 运行 curator，重建模式不再被默认 24 小时过滤误伤。
- 现在会递归修复 service session 的 ACL，覆盖已有 transcript 文件和后续新文件。
- 已安装的 OpenClaw 插件目录现在改为 root-owned，避免再被 OpenClaw 判定为可疑本地 ownership。
- audit 在可用时会携带 CodeShield 托管的 Qdrant API key。
- True Recall gems 现在使用稳定的 UUIDv5 作为 point ID，满足 Qdrant 对 point-id 格式的要求。

## CodeShield Safety / CodeShield 安全边界

- Secrets stay under CodeShield management.
- Runtime secrets are read from `/run/openclaw-memory/secrets.env`.
- No Qdrant API key or other protected secret is written into `.memory_env`.
- The recall plugin talks only to local `127.0.0.1` Qdrant and Ollama endpoints.

- 密钥继续由 CodeShield 托管。
- 运行时密钥从 `/run/openclaw-memory/secrets.env` 读取。
- 不会把 Qdrant API key 等受保护密钥写入 `.memory_env`。
- 召回插件只访问本机 `127.0.0.1` 的 Qdrant 和 Ollama。

## Fresh Install / 一行代码全新安装

```bash
git clone https://github.com/godlovestome/jarvismemory.git && cd jarvismemory && sudo bash bootstrap/bootstrap.sh
```

## Lossless Update / 一行代码无损更新

```bash
curl -fsSL https://raw.githubusercontent.com/godlovestome/jarvismemory/main/bootstrap/update.sh | sudo bash
```

The lossless update path keeps existing OpenClaw settings, CodeShield-managed secrets, Redis data, Qdrant data, and cron schedules.
无损更新会保留现有 OpenClaw 设置、CodeShield 托管密钥、Redis 数据、Qdrant 数据和 cron 调度。

## Common Operations / 常用命令

Rebuild True Recall gems from all readable historical transcripts:
从现有 transcript 强制重建 True Recall gems：

```bash
sudo bash bootstrap/rebuild_true_recall.sh
```

Default daily cron window (server stays on Los Angeles time):
```text
11:05 America/Los_Angeles  -> 02:05 China capture
11:30 America/Los_Angeles  -> 02:30 China True Recall curation (last 24h)
12:00 America/Los_Angeles  -> 03:00 China backup
12:30 America/Los_Angeles  -> 03:30 China sliding backup
```

Run the curator manually:
手动运行 curator：

```bash
sudo -u openclaw bash -lc 'source ~/.memory_env && cd /home/openclaw/.openclaw/workspace/.projects/true-recall && python3 tr-process/curate_memories.py --user-id "$USER_ID"'
```

Force curator to process all staged turns regardless of the 24-hour filter:
强制 curator 忽略 24 小时过滤，处理当前全部暂存 turn：

```bash
sudo -u openclaw bash -lc 'source ~/.memory_env && cd /home/openclaw/.openclaw/workspace/.projects/true-recall && python3 tr-process/curate_memories.py --user-id "$USER_ID" --hours 0'
```

Inspect staged Redis turns:
查看 Redis 暂存 turn：

```bash
sudo -u openclaw bash -lc 'source ~/.memory_env && redis-cli LLEN mem:$USER_ID'
```
