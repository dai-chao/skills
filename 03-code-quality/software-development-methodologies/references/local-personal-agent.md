---
name: local-personal-agent
title: Local Personal Agent with Gradio + Ollama + Chroma
version: 1.0
description: |
  Build a fully-local, privacy-first personal AI agent with visual Q&A interface.
  Stack: Gradio (UI) + Ollama (local LLM + embeddings) + Chroma (vector DB) + SQLite (structured memory).
---

# Local Personal Agent

Build a fully-local personal AI agent that remembers everything you tell it, answers questions about your past, and keeps all data on your machine.

## Architecture

```
Gradio UI  <--->  Agent Logic  <--->  Ollama (qwen2.5:7b)
                     |                    |
                     v                    v
              PersonalMemory      nomic-embed-text
              (SQLite + Chroma)
```

## Project Structure

```
myAgent/
├── app.py                  # Gradio Blocks UI
├── core/
│   ├── agent.py            # Agent: RAG retrieval + Ollama inference + auto memory extraction
│   └── memory.py           # Dual-track memory: SQLite (structured) + Chroma (semantic)
├── importers/
│   └── text_importer.py    # Parsers for WeChat / Markdown / generic text
├── data/
│   ├── memory.db           # SQLite events table
│   └── chroma/             # Chroma persistent vector store
└── requirements.txt
```

## Core Components

### 1. Memory Engine (`core/memory.py`)

- **SQLite**: stores structured events with columns `id, timestamp, content, source, event_type, project, metadata`. Enables time-range queries, project filters, keyword search via FTS5.
- **Chroma**: semantic vector search using Ollama's local embedding model (`nomic-embed-text`).
- **Hybrid search**: vector search first; if results < 3, supplement with SQLite FTS keyword search.

Key snippet:
```python
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)
collection = chroma_client.get_or_create_collection(
    name="personal_memory",
    embedding_function=ollama_ef,
)
```

### 2. Agent Logic (`core/agent.py`)

- `chat_with_thinking()` returns `(response, log)` so the UI can show step-by-step operations:
  1. Retrieve relevant memories (vector + keyword)
  2. Call Ollama with memory-augmented prompt
  3. Auto-extract facts from conversation and save to memory

### 3. Gradio UI (`app.py`)

- `lines=1` on Textbox so **Enter submits** (not Shift+Enter).
- Use `yield` in the submit handler for streaming UI updates:
  ```python
  def respond(message, history, log):
      history.append([message, "🤔 Thinking..."])
      yield "", history, "Retrieving memories..."
      reply, thinking = agent.chat_with_thinking(message)
      history[-1][1] = reply
      yield "", history, thinking
  ```
- Tabs: Chat, Manual Memory, Import Data, Search Memory, Stats.

## Requirements

```txt
gradio>=4.0
chromadb>=0.4.24
requests>=2.31
ollama>=0.3.0
huggingface_hub<0.26
```

## Pitfalls & Fixes

### A. `ImportError: cannot import name 'HfFolder'`
**Cause**: Gradio 4.44.1 incompatible with newer `huggingface_hub`.
**Fix**: Pin `huggingface_hub<0.26`.

### B. `ModuleNotFoundError: No module named 'ollama'`
**Cause**: Chroma's `OllamaEmbeddingFunction` requires a separate Python package even though Ollama server is running.
**Fix**: `pip install ollama`.

### C. `TypeError: argument of type 'bool' is not iterable` / `APIInfoParseError: Cannot parse schema True`
**Cause**: Gradio 4.44.1 + Python 3.9 + `gradio_client` 1.3.0 crashes when parsing component JSON schemas that contain boolean values.
**Fix**: Patch `venv/lib/python3.x/site-packages/gradio_client/utils.py`:

```python
def get_type(schema: dict):
    if not isinstance(schema, dict):
        return "any"
    # ... rest unchanged

def _json_schema_to_python_type(schema: Any, defs) -> str:
    if not isinstance(schema, dict):
        return "Any"
    # ... rest unchanged
```

### D. `ValueError: When localhost is not accessible`
**Cause**: System proxy (Clash/V2Ray/etc.) intercepts Gradio's localhost reachability check.
**Fix**: Set environment variables before importing gradio:
```python
os.environ["no_proxy"] = "localhost,127.0.0.1,0.0.0.0"
os.environ["GRADIO_SERVER_NAME"] = "127.0.0.1"
```
And use `server_name="0.0.0.0"` in `demo.launch()`.

### E. Chinese Quotes inside Python String → SyntaxError
**Cause**: `"["记忆1", "记忆2"]"` breaks because inner `"` terminates the string.
**Fix**: Use single quotes for the outer string: `'["记忆1", "记忆2"]'`.

### F. Gradio Textbox Submit Behavior
- `lines=1` → **Enter** submits.
- `lines>1` → **Shift+Enter** submits, Enter inserts newline.

## Data Privacy Guarantees

- `share=False` in `demo.launch()` — no public URL generated.
- All storage in `./data/` (SQLite + Chroma files).
- Ollama runs entirely locally; no cloud API keys needed.

## Extending

- **Git auto-import**: add `post-commit` hook to pipe `git log` into `agent.import_text()`.
- **Apple Notes/Reminders**: use `apple-notes` or `apple-reminders` skills to sync into memory.
- **Reflection layer**: nightly cronjob that summarizes recent events into higher-level insights.

## Verification Steps

1. `ollama serve` running (menu bar 🦙 icon on macOS).
2. `ollama pull qwen2.5:7b` and `ollama pull nomic-embed-text` done.
3. `./start.sh` opens `http://127.0.0.1:7860` without errors.
4. Send a message → see "🤔 Thinking..." → then final answer + thinking log populated.
