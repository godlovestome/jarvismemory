# Changelog

## [2.0.14] - 2026-03-23

### Added / Changed

- `memory-qdrant` now falls back to the restricted CodeShield runtime secret file `/run/openclaw-memory/secrets.env` when `QDRANT_API_KEY` is not present in the process environment.
- OpenClaw runtime config now pins `memory-qdrant` in `plugins.allow`, preventing untracked-local-plugin trust warnings while keeping trust explicit.
- Refreshed the README and package version so the repository matches the hardened CodeShield runtime behavior.

### 新增 / 调整

- 当进程环境里没有 `QDRANT_API_KEY` 时，`memory-qdrant` 现在会回退读取受限的 CodeShield 运行时密钥文件 `/run/openclaw-memory/secrets.env`。
- OpenClaw 运行时配置现在会把 `memory-qdrant` 固定写入 `plugins.allow`，在保持显式信任的同时，避免未追踪本地插件告警。
- README 与插件版本号已同步更新，使仓库说明与加固后的 CodeShield 运行时行为保持一致。

## [2.0.13] - 2026-03-23

### Added / Changed

- Added a real installable OpenClaw `memory-qdrant` plugin for True Recall auto-recall.
- Bootstrap and lossless update now install and enable that plugin for both `openclaw` and `openclaw-svc`.
- The plugin is restricted to local `127.0.0.1` Qdrant and Ollama endpoints so retrieval stays inside the CodeShield boundary.
- True Recall runtime config now passes `userId`, collection, embedding model, and recall thresholds into the plugin.
- Refreshed the README and changelog in clean UTF-8 bilingual form with fresh-install and lossless-update instructions.

### 新增 / 调整

- 新增真正可安装的 OpenClaw `memory-qdrant` 插件，用于 True Recall 自动召回。
- 安装与无损更新现在会为 `openclaw` 与 `openclaw-svc` 两套运行时安装并启用该插件。
- 插件被限制为只访问本机 `127.0.0.1` 的 Qdrant 和 Ollama，确保检索始终留在 CodeShield 边界内。
- True Recall 运行时配置现在会把 `userId`、collection、embedding 模型和召回阈值传给插件。
- README 与 changelog 已重新整理为干净的 UTF-8 中英双语文本，并补齐全新安装与无损更新说明。

## [2.0.12] - 2026-03-23

### Added / Changed

- True Recall gem storage now treats Qdrant `202 Accepted` as a successful write, so acknowledged async upserts are counted correctly.
- True Recall gem storage continues to send the CodeShield-managed `QDRANT_API_KEY` and wait for Qdrant acknowledgement.
- Bootstrap and lossless update keep writing `plugins.entries.memory-qdrant.config` into both OpenClaw runtimes so auto-recall points at `true_recall` with `mxbai-embed-large`.
- Refreshed the README and changelog in clean UTF-8 bilingual form.

### 新增 / 调整

- True Recall 的 gems 写入现在会把 Qdrant 返回的 `202 Accepted` 视为成功写入，异步确认的 upsert 不会再被误判为失败。
- True Recall 的 gems 写入会继续携带 CodeShield 托管的 `QDRANT_API_KEY`，并等待 Qdrant 明确确认。
- 安装与无损更新会持续把 `plugins.entries.memory-qdrant.config` 写入两份 OpenClaw 运行时配置，使 auto-recall 直接指向 `true_recall`，并使用 `mxbai-embed-large`。
- README 与 changelog 已重新整理为干净的 UTF-8 中英双语文本。
