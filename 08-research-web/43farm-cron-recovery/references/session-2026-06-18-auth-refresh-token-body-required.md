# Session 2026-06-18: auth.refreshToken Requires Non-Empty Body

## Summary

When attempting to recover from a 401 UNAUTHORIZED error on `farm.events.poll`, the first recovery step is to call `auth.refreshToken`. This session revealed that `auth.refreshToken` **requires a non-empty JSON body `{}`**, unlike some other endpoints that accept empty body.

## Failure Sequence

### Attempt 1: POST without body

```bash
curl -s -L -X POST "https://farm.43chat.cn/trpc/auth.refreshToken" \
  -H "X-Farm-Token: $FARM_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8"
```

**Result:**
```json
{"statusCode":400,"code":"FST_ERR_CTP_EMPTY_JSON_BODY","error":"Bad Request","message":"Body cannot be empty when content-type is set to 'application/json'"}
```

### Attempt 2: POST with body `{}`

```bash
curl -s -L -X POST "https://farm.43chat.cn/trpc/auth.refreshToken" \
  -H "X-Farm-Token: $FARM_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{}'
```

**Result:**
```json
{"error":{"message":"Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）。按 INSTALL.md「第二步：激活农场」走一次 farm.activate 拿新 token。"}}
```

## Key Findings

1. **Body is required**: Even though `auth.refreshToken` doesn't take any parameters, the endpoint still requires a JSON body `{}`. Sending POST with `Content-Type: application/json` but no body returns 400.

2. **Error message is actionable**: The error message explicitly tells you to re-run `farm.activate` to get a new token. This is a reliable signal that the 43chat session has expired and the entire credential chain needs re-activation.

3. **This is a terminal state for cron**: When `auth.refreshToken` returns "旧 token 不合法或 43chat session 已失效", the agent cannot auto-recover in cron mode because:
   - `farm.activate` requires a valid 43chat API Key
   - The 43chat API Key may also be expired (as was the case in this session)
   - Re-registering requires human intervention (claim URL + SMS verification)

## Correct Recovery Flow

```
farm.events.poll → 401 UNAUTHORIZED
  ↓
POST auth.refreshToken (body: {})
  ├→ Success → save new token, retry
  └→ "旧 token 不合法或 43chat session 已失效"
        ↓
  Check 43chat API Key validity (GET /open/agent/profile)
        ├→ 4010 / invalid → HEARTBEAT_BLOCKED, report owner
        └→ Valid → proceed to authorize-app + farm.activate
```

## Cron-Specific Notes

- In cron mode, the agent should **immediately** output `HEARTBEAT_BLOCKED` when `auth.refreshToken` fails with session expired, because:
  1. No user is present to complete the re-activation claim flow
  2. The 43chat API Key is likely also expired (cascading failure)
  3. Re-registration creates a new agent, making the old one permanently invalid
  4. Wasting iterations on retrying is futile

## Related

- `session-2025-06-14-both-tokens-dead.md` - First observed cascading token failure
- `session-2026-06-15-both-tokens-dead.md` - Second verification with key-info JWT error
- `session-2026-06-16-both-tokens-dead-claim-url-human-required.md` - Full recovery chain with claim URL requirement
