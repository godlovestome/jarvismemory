# Changelog

## [2.0.7] - 2026-03-23

### Fixed / 修复

- Restored the regular True Recall curator default to `qwen3.5:35b-a3b`.
- Treat `qwen3:14b` only as a temporary fallback and normalize it back during updates.
- Clarified that CodeShield-managed secrets stay outside `.memory_env` and are only sourced from the protected runtime path.

- 将 True Recall 的常规 curator 默认值恢复为 `qwen3.5:35b-a3b`。
- 将 `qwen3:14b` 仅视作临时回退值，并在更新时恢复到常规模型。
- 明确 CodeShield 托管的密钥不会写入 `.memory_env`，运行时只会从受保护路径加载。

## [2.0.6] - 2026-03-23

### Fixed / 修复

- Lowered the default True Recall curator generation ceiling for CPU-only deployments by introducing `CURATION_TIMEOUT_SECONDS=1200` and `CURATION_NUM_PREDICT=1200`.
- Aligned `curate_memories.py`, `bootstrap.sh`, and `audit.sh` so fresh installs, lossless updates, and troubleshooting output all use the same safer defaults.

- 为 CPU-only 部署引入了更稳的 True Recall curator 默认生成限制：`CURATION_TIMEOUT_SECONDS=1200` 与 `CURATION_NUM_PREDICT=1200`。
- 对齐了 `curate_memories.py`、`bootstrap.sh` 与 `audit.sh` 的默认值，使全新安装、无损更新与排障输出保持一致。

## [2.0.5] - 2026-03-23

### Fixed / 修复

- Fixed CodeShield True Recall pickup end-to-end by pairing session-runtime discovery with read-only service-session access.
- Auto-migrated the legacy curator default `qwen3.5:35b-a3b` to the lighter `qwen3:14b`, preventing Ollama out-of-memory failures on typical 32 GB hosts.
- Kept existing custom curator model settings untouched when they are not the legacy default.

- 修复了 CodeShield 下 True Recall 从 session 拾取到 gems 提炼的整条链路，结合了运行时 session 发现与只读 service-session ACL。
- 将 legacy curator 默认值 `qwen3.5:35b-a3b` 自动迁移到更轻量的 `qwen3:14b`，避免在常见 32 GB 主机上触发 Ollama 内存不足。
- 如果用户已经配置了非 legacy 的自定义 curator model，则继续保留，不会被覆盖。

### Docs / 文档

- Rewrote README as a clean UTF-8 bilingual document again.
- Documented the new default curator model and the one-line lossless update path.

- 再次重写 README，确保 UTF-8 双语文档干净可读。
- 补充新的默认 curator model 与一行代码无损更新说明。

## [2.0.4] - 2026-03-23

### Fixed / 修复

- Fixed True Recall cron pickup for CodeShield-managed OpenClaw deployments.
- Cron and heartbeat session discovery now prefer the live `openclaw-svc` runtime and safely fall back to `/home/openclaw`.
- Added runtime visibility to `bootstrap/audit.sh` so active session sources are visible during troubleshooting.

- 修复了 CodeShield 托管的 OpenClaw 部署中 True Recall cron 无法拾取 turns / gems 的问题。
- cron 与 heartbeat 的 session 发现逻辑现在会优先跟随实时的 `openclaw-svc` 运行时，并安全回退到 `/home/openclaw`。
- 为 `bootstrap/audit.sh` 增加了运行时可见性，排查时可以直接看到当前使用的 session 来源。
