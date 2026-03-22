# Changelog

All notable changes to Jarvis Memory are documented here.

## [2.0.1] - 2026-03-22

### Added
- Service-runtime workspace sync: when `openclaw-svc` exists, `bootstrap.sh` and `update.sh` now mirror repo-managed workspace files into `/var/lib/openclaw-svc/.openclaw/workspace`.
- Service-runtime environment sync: the managed `.memory_env` is now written for both the interactive `openclaw` workspace and the isolated `openclaw-svc` workspace.
- Regression coverage for the Codeshield-managed runtime path and non-destructive update documentation.

### Added (中文)
- 新增 service 运行时工作区同步：当 `openclaw-svc` 存在时，`bootstrap.sh` 和 `update.sh` 会将仓库托管的 workspace 文件同步到 `/var/lib/openclaw-svc/.openclaw/workspace`。
- 新增 service 运行时环境同步：托管的 `.memory_env` 现在会同时写入交互用户 `openclaw` 工作区和隔离运行用户 `openclaw-svc` 工作区。
- 新增回归测试，覆盖 Codeshield 管理运行时路径与无损更新说明。

## [2.0.0] - 2026-03-21

### Added
- CodeShield secret integration for `QDRANT_API_KEY`.
- Automatic OpenClaw `memorySearch` configuration for local Ollama.
- `diagnose.sh` checks for proxy, Ollama, Qdrant, Redis, and CodeShield interactions.
