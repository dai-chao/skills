---
name: autonomous-coding-agents
description: "Delegate coding tasks to autonomous AI coding agents: Claude Code, OpenAI Codex, and OpenCode CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Automation, PTY, Code-Review, Refactoring]
    related_skills: [hermes-agent, systematic-debugging, test-driven-development]
---

# Autonomous Coding Agents

Delegate coding tasks to autonomous AI coding agent CLIs via Hermes terminal/process tools. This skill covers Claude Code (Anthropic), Codex (OpenAI), and OpenCode (provider-agnostic).

## Quick Comparison

| Agent | Install | Auth | Best For | Key Mode |
|-------|---------|------|----------|----------|
| **Claude Code** | `npm i -g @anthropic-ai/claude-code` | OAuth or `ANTHROPIC_API_KEY` | Complex multi-step work, structured output, hooks | Print (`-p`) + Interactive tmux |
| **Codex** | `npm i -g @openai/codex` | `OPENAI_API_KEY` or OAuth | Quick exec, batch fixes, PR reviews | `exec` + `--full-auto`/`--yolo` |
| **OpenCode** | `npm i -g opencode-ai` or `brew install opencode` | Provider API keys (OpenRouter, etc.) | Provider-agnostic, multi-model, cost tracking | `run` + Interactive TUI |

## Common Patterns

### One-Shot Task (All Agents)

```bash
# Claude Code — print mode (preferred)
claude -p "Add error handling to all API calls in src/" --allowedTools "Read,Edit" --max-turns 10

# Codex — exec mode
codex exec "Add dark mode toggle to settings"

# OpenCode — run mode
opencode run "Add retry logic to API calls and update tests"
```

### Background Long Task (All Agents)

```bash
# Start in background with PTY
terminal(command="claude -p 'Refactor auth module' --max-turns 15", workdir="~/project", background=true, timeout=300)
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
terminal(command="opencode run 'Implement OAuth refresh flow'", workdir="~/project", background=true, pty=true)

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")
```

### PR Review (All Agents)

```bash
# Claude Code
claude -p "Review this PR thoroughly" --from-pr 42 --max-turns 10

# Codex
codex review --base origin/main

# OpenCode
opencode pr 42
```

### Parallel Work (All Agents)

Use separate workdirs/worktrees to avoid collisions:

```bash
# Claude Code — worktree mode
claude -w feature-x --tmux

# Codex — manual worktrees
git worktree add -b fix/issue-78 /tmp/issue-78 main
codex exec --yolo "Fix issue #78"  # in /tmp/issue-78

# OpenCode — separate workdirs
opencode run "Fix issue #101"  # in /tmp/issue-101
```

---

## Claude Code (Anthropic)

### Prerequisites

```bash
npm install -g @anthropic-ai/claude-code
claude --version  # requires v2.x+
claude auth status
claude doctor     # health check
```

### Two Orchestration Modes

**Mode 1: Print Mode (`-p`) — Non-Interactive (PREFERRED)**

```bash
claude -p "Add error handling to all API calls in src/" --allowedTools "Read,Edit" --max-turns 10
```

- Skips ALL interactive dialogs — ideal for automation
- Returns structured JSON with `--output-format json`
- Supports session continuation with `--resume` and `--continue`

**Mode 2: Interactive PTY via tmux**

```bash
tmux new-session -d -s claude-work -x 140 -y 40
tmux send-keys -t claude-work "cd /path/to/project && claude" Enter
sleep 5 && tmux send-keys -t claude-work Enter  # Trust dialog (default Yes)
sleep 15 && tmux capture-pane -t claude-work -p -S -60
```

### Key Flags

| Flag | Effect |
|------|--------|
| `-p, --print` | Non-interactive one-shot mode |
| `--max-turns N` | Limit agentic loops (prevents runaway) |
| `--max-budget-usd N` | Cap API spend |
| `--allowedTools "Read,Edit"` | Whitelist specific tools |
| `--dangerously-skip-permissions` | Auto-approve ALL tool use |
| `--output-format json` | Structured JSON output |
| `--json-schema '{...}'` | Force structured output matching schema |
| `--bare` | Skip hooks, plugins, MCP, OAuth — fastest startup |
| `--model sonnet/opus/haiku` | Model selection |
| `--effort low/medium/high/max` | Reasoning depth |
| `--continue` | Resume most recent session in current directory |
| `--resume <id>` | Resume specific session |
| `--from-pr <number>` | Resume session linked to a GitHub PR |

### Interactive Slash Commands

| Command | Purpose |
|---------|---------|
| `/compact [focus]` | Compress context to save tokens |
| `/review` | Request code review of current changes |
| `/security-review` | Security analysis of current changes |
| `/plan [description]` | Enter Plan mode |
| `/context` | Visualize context usage |
| `/cost` | Token usage with per-model breakdown |
| `/model [model]` | Switch models mid-session |
| `/effort [level]` | Set reasoning effort |
| `/voice` | Push-to-talk voice mode |
| `/exit` or `Ctrl+D` | End session |

### Project Context (CLAUDE.md)

Claude auto-loads `CLAUDE.md` from project root. Use it for persistent project context:

```markdown
# Project: My API
## Architecture
- FastAPI backend with SQLAlchemy ORM
## Key Commands
- `make test` — run full test suite
## Code Standards
- Type hints on all public functions
- 2-space indentation for YAML, 4-space for Python
```

Also supports modular rules in `.claude/rules/*.md` and custom agents in `.claude/agents/*.md`.

### MCP Integration

```bash
claude mcp add -s user github -- npx @modelcontextprotocol/server-github
claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres
```

### Cost & Performance Tips

1. Use `--max-turns` to prevent runaway loops
2. Use `--max-budget-usd` for cost caps (minimum ~$0.05)
3. Use `--bare` for CI/scripting
4. Use `--allowedTools` to restrict capabilities
5. Use `/compact` when context > 70%
6. Start new sessions for distinct tasks

### Pitfalls

- Interactive mode REQUIRES tmux — `pty=true` alone works but tmux gives `capture-pane` for monitoring
- `--dangerously-skip-permissions` dialog defaults to "No, exit" — must send Down then Enter
- `--max-turns` is print-mode only — ignored in interactive sessions
- Context degradation above 70% — monitor with `/context` and proactively `/compact`
- Trust dialog only appears once per directory
- Background tmux sessions persist — clean up with `tmux kill-session`

---

## Codex (OpenAI)

### Prerequisites

```bash
npm install -g @openai/codex
# Auth: OPENAI_API_KEY or Codex OAuth
# Must run inside a git repository
```

### Key Modes

```bash
# One-shot
codex exec "Add dark mode toggle to settings"

# Background with auto-approve
codex exec --full-auto "Refactor the auth module"

# No sandbox, fastest (dangerous)
codex exec --yolo "Refactor the auth module"

# Gateway context: if sandbox fails with bubblewrap errors
codex exec --sandbox danger-full-access "<task>"
```

### Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |
| `--sandbox danger-full-access` | No Codex sandbox — use when bubblewrap fails in gateway contexts |

### Parallel Issue Fixing with Worktrees

```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main
codex exec --yolo "Fix issue #78"  # in /tmp/issue-78
codex exec --yolo "Fix issue #99"  # in /tmp/issue-99
# After completion: push and create PRs
```

### Pitfalls

- **Always use `pty=true`** — Codex is an interactive terminal app
- **Git repo required** — Codex refuses to run outside a git directory
- **Gateway caveat:** In Hermes gateway/service contexts, Codex sandboxing may fail with bubblewrap errors. Use `--sandbox danger-full-access` and rely on process boundaries for safety
- Background for long tasks — use `background=true` and monitor with `process` tool

---

## OpenCode (Provider-Agnostic)

### Prerequisites

```bash
npm i -g opencode-ai@latest
# or: brew install anomalyco/tap/opencode
opencode auth list  # verify at least one provider
```

### Key Modes

```bash
# One-shot
opencode run "Add retry logic to API calls"

# With context files
opencode run "Review this config" -f config.yaml -f .env.example

# Show model thinking
opencode run "Debug why tests fail" --thinking

# Force specific model
opencode run "Refactor auth" --model openrouter/anthropic/claude-sonnet-4
```

### Interactive TUI (Background)

```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Send prompt: process(action="submit", session_id="<id>", data="Implement OAuth refresh flow")
# Monitor: process(action="poll", session_id="<id>")
# Exit: process(action="write", session_id="<id>", data="\x03")  # Ctrl+C
```

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` (x2) | Submit message |
| `Tab` | Switch between agents |
| `Ctrl+P` | Command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+C` | Exit OpenCode |

### Session Management

```bash
opencode -c                    # Continue last session
opencode -s ses_abc123         # Continue specific session
opencode session list          # List past sessions
opencode stats                 # Check token usage and costs
opencode stats --days 7 --models anthropic/claude-sonnet-4
```

### Pitfalls

- Interactive `opencode` requires `pty=true`; `opencode run` does NOT
- `/exit` is NOT valid — it opens an agent selector. Use Ctrl+C to exit
- PATH mismatch can select wrong binary/model config
- Enter may need to be pressed twice to submit in TUI
- Avoid sharing one working directory across parallel sessions

---

## Shared Rules for Hermes Agents

1. **Prefer one-shot modes for single tasks** — `claude -p`, `codex exec`, `opencode run`
2. **Use tmux/background PTY only for multi-turn iterative work**
3. **Always set `workdir`** — keep the agent focused on the right project
4. **Set `--max-turns` / cost caps** — prevents infinite loops and runaway spend
5. **Monitor background sessions** — use `process(action="poll"|"log")` for progress
6. **Look for idle indicators** — `❯` (Claude) or prompt return = waiting for input
7. **Clean up sessions** — kill tmux/processes when done to avoid resource leaks
8. **Report concrete outcomes** — summarize files changed, tests passed, remaining risks
9. **Use tool restrictions** — `--allowedTools` / `--sandbox` to limit capabilities
10. **Parallel is fine** — run multiple agents simultaneously for batch work
