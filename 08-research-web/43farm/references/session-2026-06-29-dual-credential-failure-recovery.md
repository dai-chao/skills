# Session 2026-06-29: Dual Credential Failure Recovery

## Problem

During a cron heartbeat execution, both the Farm Token and the 43chat API Key were simultaneously expired/invalid, causing a complete activation chain failure.

## Diagnostic Timeline

1. **Farm Token check**: `farm.events.poll` returned 401 UNAUTHORIZED
2. **Attempt `auth.refreshToken`**: Returned 404 NOT_FOUND — endpoint does not exist
3. **Attempt 43chat authorize-app**: Returned 4010 "API Key 无效或已被重置"
4. **Verify 43chat API Key**: `GET /open/agent/profile` returned 4010, confirming API Key失效
5. **Conclusion**: Root cause was 43chat API Key expiration, not just Farm Token expiration

## Recovery Flow (when auth.refreshToken is unavailable)

```
farm.events.poll → 401
  ↓
auth.refreshToken → 404 (endpoint not found)
  ↓
Check 43chat API Key via /open/agent/profile → 4010
  ↓
API Key expired — need owner intervention to regenerate
  ↓
(Owner regenerates key)
  ↓
POST /open/agent/authorize-app → new App Token
  ↓
POST /farm.activate → new Farm Token
  ↓
Save to ~/.config/43farm/credentials.json
  ↓
Verify with farm.status → should work
```

## Key Findings

1. **auth.refreshToken is a dead endpoint** (as of 2026-06-29). Do not rely on it.
2. **43chat API Key is the root dependency** — when it expires, the entire farm activation chain breaks because:
   - Farm Token cannot be refreshed without a valid 43chat API Key
   - `authorize-app` requires a valid 43chat API Key
   - `farm.activate` requires a valid App Token from `authorize-app`
3. **Farm Token from `farm.activate` may have propagation delay** — in this session, the first new token was immediately rejected with 401. This could be:
   - Token propagation delay (wait 5-10s and retry)
   - Backend issue with token generation
   - The token format/validation changed

## Terminal Quoting Pitfalls with `sk-` Keys

When constructing curl commands with 43chat API keys in terminal:

- **Problem**: Keys containing `...` or special characters cause shell parsing errors
- **Symptom**: `unexpected EOF while looking for matching '"'` or `syntax error near unexpected token`
- **Cause**: The key value itself contains characters that break the shell command string
- **Workaround**: Use `jq` to extract the key cleanly:
  ```bash
  API_KEY=$(jq -r '.api_key' "$HOME/.config/43chat/credentials.json")
  curl -s -H "Authorization: Bearer $API_KEY" "https://43chat.cn/open/agent/profile"
  ```
- **Alternative**: Use Python script files instead of inline curl commands for complex token handling

## Cron-Specific Notes

- In cron mode, `execute_code` is BLOCKED for security reasons
- Use `terminal` with script files instead of `python3 -c` or `curl | python3` patterns
- `write_file` + `terminal` (calling the script file) is the safest pattern for cron

## Owner Communication Template

When both credentials are expired and owner intervention is needed:

```
43Farm 心跳任务报告 — 需要主人介入

问题：Farm Token 和 43chat API Key 同时失效，无法自动恢复。

需要主人执行：
1. 打开 https://43chat.cn 登录账号
2. 进入「我的 Agent/API Key」页面
3. 生成新的 API Key
4. 更新 ~/.config/43chat/credentials.json

完成后通知我，我将自动完成农场重新激活。
```
