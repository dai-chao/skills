# Cursor Hooks — Patterns

Hooks are scripts that run on agent lifecycle events. Cursor's hook system is **Claude Code-compatible** — configs from either tool generally work in the other.

## Supported Events (Cursor 2.4+)

| Event | Fires When | Use For |
|-------|------------|---------|
| `sessionStart` | New agent session begins | Load context, print project status |
| `sessionEnd` | Session ends | Cleanup, log summary |
| `beforeSubmitPrompt` | User submits a prompt | Modify/scan the prompt (secret-blocking) |
| `PreToolUse` | Before a tool call (Edit, Write, Bash) | Block or modify tool call |
| `PostToolUse` | After a tool call | Format, lint, test |
| `stop` | Agent tries to finish | Gate: re-prompt if work incomplete |

## Config Location

- `.cursor/hooks/*.json` — project-scoped, check into repo
- Multi-root workspaces read hooks from **all** workspace folders (Cursor 3.x)

## Basic Hook Shape

```json
{
  "event": "PostToolUse",
  "matcher": { "tool": "Edit|Write" },
  "command": "prettier --write \"$CURSOR_TOOL_FILE_PATH\""
}
```

Environment variables available to hooks:
- `$CURSOR_TOOL_NAME` — the tool being called
- `$CURSOR_TOOL_FILE_PATH` — target file (for file tools)
- `$CURSOR_PROMPT` — user prompt (for beforeSubmitPrompt)
- `$CURSOR_SESSION_ID` — current session

## Recommended Hooks by Signal

### Auto-format on edit (Prettier)
**Signal**: `.prettierrc*`, `prettier` in deps.
```json
{
  "event": "PostToolUse",
  "matcher": { "tool": "Edit|Write", "filePattern": "**/*.{ts,tsx,js,jsx,css,md}" },
  "command": "prettier --write \"$CURSOR_TOOL_FILE_PATH\""
}
```

### Auto-lint on edit (ESLint)
**Signal**: `eslint.config.*`, `.eslintrc*`.
```json
{
  "event": "PostToolUse",
  "matcher": { "tool": "Edit|Write", "filePattern": "**/*.{ts,tsx,js,jsx}" },
  "command": "eslint --fix \"$CURSOR_TOOL_FILE_PATH\" || true"
}
```
> Use `|| true` if you want lint issues to surface without blocking.

### Python: ruff + format
**Signal**: `pyproject.toml` with ruff, `ruff.toml`.
```json
{
  "event": "PostToolUse",
  "matcher": { "tool": "Edit|Write", "filePattern": "**/*.py" },
  "command": "ruff check --fix \"$CURSOR_TOOL_FILE_PATH\" && ruff format \"$CURSOR_TOOL_FILE_PATH\""
}
```

### Type-check on TS edit
**Signal**: `tsconfig.json`.
```json
{
  "event": "PostToolUse",
  "matcher": { "tool": "Edit|Write", "filePattern": "**/*.{ts,tsx}" },
  "command": "tsc --noEmit --incremental"
}
```
> Incremental compilation keeps this fast.

### Run related tests after edit
**Signal**: Jest/Vitest configured with test discovery.
```json
{
  "event": "PostToolUse",
  "matcher": { "tool": "Edit|Write", "filePattern": "src/**/*.{ts,tsx}" },
  "command": "vitest related \"$CURSOR_TOOL_FILE_PATH\" --run"
}
```

### Block `.env` edits
**Signal**: `.env*` files in repo.
```json
{
  "event": "PreToolUse",
  "matcher": { "tool": "Edit|Write", "filePattern": "**/.env*" },
  "command": "echo 'REJECT: .env files must be edited manually' && exit 1"
}
```
> Non-zero exit code blocks the tool call.

### Block lock file edits
**Signal**: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `Cargo.lock`.
```json
{
  "event": "PreToolUse",
  "matcher": { "tool": "Edit|Write", "filePattern": "**/{pnpm-lock.yaml,package-lock.json,yarn.lock,Cargo.lock,poetry.lock}" },
  "command": "echo 'REJECT: lock files are generated — run the package manager instead' && exit 1"
}
```

### Secret scan on prompt submit
**Signal**: Project handles credentials (AWS, Stripe, etc.).
```json
{
  "event": "beforeSubmitPrompt",
  "command": ".cursor/hooks/scripts/scan-secrets.sh"
}
```
Where `scan-secrets.sh` checks `$CURSOR_PROMPT` for patterns like `sk-`, `AKIA`, `ghp_`.

### TDD grind loop
**Signal**: User wants autonomous TDD iteration.
```json
{
  "event": "stop",
  "command": ".cursor/hooks/scripts/keep-going.sh"
}
```
Where the script runs tests; if failing, echoes a continuation prompt so the agent restarts.

### Session start: project status
**Signal**: Any project — nice welcome.
```json
{
  "event": "sessionStart",
  "command": "git status --short && echo '---' && git log --oneline -5"
}
```

### Block destructive git commands
**Signal**: Always relevant.
```json
{
  "event": "PreToolUse",
  "matcher": { "tool": "Bash", "commandPattern": "git (reset --hard|push --force|clean -fd)" },
  "command": "echo 'REJECT: destructive git command — run manually' && exit 1"
}
```

### Log agent actions for audit
**Signal**: Security-sensitive codebase.
```json
{
  "event": "PostToolUse",
  "command": "echo \"$(date -Iseconds) $CURSOR_SESSION_ID $CURSOR_TOOL_NAME $CURSOR_TOOL_FILE_PATH\" >> .cursor/audit.log"
}
```

## Patterns

### Fast hooks
Hook commands start in ~milliseconds (Cursor 2.4+ made this 40x faster), but long-running commands still block the agent. Keep hooks under ~2s:
- Use `--incremental` for type-checking
- Use `vitest related` over full suite
- Use `ruff` (fast) over older Python linters

### Non-blocking vs blocking
- Want to **surface issues without stopping**: append `|| true` to the command
- Want to **block on failure**: non-zero exit stops the tool call

### Team vs personal
- Commit hooks that enforce team standards (`.cursor/hooks/format.json`)
- Keep personal preferences out of repo (use global Cursor settings instead)

### Enterprise distribution
Enterprise teams can push hooks from the Cursor dashboard — useful for org-wide security rules.

## Debugging

- Hooks that silently fail: check exit codes and stderr
- Test a hook script standalone first: `CURSOR_TOOL_FILE_PATH=src/foo.ts ./hook.sh`
- Cursor logs hook invocations in the Output panel
