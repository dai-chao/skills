# Terminal JWT Quoting Pitfalls

## Problem

Farm Token (JWT) contains dots (`.`) and other characters that cause bash parsing errors when embedded in heredocs, double-quoted strings, or complex curl commands.

## Symptoms

- `unexpected EOF while looking for matching '"'`
- `syntax error near unexpected token ')'`
- `No such file or directory` (URL interpreted as filename)

## Root Cause

Bash eval processes the command string before execution. JWT tokens like `eyJhbGciOiJIUzI1NiJ9.eyJ0eXBl...` contain dots which bash interprets as command separators in certain contexts.

## Solutions (in order of preference)

### 1. Write script to file, then execute (BEST)

```bash
# Write the script to a file first
cat > /tmp/farm_check.sh << 'SCRIPT_EOF'
#!/bin/bash
TOKEN="YOUR_TOKEN_HERE"
curl -s -H "X-Farm-Token: $TOKEN" -X POST \
  -H "Content-Type: application/json" \
  "https://farm.43chat.cn/trpc/farm.view" \
  -d '{"json":{}}'
SCRIPT_EOF

chmod +x /tmp/farm_check.sh
/tmp/farm_check.sh
```

**Critical**: Use `<< 'SCRIPT_EOF'` (with quotes around the delimiter) to prevent variable expansion and special character interpretation inside the heredoc.

### 2. Use single-quoted export + double-quoted reference

```bash
export TOKEN='eyJhbG...full.token.here'
curl -s -H "X-Farm-Token: $TOKEN" -X POST \
  -H "Content-Type: application/json" \
  'https://farm.43chat.cn/trpc/farm.view' \
  -d '{"json":{}}'
```

Note: The URL itself must be single-quoted or escaped to prevent bash from interpreting special characters.

### 3. Use a Python script (when execute_code is available)

```python
import subprocess, json
TOKEN = "eyJhbG..."
result = subprocess.run([
    "curl", "-s", "-H", f"X-Farm-Token: {TOKEN}",
    "-X", "POST", "-H", "Content-Type: application/json",
    "https://farm.43chat.cn/trpc/farm.view",
    "-d", json.dumps({"json": {}})
], capture_output=True, text=True)
print(result.stdout)
```

## Special Case: sed with regex capture groups inside `$()`

When extracting a token with sed using regex capture groups (`\(` and `\)`), embedding the `$()` inside a larger command string can cause bash eval errors:

```bash
# BAD — causes "syntax error near unexpected token `)'"
FARM_TOKEN=$(cat file.json | sed 's/.*"farmToken": "\([^"]*\)".*/\1/')
curl -s -H "X-Farm-Token: $FARM_TOKEN" "https://..."
```

The `\(` and `\)` in sed's regex pattern are interpreted by bash during `$()` expansion in certain contexts, leading to unmatched parenthesis errors.

**Fix**: Write the token to a temp file first, then read it back:

```bash
# Extract token to file
cat file.json | sed 's/.*"farmToken": "\([^"]*\)".*/\1/' > /tmp/token.txt
# Then use it
FARM_TOKEN=$(cat /tmp/token.txt)
curl -s -H "X-Farm-Token: $FARM_TOKEN" "https://..."
```

Or use `grep -o` + `cut` (no regex capture groups):

```bash
FARM_TOKEN=$(cat file.json | grep -o '"farmToken":"[^"]*"' | cut -d'"' -f4)
```

## What NOT to do

- ❌ Do NOT embed the token directly in a double-quoted curl command with other double-quoted headers
- ❌ Do NOT use `echo` with the token to construct commands
- ❌ Do NOT use `eval` with token-containing strings
- ❌ Do NOT use backticks or `$()` with token-containing commands
- ❌ Do NOT use sed with `\(` `\)` capture groups inside `$()` without isolation

## Cron Context

In cron jobs, prefer calling the built-in `heartbeat.py` script rather than constructing curl commands manually. The script handles token management internally and avoids these quoting issues entirely.
