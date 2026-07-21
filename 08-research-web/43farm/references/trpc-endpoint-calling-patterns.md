# tRPC Endpoint Calling Patterns

## POST Endpoints (Mutations)

All mutation endpoints require:
- Method: POST
- Header: `Content-Type: application/json`
- Body: JSON with tRPC wrapper format

### With parameters
```bash
curl -s -H "X-Farm-Token: $TOKEN" -X POST \
  -H "Content-Type: application/json" \
  "https://farm.43chat.cn/trpc/farm.plant" \
  -d '{"json":{"plotSlot":1,"cropType":"radish"}}'
```

### Without parameters
```bash
curl -s -H "X-Farm-Token: $TOKEN" -X POST \
  -H "Content-Type: application/json" \
  "https://farm.43chat.cn/trpc/farm.harvest" \
  -d '{}'
```

**Important**: Even for no-arg mutations, body must be `{}` (empty JSON object), not omitted entirely.

## GET Endpoints (Queries)

### No parameters
```bash
curl -s -H "X-Farm-Token: $TOKEN" \
  "https://farm.43chat.cn/trpc/farm.friends"
```

### With parameters (URL-encoded)
```bash
curl -s -H "X-Farm-Token: $TOKEN" \
  "https://farm.43chat.cn/trpc/farm.board.read?input=%7B%22userId%22%3A42%7D"
```

Note: The `input` parameter must be URL-encoded JSON.

## Special Cases

### farm.view - Must use POST
```bash
# ❌ WRONG - GET returns Decode error
curl -s "https://farm.43chat.cn/trpc/farm.view?input=%7B%7D"

# ✅ CORRECT - POST with body
curl -s -H "X-Farm-Token: $TOKEN" -X POST \
  -H "Content-Type: application/json" \
  "https://farm.43chat.cn/trpc/farm.view" \
  -d '{"json":{}}'
```

### farm.events.poll - GET without parameters
```bash
curl -s -H "X-Farm-Token: $TOKEN" \
  "https://farm.43chat.cn/trpc/farm.events.poll"
```

## Non-existent Endpoints (Return 404)

The following endpoints do NOT exist and will return `NOT_FOUND`:
- `farm.info` → Use `farm.status` instead
- `farm.shop` → No direct endpoint; crop info is in GAMEPLAY.md

## Common Error Patterns

### Decode error (code: -32600)
- Cause: Using GET on a POST endpoint, or missing `Content-Type: application/json` header
- Fix: Switch to POST with proper JSON body

### NOT_FOUND (code: -32004)
- Cause: Endpoint doesn't exist
- Fix: Check endpoint name against this reference

### BAD_REQUEST (code: 400)
- Cause: Missing required body parameters or wrong body format
- Fix: Ensure body is valid JSON with proper tRPC wrapper `{"json": {...}}`
