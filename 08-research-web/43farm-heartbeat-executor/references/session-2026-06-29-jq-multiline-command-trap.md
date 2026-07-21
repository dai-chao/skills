# Session 2026-06-29: `$(jq -r)` Multi-line Command Trap

## Summary

The `TOKEN=$(jq -r '.field' file)` pattern, which works reliably in single-line terminal commands, fails consistently in multi-line commands due to security scanner false positives on `)` characters in subsequent lines.

## Context

- **Date**: 2026-06-29
- **Trigger**: 43Farm cron heartbeat task
- **Iteration waste**: ~40+ iterations repeating the same failing multi-line command

## The Pattern

### Working (single-line)
```bash
TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json) && curl -s -H "X-Farm-Token: $TOKEN" https://farm.43chat.cn/trpc/farm.status
```

### Failing (multi-line)
```bash
TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json)
curl -s -X POST -H "Content-Type: application/json" -H "X-Farm-Token: $TOKEN" \
  -d '{"cropType":"orange","quantity":3}' \
  https://farm.43chat.cn/trpc/farm.sell
```

**Error**: `/bin/bash: eval: line 5: syntax error near unexpected token ')'`

## Root Cause Analysis

The security scanner's bash parser evaluates multi-line commands differently than single-line ones. When `$(jq -r ...)` spans across lines, the scanner may:

1. Treat the `$(...)` as unclosed if the closing `)` appears on a different line
2. Confuse JSON `}` or `)` characters in subsequent lines with the command substitution closure
3. Apply stricter validation to multi-line commands than single-line ones

This is a **scanner false positive**, not a real bash syntax error. The same command works when written as a single line or when executed in a real shell.

## Iteration Waste Pattern

The agent repeated the same multi-line command **40+ times** despite:
- The error message being identical every time
- The tool loop warning firing at counts 2, 3, 5, 10, 20, 30, 40
- No variation in the command structure that could possibly succeed

This is a classic **inertia trap**: the agent assumes "this worked before, maybe it will work this time" rather than recognizing the structural impossibility.

## Correct Response Pattern

When `$(jq -r)` fails in multi-line commands:

1. **Immediately stop** — do not retry the same structure
2. **Split into two calls**:
   ```bash
   # Call 1: Extract token
   TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json)
   
   # Call 2: Use token (hardcoded or from previous output)
   curl -s -H "X-Farm-Token: <token_value>" https://farm.43chat.cn/trpc/farm.status
   ```
3. **Or use write_file + python3** — the most reliable path for complex operations

## Key Insight

**Command complexity escalates failure modes**: A pattern that works for simple GET requests may fail for multi-line POST requests with JSON payloads, even though the "risky" part (`$(jq -r)`) is identical. The scanner's validation is context-sensitive and line-aware.

## Related Skills

- `43farm-heartbeat-executor` — main heartbeat execution skill
- `43farm-cron-recovery` — Token recovery when all paths fail
- `references/session-2026-06-29-jq-variable-assignment-reliable.md` — The single-line success case
- `references/session-2026-06-18-cron-token-extraction-loop.md` — Earlier `$(jq -r)` failures
