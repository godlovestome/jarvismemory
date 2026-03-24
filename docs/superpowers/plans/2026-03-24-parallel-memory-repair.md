# Parallel Memory Repair Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the parallel `True Recall` + `QMD` enhancement pipeline so transcript rebuilds are diagnosable and OpenClaw configuration explicitly supports both independent retrieval chains.

**Architecture:** Keep the retrieval chains separate. Strengthen transcript discovery and rebuild diagnostics for `True Recall`, and add explicit bootstrap/audit support for `QMD` so either chain can succeed, miss, or fail independently without blocking the base answer path.

**Tech Stack:** Python, Bash, OpenClaw JSON configuration, unittest

---

## Chunk 1: True Recall Transcript Discovery And Diagnostics

### Task 1: Make session directory discovery test real listability

**Files:**
- Modify: `D:\23_QMD\jarvismemory\workspace\skills\mem-redis\scripts\session_runtime.py`
- Test: `D:\23_QMD\jarvismemory\tests\test_session_runtime.py`

- [ ] **Step 1: Write the failing tests**

Add tests that prove:
- a directory that exists but cannot be listed is rejected
- transcript enumeration still returns readable files when one candidate raises a permission/stat error

- [ ] **Step 2: Run the target tests to verify they fail**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_session_runtime.py -v`
Expected: FAIL for the new directory-listability and partial-readability cases

- [ ] **Step 3: Write the minimal implementation**

Update `session_runtime.py` to:
- distinguish "is a directory" from "is listable"
- use safer enumeration that can keep readable transcripts when a sibling entry fails
- expose enough metadata for diagnostics

- [ ] **Step 4: Run the target tests to verify they pass**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_session_runtime.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add workspace/skills/mem-redis/scripts/session_runtime.py tests/test_session_runtime.py
git commit -m "fix: harden session discovery diagnostics"
```

### Task 2: Add capture and rebuild diagnostics for transcript visibility

**Files:**
- Modify: `D:\23_QMD\jarvismemory\workspace\skills\mem-redis\scripts\cron_capture.py`
- Modify: `D:\23_QMD\jarvismemory\bootstrap\rebuild_true_recall.sh`
- Test: `D:\23_QMD\jarvismemory\tests\test_session_runtime.py`
- Test: `D:\23_QMD\jarvismemory\tests\test_runtime_paths.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:
- rebuild script contains an explicit visibility probe / diagnostics step
- capture path has a diagnostic message path for empty discovery

- [ ] **Step 2: Run the target tests to verify they fail**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_session_runtime.py D:\23_QMD\jarvismemory\tests\test_runtime_paths.py -v`
Expected: FAIL for the new diagnostics assertions

- [ ] **Step 3: Write the minimal implementation**

Update:
- `cron_capture.py` to print useful discovery diagnostics when no transcripts are found or when running dry-run
- `rebuild_true_recall.sh` to run a visibility probe as `openclaw` before capture and print actionable details

- [ ] **Step 4: Run the target tests to verify they pass**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_session_runtime.py D:\23_QMD\jarvismemory\tests\test_runtime_paths.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add workspace/skills/mem-redis/scripts/cron_capture.py bootstrap/rebuild_true_recall.sh tests/test_session_runtime.py tests/test_runtime_paths.py
git commit -m "fix: add transcript rebuild diagnostics"
```

## Chunk 2: QMD Bootstrap And Audit Coverage

### Task 3: Manage QMD configuration separately from True Recall

**Files:**
- Modify: `D:\23_QMD\jarvismemory\bootstrap\bootstrap.sh`
- Test: `D:\23_QMD\jarvismemory\tests\test_runtime_paths.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert bootstrap writes explicit QMD configuration alongside, but separate from, `memory-qdrant`.

- [ ] **Step 2: Run the target tests to verify they fail**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_runtime_paths.py -v`
Expected: FAIL for missing QMD bootstrap assertions

- [ ] **Step 3: Write the minimal implementation**

Update `bootstrap.sh` to:
- add a dedicated QMD configuration function
- write QMD settings into each runtime's `openclaw.json`
- keep `memory-qdrant` config intact and separate
- set QMD-friendly timeout / citation defaults for CPU-only hosts

- [ ] **Step 4: Run the target tests to verify they pass**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_runtime_paths.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bootstrap/bootstrap.sh tests/test_runtime_paths.py
git commit -m "fix: configure qmd alongside true recall"
```

### Task 4: Expand audit output for independent chain health

**Files:**
- Modify: `D:\23_QMD\jarvismemory\bootstrap\audit.sh`
- Test: `D:\23_QMD\jarvismemory\tests\test_runtime_paths.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert audit reports:
- QMD configuration state
- True Recall plugin state
- transcript accessibility checks that actually reflect listability

- [ ] **Step 2: Run the target tests to verify they fail**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_runtime_paths.py -v`
Expected: FAIL for the new audit assertions

- [ ] **Step 3: Write the minimal implementation**

Update `audit.sh` to:
- print separate QMD and True Recall sections
- show effective session directory visibility checks
- show relevant OpenClaw config state for QMD and plugin state for `memory-qdrant`

- [ ] **Step 4: Run the target tests to verify they pass**

Run: `python -m unittest D:\23_QMD\jarvismemory\tests\test_runtime_paths.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bootstrap/audit.sh tests/test_runtime_paths.py
git commit -m "fix: audit parallel memory chains separately"
```

## Chunk 3: Final Verification

### Task 5: Run full verification for the repaired path

**Files:**
- Verify only

- [ ] **Step 1: Run the focused unit test suite**

Run:
`python -m unittest D:\23_QMD\jarvismemory\tests\test_session_runtime.py D:\23_QMD\jarvismemory\tests\test_curate_memories.py D:\23_QMD\jarvismemory\tests\test_runtime_paths.py -v`

Expected:
- exit code 0
- all tests passing

- [ ] **Step 2: Review the diff for unrelated regressions**

Run:
`git -C D:\23_QMD\jarvismemory diff --stat`

Expected:
- only the planned files changed

- [ ] **Step 3: Commit the integrated repair**

```bash
git add bootstrap/bootstrap.sh bootstrap/audit.sh bootstrap/rebuild_true_recall.sh workspace/skills/mem-redis/scripts/session_runtime.py workspace/skills/mem-redis/scripts/cron_capture.py tests/test_session_runtime.py tests/test_runtime_paths.py docs/superpowers/specs/2026-03-24-parallel-memory-design.md docs/superpowers/plans/2026-03-24-parallel-memory-repair.md
git commit -m "fix: harden parallel memory enhancement paths"
```
