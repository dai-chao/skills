# Hermes `config set` CLI Pitfall — Arrays Become Strings

## Problem

`hermes config set <key> <value>` treats all values as strings. When setting array fields like `mcp_servers.*.args`, the result is a quoted JSON string instead of a YAML list:

```yaml
# WRONG — what `hermes config set` produces
args: '["-y", "@modelcontextprotocol/server-filesystem", "/Users/chao"]'

# CORRECT — what MCP needs
args:
  - "-y"
  - "@modelcontextprotocol/server-filesystem"
  - "/Users/chao"
```

## Impact

The MCP server subprocess receives a single argument that is a JSON-encoded string, not the intended individual arguments. This typically causes:
- "Package not found" or "command not found" errors
- The server fails to start
- Tool discovery fails

## Fix

Edit `~/.hermes/config.yaml` directly using `hermes config edit` (opens nano/pico) or any text editor. Use proper YAML list syntax.

## Workaround for Scripting

If you must script config changes, use `sed`/`awk` or Python to modify the YAML file directly rather than `hermes config set` for array fields. Example:

```python
import yaml

with open("~/.hermes/config.yaml", "r") as f:
    config = yaml.safe_load(f)

config["mcp_servers"] = {
    "time": {"command": "uvx", "args": ["mcp-server-time"]},
    "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/chao"]},
}

with open("~/.hermes/config.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

## Session Reference

- Date: 2026-06-17
- User: chao
- Hermes version: current (config.yaml at ~/.hermes/config.yaml)
- Commands that reproduced the issue:
  ```
  hermes config set mcp_servers.time.args '["mcp-server-time"]'
  hermes config set mcp_servers.filesystem.args '["-y", "@modelcontextprotocol/server-filesystem", "/Users/chao"]'
  ```
- Result: args fields stored as quoted strings, not YAML arrays.
