# Parallel Memory Enhancement Design

**Date:** 2026-03-24

## Goal

Keep `True Recall` and `QMD` as two independent retrieval chains that both enhance OpenClaw answers without blocking each other.

## Required Behavior

- `True Recall` remains the long-term conversational memory system.
- `QMD` remains the SOP / policy / work-document retrieval system.
- Retrieval order is:
  1. `True Recall` gems
  2. `QMD` document results
- Each chain is optional at answer time:
  - if a chain returns relevant results, inject them
  - if a chain returns nothing, skip it silently
  - if a chain fails, log the failure and continue answering
- Main answering must continue even when one or both retrieval chains miss.

## Problems To Fix

### True Recall

- Full-history rebuild still misses service transcripts even when `.jsonl` files exist.
- The current transcript discovery path can report "No session transcripts found" without telling us whether:
  - the directory was unreachable
  - listing failed
  - files were unreadable
  - there were simply no matching transcripts
- Rebuild and cron diagnostics are too weak to separate ACL failures from normal empty-state behavior.

### QMD

- This repository currently manages `True Recall` plugin setup, but does not explicitly manage or audit the OpenClaw QMD configuration path.
- Audit output does not clearly show whether OpenClaw is configured for QMD, whether QMD is expected to run, and whether QMD timeouts are tuned for CPU-only hosts.

## Design

### 1. Stronger Transcript Discovery

Improve transcript discovery so it tests whether a session directory is truly listable by the runtime user rather than only checking `is_dir()`.

Behavior:

- explicit and discovered session directories should only be considered usable if the process can traverse and list them
- transcript enumeration should skip unreadable files but keep other readable files
- diagnostics should explain why directories or transcripts were skipped

### 2. Better Capture / Rebuild Diagnostics

`cron_capture.py` and `rebuild_true_recall.sh` should emit structured human-readable diagnostics when transcript discovery fails or partially succeeds.

Expected diagnostics:

- discovered session directories
- usable session directories
- transcript count per usable directory
- skipped directories with reason
- skipped transcript files with reason

These diagnostics should be especially clear for `--dry-run` and rebuild usage.

### 3. Explicit QMD Configuration Management

Bootstrap should manage the OpenClaw QMD configuration alongside the existing `memory-qdrant` plugin setup.

Expected configuration intent:

- QMD stays independent from `memory-qdrant`
- QMD is configured as an OpenClaw memory/document retrieval path
- QMD citations remain enabled
- QMD timeout is tuned higher for CPU-only environments
- bootstrap writes the config for both `openclaw` and `openclaw-svc` runtimes

### 4. Separate Audit Coverage

Audit should report `True Recall` and `QMD` independently so operators can tell:

- whether `memory-qdrant` is installed and enabled
- whether OpenClaw QMD settings are present
- whether transcript access is healthy
- whether the runtime can see the service session directory

## Non-Goals

- Do not merge `True Recall` and `QMD` into one storage layer.
- Do not make either retrieval chain mandatory for answering.
- Do not rewrite unrelated memory architecture.

## Success Criteria

- Rebuild logic can clearly diagnose and enumerate service transcripts.
- Transcript discovery tolerates partial readability instead of collapsing to zero.
- Bootstrap and audit explicitly manage and report QMD state.
- `True Recall` and `QMD` remain independent and are documented as parallel enhancement chains.
