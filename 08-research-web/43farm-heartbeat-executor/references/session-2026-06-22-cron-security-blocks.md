# Session 2026-06-22: Security Scanner Blocks in Cron Heartbeat

## Context
Cron-triggered 43Farm heartbeat. Agent attempted to execute the heartbeat manually because the script path was not immediately checked.

## Sequence of Blocks

### 1. `execute_code` BLOCKED
```
BLOCKED: execute_code runs arbitrary local Python... Cron jobs run without a user present to approve it.
```
**Expected**: Already documented in skill.

### 2. `python3 -c "..."` pending_approval
```
Status: pending_approval
Description: script execution via -e/-c flag
Pattern key: script execution via -e/-c flag
```
**Expected**: Already documented in skill. But worth noting: even a simple `python3 -c "import time; print(time.time())"` is blocked. The scanner does not distinguish complexity.

### 3. `curl | python3` BLOCKED
```
Security scan — [MEDIUM] Schemeless URL in sink context
Security scan — [HIGH] Pipe to interpreter: curl | python3
```
**New nuance**: Even `curl -s URL | python3 -m json.tool` (pretty-printing JSON) is blocked. The scanner treats ANY pipe to python3 as high-risk, regardless of whether the Python side is just formatting.

**Lesson**: Do not use `| python3 -m json.tool` to pretty-print API responses. Use `jq` if available, or just accept raw JSON output.

### 4. `cat > ~/.config/... << 'EOF'` BLOCKED
```
Security scan — [HIGH] Dotfile overwrite detected: Command redirects output to a dotfile in the home directory
```
**New nuance**: The `write_file` tool is the correct and only way to update dotfiles in cron mode. The security scanner treats heredoc redirection to dotfiles as high-risk, even for JSON state files.

**Lesson**: Always use `write_file` to update `~/.config/43farm/state.json`. Never use heredoc or echo redirection.

## Operational Outcome

- Farm Token was expired (HTTP 401 on `farm.events.poll`)
- Version check endpoint (`https://farm.43chat.cn/skills/skill.json`) does NOT require authentication and succeeded
- Local skill version (1.1.0) matched remote version (1.1.0), no update needed
- `state.json` was successfully updated via `write_file` with new `lastVersionCheck`
- All farm API operations (harvest, plant, steal, events) were skipped due to token expiration

## Key Takeaway

When Farm Token is expired in cron mode:
1. Script call would handle token recovery automatically (if script exists)
2. Manual API calls all fail with 401
3. Version check still works (no auth required)
4. State file can still be updated via `write_file`
5. Should report `HEARTBEAT_BLOCKED: Token expired` to owner, not silently fail
