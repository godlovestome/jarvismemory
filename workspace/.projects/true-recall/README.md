# True-Recall: Holistic Contextual Gem Curation

<h2><em>Works with openclaw-jarvis-memory - one timing adjustment</em></h2>

**Status:** ✅ Operational (v1.0)  
**Video Tutorial:** [Watch on YouTube](https://www.youtube.com/watch?v=QKpwZB7Lc_Q)  
**Goal:** Store high-context gems without muddying the data  
**Approach:** 24-hour holistic evaluation with contextual extraction  
**Embedding:** mxbai-embed-large (1024 dims)  
**Collection:** true_recall (Qdrant)  
**Archive:** kimi_memories (frozen, read-only)

---

## ⚠️ CRITICAL: Cron Scheduling Conflict

**If you use jarvis-memory AND True-Recall together, you MUST adjust cron timing.**

The jarvis-memory cron job at 3:00 AM **clears the Redis buffer** after backing up. If True-Recall runs after (3:30 AM), there's nothing to curate.

**Current conflict:**
| Time | Job | Action | Redis |
|------|-----|--------|-------|
| 3:00 AM | jarvis-memory | Backup → `kimi_memories` | **CLEARED** ❌ |
| 3:30 AM | True-Recall | Curate → `true_recall` | Empty! ❌ |

**Solutions:**
1. **Move True-Recall earlier** — Run curator at 2:30 AM (before jarvis clears)
2. **Modify jarvis** — Remove the Redis clear from jarvis, let True-Recall handle it
3. **Pick one system** — Use either jarvis OR True-Recall, not both

**Recommended:** Run True-Recall at 2:30 AM, keep jarvis at 3:00 AM.

---

## The Problem

Current memory systems suffer from:

| Approach | Issue | Result |
|----------|--------|--------|
| **Line-by-line** | Loses context | "User chose Redis" (why?) |
| **Full dump** | Unsearchable | 24 hours of banter + 1 gem |
| **Extracted facts** | Lossy | "User prefers Redis" (when? why?) |

**We want:** The gem + just enough context to understand it

---

## The Solution: Contextual Gems

### What Gets Stored

```json
{
  "gem": "User decided to use Redis over Postgres for memory system caching",
  "context": "After discussing tradeoffs between persistence vs speed for short-term storage",
  "conversation_snippet": "[rob]: Should I use Redis or Postgres?\n[Kimi]: For caching, Redis is faster\n[rob]: I decided on Redis",
  "full_context_available": true,
  "categories": ["decision", "technical"],
  "importance": "high",
  "confidence": 0.92,
  "timestamp": "2026-02-22T14:30:00",
  "date": "2026-02-22",
  "conversation_id": "uuid-here",
  "turn_range": "15-17"
}
```

### Components Explained

| Field | Purpose | Example |
|-------|---------|---------|
| **gem** | The core insight | "User chose Redis" |
| **context** | Why it matters | "After discussing tradeoffs..." |
| **conversation_snippet** | Surrounding dialogue | ±2 turns for context |
| **full_context_available** | Can retrieve more if needed | true |
| **categories** | Classification | ["decision", "technical"] |
| **importance** | Priority level | high |
| **confidence** | AI certainty | 0.92 |
| **timestamp** | When it happened | 2026-02-22T14:30:00 |
| **date** | Date for grouping | 2026-02-22 |

### Temporal Considerations

**The Curator** includes precise timestamps in every gem:

```json
{
  "gem": "User decided on Redis for caching",
  "timestamp": "2026-02-22T14:30:00",
  "date": "2026-02-22",
  "conversation_id": "uuid-here",
  "turn_range": "15-17"
}
```

**Why Timestamps Matter:**

1. **Recency Bias** - Recent decisions may override older ones
2. **Temporal Context** - "You decided this 3 months ago" vs "yesterday"
3. **Versioning** - Track how preferences evolve over time
4. **Decay** - Older gems may be less relevant

**Retrieval with Temporal Awareness:**

```python
# Search with recency weighting
search_memories(
    query="database decision",
    user_id="USER_ID",
    recency_boost=True,      # Boost recent results
    temporal_window="6m"     # Prioritize last 6 months
)
```

**Future Enhancement:**
- Weighted scoring: `score = semantic_similarity * recency_factor`
- Temporal decay: `relevance = base_score * e^(-age_in_days/30)`
- Explicit versioning: "User preferred X in March, switched to Y in June"

---

## The Flow

### Step 1: Staging (Unchanged)

```
Every turn → Redis buffer (24h retention)
```

Individual turns stored as-is (already filtered for system metadata).

### Step 2: Holistic Curation (New)

```
Daily @ 3 AM:
  1. Read ALL 24h of turns from Redis
  2. Present to AI curator as single context block
  3. AI identifies "gems" (decisions, insights, etc.)
  4. For each gem:
     - Extract the gem statement
     - Capture ±2 turn snippet for context
     - Generate context summary
     - Store to Qdrant
  5. Clear Redis buffer
```

### Step 3: Retrieval (Enhanced)

```
User asks: "What did I decide about the database?"

Search Qdrant → Find gem:
  "User decided to use Redis over Postgres..."
  
Return to user:
  "On Feb 22, you decided on Redis for your memory system 
   caching after discussing tradeoffs between persistence 
   and speed."
```

---

## Implementation Plan

### Phase 1: Update Curator Script

Modify `curate_memories.py`:

```python
def holistic_curation(user_id: str, hours: int = 24):
    # 1. Get all turns from Redis
    turns = get_all_staged_turns(user_id, hours)
    
    # 2. Build full conversation transcript
    transcript = build_transcript(turns)
    
    # 3. Ask AI to identify gems with context
    gems = extract_gems_with_context(transcript)
    
    # 4. Store each gem to Qdrant
    for gem in gems:
        store_gem_to_qdrant(gem)
    
    # 5. Clear Redis buffer
    clear_staged_turns(user_id)
```

### Phase 2: Update Qdrant Schema

New payload structure:

```python
{
    "user_id": "USER_ID",
    "gem": "User decided on Redis over Postgres...",
    "context": "After discussing tradeoffs...",
    "snippet": "[rob]: Should I use Redis...\n[Kimi]: For caching...\n[rob]: I decided on Redis",
    "categories": ["decision", "technical"],
    "importance": "high",
    "confidence": 0.92,
    "date": "2026-02-22",
    "conversation_id": "uuid",
    "turn_range": "15-17"
}
```

### Phase 3: Update Search

Search returns gems with context:

```python
def search_gems(query: str, user_id: str):
    # Semantic search on gem + context + snippet
    results = qdrant.search(
        query=query,
        filter={"user_id": user_id},
        vector_fields=["gem_embedding", "context_embedding", "snippet_embedding"]
    )
    return results
```

---

## Historical Context: Predecessor System

**Important:** True-Recall is ONE unified system that replaced an earlier attempt. It has two parts: **tr-in** (input) and **tr-out** (output).

### Predecessor: Native OpenClaw Plugin (Feb 21) — DISABLED

**Location:** `~/.openclaw/extensions/memory-qdrant/`

This was a **separate earlier attempt** at memory, NOT part of True-Recall.

**What it was:**
- TypeScript plugin using OpenClaw's native plugin SDK
- Dumb semantic search only (cosine similarity)
- Real-time injection before each response
- Collection: `kimi_memories` (snowflake-arctic-embed2)

**Why it failed:**
- No context awareness — just "similar embeddings = relevant"
- No curation — injected raw memories, not insights
- Created noise and frequent compaction
- Couldn't understand conversation flow

**Current status:**
- Plugin still loaded in OpenClaw
- `"autoRecall": false` — completely disabled
- `kimi_memories` collection frozen (11,238 items, read-only)
- See `~/.openclaw/workspace/memory/2026-02-21.md` for full history

### True-Recall: One Unified System (Feb 22) — ACTIVE

**True-Recall is ONE system using mem-redis for capture:**

```
┌─────────────────────────────────────────────────────────────┐
│                     True-Recall                             │
│              (Unified Memory System)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐      ┌──────────────┐      ┌──────────┐     │
│   │mem-redis │ ───→ │  tr-process  │ ───→ │  tr-out  │     │
│   │(Capture) │      │  (Curator)   │      │ (Output) │     │
│   └──────────┘      └──────────────┘      └──────────┘     │
│                                                             │
│   Real-time     24h holistic        Retrieves               │
│   turn capture   curation           gems                    │
│   via systemd    (qwen3 LLM)        (Qdrant)               │
│                                                             │
│   Redis:        Reads:              Stores:                 │
│   mem:USER_ID   mem:USER_ID         true_recall             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- **mem-redis**: Real-time capture via systemd daemon → Redis `mem:{user_id}`
- **tr-process**: The Curator runs daily at 3:30 AM, reads mem:USER_ID, extracts gems, stores to Qdrant
- **tr-out**: Retrieves curated gems for AI context
- Collection: `true_recall` (mxbai-embed-large, 1024 dims)
- Status: **Active** — 4 gems stored, daily curation

**How it works:**
1. mem-redis daemon watches session files in real-time → saves each turn to Redis `mem:USER_ID`
2. Daily at 3:30 AM: Curator reads 24h from `mem:USER_ID` → extracts gems → stores to Qdrant
3. Retrieval: Search `true_recall` for relevant gems

### Comparison: Predecessor vs True-Recall

| Aspect | memory-qdrant Plugin | True-Recall (Unified) |
|--------|---------------------|----------------------|
| **Language** | TypeScript | Python |
| **Architecture** | Single plugin | Three-part pipeline (tr-in/process/out) |
| **Curation** | ❌ None (raw search) | ✅ LLM (qwen3) |
| **Timing** | Real-time | 24h delayed |
| **Context** | ❌ Raw embeddings | ✅ Full conversation snippet |
| **Collection** | `kimi_memories` | `true_recall` |
| **Embedding** | snowflake-arctic-embed2 | mxbai-embed-large |
| **Status** | ❌ Disabled | ✅ Active |

---

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Storage** | Individual turns | Contextual gems |
| **Noise** | High (all turns) | Low (curated gems) |
| **Context** | Lost | Preserved |
| **Retrieval** | May find banter | Finds insights |
| **Quality** | Mixed | High |

---

## Next Steps

1. ✅ **Design** (this document)
2. ⏳ **Implement** holistic curator
3. ⏳ **Update** Qdrant schema
4. ⏳ **Test** with real conversations
5. ⏳ **Deploy** to production

---

## Project Structure

```
.projects/true-recall/
├── README.md                    # This file
├── tr-in/                       # INPUT (Capture & Staging)
│   ├── hook/                    # OpenClaw integration
│   │   └── true-recall-stager/  # message:sent hook
│   │       ├── HOOK.md
│   │       └── handler.ts
│   └── stage_turn.py            # Stages to Redis (filtered)
├── tr-process/                  # PROCESS (Curation)
│   └── curate_memories.py       # Holistic AI curation (qwen3)
└── tr-out/                      # OUTPUT (Retrieval)
    ├── SKILL.md
    ├── config/
    │   ├── agent_curation_prompt.md
    │   └── config.yaml
    └── scripts/
        └── search_memories.py   # Gem retrieval
```

## The Curator

**The Curator** is the AI agent (qwen3:4b-instruct) that evaluates 24 hours of conversation and extracts "gems" — the insights, decisions, and knowledge worth remembering.

**The Curator's Job:**
1. Read 24 hours of conversation from Redis
2. Evaluate holistically (not line-by-line)
3. Identify gems: decisions, solutions, preferences, projects
4. **Extract each gem with timestamp and context**
5. Store gems to Qdrant
6. Clear Redis buffer

**Timestamp Requirement:**
Every gem MUST include:
- `timestamp`: ISO 8601 datetime (2026-02-22T14:30:00)
- `date`: Date for grouping (2026-02-22)
- `conversation_id`: Full conversation reference
- `turn_range`: Which turns in conversation

**Why Timestamps Are Critical:**
- **Recency Bias:** Recent decisions may override older ones
- **Temporal Context:** "You decided this 3 months ago" vs "yesterday"
- **Versioning:** Track how preferences evolve over time
- **Decay:** Older gems may be less relevant

**Retrieval with Temporal Awareness:**
```python
# Search with recency weighting
search_memories(
    query="database decision",
    user_id="USER_ID",
    recency_boost=True,      # Boost recent results
    temporal_window="6m"     # Prioritize last 6 months
)
```

**Why "The Curator":**
- Like a museum curator selecting pieces for an exhibit
- Discerning judgment about what matters
- Preserves context and meaning
- Creates a collection of value

**Current Status:** ⚠️ Needs update from line-by-line to holistic evaluation

**Qdrant Storage:**
Based on recent searches, The Curator has already stored 5 True-Recall related memories in Qdrant from today's development session, including:
- Mattermost vs Discord decision
- Redis buffer implementation details
- True-Recall architecture decisions
- System automation setup

These memories are now available for retrieval via tr-out.

---

## Current Status

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| **Capture** | `mem-redis` (systemd) | ✅ **Active** | Real-time, 70+ turns in `mem:USER_ID` |
| **Curation** | `tr-process/curate_memories.py` | ✅ **Operational** | Holistic curation with native system prompt |
| **Storage** | Qdrant `true_recall` | ✅ **Active** | **4 gems stored**, retrievable |
| **Archive** | Qdrant `kimi_memories` | ✅ **Frozen** | 11,238 items (from disabled plugin) |
| **Retrieval** | `tr-out/scripts/search_memories.py` | ✅ **Working** | mxbai-embed-large search |
| **Automation** | Cron daily @ 3:30 AM | ✅ **Active** | Runs holistic curation |
| **System Prompt** | `curator_prompt.md` | ✅ **Active** | Native system prompt with qwen3 |
| **Auto-Recall** | `~/.openclaw/extensions/memory-qdrant/` | ✅ **Active** | `autoRecall: true` for true_recall collection |

## What Works Now

1. ✅ **mem-redis captures** in real-time (systemd daemon → `mem:USER_ID`)
2. ✅ **24h buffer** in Redis (`mem:USER_ID`)
3. ✅ **Curator operational** — holistic evaluation with **custom system prompt** ([see `curator_prompt.md`](curator_prompt.md))
4. ✅ **Flexible LLM choice** — Use ANY local model for curation (qwen3, llama, mistral, etc.)
5. ✅ **mxbai-embed-large** for state-of-the-art embeddings
6. ✅ **true_recall collection** — **4 gems stored and retrievable**
7. ✅ **Search working** — retrieves gems with context
8. ✅ **Cron job active** — daily curation at 3:30 AM
9. ✅ **Auto-injection** — ENABLED via memory-qdrant plugin (autoRecall: true, maxResults: 2, minScore: 0.7)

## What Needs Work

1. ⏳ **Auto-injection** — Wire up context injection from `true_recall` before responses
2. ⏳ **Monitor first automated run** — Tomorrow at 3:30 AM, verify cron job executes
3. ⏳ **Tune thresholds** — Adjust confidence/importance based on real-world results
4. ⏳ **Decide on old plugin** — Keep, delete, or repurpose for `true_recall`

## Files Created/Updated

| File | Purpose | Status |
|------|---------|--------|
| `curator_prompt.md` | System prompt for qwen3 The Curator | ✅ Created |
| `tr-process/curate_memories.py` | Holistic curation script | ✅ Created |
| `tr-out/scripts/search_memories.py` | Gem retrieval script | ✅ Created |
| `temp_true_recall` | Test collection | ✅ Created |
| `true_recall` | Production collection | ✅ Created |

## Migration Summary

| From | To | Status |
|------|-----|--------|
| `kimi_memories` (11,238 items) | `true_recall` (4 gems) | ✅ Archive frozen |
| `snowflake-arctic-embed2` | `mxbai-embed-large` | ✅ Model pulled |
| Line-by-line curation | Holistic curation | ✅ Operational |
| Old curator script | New curator script | ✅ Cron active |
| Native memory-qdrant plugin | Python True-Recall system | ✅ Replaced |

## Scripts

### Staging: `stage_turn.py`
**Location:** `skills/true-recall-out/scripts/stage_turn.py`  
**Purpose:** Capture conversation turns and stage to Redis buffer  
**Called by:** OpenClaw `message:sent` hook  
**Usage:**
```bash
python3 stage_turn.py \
  --user-id USER_ID \
  --user-msg "Hello" \
  --ai-response "Hi there" \
  --turn 1
```

### Curation: `curate_memories.py`
**Location:** `tr-process/curate_memories.py`  
**Purpose:** Read 24h from Redis, extract gems with qwen3, store to Qdrant  
**Called by:** Cron daily at 3:30 AM  
**Usage:**
```bash
python3 curate_memories.py --user-id USER_ID
python3 curate_memories.py --user-id USER_ID --hours 48
```

### Retrieval: `search_memories.py`
**Location:** `tr-out/scripts/search_memories.py`  
**Purpose:** Search `true_recall` collection for relevant gems  
**Usage:**
```bash
python3 search_memories.py "database decision" --user-id USER_ID
python3 search_memories.py --user-id USER_ID --limit 5 --min-score 0.6 "What about Redis?"
```

---

## Relationship to jarvis-memory

**True-Recall and jarvis-memory are TWO SEPARATE PROJECTS.**

| Project | Purpose | Location | Approach |
|---------|---------|----------|----------|
| **jarvis-memory** | Python skill for OpenClaw | `skills/jarvis-memory/` | Manual tools (`save q`, `q topic`) |
| **True-Recall** | Standalone memory system | `.projects/true-recall/` | Automatic curation |

**Key differences:**
- jarvis-memory: User explicitly saves/searches memories
- True-Recall: System automatically captures → curates → stores

**No dependency:**
- True-Recall does NOT depend on jarvis-memory
- True-Recall does NOT extend jarvis-memory
- They are parallel memory systems with different approaches

---

## I Do Nothing

- ❌ No manual staging
- ❌ No evaluation
- ❌ No memory management

**I just chat. System handles everything.**

---

## The Curator System Prompt

True-Recall uses a **custom system prompt** to guide the LLM in extracting contextual gems from conversations. The prompt is designed to:

- Read 24 hours of conversation as a cohesive narrative (not line-by-line)
- Identify gems with high accuracy (>80% precision target)
- Extract 11 required fields for each gem including temporal metadata
- Skip trivial or duplicate content
- Output valid JSON consistently

**Key Features:**
- **Flexible LLM Choice** — Works with any local model (qwen3, llama, mistral, etc.)
- **Native System Prompt** — Uses Ollama's native system prompt for cleaner separation
- **Holistic Reading** — Treats entire conversation as one story to find arcs and patterns
- **Quality Thresholds** — Only stores gems with confidence >= 0.6 and importance >= medium

**See the full prompt:** [`curator_prompt.md`](curator_prompt.md)

### Infrastructure Details

| Component | Setting |
|-----------|---------|
| **Qdrant Collection** | `true_recall` at `http://localhost:6333` |
| **Archive Collection** | `kimi_memories` (frozen, read-only) |
| **Redis Buffer** | `mem:{user_id}` at `REDIS_HOST:REDIS_PORT` |
| **Ollama (Curation)** | Any local model (default: `qwen3:4b-instruct`) at `http://localhost:11434` |
| **Ollama (Embedding)** | `mxbai-embed-large` at `http://localhost:11434` |
| **Vector Dimensions** | 1024 |
| **Similarity Metric** | Cosine |

### Success Criteria

The Curator system prompt enables an AI to:
- Read 24 hours of conversation as a narrative, not line-by-line
- Identify gems with high accuracy (precision > 80%)
- Extract gems with complete temporal metadata
- Include all 11 required fields for every gem
- Skip trivial or duplicate content appropriately
- Output valid JSON consistently
- Handle edge cases gracefully

---

*Created: 2026-02-22 09:00 CST*  
*Updated: 2026-02-22 10:20 CST*  
*Status: ✅ OPERATIONAL — All components ready for production*

---

## Implementation Complete — 2026-02-22

### What Was Accomplished Today

**1. Embedding Model Upgrade**
- ✅ Evaluated Ollama embedding models (mxbai vs snowflake vs nomic)
- ✅ Selected **mxbai-embed-large** (66.5 MTEB, state-of-the-art)
- ✅ Model pulled on localhost Ollama server

**2. Qdrant Collections Created**
- ✅ `true_recall` — Production collection (1024 dims, cosine)
- ✅ `temp_true_recall` — Test collection for validation
- ✅ `kimi_memories` — Archived (11,238 items, frozen)

**3. Curator System Prompt**
- ✅ Designed and written (custom system prompt for holistic curation)
- ✅ Evaluated against success criteria (all 11 fields, holistic reading, quality thresholds)
- ✅ Saved to `curator_prompt.md`

**4. Curation Script Created**
- ✅ `tr-process/curate_memories.py` — Holistic curation with:
  - mxbai-embed-large for embeddings
  - qwen3:4b-instruct for gem extraction
  - 11-field gem structure with temporal metadata
  - Redis buffer clearing after curation

**5. Search Script Created**
- ✅ `tr-out/scripts/search_memories.py` — Gem retrieval with:
  - mxbai-embed-large for query embedding
  - Semantic search in `true_recall` collection
  - Formatted output with context and metadata

**6. Automation Configured**
- ✅ Cron job added: Daily at 3:30 AM
- ✅ Logs to `/var/log/true-recall-curator.log`
- ✅ Runs from `.projects/true-recall` directory

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Start fresh** vs migrate | `kimi_memories` has 11k items in old format; starting fresh ensures clean gem structure |
| **mxbai-embed-large** | Highest MTEB score (66.5), same 1024 dims as snowflake, drop-in replacement |
| **3:30 AM curation** | After mem-redis backup (3:00 AM), no conflicts |
| **11 required fields** | Complete metadata for temporal awareness and context preservation |
| **Holistic curation** | Narrative evaluation vs line-by-line for better context understanding |

### Next Steps (When Ready)

1. **Test curation manually** — Run curator on current Redis buffer to verify gem extraction
2. **Validate search** — Test `search_memories.py` with sample queries
3. **Monitor first automated run** — Check 3:30 AM curation on next day
4. **Tune thresholds** — Adjust confidence/importance thresholds based on results

### Commands Reference

```bash
# Manual curation (dry run)
cd ~/.openclaw/workspace/.projects/true-recall
python3 tr-process/curate_memories.py --user-id USER_ID --dry-run

# Manual curation (live)
python3 tr-process/curate_memories.py --user-id USER_ID

# Search memories
python3 tr-out/scripts/search_memories.py "What did I decide about Redis?"

# Check collections
curl -s "http://localhost:6333/collections/true_recall" | jq .
curl -s "http://localhost:6333/collections/kimi_memories" | jq .

# View cron
crontab -l | grep true

# Check logs
tail -f /var/log/true-recall-curator.log
```

---

## What's Next

### Immediate (Today)

1. **Test the curator manually** — Run a dry-run curation to verify gem extraction works
   ```bash
   cd ~/.openclaw/workspace/.projects/true-recall
   python3 tr-process/curate_memories.py --user-id USER_ID --dry-run
   ```

2. **Test search** — Verify gem retrieval works
   ```bash
   python3 tr-out/scripts/search_memories.py "What did I decide about Redis?"
   ```

3. **Check first automated run** — Tomorrow at 3:30 AM, verify the cron job runs
   ```bash
   tail -f /var/log/true-recall-curator.log
   ```

### Short Term (This Week)

4. **Tune thresholds** — Adjust `min_score` in search and confidence thresholds in curation based on real results

5. **Validate gem quality** — Review first few days of gems to ensure The Curator is extracting meaningful context

6. **Update OpenClaw plugin** (if desired) — Point memory-qdrant plugin to `true_recall` collection for auto-recall

### Long Term (Future)

7. **v2 Research** — LLM middleman for context-aware curation (if v1 proves insufficient)

8. **Temporal decay** — Implement recency weighting in search

9. **Multi-user support** — Extend beyond single user if needed

---

*Last Updated: 2026-02-22 10:35 CST*  
*Status: ✅ Ready for production testing*

---

## Test Results (2026-02-22)

### Curation Test
- **Input:** 2 conversation turns (Discord → Mattermost decision)
- **Output:** 1 gem extracted
- **Gem Quality:** High importance, 0.95 confidence
- **Categories:** decision, preference, project, privacy

### Search Test
- **Query:** "What did I decide about Mattermost?"
- **Result:** 1 gem retrieved
- **Similarity Score:** 0.656 (good match)
- **Context:** Full snippet and explanation included

### Technical Validation
| Component | Test | Result |
|-----------|------|--------|
| mxbai-embed-large | Embedding generation | ✅ 1024 dims |
| qwen3:4b-instruct | Gem extraction | ✅ 1 gem from 2 turns |
| Qdrant storage | Point insertion | ✅ Stored successfully |
| Qdrant search | Semantic retrieval | ✅ Retrieved with context |
| Redis buffer | Staging & clearing | ✅ Working |

**Status: All systems operational ✅**
# True-Recall Progress Update — 2026-02-22 10:58 CST

## What Was Accomplished Today

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
- ✅ Received Grok-generated prompt
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
- ✅ `README.md` — Full documentation with test results
- ✅ `session.md` — Continuity file for future sessions
- ✅ `curator_prompt.md` — System prompt

## Architecture Decisions Finalized

| Decision | Rationale |
|----------|-----------|
| **mxbai-embed-large** | 66.5 MTEB (SOTA), 1024 dims, quality-first |
| **Native system prompt** | Preferred over prepended, cleaner separation |
| **Integer IDs** | Qdrant requirement (not hex strings) |
| **Start fresh** | `kimi_memories` frozen, `true_recall` active with 4 gems |
| **3:30 AM curation** | After mem-redis backup (3:00 AM) |

## Test Results Summary

| Test | Input | Output | Score |
|------|-------|--------|-------|
| Curation | 2 turns (Discord→Mattermost) | 1 gem | 0.95 confidence |
| Native prompt | 1 turn (local AI preference) | 1 gem | 0.95 confidence |
| Search | "What about Mattermost?" | 1 gem | 0.656 similarity |
| Search | "What about PostgreSQL?" | 1 gem | 0.707 similarity |

**All tests passed ✅**

## Current State

- **4 gems** stored in `true_recall`
- **Native system prompt** active
- **mxbai-embed-large** for embeddings
- **Cron job** set for 3:30 AM daily
- **All components tested and operational**

## Next Steps

1. **Monitor first automated run** — Tomorrow at 3:30 AM
2. **Tune thresholds** — Adjust based on real-world results
3. **Scale testing** — Verify with larger conversation volumes

---

*Last Updated: 2026-02-22 10:58 CST*  
*Status: ✅ OPERATIONAL — All systems tested and ready for production*
