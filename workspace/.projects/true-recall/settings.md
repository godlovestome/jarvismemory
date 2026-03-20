# True-Recall Settings

Configuration settings for the True-Recall memory system. All settings can be manually adjusted.

---

## Redis Settings

### Redis Host
- **Variable:** `REDIS_HOST`
- **Default:** `localhost`
- **Description:** Hostname or IP address of the Redis server
- **Format:** IP address or hostname string

### Redis Port
- **Variable:** `REDIS_PORT`
- **Default:** `6379`
- **Description:** Port number Redis is listening on
- **Format:** Integer (1-65535)
- **Range:** Well-known ports: 6379, 6380

### Redis Key Pattern
- **Variable:** `REDIS_KEY_PREFIX`
- **Default:** `mem:{user_id}`
- **Description:** Pattern for Redis keys storing conversation turns
- **Format:** String with `{user_id}` placeholder
- **Example:** `mem:USER_ID`, `memory:user123`

### Redis TTL (Time-To-Live)
- **Variable:** `REDIS_TTL_HOURS`
- **Default:** `24` (hours)
- **Description:** How long conversation data stays in Redis before curation
- **Format:** Integer
- **Range:** 1-168 hours (1 hour to 1 week)
- **Note:** 24 hours recommended for daily curation

---

## Qdrant Settings

### Qdrant URL
- **Variable:** `QDRANT_URL`
- **Default:** `http://localhost:6333`
- **Description:** HTTP endpoint of Qdrant vector database
- **Format:** `http://hostname:port`

### Qdrant Collection Name
- **Variable:** `QDRANT_COLLECTION`
- **Default:** `true_recall`
- **Description:** Name of the Qdrant collection storing curated gems
- **Format:** String (alphanumeric, underscores allowed)
- **Note:** Must use the same collection name across all scripts

### Qdrant Vector Size
- **Variable:** `VECTOR_SIZE`
- **Default:** `1024`
- **Description:** Dimension of embedding vectors
- **Format:** Integer
- **Note:** Must match the embedding model output size

---

## Ollama / Embedding Settings

### Ollama URL
- **Variable:** `OLLAMA_URL`
- **Default:** `http://localhost:11434`
- **Description:** HTTP endpoint of Ollama server
- **Format:** `http://hostname:port`

### Embedding Model
- **Variable:** `EMBEDDING_MODEL`
- **Default:** `mxbai-embed-large`
- **Description:** Model used for generating embeddings
- **Format:** String (Ollama model name)
- **Options:** 
  - `mxbai-embed-large` (recommended, 1024 dims, 66.5 MTEB)
  - `snowflake-arctic-embed2` (1024 dims)
  - `nomic-embed-text` (768 dims)
- **Note:** Must match the model used during curation; affects vector size

### Embedding Dimensions
- **Variable:** `EMBEDDING_DIMENSIONS`
- **Default:** `1024`
- **Description:** Output dimension of the embedding model
- **Format:** Integer
- **Must match:** The Qdrant collection vector_size

---

## Curation Settings (curate_memories.py)

### Hours to Process
- **Variable:** `HOURS_TO_PROCESS`
- **Default:** `24`
- **Description:** How many hours of conversation to process per curation run
- **Format:** Integer
- **Range:** 1-168 hours

### Confidence Threshold
- **Variable:** `MIN_CONFIDENCE`
- **Default:** `0.6`
- **Description:** Minimum confidence score for a gem to be stored
- **Format:** Float
- **Range:** 0.0-1.0
- **Recommendation:** 0.6-0.8; higher = stricter filtering

### Curator LLM Model
- **Variable:** `CURATOR_MODEL`
- **Default:** `qwen3:4b-instruct`
- **Description:** Ollama model used for curation (extracting gems)
- **Format:** String (Ollama model name)
- **Options:**
  - `qwen3:4b-instruct` (recommended, fast, capable)
  - `qwen3:8b-instruct` (more capable, slower)
  - `llama3:8b` (alternative)

### Curator System Prompt
- **Variable:** `CURATOR_PROMPT_FILE`
- **Default:** `curator-prompt.md`
- **Description:** Path to the system prompt file for the curator LLM
- **Format:** File path string

---

## Search Settings (search_memories.py)

### Default Search Limit
- **Variable:** `DEFAULT_LIMIT`
- **Default:** `5`
- **Description:** Maximum number of results to return
- **Format:** Integer
- **Range:** 1-100

### Minimum Similarity Score
- **Variable:** `MIN_SCORE` / `--min-score`
- **Default:** `0.5`
- **Description:** Minimum similarity threshold for search results
- **Format:** Float
- **Range:** 0.0-1.0
- **Recommendation:** 0.5-0.7; higher = more precise but may miss relevant results

---

## OpenClaw Plugin Settings (memory-qdrant)

These settings are in `openclaw.json` under `plugins.entries.memory-qdrant.config`:

### autoCapture
- **Default:** `false`
- **Description:** Whether to automatically capture conversations to memory
- **Format:** Boolean
- **Note:** Keep false; use mem-redis for capture instead

### autoRecall
- **Default:** `true`
- **Description:** Whether to automatically inject relevant memories before AI responses
- **Format:** Boolean
- **Recommendation:** `true` for auto-injection

### collectionName
- **Default:** `true_recall`
- **Description:** Qdrant collection to use for recall
- **Format:** String

### embeddingModel
- **Default:** `mxbai-embed-large`
- **Description:** Embedding model for query encoding
- **Format:** String (must match curation model)
- **Must match:** The collection's embedding model

### maxRecallResults
- **Default:** `2`
- **Description:** Maximum number of memories to inject per response
- **Format:** Integer
- **Range:** 1-10
- **Note:** Higher = more context but more token usage

### minRecallScore
- **Default:** `0.7`
- **Description:** Minimum similarity score for memories to be injected
- **Format:** Float
- **Range:** 0.0-1.0
- **Important:** This is the MAIN setting affecting auto-injection
- **Recommendation:** Lower to `0.5` if memories aren't being injected

---

## Cron Schedule

### Curation Time
- **Default:** `30 3 * * *` (3:30 AM daily)
- **Description:** When the curator runs automatically
- **Format:** Standard cron format (minute hour day month weekday)
- **Example:** `30 3 * * *` = 3:30 AM every day

---

## File Locations

| Component | Script Location |
|-----------|-----------------|
| Curation | `tr-process/curate_memories.py` |
| Search | `tr-out/scripts/search_memories.py` |
| System Prompt | `curator-prompt.md` |
| Redis Buffer | `mem:{user_id}` |
| Qdrant Collection | `true_recall` |

---

## Quick Reference

```bash
# Minimal environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export QDRANT_URL=http://localhost:6333
export OLLAMA_URL=http://localhost:11434
export EMBEDDING_MODEL=mxbai-embed-large
export QDRANT_COLLECTION=true_recall
```

---

*Last updated: 2026-02-22*
