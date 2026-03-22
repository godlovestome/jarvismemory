# Jarvis Memory v2.0.1

**Persistent Memory System for OpenClaw AI Agents / OpenClaw AI Agent 姘哥画璁板繂绯荤粺**

Jarvis Memory + True Recall provides a persistent, cross-session memory system that operates independently from OpenClaw's built-in `memory_search`. It uses Qdrant (vector DB) + Ollama (local embeddings) + Redis (buffer), and survives OpenClaw upgrades without data loss. V2.0.1 adds Codeshield runtime workspace sync so the isolated `openclaw-svc` service keeps the same managed memory scripts and `.memory_env` as the interactive workspace.

---

**Jarvis Memory v2.0.1 鈥?OpenClaw AI Agent 姘哥画璁板繂绯荤粺**

Jarvis Memory + True Recall 鎻愪緵鐙珛浜?OpenClaw 鍐呯疆 `memory_search` 鐨勬寔涔呭寲璺ㄤ細璇濊蹇嗙郴缁熴€備娇鐢?Qdrant锛堝悜閲忔暟鎹簱锛? Ollama锛堟湰鍦板祵鍏ワ級+ Redis锛堢紦鍐诧級锛孫penClaw 鍗囩骇涓嶅奖鍝嶈蹇嗘暟鎹€俈2.0.1 鏂板 CodeShield V3.0.11 闆嗘垚銆佸畨鍏ㄥ瘑閽ョ鐞嗐€佽嚜鍔ㄩ厤缃?OpenClaw `memorySearch` 浣跨敤鏈湴 Ollama銆?

---

## Quick Start / 蹇€熷紑濮?

### Fresh Install / 鍏ㄦ柊瀹夎锛堜竴琛屽懡浠わ級

```bash
git clone https://github.com/godlovestome/jarvismemory.git && cd jarvismemory && sudo bash bootstrap/bootstrap.sh
```

### Update Existing / 鏃犳崯鏇存柊锛堜竴琛屽懡浠わ級

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/update.sh
```

> **OpenClaw updates are safe / OpenClaw 鏇存柊瀹夊叏锛?*
> ```bash
> curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard
> ```
> This only updates OpenClaw code. It does **NOT** touch:
> - Jarvis Memory data (Qdrant/Redis)
> - `openclaw.json` configuration (memorySearch settings preserved)
> - `.memory_env` / cron jobs / workspace scripts
> - CodeShield security framework
>
> After OpenClaw update, re-run `sudo bash bootstrap/update.sh` to re-sync scripts.
>
> 姝ゅ懡浠や粎鏇存柊 OpenClaw 浠ｇ爜锛?*涓嶄細**褰卞搷 Jarvis Memory 鏁版嵁銆侀厤缃€佸畾鏃朵换鍔℃垨 CodeShield 瀹夊叏妗嗘灦銆傛洿鏂板悗鎵ц `sudo bash bootstrap/update.sh` 閲嶆柊鍚屾鑴氭湰銆?

---

## Architecture / 鏋舵瀯

Two independent memory systems running side by side:

涓ゅ鐙珛鐨勮蹇嗙郴缁熷苟琛岃繍琛岋細

| | OpenClaw memory_search | Jarvis Memory + True Recall |
|---|---|---|
| **Storage / 瀛樺偍** | SQLite + sqlite-vec | Qdrant vector DB |
| **Embedding** | Ollama `qwen3-embedding:4b` (2560d) | Ollama `mxbai-embed-large` (1024d) |
| **Data / 鏁版嵁** | OpenClaw workspace memory files | Conversations, facts, curated gems |
| **Scope / 鑼冨洿** | Current workspace context | Cross-session persistent memory |
| **Conflict / 鍐茬獊** | None 鈥?separate storage, models, config / 鏃犫€斺€斿瓨鍌ㄣ€佹ā鍨嬨€侀厤缃畬鍏ㄧ嫭绔?|

---

## What's New in v2.0.1 / v2.0.1 鏇存柊鍐呭

| Change / 鍙樻洿 | Description / 璇存槑 |
|---|---|
| CodeShield integration | `QDRANT_API_KEY` sourced from `/run/openclaw-memory/secrets.env` (CodeShield V3.0.11) instead of plaintext / 瀵嗛挜浠?CodeShield 瀹夊叏璺緞鍔犺浇锛屼笉鍐嶆槑鏂囧瓨鍌?|
| OpenClaw memorySearch config | Auto-configures `memorySearch.provider=ollama` + `model=qwen3-embedding:4b` / 鑷姩閰嶇疆 OpenClaw 浣跨敤鏈湴 Ollama 鍋?embedding |
| `.memory_env` hardening | Permissions tightened to 600; QDRANT_API_KEY no longer stored in plaintext / 鏉冮檺鏀剁揣涓?600锛涘瘑閽ヤ笉鍐嶆槑鏂囧瓨鍌?|
| Diagnose: CodeShield checks | `diagnose.sh` now checks CodeShield interaction, proxy, and secret paths / 璇婃柇鑴氭湰鏂板 CodeShield 妫€鏌ラ」 |
| Codeshield runtime sync | Mirrors managed workspace files and `.memory_env` into `openclaw-svc` when the isolated runtime exists / 当 `openclaw-svc` 存在时同步托管 workspace 与 `.memory_env` |

---

## Usage / 浣跨敤璇存槑

### 1. Fresh Install / 棣栨閮ㄧ讲

On a VPS where OpenClaw is already installed:

鍦ㄥ凡瀹夎 OpenClaw 鐨?VPS 涓婃墽琛岋細

```bash
git clone https://github.com/godlovestome/jarvismemory.git
cd jarvismemory
sudo bash bootstrap/bootstrap.sh
```

The script will prompt for `USER_ID` on first run if not set in the environment.

棣栨杩愯鏃惰剼鏈細浜や簰寮忚闂?`USER_ID`锛圤penClaw 鐨勭敤鎴锋爣璇嗙锛夈€?

**What bootstrap.sh does / bootstrap.sh 鍋氫簡浠€涔堬細**

| Step | English | 涓枃 |
|------|---------|------|
| 1 | Install host dependencies (Docker, Python, etc.) | 瀹夎瀹夸富鏈轰緷璧?|
| 2 | Start Redis and Qdrant via Docker | 鍚姩 Redis 鍜?Qdrant 瀹瑰櫒 |
| 3 | Validate Ollama and pull required models | 妫€鏌?Ollama 骞舵媺鍙栨墍闇€妯″瀷 |
| 4 | Sync workspace scripts to `~/.openclaw/workspace` | 鍚屾鑴氭湰鍒?workspace |
| 5 | Write `.memory_env` configuration file | 鐢熸垚 `.memory_env` 閰嶇疆鏂囦欢 |
| 6 | Configure system timezone and cron schedules | 璁剧疆鏃跺尯鍜屽畾鏃朵换鍔?|
| 7 | Configure OpenClaw memorySearch (local Ollama) | 閰嶇疆 OpenClaw memorySearch 浣跨敤鏈湴 Ollama |
| 8 | Run final audit | 鎵ц鏈€缁堟鏌?|

**Configurable defaults / 鍙厤缃粯璁ゅ€硷細**

| Variable | Default | Description / 璇存槑 |
|----------|---------|---------------------|
| `OPENCLAW_USER` | `openclaw` | System user / 绯荤粺鐢ㄦ埛 |
| `TIMEZONE` | `America/Los_Angeles` | System timezone / 绯荤粺鏃跺尯 |
| `EMBEDDING_MODEL` | `mxbai-embed-large` | Jarvis Memory embedding model / Jarvis 鍚戦噺宓屽叆妯″瀷 |
| `CURATION_MODEL` | `qwen3.5:35b-a3b` | LLM for True Recall curation / True Recall 鏁寸悊妯″瀷 |
| `OPENCLAW_MEMORYSEARCH_MODEL` | `qwen3-embedding:4b` | OpenClaw memory_search embedding / OpenClaw 鎼滅储宓屽叆妯″瀷 |
| `TR_SCHEDULE` | `30 10 * * *` | True Recall daily run / True Recall 姣忔棩鎵ц |
| `BACKUP_SCHEDULE` | `0 11 * * *` | Daily backup / 姣忔棩澶囦唤 |
| `SLIDING_SCHEDULE` | `30 11 * * *` | Sliding backup / 婊戝姩澶囦唤 |

Override any variable before running:

杩愯鍓嶅彲鐩存帴瑕嗙洊鍙橀噺锛?

```bash
sudo TIMEZONE=Asia/Shanghai OPENCLAW_MEMORYSEARCH_MODEL=nomic-embed-text bash bootstrap/bootstrap.sh
```

---

### 2. Update an Existing Deployment / 鏇存柊鐜版湁閮ㄧ讲

For deployments already running, use the non-destructive updater:

宸查儴缃茬殑绯荤粺璇蜂娇鐢ㄦ棤鎹熸洿鏂拌剼鏈細

```bash
cd ~/jarvismemory && git pull && sudo bash bootstrap/update.sh
```

This **preserves all secrets and running containers**. It only syncs scripts and
regenerates config/cron.

璇ヨ剼鏈?*涓嶄細瑙︾瀵嗛挜銆丏ocker 瀹瑰櫒鎴栨暟鎹簱**锛屽彧鍚屾鑴氭湰鏂囦欢骞堕噸鏂扮敓鎴愰厤缃拰瀹氭椂浠诲姟銆?

**What update.sh preserves vs updates / 淇濈暀 vs 鏇存柊瀵规瘮锛?*

| Item / 鍐呭 | Preserved / 淇濈暀 | Updated / 鏇存柊 |
|-------------|:---:|:---:|
| `USER_ID`, `QDRANT_API_KEY` | 鉁?| |
| `OLLAMA_URL`, `QDRANT_URL`, `REDIS_*` | 鉁?| |
| Qdrant vector data / 鍚戦噺鏁版嵁 | 鉁?| |
| Redis buffer / Redis 缂撳瓨 | 鉁?| |
| Running Docker containers / 杩愯涓鍣?| 鉁?| |
| Ollama models / Ollama 妯″瀷 | 鉁?| |
| OpenClaw `memorySearch` config | 鉁?| |
| Python scripts in `workspace/skills/` | | 鉁?|
| True Recall scripts in `workspace/.projects/` | | 鉁?|
| `.memory_env` values | | 鉁?(淇濈暀鐜版湁鍊奸噸鏂板啓鍏? |
| Cron managed block / 瀹氭椂浠诲姟鍧?| | 鉁?|

> **When to use which / 濡備綍閫夋嫨锛?*
> - First time on a new server 鈫?`bootstrap.sh`
> - Pulling code updates on existing server 鈫?`update.sh`
>
> 鏂版湇鍔″櫒棣栨閮ㄧ讲鐢?`bootstrap.sh`锛涘凡鏈夐儴缃叉媺鍙栨洿鏂扮敤 `update.sh`銆?

---

### 3. Diagnose Errors / 鏁呴殰鎺掓煡

If you see embedding or memory search errors, run the diagnostic script:

閬囧埌鍚戦噺宓屽叆鎴栬蹇嗘悳绱㈡姤閿欐椂锛屾墽琛岃瘖鏂剼鏈細

```bash
sudo bash bootstrap/diagnose.sh
```

**What it checks / 妫€鏌ラ」鐩細**

| Check / 妫€鏌?| Description / 璇存槑 |
|-------------|---------------------|
| Proxy environment | HTTP_PROXY / HTTPS_PROXY / NO_PROXY 閰嶇疆 |
| Local bypass | 纭 127.0.0.1 / localhost / 10.x 缁曡繃浠ｇ悊 |
| Ollama availability | Ollama 鏈嶅姟鏄惁鍙闂?|
| Embedding model | 鎵€闇€宓屽叆妯″瀷鏄惁宸插姞杞?|
| Qdrant connectivity | Qdrant 绔彛鍜?API key 鏄惁姝ｅ父 |
| Redis connectivity | Redis 杩炴帴鏄惁姝ｅ父 |
| CodeShield interaction | CodeShield 瀹夊叏妗嗘灦鍏煎鎬ф鏌?|

Output uses `[PASS]` / `[FAIL]` / `[WARN]` indicators.

杈撳嚭浣跨敤 `[PASS]` / `[FAIL]` / `[WARN]` 鏍囪瘑姣忛」鐘舵€併€?

---

### 4. Environment Configuration / 鐜閰嶇疆

The deployment writes `~/.memory_env` (sourced by all scripts). Reference
template: `templates/.memory_env.example`.

鎵€鏈夎剼鏈€氳繃 `source ~/.memory_env` 璇诲彇閰嶇疆銆傚弬鑰冩ā鏉匡細`templates/.memory_env.example`銆?

| Variable | Description / 璇存槑 |
|----------|---------------------|
| `WORKSPACE_DIR` | Main workspace path / 宸ヤ綔鍖鸿矾寰?|
| `USER_ID` | OpenClaw user identifier / 鐢ㄦ埛鏍囪瘑绗?|
| `REDIS_HOST` / `REDIS_PORT` | Redis connection / Redis 杩炴帴 |
| `QDRANT_URL` | Qdrant API endpoint / Qdrant 鍦板潃 |
| `QDRANT_COLLECTION` | Memory collection name (default: `kimi_memories`) |
| `TR_COLLECTION` | True Recall collection (default: `true_recall`) |
| `OLLAMA_URL` | Ollama API endpoint / Ollama 鍦板潃 |
| `EMBEDDING_MODEL` | Jarvis embedding model / Jarvis 宓屽叆妯″瀷鍚嶇О |
| `CURATION_MODEL` | LLM for memory curation / 璁板繂鏁寸悊妯″瀷 |
| `QDRANT_API_KEY` | Loaded from CodeShield (auto) or set manually / 浠?CodeShield 鍔犺浇鎴栨墜鍔ㄨ缃?|
| `NO_PROXY` / `no_proxy` | Proxy bypass list / 浠ｇ悊缁曡繃鍒楄〃 |

---

### 5. Key Scripts / 鏍稿績鑴氭湰

**Qdrant memory scripts** (`workspace/skills/qdrant-memory/scripts/`):

| Script | Purpose / 鐢ㄩ€?|
|--------|----------------|
| `store_memory.py` | Store a memory to Qdrant / 瀛樺偍璁板繂 |
| `smart_search.py` | Hybrid semantic search / 娣峰悎璇箟鎼滅储 |
| `search_memories.py` | Basic memory retrieval / 鍩虹璁板繂妫€绱?|
| `harvest_sessions.py` | Harvest sessions from OpenClaw / 閲囬泦浼氳瘽鏁版嵁 |
| `extract_facts.py` | Extract structured facts from text / 鎻愬彇缁撴瀯鍖栦簨瀹?|
| `daily_backup.py` | Daily snapshot to disk / 姣忔棩蹇収澶囦唤 |
| `init_all_collections.py` | Initialize all Qdrant collections / 鍒濆鍖栭泦鍚?|
| `qd.py` | CLI for quick Qdrant operations / 鍛戒护琛屽揩閫熸搷浣?|

**Redis memory scripts** (`workspace/skills/mem-redis/scripts/`):

| Script | Purpose / 鐢ㄩ€?|
|--------|----------------|
| `cron_capture.py` | Periodic memory capture (every 5 min) / 瀹氭椂閲囬泦璁板繂 |
| `save_mem.py` | Save a memory entry to Redis / 鍐欏叆 Redis 璁板繂 |
| `mem_retrieve.py` | Retrieve memories from Redis / 璇诲彇 Redis 璁板繂 |
| `search_mem.py` | Search Redis memory store / 鎼滅储 Redis 璁板繂 |
| `cron_backup.py` | Scheduled Redis backup / 瀹氭椂澶囦唤 |

---

## CodeShield Integration / CodeShield 闆嗘垚

When CODE SHIELD V3.0.11+ is installed, Jarvis Memory automatically:

瀹夎 CODE SHIELD V3.0.11+ 鍚庯紝Jarvis Memory 鑷姩锛?

1. **Loads `QDRANT_API_KEY` from CodeShield-managed tmpfs** (`/run/openclaw-memory/secrets.env`) 鈥?no plaintext key in `~/.memory_env`
   浠?CodeShield 绠＄悊鐨?tmpfs 鍔犺浇瀵嗛挜鈥斺€擿~/.memory_env` 涓嶅瓨鍌ㄦ槑鏂囧瘑閽?

2. **Bypasses Squid proxy for local services** via `NO_PROXY=127.0.0.1,localhost` 鈥?Ollama, Qdrant, Redis connections go direct
   閫氳繃 `NO_PROXY` 缁曡繃 Squid 浠ｇ悊鈥斺€擮llama銆丵drant銆丷edis 鐩磋繛

3. **Configures OpenClaw memorySearch** to use local Ollama (`qwen3-embedding:4b`) 鈥?avoids iptables blocking of external embedding APIs
   閰嶇疆 OpenClaw memorySearch 浣跨敤鏈湴 Ollama鈥斺€旈伩鍏?iptables 闃绘柇澶栭儴宓屽叆 API

---

## Docs / 鏂囨。

- Deployment guide / 閮ㄧ讲鎵嬪唽: `docs/DEPLOYMENT.md`
- Audit notes / 瀹¤璇存槑: `docs/AUDIT.md`

---

## Safety Goal / 瀹夊叏鐩爣

- OpenClaw can be updated independently / OpenClaw 鍙嫭绔嬪崌绾э紝涓嶅奖鍝嶈蹇嗙郴缁?
- This repo remains the source of truth for memory deployment / 鏈粨搴撴槸璁板繂閮ㄧ讲鐨勫敮涓€鍙俊鏉ユ簮
- Rerunning bootstrap or update restores managed files and schedules / 閲嶈窇鑴氭湰鍙仮澶嶆墭绠℃枃浠跺拰瀹氭椂浠诲姟

杩欐剰鍛崇潃浠ュ悗鏂拌 OpenClaw 鍚庯紝鍙互鐩存帴浠庤繖涓?GitHub 浠撳簱鎷変唬鐮佸苟鎵ц bootstrap锛?
鑰屼笉鏄噸鏂版墜宸ョ収鏃ф枃妗ｉ€愭潯淇敼銆?
