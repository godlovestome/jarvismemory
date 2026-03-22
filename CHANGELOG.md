# Changelog

All notable changes to Jarvis Memory are documented here.

## [2.0.2] - 2026-03-22

### Docs
- Clarified that Jarvis Memory and OpenClaw's QMD backend can coexist.
- Documented the split between built-in retrieval and long-term memory responsibilities.
- Refreshed the bilingual README and update guidance for Codeshield-based deployments.

## [2.0.1] - 2026-03-22

### Runtime sync
- Service-runtime workspace sync: when `openclaw-svc` exists, `bootstrap.sh` and `update.sh` now mirror repo-managed workspace files into `/var/lib/openclaw-svc/.openclaw/workspace`.
- Service-runtime environment sync: the managed `.memory_env` is now written for both the interactive `openclaw` workspace and the isolated `openclaw-svc` workspace.
