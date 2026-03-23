# Changelog

## [2.0.10] - 2026-03-23

### Fixed / 修复

- Made `session_runtime.py` skip unreadable session directories so CodeShield-isolated runtimes no longer crash `cron_capture.py` when `/var/lib/openclaw-svc/.../sessions` is temporarily inaccessible.
- Changed the managed cron block to run `sliding_backup.sh` through `/bin/bash`, avoiding backup failures on older deployments where the execute bit was missing.
- Refreshed the README and changelog as clean UTF-8 bilingual documents and added explicit ops-check commands for cron pickup, curator output, and Redis staging.

- 让 `session_runtime.py` 在遇到不可读的 session 目录时自动跳过，这样 CodeShield 隔离运行时下即使 `/var/lib/openclaw-svc/.../sessions` 暂时不可访问，也不会再把 `cron_capture.py` 直接打崩。
- 将托管 cron 中的 `sliding_backup.sh` 改为通过 `/bin/bash` 执行，避免旧部署因执行位丢失而导致备份任务失败。
- 将 README 与 changelog 刷新为干净的 UTF-8 中英双语文档，并补充 cron 拾取、curator 输出、Redis 暂存的显式检查命令。

## [2.0.9] - 2026-03-23

### Fixed / 修复

- Added `bootstrap/rebuild_true_recall.sh` for CodeShield-safe True Recall rebuilding: reset the `true_recall` collection, clear staged pickup state, and rerun capture plus gem curation without moving secrets into `.memory_env`.
- Repaired the root README and changelog as clean UTF-8 bilingual documents.
- Clarified that CodeShield-managed secrets stay outside `.memory_env` and are sourced only from the protected runtime path.

- 新增 `bootstrap/rebuild_true_recall.sh`，用于在 CodeShield 安全框架下重建 True Recall：重置 `true_recall` collection、清空拾取状态，并重新执行 capture 与 gem 提炼，全程不把密钥写入 `.memory_env`。
- 修复根 README 与 changelog，恢复为干净的 UTF-8 双语文档。
- 明确说明 CodeShield 托管密钥不会写入 `.memory_env`，只会从受保护的运行时路径加载。

## [2.0.8] - 2026-03-23

### Fixed / 修复

- Forced `format=json` for True Recall curator requests and added a JSON payload extraction fallback, reducing parse failures when the 35b model drifts into prose.

- 为 True Recall curator 请求强制启用 `format=json`，并增加 JSON payload 提取兜底，降低 35b 模型输出自然语言时的解析失败。

## [2.0.7] - 2026-03-23

### Fixed / 修复

- Restored the regular True Recall curator default to `qwen3.5:35b-a3b`.
- Treated `qwen3:14b` only as a temporary fallback and normalized it back during updates.
- Clarified that CodeShield-managed secrets stay outside `.memory_env` and are only sourced from the protected runtime path.

- 将 True Recall 的常规 curator 默认值恢复为 `qwen3.5:35b-a3b`。
- 将 `qwen3:14b` 仅视作临时回退值，并在更新时恢复到常规模型。
- 明确 CodeShield 托管的密钥不会写入 `.memory_env`，运行时只会从受保护路径加载。

## [2.0.6] - 2026-03-23

### Fixed / 修复

- Lowered the default True Recall curator generation ceiling for CPU-only deployments with `CURATION_TIMEOUT_SECONDS=1200` and `CURATION_NUM_PREDICT=1200`.
- Aligned `curate_memories.py`, `bootstrap.sh`, and `audit.sh` so fresh installs, lossless updates, and troubleshooting output all use the same safer defaults.

- 为 CPU-only 部署降低了 True Recall curator 的默认生成上限，引入 `CURATION_TIMEOUT_SECONDS=1200` 与 `CURATION_NUM_PREDICT=1200`。
- 对齐 `curate_memories.py`、`bootstrap.sh` 与 `audit.sh` 的默认值，使全新安装、无损更新与排障输出保持一致。
