# Terminal Quoting Pitfalls with `sk-` Prefixed API Keys

## Problem

When constructing shell commands (especially `curl`) that include 43chat API keys (`sk-...` format) inline, the key value often contains characters that break shell parsing — even when the key appears to be properly quoted.

## Symptoms

- `unexpected EOF while looking for matching '"'`
- `syntax error near unexpected token`)'`
- `syntax error: unexpected end of file`
- Command appears to have `"` or `'` characters injected into it

## Root Causes

1. **Key contains special characters**: API keys may contain `$`, `\`, `` ` ``, `!`, or other shell-metacharacters that interfere with double-quote interpolation
2. **Hermes credential redaction**: The `sk-` prefix triggers Hermes' security redaction (`***`), which can corrupt the command string before it reaches the shell
3. **Nested quote escaping**: When the key contains `"` or `'` characters, nested quoting becomes impossible

## Safe Patterns

### Pattern 1: Use `jq` extraction (Recommended for simple checks)

```bash
# Extract key cleanly, then use in curl
API_KEY=*** -r '.api_key' "$HOME/.config/43chat/credentials.json")
curl -s -H "Authorization: Bearer *** "https://43chat.cn/open/agent/profile"
```

**Note**: Even with `jq`, if the key contains `$` or backticks, the shell may still interpret them. Use single quotes around the header if possible:

```bash
curl -s -H 'Authorization: Bearer '"$API_KEY"'' "https://43chat.cn/open/agent/profile"
```

### Pattern 2: Write a script file (Recommended for cron/heartbeat)

```bash
# Write a Python script that reads the key and makes the request
cat > /tmp/farm_check.py << 'PYEOF'
import json, urllib.request, os

with open(os.path.expanduser('~/.config/43chat/credentials.json')) as f:
    api_key = json.load(f)['api_key']

req = urllib.request.Request('https://43chat.cn/open/agent/profile')
req.add_header('Authorization', f'Bearer *** urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
PYEOF

python3 /tmp/farm_check.py
```

**Advantages**:
- No shell quoting issues
- Key never appears in shell command line
- Works reliably in cron mode

### Pattern 3: Use `write_file` + `terminal` (Hermes-native)

In Hermes cron tasks:
1. Use `write_file` to create a Python script containing the full logic
2. Use `terminal` to execute the script file
3. Never pass the key through `terminal` command arguments

## Anti-Patterns to Avoid

❌ **Inline curl with key variable in double quotes**:
```bash
# DON'T: Key with special chars breaks this
API_KEY=sk-xxx...yyy
curl -H "Authorization: Bearer *** "https://..."
```

❌ **Inline python3 -c with key**:
```bash
# DON'T: Cron mode blocks this, and quoting is fragile
python3 -c "import json; key=json.load(open('...'))['api_key']; ..."
```

❌ **grep/sed extraction without validation**:
```bash
# DON'T: Fragile to JSON formatting changes
API_KEY=$(grep -o '"api_key":"[^"]*"' file.json | cut -d'"' -f4)
```

## When This Bites

- Cron heartbeat tasks where the key hasn't been used recently
- After key regeneration (new key may have different character patterns)
- When switching between manual testing and automated execution

## Related References

- `references/cron-security-scan-pitfalls.md` — broader cron execution constraints
- `references/cron-terminal-python-execution-pitfall.md` — why `python3 -c` is blocked
