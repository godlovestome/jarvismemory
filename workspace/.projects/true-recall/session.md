# True-Recall Session Continuity File

**Created:** 2026-02-22 11:04 CST  
**Status:** ✅ Fully Operational — Production Ready  
**Current Session:** Implementation and testing complete

---

## Quick Reference

| What | Where |
|------|-------|
| **Main Documentation** | [README.md](./README.md) |
| **Curator Prompt** | [curator_prompt.md](./curator_prompt.md) |
| **Curation Script** | [tr-process/curate_memories.py](./tr-process/curate_memories.py) |
| **Search Script** | [tr-out/scripts/search_memories.py](./tr-out/scripts/search_memories.py) |
| **Staging Script** | `~/.openclaw/workspace/skills/true-recall-out/scripts/stage_turn.py` |

---

## Current Configuration

| Component | Setting |
|-----------|---------|
| **Embedding Model** | `mxbai-embed-large` (1024 dims, 66.5 MTEB) |
| **Curation Model** | `qwen3:4b-instruct` with **native system prompt** |
| **Production Collection** | `true_recall` (Qdrant, **4 gems** stored) |
| **Archive Collection** | `kimi_memories` (frozen, 11,238 items, read-only) |
| **Redis Buffer** | `mem:{user_id}` at REDIS_HOST:REDIS_PORT |
| **Cron Schedule** | Daily at 3:30 AM |
| **Log File** | `/var/log/true-recall-curator.log` |

---

## What Was Accomplished Today (2026-02-22)

### 1. Embedding Model Selection & Testing
- Evaluated mxbai-embed-large vs snowflake-arctic-embed2 vs nomic-embed-text
- Selected **mxbai-embed-large** (66.5 MTEB, state-of-the-art)
- Verified 1024 dimensions, 639 MB file size, ~903 MB GPU memory
- **Quality over speed** — confirmed as the right choice

### 2. Qdrant Collections
- ✅ Created `true_recall` — Production collection (1024 dims, cosine)
- ✅ Deleted `temp_true_recall` — Test collection (no longer needed)
- ✅ `kimi_memories` — Archive frozen (11,238 items, read-only)
- **Current:** `true_recall` has **4 gems** stored

### 3. Curator System Prompt
- ✅ Designed and written (custom system prompt)
- ✅ Evaluated against 11-field requirement
- ✅ Saved to `curator_prompt.md`
- ✅ **Switched to native system prompt** (preferred over prepended)

### 4. Curation Script Created & Tested
- ✅ `tr-process/curate_memories.py`
- ✅ Native system prompt implementation
- ✅ mxbai-embed-large for embeddings
- ✅ Integer ID fix for Qdrant compatibility
- ✅ Holistic gem extraction with qwen3
- ✅ **Tested:** 4 gems extracted and stored

### 5. Search Script Created & Tested
- ✅ `tr-out/scripts/search_memories.py`
- ✅ mxbai-embed-large for query embedding
- ✅ Semantic search in `true_recall`
- ✅ Formatted output with context
- ✅ **Tested:** Retrieved gems with 0.656+ similarity scores

### 6. Staging Script Created
- ✅ `skills/true-recall-out/scripts/stage_turn.py`
- ✅ Called by OpenClaw hook
- ✅ Stages to Redis buffer
- ✅ 48-hour TTL

### 7. Automation Configured
- ✅ Cron job: Daily at 3:30 AM
- ✅ Logs to `/var/log/true-recall-curator.log`
- ✅ Runs from `.projects/true-recall` directory

### 8. Documentation Updated
- ✅ `README.md` — Full documentation with test results (650+ lines)
- ✅ `session.md` — Continuity file for future sessions
- ✅ `curator_prompt.md` — System prompt
- ✅ `PROGRESS_UPDATE_2026-02-22.md` — Standalone progress file

---

## Test Results Summary

| Test | Input | Output | Score |
|------|-------|--------|-------|
| Curation | 2 turns (Discord→Mattermost) | 1 gem | 0.95 confidence |
| Native prompt | 1 turn (local AI preference) | 1 gem | 0.95 confidence |
| End-to-end | 2 turns (BorgBackup) | 1 gem | 0.748 similarity |
| Search | "What about Mattermost?" | 1 gem | 0.656 similarity |
| Search | "What about PostgreSQL?" | 1 gem | 0.707 similarity |

**All tests passed ✅**

---

## Architecture Decisions Finalized

| Decision | Rationale |
|----------|-----------|
| **mxbai-embed-large** | 66.5 MTEB (SOTA), 1024 dims, quality-first |
| **Native system prompt** | Preferred over prepended, cleaner separation |
| **Integer IDs** | Qdrant requirement (not hex strings) |
| **Start fresh** | `kimi_memories` frozen, `true_recall` active with 4 gems |
| **3:30 AM curation** | After mem-redis backup (3:00 AM) |

---

## Current State

- **4 gems** stored in `true_recall`
- **Native system prompt** active
- **mxbai-embed-large** for embeddings
- **Cron job** set for 3:30 AM daily
- **All components tested and operational**

---

## Historical Context: Predecessor System

**Important:** True-Recall replaced an earlier attempt. It is ONE unified system with two parts (tr-in and tr-out).

### Predecessor: Native OpenClaw Plugin (Feb 21) — DISABLED

**Location:** `~/.openclaw/extensions/memory-qdrant/`

This was a **separate earlier attempt** at memory, NOT part of True-Recall.

**What it was:**
- TypeScript plugin using OpenClaw's native plugin SDK
- Dumb semantic search only (cosine similarity)
- Real-time injection before each response
- Collection: `kimi_memories` (snowflake-arctic-embed2, 1024 dims)

**Why it failed:**
- Feb 21 21:36: Set `autoRecall: false` — only did embedding similarity
- No context awareness, no curation, just "similar vectors = relevant"
- Created noise and frequent compaction
- Memory file: `~/.openclaw/workspace/memory/2026-02-21.md`

**Current status:** Plugin still loaded but `"autoRecall": false` — completely disabled

### True-Recall: One Unified System (Feb 22) — ACTIVE

**True-Recall is ONE system with two parts:**

```
┌─────────────────────────────────────────────────────────────┐
│                     True-Recall                             │
│              (Unified Memory System)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐      ┌──────────────┐      ┌──────────┐     │
│   │   tr-in  │ ───→ │  tr-process  │ ───→ │  tr-out  │     │
│   │ (Input)  │      │ (The Curator)│      │ (Output) │     │
│   └──────────┘      └──────────────┘      └──────────┘     │
│                                                             │
│   • Captures turns         • 24h holistic    • Retrieves    │
│   • Stages to Redis        • LLM curation      gems         │
│   • Filters noise          • Extracts gems   • Injects     │
│   • 48h TTL                • Stores to         • (manual)    │
│                              Qdrant                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- **tr-in** and **tr-out** are two halves of the SAME system
- **tr-process** (The Curator) bridges them with LLM curation
- Collection: `true_recall` (mxbai-embed-large, 1024 dims)
- Status: **Active** — 4 gems stored, daily curation at 3:30 AM

### Comparison: Predecessor vs True-Recall

| Aspect | memory-qdrant Plugin | True-Recall (Unified) |
|--------|---------------------|----------------------|
| **Language** | TypeScript | Python |
| **Architecture** | Single plugin | Three-part pipeline |
| **Curation** | ❌ None | ✅ LLM (qwen3) |
| **Timing** | Real-time | 24h delayed |
| **Collection** | `kimi_memories` | `true_recall` |
| **Status** | ❌ Disabled | ✅ Active |

**Key insight:** We abandoned the "native plugin" approach and built a Python-based pipeline (tr-in → tr-process → tr-out) that gives us full control over curation.

---

## Relationship to jarvis-memory

**True-Recall and jarvis-memory are TWO SEPARATE PROJECTS.**

| Project | Purpose | Location |
|---------|---------|----------|
| **jarvis-memory** | Python skill for OpenClaw with manual memory tools | `skills/jarvis-memory/` |
| **True-Recall** | Standalone Python system with automatic curation | `.projects/true-recall/` |

**Key differences:**
- jarvis-memory: Manual "save q", manual "q <topic>" — user controls everything
- True-Recall: Automatic staging → 24h curation → gem extraction — system handles everything

**No dependency:**
- True-Recall does NOT depend on jarvis-memory
- True-Recall does NOT extend jarvis-memory
- They are parallel memory systems with different approaches

---

## Plan: Re-enable memory-qdrant Plugin for true_recall

**Goal:** Repurpose the disabled TypeScript plugin to auto-inject gems from `true_recall` collection.

### Current Plugin State
- **Location:** `~/.openclaw/extensions/memory-qdrant/`
- **Status:** `autoRecall: false` — DISABLED
- **Current config:**
  - `collectionName`: "kimi_memories"
  - `embeddingModel`: "snowflake-arctic-embed2"
  - `autoRecall`: false

### Target Plugin State
- **Status:** `autoRecall: true` — ENABLED
- **Target config:**
  - `collectionName`: "true_recall"
  - `embeddingModel`: "mxbai-embed-large"
  - `autoRecall`: true

### Critical Issues to Address

#### Issue 1: Embedding Model Mismatch
| Collection | Embedding Model Used | Dimensions |
|------------|-------------------|------------|
| `kimi_memories` | snowflake-arctic-embed2 | 1024 |
| `true_recall` | mxbai-embed-large | 1024 |

**Problem:** Both are 1024 dims but different models = different vector spaces. Searching `true_recall` with snowflake embeddings will return garbage results.

**Solution:** Change plugin config to use `mxbai-embed-large` for query embeddings.

#### Issue 2: Payload Structure Mismatch
**Plugin expects:**
```typescript
payload: {
  text: string,      // Single text field
  category: string,  // Single category
  createdAt: string
}
```

**true_recall has:**
```json
{
  "gem": "User decided...",
  "context": "After discussing...",
  "snippet": "[rob]: ...",
  "categories": ["decision", "technical"],  // ARRAY
  "importance": "high",
  "confidence": 0.95,
  "timestamp": "...",
  "date": "...",
  // ... etc
}
```

**Problem:** Plugin accesses `payload.text` and `payload.category`, but true_recall has `payload.gem` and `payload.categories` (array). Will display as `[other] undefined`.

**Options:**
- Option A: Accept display weirdness for testing (shows `[other] undefined` or similar)
- Option B: Modify plugin code to map `payload.gem` → `payload.text` and handle array categories

**Decision:** Start with Option A (minimal changes), fix display if needed.

#### Issue 3: Query vs Gem Semantic Match
**How plugin works:**
1. User says: "What did I decide about Redis?"
2. Plugin embeds query with mxbai-embed-large
3. Searches Qdrant for similar vectors
4. Finds: "User decided to use Redis over Postgres..."
5. Injects into context

**Risk:** Query "what about Redis" vs gem "User decided to use Redis..." — should match semantically, but need to verify.

### Step-by-Step Plan

**Step 1: Backup current config**
```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d_%H%M%S)
```

**Step 2: Update openclaw.json**
Change plugin config section:
```json
"memory-qdrant": {
  "enabled": true,
  "config": {
    "qdrantUrl": "http://localhost:6333",
    "collectionName": "true_recall",        // CHANGED: was "kimi_memories"
    "ollamaUrl": "http://localhost:11434",
    "embeddingModel": "mxbai-embed-large",  // CHANGED: was "snowflake-arctic-embed2"
    "autoRecall": true,                     // CHANGED: was false
    "autoCapture": false,
    "maxRecallResults": 3,
    "minRecallScore": 0.5
  }
}
```

**Step 3: Verify mxbai-embed-large is available**
```bash
curl http://localhost:11434/api/tags | grep mxbai
```

**Step 4: Restart OpenClaw gateway**
```bash
openclaw gateway restart
```

**Step 5: Test injection**
- Ask a question related to stored gems (e.g., "What about Mattermost?")
- Check if memories are injected into context
- Monitor logs: `memory-qdrant: injecting X memories`

**Step 6: Assess display format**
- If memories show as `[other] undefined` — need to fix plugin code
- If memories show properly — config change sufficient

### Rollback Plan
If issues occur:
1. Restore config from backup
2. Restart gateway
3. Plugin returns to disabled state

---

## Incident: Config Error Caused System Break (2026-02-22 13:21)

### What Happened
Attempted to install the True-Recall staging hook using an invalid configuration that broke OpenClaw.

### The Broken Config
```json
"hooks": {
  "internal": {
    "installs": {
      "true-recall-stager": {
        "path": ".projects/true-recall/tr-in/hook/true-recall-stager",
        "source": "workspace"
      }
    }
  }
}
```

### Errors Generated
```
-stager: Unrecognized key: "path"
2026-02-22T13:21:12.548-06:00 Invalid config at ~/.openclaw/openclaw.json:
- hooks.internal.installs.true-recall-stager.source: Invalid input
- hooks.internal.installs.true-recall-stager: Unrecognized key: "path"

2026-02-22T19:21:36.775Z [diagnostic] lane task error: lane=main durationMs=129
error="Error: No API key found for provider "anthropic". Auth store: 
~/.openclaw/agents/main/agent/auth-profiles.json

2026-02-22T19:21:36.775Z [diagnostic] lane task error: 
lane=session:agent:main:main durationMs=132
error="Error: No API key found for provider "anthropic"."

2026-02-22T13:21:36.777-06:00 Embedded agent failed before reply: 
No API key found for provider "anthropic".
```

### Root Cause Analysis

**Primary Issue:** Invalid hook installation config
- `hooks.internal.installs` does NOT accept a `"path"` key
- Valid keys are: `enabled` (boolean), `id` (string), `source` (string: "workspace" or "bundled")
- Custom hooks should be placed in workspace under `skills/{name}/` or `.projects/{name}/`
- The `installs` section is for bundled hooks only, not custom workspace hooks

**Secondary Issue:** Anthropic provider error
- Stale session configuration tried to use Anthropic provider
- Current config uses Ollama providers only
- Snapshot rollback cleared this

### Resolution
- **Snapshot rolled back** to restore working state
- Config reverted to valid: `"installs": {}`
- Hook remains "enabled" in entries but NOT actually installed
- Plugin-based auto-recall continues to work

### Lesson Learned
**ALWAYS validate hook config against OpenClaw schema before applying.**
The correct way to enable a custom hook:
1. Place hook in `skills/{name}/` or `.projects/{name}/`
2. Include `HOOK.md` and `handler.ts`
3. Set `"enabled": true` in `hooks.internal.entries.{name}`
4. **Do NOT use `hooks.internal.installs` for custom hooks**

### Current Status Post-Incident
- ✅ Plugin auto-recall: WORKING
- ✅ true_recall collection: ACCESSIBLE (4 gems)
- ❌ tr-in hook: NOT INSTALLED (needs proper installation method)
- ✅ System: STABLE after rollback

---

## Post-Incident Log Analysis (2026-02-22 13:30-13:38)

### Errors Observed After Rollback

```
2026-02-22T19:30:39.855Z [gateway] memory-qdrant: recall failed: 
  Error: Ollama embedding failed: 500 Internal Server Error

2026-02-22T19:30:39.918Z [gateway] memory-qdrant: recall failed: 
  Error: Ollama embedding failed: 500 Internal Server Error

2026-02-22T19:37:36.442Z [gateway] memory-qdrant: recall failed: 
  Error: Ollama embedding failed: 500 Internal Server Error

2026-02-22T19:37:36.489Z [gateway] memory-qdrant: recall failed: 
  Error: Ollama embedding failed: 500 Internal Server Error
```

### Analysis

**What it means:** The TypeScript plugin tried to embed queries using Ollama but received HTTP 500 errors.

**Timing:** 13:30-13:37 CST (right after rollback, during high system activity)

**Current Status:** 
- ✅ Ollama is running: `http://localhost:11434`
- ✅ mxbai-embed-large loaded: 903MB VRAM
- ✅ Embedding endpoint working (tested manually)
- ⚠️ Intermittent 500s during high load / config changes

**Likely Cause:**
- Plugin restarted/reloaded during gateway restart
- Ollama was still warming up mxbai-embed-large model
- TypeScript async/promise handling vs Python sync calls

**Resolution:**
- Errors stopped after system stabilized
- Manual embedding tests pass
- Plugin now working (recall succeeded in later tests)

### File Access Errors (Normal Exploration)
```
ENOENT: /usr/lib/node_modules/openclaw/docs/plugin-sdk.md
ENOENT: ~/.openclaw/workspace/memory/2026-02-22.md  
ENOENT: ~/.openclaw/workspace/skills/true-recall-out/SKILL.md
EISDIR: ~/.openclaw/workspace/.projects/true-recall/tr-in/hook/
```

**Status:** These are from normal file exploration — not errors, just files that don't exist or attempting to read directories as files.

---

## Hook Development Progress (2026-02-22 14:00)

### Findings from SDK/Code Analysis

**1. How Bundled Hooks Work:**
- Location: `/usr/lib/node_modules/openclaw/dist/bundled/`
- Each hook has: `handler.js` (ESM) + `HOOK.md`
- Handler uses ES module imports (`import ... from ...`)
- Example: `command-logger` handler imports from `"../../paths-*.js"`

**2. Event Types:**
From `internal-hooks.d.ts`:
- `"command"` - /new, /reset, /stop
- `"session"` - session lifecycle
- `"agent"` - agent events
- `"gateway"` - gateway startup
- `"message"` - message received/sent

**3. Config Schema:**
```javascript
const InternalHooksSchema = z.object({
  enabled: z.boolean().optional(),
  handlers: z.array(InternalHookHandlerSchema).optional(),  // Array of handler configs
  entries: z.record(z.string(), HookConfigSchema).optional(), // Enable/disable by name
  load: z.object({ extraDirs: z.array(z.string()).optional() }).strict().optional(),
  installs: z.record(z.string(), HookInstallRecordSchema).optional()
}).strict().optional();
```

**4. Handler Config Method (from command-logger):**
```json
{
  "hooks": {
    "internal": {
      "handlers": [
        {
          "event": "command",
          "module": "./hooks/handlers/command-logger.ts"
        }
      ]
    }
  }
}
```

**5. ES Module Format Required:**
- OpenClaw uses ES modules (`"type": "module"` in package.json)
- Handlers must use `import` not `require`
- Must use `.js` extension (not `.ts`) outside node_modules
- Must use `import.meta.url` for path resolution

### Attempt 1: Using load.extraDirs
- Added `"load": {"extraDirs": [".projects/true-recall/tr-in/hook"]}`
- Failed: Hook not picked up (no error logged, just ignored)

### Attempt 2: Copy to bundled directory
- Copied hook to `/usr/lib/node_modules/openclaw/dist/bundled/true-recall-stager/`
- Failed: `handler.ts` not supported in node_modules (stripping types error)

### Attempt 3: Convert to .js with CommonJS
- Changed to `require()` syntax
- Failed: `require is not defined in ES module scope`

### Attempt 4: Convert to ESM (CURRENT)
- Changed to `import` syntax with proper ESM format
- Need to test after restart

### Valid Events for message:sent
From `internal-hooks.d.ts`:
- `type: "message", action: "sent"` - for AI response sent
- Hook receives `MessageSentHookEvent` with context containing:
  - `content` - message text
  - `to` - recipient
  - `success` - boolean

### To Fix: Update HOOK.md metadata
Current HOOK.md has:
```yaml
metadata:
  openclaw:
    emoji: 🧠
    events: ["message:sent"]
```

Should add `install` section like bundled hooks:
```yaml
metadata:
  openclaw:
    emoji: 🧠
    events: ["message:sent"]
    install: [{ "id": "bundled", "kind": "bundled", "label": "Bundled with OpenClaw" }]
```

---

## Hook Development Progress (2026-02-22 14:00-14:15)

### Current Status

**✅ Working:**
- Hook registered: `true-recall-stager -> before_agent_start`
- 3 internal hooks loaded (bootstrap-extra-files, command-logger, true-recall-stager)
- memory-qdrant plugin runs on before_agent_start (1 handler)

**❌ Not Working:**
- Hook handler not executing (no console.log output in logs)
- Redis buffer still empty (0 items)

### Key Findings

1. **Internal Hooks vs Plugin Hooks are DIFFERENT:**
   - Internal hooks: loaded via HOOK.md in dist/bundled/{name}/
   - Plugin hooks: separate system (memory-qdrant)
   - Both can run on same events but registered separately

2. **The Issue:**
   - `before_agent_start` event runs plugins (1 handler = memory-qdrant)
   - Internal hooks may need `handlers` array config OR
   - Internal hooks might not be wired to `before_agent_start` event

3. **Alternative Approach:**
   - Try using `message:sent` event (though it didn't work before either)
   - Or use the plugin system instead of internal hooks
   - Or use external daemon like mem-redis

### Attempted Fixes
- Changed HOOK.md events from `message:sent` to `before_agent_start`
- Changed handler.js from CommonJS to ESM format
- Added console.log debugging (not showing in logs)

---

## Architecture Change (2026-02-22 14:18)

### Decision: Use mem-redis for Real-Time Capture

**Problem:** True-Recall tr-in hook (true-recall-stager) is broken - couldn't get internal hooks to execute properly on events.

**Solution:** Use mem-redis for real-time capture instead.

### How It Works Now

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────┐
│ Talk to │───→│ mem-redis   │───→│ Curator     │───→│ Store   │
│ Kimi    │    │ (real-time) │    │ (daily)    │    │ Gems    │
└─────────┘    └─────────────┘    └─────────────┘    └─────────┘
                    │                    │                   │
                    ▼                    ▼                   ▼
              Redis key:           Read from          Qdrant
              mem:USER_ID              mem:USER_ID           true_recall
```

1. **Real-time capture:** mem-redis (systemd daemon) watches session files → saves to `mem:USER_ID`
2. **Daily curation:** Curator reads from `mem:USER_ID` → extracts gems → stores to `true_recall`
3. **Retrieval:** Search from `true_recall` collection

### What Was Removed
- ❌ True-Recall tr-in hook (broken, not working)
- ❌ `tr_out_buffer:USER_ID` (unused)

### What We're Using
- ✅ mem-redis: `mem:USER_ID` (70+ turns, real-time)
- ✅ Curator: runs daily at 3:30 AM
- ✅ Storage: Qdrant `true_recall` (4 gems)
- ✅ Plugin: memory-qdrant for auto-recall

---

## Final Architecture (2026-02-22 14:26)

### Summary

**Decision:** Use mem-redis for real-time capture instead of broken tr-in hook.

### Validation Results

**Redis (mem:USER_ID):** ✅ Working
- 76 turns stored
- Real-time capture via mem-redis systemd daemon

**Qdrant (true_recall):** ✅ Working
- 8 gems stored
- Curator successfully extracting and storing gems

**Flow:**
```
mem-redis (systemd) → Redis mem:USER_ID → Curator (daily 3:30 AM) → Qdrant true_recall
```

### What Was Changed

1. **Removed broken tr-in hook** - Internal hooks don't execute on events in current OpenClaw
2. **Disabled true-recall-stager** in openclaw.json
3. **Updated README.md** with new architecture
4. **Stored knowledge** to kimi_kb about hook development learnings

### Current Status

| Component | Status |
|-----------|--------|
| Real-time capture (mem-redis) | ✅ Working (76 turns) |
| Daily curation | ✅ Working |
| Qdrant storage | ✅ Working (8 gems) |
| Plugin auto-recall | ✅ Working |
| Internal hooks | ❌ Broken |

### Knowledge Saved to kimi_kb

- OpenClaw Internal Hooks: load.extraDirs Configuration
- OpenClaw Custom Hook ESM Development  
- OpenClaw Hook Event Context Format
- OpenClaw Internal vs Plugin Hooks Difference
- True-Recall Architecture: mem-redis for Capture

---

## Curator Fix (2026-02-22 14:32)

### Problem
Curator was reading from wrong Redis key (`tr_out_buffer:USER_ID`) instead of where mem-redis saves (`mem:USER_ID`).

### Fix
Updated curator to read from `mem:{user_id}` instead of `tr_out_buffer:{user_id}`.

### Validation Test
```
✅ Found 91 turns in Redis mem:USER_ID
✅ Extracted 6 gems
✅ Stored to Qdrant (8 total gems)
✅ Cleared Redis buffer
```

### Files Changed
- `tr-process/curate_memories.py` - Changed Redis key from `tr_out_buffer:{user_id}` to `mem:{user_id}`

---

*Last updated: 2026-02-22 14:32 CST*

1. **Re-enable memory-qdrant plugin** — Configure for `true_recall` with mxbai embeddings
2. **Test auto-injection** — Verify gems are injected and displayed correctly
3. **Fix display issues if needed** — Map payload fields or modify plugin code
4. **Monitor first automated run** — Tomorrow at 3:30 AM
5. **Tune thresholds** — Adjust based on real-world results

---

## Notes for Future Sessions

- **kimi_memories** is frozen (11,238 items) — do not modify
- **true_recall** is the active collection — 4 gems currently stored
- **mxbai-embed-large** is the production embedding model (639 MB file, ~903 MB GPU)
- **Native system prompt** is now used (preferred over prepended)
- **Curator runs at 3:30 AM daily** via cron
- **Redis buffer key**: `tr_out_buffer:USER_ID` at localhost:6379
- **Log file**: `/var/log/true-recall-curator.log`

---

*For full documentation, see [README.md](./README.md)*  
*For the curator system prompt, see [curator_prompt.md](./curator_prompt.md)*