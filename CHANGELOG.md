# Changelog

## [2.0.17] - 2026-03-23

### Added / Changed

- Normalized staged Redis message items into structured True Recall turns before curation.
- Rewrote the curator prompt so it matches the current turn schema instead of the legacy `kimi_memories` contract.
- Added gem payload normalization before Qdrant writes, including safe defaults for `importance`, `confidence`, `conversation_id`, `turn_range`, and `snippet`.
- Qdrant write failures now print the response body, making remote troubleshooting of `400 Bad Request` errors much easier.
- Invalid gems now fail closed and are skipped safely instead of crashing the whole curator run.
- Refreshed the README with clean UTF-8 bilingual usage, one-line fresh install, and one-line lossless update instructions.

### 新增 / 调整

- 在 curator 提炼前，先把 Redis 暂存消息标准化成结构化的 True Recall turn。
- 重写 curator 提示词，使其对齐当前 turn 结构，不再沿用旧的 `kimi_memories` 协议。
- 在写入 Qdrant 前增加 gem 规范化，补齐 `importance`、`confidence`、`conversation_id`、`turn_range`、`snippet` 等字段。
- Qdrant 写入失败时现在会打印响应体，远端排查 `400 Bad Request` 会更直观。
- 非法 gem 现在会安全跳过，不再让整个 curator 进程直接崩掉。
- README 已更新为干净的 UTF-8 中英双语说明，并补齐一行全新安装与一行无损更新命令。

## [2.0.16] - 2026-03-23

### Added / Changed

- Lossless update now rewrites `plugins.installs.memory-qdrant` with the correct runtime-specific `sourcePath`, `installPath`, and plugin version for both `openclaw` and `openclaw-svc`.
- This removes stale home-runtime provenance from the service runtime and lets OpenClaw treat the plugin as a properly tracked installed extension.

### 新增 / 调整

- 无损更新现在会为 `openclaw` 与 `openclaw-svc` 两套运行时重写 `plugins.installs.memory-qdrant`，同步正确的 `sourcePath`、`installPath` 与插件版本号。
- 这会移除 service runtime 里遗留的 home-runtime provenance，并让 OpenClaw 把该插件视为被正确追踪的已安装扩展。
