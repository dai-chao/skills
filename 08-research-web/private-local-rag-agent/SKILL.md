---
name: private-local-rag-agent
description: >
  Build a fully-local personal memory agent (RAG + Agent) that answers
  "what have I done before" from private data. Zero cloud dependency.
  Uses Gradio UI, Ollama (local LLM + embedding), Chroma (vector), SQLite (structured).
triggers:
  - "我想做一个个人智能体"
  - "完全本地的RAG"
  - "private personal agent"
  - "local memory assistant"
  - "私有的智能体"
  - "记录我做过什么"
  - "personal knowledge base"
  - "本地RAG Agent"
  - "私有数据 不上传"
  - "offline AI agent"
---

# Private Local RAG Agent

Build a completely offline personal memory agent that can answer questions about the user's past actions, decisions, and projects.

## Context

- All data must stay on user's machine. No cloud APIs for LLM or embedding.
- macOS environment with Ollama installed (or needs installation guidance).
- User may want to import WeChat logs, Markdown notes, diaries, Git history.
- Gradio is the simplest local UI; `share=False` is mandatory for privacy.
- Ollama models used: `qwen2.5:7b` (generation) and `nomic-embed-text` (embedding).

## Steps

### 1. Project scaffold

```bash
mkdir -p myAgent/{core,importers,data}
```

Files: `app.py`, `core/memory.py`, `core/agent.py`, `importers/text_importer.py`, `requirements.txt`, `start.sh`

### 2. Memory engine (`core/memory.py`)

**Dual-track storage**:
- `SQLite`: structured events table + FTS5 full-text index for exact filtering by time/project/source.
- `Chroma`: semantic vector search with `OllamaEmbeddingFunction` pointing to local Ollama (`nomic-embed-text`).

Key methods:
- `add()`: writes to both SQLite and Chroma atomically.
- `search()`: vector query via Chroma with optional project filter.
- `keyword_search()`: SQLite FTS5 fallback when vector results are sparse.
- `get_recent()` / `get_timeline()`: time-range structured queries.
- All DB paths use `BASE_DIR` relative to project root so it works regardless of cwd.

### 3. Agent core (`core/agent.py`)

`_ollama_generate()`: POST to `http://localhost:11434/api/generate`. Handle `ConnectionError` gracefully.

`chat()` workflow:
1. Vector search + keyword search (combined, deduplicated).
2. Build system prompt with memory stats and strict instruction: "do not hallucinate memories".
3. Append recent conversation history (sliding window, ~10 turns).
4. Call local LLM (`qwen2.5:7b`).
5. **Auto-extract facts**: after each turn, prompt the LLM with `temperature=0.1` to extract 0-3 facts about the user from the dialogue. Parse JSON array via regex and store into memory with `source="auto_extract"`.

`import_text()`: chunk long text by paragraph (split on `\n\n`), further split oversized chunks by sentence boundaries. Cap at 500 chunks per import.

### 4. Data importers (`importers/text_importer.py`)

- `clean_text()`: normalize newlines, remove control chars, compress blank lines.
- `parse_wechat_txt()`: regex match `YYYY-MM-DD HH:MM:SS sender_name` lines, capture message body between timestamps.
- `parse_markdown_notes()`: split on `#{1,3} ` headers.
- `parse_generic()`: paragraph split.

### 5. Gradio UI (`app.py`)

Layout: left column chat (~70%), right column management tabs (~30%).

Tabs:
- **Chat**: text input + send + clear.
- **Manual Memory**: textarea + source/project/type fields.
- **Import Data**: File upload + source tag + project + parser selector (generic / WeChat / Markdown).
- **Search Memory**: query box + optional project filter, display top-10 with distance scores.
- **Stats**: total count, project distribution, type distribution, recent memories slider.

**Privacy**: `demo.launch(share=False, server_name="127.0.0.1")`.
On load: display stats automatically.

### 6. Start script (`start.sh`)

- Create venv if absent.
- Install deps (touch `venv/.installed` flag to avoid repeated installs).
- Check `curl localhost:11434` for Ollama health.
- Warn if Ollama not running; prompt to continue.
- Check `ollama list` for required models; `ollama pull` if missing.
- Launch `python app.py`.
- Make executable: `chmod +x start.sh`.

### 7. Ollama setup (macOS)

If Ollama not installed: `brew install ollama` or download from ollama.com.

If Ollama installed but not running:
- Preferred: `open -a Ollama` (launches macOS app, menu-bar icon confirms).
- Alternative: `/Applications/Ollama.app/Contents/Resources/ollama serve`.

Pull models:
```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

If `start.sh` warns even after launch, verify with `curl http://localhost:11434/api/tags`.

### 8. Privacy & security checklist

- `share=False` in Gradio.
- `server_name="127.0.0.1"` (not `0.0.0.0`).
- `OllamaEmbeddingFunction` uses local URL, no cloud embedding service.
- All file paths under project root (`./data/`).
- Original uploaded files are read-only; parsed content is stored locally and can be deleted.

## Pitfalls

- **Ollama background PATH issue**: `ollama serve` run via `terminal(background=true)` may fail to find binary because `$PATH` differs. Use full path `/Applications/Ollama.app/Contents/Resources/ollama serve` or `open -a Ollama`.
- **Chroma OllamaEmbeddingFunction timeout**: if `nomic-embed-text` is not pulled, Chroma queries will fail silently or hang. Always verify models exist before first run.
- **Gradio File object type**: in Gradio 4.x, uploaded file may be a temp file path string or object. Use `file_obj.name if hasattr(file_obj, 'name') else str(file_obj)` for compatibility.
- **SQLite FTS5 trigger compatibility**: the `events_ai` trigger uses `new.rowid`; ensure virtual table `events_fts` is created before the trigger or the trigger creation will fail on first init.
- **Auto-extract JSON parsing**: LLM may output markdown around JSON. Always regex-search for `\[.*?\]` before `json.loads`, and catch exceptions to avoid crashing the chat loop.
- **Memory explosion**: auto-extract runs after every turn. Without deduplication, similar facts may be stored repeatedly. For long-term use, add a similarity check before inserting auto-extracted facts.
- **Large file imports**: a 10MB WeChat log could produce thousands of chunks. Cap chunk count (e.g., 500) per import to prevent UI freeze.

## Example Usage

```bash
# In terminal
cd /Users/chao/Desktop/myAgent
./start.sh

# Or manually
open -a Ollama
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:7860
```
