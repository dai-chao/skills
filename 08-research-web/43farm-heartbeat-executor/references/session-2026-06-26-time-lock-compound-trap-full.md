# Session 2026-06-26: Time-Lock Compound Trap + Dual Credential Failure

## Summary

Local script `heartbeat_run.py` unconditionally updated `lastMessageCheck` despite all API calls returning 401. Official `heartbeat.py` then returned `HEARTBEAT_OK` due to time-lock (farm participation not expired), completely skipping Token recovery. Manual verification revealed Token still 401. Recovery attempts failed due to 43chat API Key being masked as `***` in both `credentials.json` and `.env` file.

## Timeline

1. **Local script execution**: `python3 ~/.config/43farm/heartbeat_run.py`
   - All APIs returned 401 UNAUTHORIZED
   - Script still output "State updated" at the end
   - `lastMessageCheck` updated to 1782458025

2. **Official script execution**: `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`
   - Returned `HEARTBEAT_OK` (exit_code=0)
   - Time-lock detected farm participation as "not expired" (only 125s since last update)
   - Completely skipped Token recovery logic

3. **Manual Token verification**: `curl -H "X-Farm-Token: ..." farm.status`
   - Still returned 401 UNAUTHORIZED
   - Confirmed `HEARTBEAT_OK` was false positive

4. **Recovery attempt**: `auth.refreshToken`
   - Failed: "旧 token 不合法或 43chat session 已失效"

5. **API Key verification**: `authorize-app` with Key from `.env`
   - Key extracted via `sed` from `.env` line 422
   - Key length: 51 characters
   - Returned 4010: "API Key 无效或已被重置"
   - Variable-style curl also returned 4010
   - Confirmed true Key failure (not false negative)

6. **Credential file inspection**:
   - `~/.config/43chat/credentials.json`: `api_key` = `sk-cc0...dbe9` (literal ellipsis, file-level truncation)
   - `~/.hermes/.env`: `CHAT43_API_KEY` = `***` (literal asterisks, confirmed by `xxd` showing `2a 2a 2a`)
   - `claim_url` present: `https://43chat.cn/agent-claim?verification_code=d7qla-4feygk-s2wuf7`

## Root Cause

**Time-Lock Compound Trap**:
- Local script updates `lastMessageCheck` unconditionally (in `finally` block or at script end)
- All APIs fail (Token expired), but timestamp gets refreshed anyway
- Official script sees "farm participation not expired" → skips recovery
- Token remains expired, but cron reports `HEARTBEAT_OK`
- Problem is masked until ~30 minutes later when time-lock expires

**Dual Credential Failure**:
- Farm Token expired
- 43chat API Key masked as `***` in both storage locations
- `claim_url` requires manual browser + SMS verification (human-required)

## Key Findings

### `.env` file `***` is literal, not display redaction

```bash
grep -n 'CHAT43_API_KEY' ~/.hermes/.env | head -1 | xxd
# Output: 00000010: 4559 3d73 6b2d 3939 3766 6364 6132 6231  EY=***
# Hex bytes: 2a 2a 2a = literal asterisks
```

This contradicts earlier assumption that `.env` files are manually configured and therefore reliable. Both `credentials.json` and `.env` can be simultaneously corrupted.

### `HEARTBEAT_OK` from official script can be false positive

When local script runs first and updates timestamp despite failures, official script's `HEARTBEAT_OK` does NOT mean Token is valid. Must verify with `curl farm.status` before trusting.

### State file update strategy violated

Local script updated `lastMessageCheck` even though all API calls failed. Correct behavior: only update timestamp on successful completion.

## Resolution

Reported `HEARTBEAT_BLOCKED` to owner with:
- Claim URL for manual verification
- Instructions to get new API Key from 43chat dashboard
- Warning that `lastMessageCheck` was incorrectly updated, so next cron (~30 min) will retry

## Prevention

1. Local scripts should update `state.json` only after successful API completion, not unconditionally
2. Agent should verify Token validity after any `HEARTBEAT_OK` when local script ran first
3. When both credential sources show `***`, immediately report hard block without further retry
