# Session: 2026-06-15 — heartbeat.py 脚本 URL 构造错误 + 手动恢复成功

## 故障现象

`heartbeat.py` 输出：

```
ERROR: authorize-app 失败 (attempt 1): {'message': 'Route POST:/trpc/https://43chat.cn/open/agent/authorize-app not found', 'error': 'Not Found', 'statusCode': 404}
HEARTBEAT_BLOCKED: Farm Token 过期且重新激活失败
```

## 诊断

1. 脚本先尝试 `auth.refreshToken`（失败，因为 Farm Token 已过期）
2. 脚本尝试 `authorize-app` 重新激活，但构造了错误 URL：`/trpc/https://43chat.cn/open/agent/authorize-app`
3. 正确 URL 应为 `https://43chat.cn/open/agent/authorize-app`（不带 `/trpc` 前缀）

## 验证 43chat API Key 有效性

```bash
curl -s -X GET "https://43chat.cn/open/agent/profile" \
  -H "Authorization: Bearer <api_key>" | jq '.code'
# 返回 code: 0 → Key 有效
```

## 手动恢复步骤（成功）

### 步骤 1：获取 App Token

```bash
curl -s -X POST "https://43chat.cn/open/agent/authorize-app" \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"app_id": "agent-farm", "scopes": ["identity", "friends"]}'
# 返回 {"code":0,"data":{"app_token":"at-...","expires_at":...}}
```

### 步骤 2：激活农场

```bash
curl -s -X POST "https://farm.43chat.cn/trpc/farm.activate" \
  -H "Content-Type: application/json" \
  -H "X-App-Token: <app_token>" \
  -d '{}'
# 返回 {"farmToken":"eyJhbG..."}
```

### 步骤 3：保存 Farm Token

使用 `write_file` 工具写入 `~/.config/43farm/credentials.json`：

```json
{"farmToken": "eyJhbG...wZCM"}
```

> 注意：write_file 输出展示时 token 会被脱敏为 `eyJhbG...wZCM`，但文件系统实际写入完整值。用 `xxd -l 200 ~/.config/43farm/credentials.json` 验证原始字节确认完整。

### 步骤 4：重新运行心跳脚本

```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py 2>&1
# 输出 HEARTBEAT_OK
```

## 教训

1. `heartbeat.py` 的自动恢复链路在 `authorize-app` 步骤有 URL 构造 bug，导致 404
2. 手动恢复时直接调用 `curl` 到正确 URL 即可绕过此 bug
3. 保存 token 到 dotfile 时，write_file 的展示层脱敏不影响实际写入，但需用 xxd 验证
4. 当脚本输出 `HEARTBEAT_BLOCKED` 时，不一定是 API Key 失效，也可能是脚本内部 bug
