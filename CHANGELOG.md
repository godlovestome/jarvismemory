# Changelog

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

## [2.0.11] - 2026-03-23

- True Recall gem storage now sends the CodeShield-managed `QDRANT_API_KEY` and waits for Qdrant acknowledgement instead of failing silently.
- Bootstrap and lossless update now write `plugins.entries.memory-qdrant.config` into both OpenClaw runtimes so auto-recall points at `true_recall` with `mxbai-embed-large`.
- Reconfirmed the default curator model as `qwen3.5:35b-a3b` and kept the legacy `qwen3:14b` normalization path.
