# Changelog

## [2.0.21] - 2026-03-24

### Added / Changed

- Service session ACL repair is now recursive, covering both existing transcript files and future files created under the CodeShield service runtime.
- Rebuild now self-heals those ACLs before capture so root-triggered rebuild runs do not silently lose access.
- Installed OpenClaw plugin directories are now root-owned and world-readable, matching OpenClaw's trust expectations and avoiding suspicious-ownership plugin blocks.
- Audit collection checks now send the CodeShield-managed Qdrant API key when available, so local audits no longer misreport authorized collections as missing.

### 新增 / 调整

- service session ACL 修复现在改为递归方式，覆盖现有 transcript 文件以及后续在 CodeShield service runtime 下创建的新文件。
- 重建脚本在抓取前会先自愈这些 ACL，避免 root 触发的重建任务再次悄悄失去访问权限。
- 已安装的 OpenClaw 插件目录现在改为 root-owned 且全局可读，符合 OpenClaw 的信任预期，不再被当成可疑 ownership 插件阻断。
- audit 在可用时会携带 CodeShield 托管的 Qdrant API key，本地审计不再把本来可访问的 collection 误报为 missing。

## [2.0.20] - 2026-03-24

### Added / Changed

- Cron capture and rebuild now pass the CodeShield service session directory explicitly when it exists.
- This avoids silent fallback to `/home/openclaw/.openclaw/agents/main/sessions` when environment ordering or stale runtime values still point at the old home transcript tree.

### 新增 / 调整

- cron 抓取与重建流程现在会在 service runtime 存在时显式传入 CodeShield 的 service session 目录。
- 这样可以避免在环境变量顺序或旧运行时值仍指向 home transcript 树时，又悄悄退回 `/home/openclaw/.openclaw/agents/main/sessions`。

## [2.0.19] - 2026-03-23

### Added / Changed

- Session discovery now prefers the readable CodeShield service runtime transcript directory before falling back to the interactive home runtime.
- This prevents old home-session files from outranking the live `openclaw-svc` transcript stream during capture.
- `bootstrap/rebuild_true_recall.sh` now runs curator with `--hours 0`, so rebuild mode processes the staged backlog instead of reapplying the default 24-hour filter.

### 新增 / 调整

- session 发现逻辑现在会优先使用可读的 CodeShield service runtime transcript 目录，再回退到交互式 home runtime。
- 这样可以避免旧的 home-session 文件继续压过 live 的 `openclaw-svc` transcript 流。
- `bootstrap/rebuild_true_recall.sh` 现在会用 `--hours 0` 运行 curator，重建模式会处理当前暂存 backlog，而不会再次套用默认 24 小时过滤。

## [2.0.18] - 2026-03-23

### Added / Changed

- `bootstrap/update.sh` now works in both local-repo mode and `curl ... | sudo bash` mode.
- When no local repo context is available, the update flow now clones the repository into a temporary directory and sources `bootstrap.sh` and `audit.sh` from there.
- This fixes the broken one-line lossless update path that previously failed before any new True Recall code could reach the server.

### 新增 / 调整

- `bootstrap/update.sh` 现在同时支持本地 repo 模式和 `curl ... | sudo bash` 模式。
- 当没有本地 repo 上下文时，更新流程会先把仓库临时 clone 到临时目录，再从那里加载 `bootstrap.sh` 与 `audit.sh`。
- 这修复了之前“一行无损更新”在真正下发新 True Recall 代码前就提前失败的问题。

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
