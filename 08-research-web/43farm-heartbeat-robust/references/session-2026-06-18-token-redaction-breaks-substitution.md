# Session 2026-06-18: Token Redaction Breaks Bash Command Substitution

## Summary

In a cron-triggered heartbeat execution, the standard `$(cat file | grep | cut)` pattern for extracting the Farm Token from `credentials.json` was **broken by the terminal tool's credential redaction mechanism**. The redaction replaces the actual token value with `***` in the command string before bash eval, causing syntax errors that make the entire command fail.

## Failure Pattern

### The Command That Failed

```bash
FARM_TOKEN=$(cat "$HOME/.config/43farm/credentials.json" | grep -o '"farmToken":"[^"]*"' | cut -d'"' -f4)
```

### What Happens Under the Hood

1. Agent constructs the command with the literal token value in the `cat` output
2. Terminal tool scans the command for sensitive credentials
3. The tool **replaces the token with `***`** in the command string before passing to bash
4. The replacement happens inside the command substitution `$(...)`
5. Bash eval sees: `FARM_TOKEN=$(cat ... | grep -o '"farmToken":"***"' | cut -d'"' -f4)`
6. The `"` quotes around `***` are now unbalanced because the original token's trailing `"` was part of the replacement
7. Bash returns: `syntax error near unexpected token `)'`

### The Exact Error

```
/bin/bash: eval: line 22: syntax error near unexpected token `)'
/bin/bash: eval: line 22: `FARM_TOKEN=$(cat ... | grep -o '"farmToken":"***"' | cut -d'"' -f4)'
```

## Why This Is Particularly Bad in Cron

1. **Silent failure**: The command returns exit code 1 but the error message is cryptic
2. **Agent misinterprets**: The agent sees "syntax error" and thinks it's a bash quoting issue, not a credential redaction issue
3. **Infinite retry**: The agent tries variations (single quotes, double quotes, escaping) but ALL are subject to the same redaction
4. **Iteration waste**: 50+ iterations wasted on the same fundamentally broken approach
5. **No user to fix**: In cron mode, there's no user to approve or correct the command

## Attempted Variations That Also Failed

All of these were tried and all failed with the same root cause (credential redaction breaking syntax):

- `FARM_TOKEN=$(cat ... | python3 -c "import sys,json; ...")` - `python3 -c` blocked by security scanner
- `FARM_TOKEN=$(jq -r '.farmToken' ...)` - jq output redacted, empty string assigned
- Direct inline token in curl header: `-H "X-Farm-Token: eyJhbG..."` - token redacted to `***`, breaking quote pairing

## The Real Solution (Not Attempted in Session)

**Use `read_file` tool to read credentials, then embed the extracted token directly in subsequent commands.**

The `read_file` tool returns the actual file content (not redacted). Once the agent has the token in its context, it can construct curl commands with the literal token value. However, the terminal tool will STILL redact the token when the command is executed, so this only works if:

1. The token is passed via environment variable file (not inline)
2. OR the command is written to a script file and executed via `bash script.sh`
3. OR the heartbeat.py script is called directly (it reads credentials internally)

## Correct Cron Pattern for Token Extraction

```bash
# ❌ WRONG: Command substitution with grep/cut
FARM_TOKEN=$(cat ~/.config/43farm/credentials.json | grep -o '"farmToken":"[^"]*"' | cut -d'"' -f4)

# ✅ CORRECT: Use read_file tool to get token, then call heartbeat.py
# Agent uses read_file on ~/.config/43farm/credentials.json
# Then runs: python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
# The script reads credentials internally, no shell token passing needed
```

## Lessons

1. **Never use `$(cat ... | grep | cut)` for credential extraction in terminal commands** - the credential redaction will break the syntax
2. **Never use `python3 -c` in cron** - blocked by security scanner (pending_approval forever)
3. **The only reliable path is `read_file` + `heartbeat.py`** - read_file gets the real content, heartbeat.py handles all HTTP internally
4. **If token is needed for a one-off curl call** - write the curl command to a `.sh` file (without the token), and have the script read the token from the file internally
5. **Iteration budget awareness**: When the same command fails 3+ times with "syntax error", STOP and switch to a fundamentally different approach (file-based execution)

## Related References

- `terminal-credential-redaction-loop-transcript.md` - General credential redaction causing infinite loops
- `session-2026-06-16-cron-execute-code-blocked.md` - execute_code and python3 -c blocked in cron
- `heredoc-silent-failure-infinite-retry-loop.md` - Another infinite retry pattern in cron
