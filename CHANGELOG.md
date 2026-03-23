# Changelog

## [2.0.11] - 2026-03-23

### Added / Changed

- True Recall gem storage now sends the CodeShield-managed `QDRANT_API_KEY` and waits for Qdrant acknowledgement instead of failing silently.
- Bootstrap and lossless update now write `plugins.entries.memory-qdrant.config` into both OpenClaw runtimes so auto-recall points at `true_recall` with `mxbai-embed-large`.
- Reconfirmed the default curator model as `qwen3.5:35b-a3b` and kept the legacy `qwen3:14b` normalization path.
- Refreshed the README and changelog in clean UTF-8 bilingual form.

### 新增 / 调整

- True Recall 的 gems 写入现在会携带 CodeShield 托管的 `QDRANT_API_KEY`，并等待 Qdrant 明确确认，不再静默失败。
- 安装与无损更新现在都会把 `plugins.entries.memory-qdrant.config` 写入两份 OpenClaw 运行时配置，使 auto-recall 直接指向 `true_recall`，并使用 `mxbai-embed-large`。
- 再次确认默认 curator 模型为 `qwen3.5:35b-a3b`，并保留旧的 `qwen3:14b` 自动纠正路径。
- 重新整理 README 与 changelog，统一为干净的 UTF-8 中英双语文本。

## [2.0.10] - 2026-03-23

- Stabilized cron pickup for CodeShield service sessions.
- Regenerated sliding backup cron to run through `/bin/bash`.
