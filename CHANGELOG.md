# Changelog

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

### Docs / 文档

- Refreshed README as clean UTF-8 bilingual documentation.
- Documented one-line fresh install and one-line lossless update commands.
- Clarified that Jarvis Memory continues to operate inside the CodeShield security framework.

- 将 README 刷新为干净的 UTF-8 双语文档。
- 补充了一行代码全新安装与一行代码无损更新命令。
- 明确说明 Jarvis Memory 继续在 CodeShield 安全框架内运行。

## [2.0.3] - 2026-03-23

### Docs / 文档

- Rewrote `README.md` and `CHANGELOG.md` as clean UTF-8 bilingual documents.
- Clarified that Jarvis Memory and OpenClaw QMD retrieval are meant to coexist.

- 重写 `README.md` 与 `CHANGELOG.md`，修复中文乱码并统一为 UTF-8 双语文档。
- 明确说明 Jarvis Memory 与 OpenClaw QMD 检索的并存关系。
