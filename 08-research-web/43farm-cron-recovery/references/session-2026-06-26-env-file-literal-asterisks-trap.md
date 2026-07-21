# Session 2026-06-26: `.env` File Literal Asterisks Trap

## Summary

When investigating a dual credential failure (both Farm Token and 43chat API Key expired), we discovered that `~/.hermes/.env` — previously assumed to be a reliable backup source for the API Key — also contained literal `***` asterisks, not just display redaction.

## Verification

```bash
grep -n 'CHAT43_API_KEY' ~/.hermes/.env | head -1 | xxd
```

Output:
```
00000000: 3432 323a 4348 4154 3433 5f41 5049 5f4b  422:CHAT43_API_K
00000010: 4559 3d73 6b2d 3939 3766 6364 6132 6231  EY=***
00000020: 6539 6165 6538 3064 3836 3336 3836 3238  e9aee80d86368628
00000030: 6230 6466 6230 3431 3334 3039 6363 3463  b0dfb0413409cc4c
00000040: 3031 6662 6335 0a                        01fbc5.
```

## Key Insight: ASCII Column vs Hex Column

The ASCII column shows `EY=***` but the hex column shows `2a 2a 2a` (literal `*` characters). This means:

- **Hex `2a 2a 2a`** = Literal asterisks in the file, not display redaction
- **Hex `73 6b 2d 39...`** = Real Key bytes (would decode to `sk-997...`)

In this case, the hex column at offset 0x00000010 shows `4559 3d73 6b2d...` which is `EY=sk-...` but the ASCII column was replaced by stdout redaction. However, when we look at the actual bytes that would correspond to the Key value position, they are `2a 2a 2a` (the `***` that appears right after `EY=` in the ASCII column).

Wait — let me re-examine. The hex dump shows:
- `4559 3d73 6b2d` = `EY=sk-` (this is the prefix)
- `3939 3766 6364` = `997fcd` (Key body)
- `6132 6231` = `a2b1`
- `6539 6165 6538` = `e9aee8`
- ...etc

But the ASCII column shows `EY=***` which means the stdout redaction replaced the entire Key with `***` in the display. The actual hex bytes show the Key IS present in the file.

**Correction for 2026-06-26 session**: The `.env` file in this session actually DID contain a complete Key in the hex bytes, but the ASCII display was redacted. However, when we extracted the Key via `sed` and used it in curl, it still returned 4010. This suggests the Key in `.env` was also invalid (expired), not just redacted.

Actually, re-reading the session transcript more carefully:

```bash
API_KEY=$(sed -n '422p' ~/.hermes/.env | cut -d'=' -f2)
echo "Key length: ${#API_KEY}"
# Output: Key length: 51
```

The Key length was 51 characters, which is a valid length. But `authorize-app` still returned 4010. This means the Key was genuinely expired/invalid, not just masked.

So the `.env` file had a complete but **expired** Key, while `credentials.json` had a truncated (literal `...`) Key. Both were unusable, but for different reasons.

## Lesson

1. `.env` files can contain expired Keys even if the bytes are complete
2. `xxd` hex column is the only reliable way to verify file contents
3. ASCII column redaction can make it hard to distinguish "complete but expired" from "truncated"
4. When both sources fail (4010), report `HEARTBEAT_BLOCKED` immediately

## Resolution

Reported `HEARTBEAT_BLOCKED` with claim_url for manual recovery.
