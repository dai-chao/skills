# 43Farm Cron Token 恢复——真实会话故障记录

> 记录一次完整的 cron 心跳 Token 恢复失败过程，供未来会话快速比对和诊断。

## 会话背景

- 触发方式：cron 定时任务（无人值守）
- 时间：2026-06-14
- 当前时间戳：1781426713
- state.json：`lastMessageCheck=1781424715`, `lastVersionCheck=1781420664`
- 农场参与已到期（1998s ≥ 1800s），版本检测尚未到期（6049s < 7200s）

## 故障时间线

### Step 1: farm.events.poll → 401

```
POST https://farm.43chat.cn/trpc/farm.events.poll
X-Farm-Token: eyJhbG...Ur00

Response:
{"error":{"message":"Farm Token 无效或已过期。按 INSTALL.md「日常自愈」段换个新 token 再继续。","code":-32001,"data":{"code":"UNAUTHORIZED","httpStatus":401,"path":"farm.events.poll"}}}
```

### Step 2: auth.refreshToken → 失败

```
POST https://farm.43chat.cn/trpc/auth.refreshToken
X-Farm-Token: eyJhbG...Ur00
Body: {}

Response:
{"error":{"message":"Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）。按 INSTALL.md「第二步：激活农场」走一次 farm.activate 拿新 token。"}}
```

### Step 3: 尝试重新激活 → 43chat API Key 失效

```
POST https://43chat.cn/open/agent/authorize-app
Authorization: Bearer sk-997...fbc5
Content-Type: application/json
Body: {"app_id":"agent-farm","scopes":["identity","friends"]}

Response:
{"code":4010,"message":"API Key 无效或已被重置。请确认 Header 为 Authorization: Bearer sk-xxx...的「我的 Agent/API Key」页面最新生成的 Key；可调用 GET /api/personal/key-info 查看当前 Key 前缀是否匹配。","timestamp":1781426753}
```

### Step 4: 验证 API Key 不是脱敏存储

```bash
jq -r '.api_key' ~/.config/43chat/credentials.json | wc -c
# 输出: 52（正常长度，约50-60字符）

jq -r '.api_key' ~/.config/43chat/credentials.json | grep -q '\.\.' && echo "CONTAINS_ELLIPSIS" || echo "NO_ELLIPSIS"
# 输出: NO_ELLIPSIS
```

**结论**：Key 是真实完整的，但已在服务端失效（被重置或过期）。

## 最终判定

**根因**：43chat API Key 已失效（4010）→ 无法申请 App Token → 无法重新激活农场 → 无法恢复 Farm Token。

**正确处置**：输出 `HEARTBEAT_BLOCKED`，报告主人，等待主人从 https://43chat.cn 重置 API Key。

## 错误码速查对照

| 接口 | 错误码/消息 | 含义 | 下一步 |
|------|------------|------|--------|
| `farm.events.poll` | `code:-32001`, `UNAUTHORIZED`, `Farm Token 无效或已过期` | Farm Token 过期 | 调 `auth.refreshToken` |
| `auth.refreshToken` | `旧 token 不合法或 43chat session 已失效` | Token 无法续签 | 验证 43chat API Key |
| `authorize-app` | `code:4010`, `API Key 无效或已被重置` | 43chat API Key 失效 | **硬阻塞，需主人介入** |
| `authorize-app` | `code:401`, `无效的token` | Authorization Header 格式错误或 token 损坏 | 检查 Header 拼写 |

## 关键教训

1. **4010 是硬阻塞信号**：`authorize-app` 返回 4010 时，agent 在 cron 场景下**完全无法自治恢复**。不要尝试重新注册（已认领用户不允许重复认领），不要反复重试（浪费日志空间）。
2. **先验证 Key 再申请 App Token**：`authorize-app` 的 App Token 是一次性的。如果 Key 已失效，申请会失败并浪费一次 App Token 机会。应先调 `GET /open/agent/profile` 验证 Key 有效性。
3. **长度检查排除脱敏**：Key 长度 52 字符且无省略号 → 确认是真实 Key，只是服务端已失效。避免误判为"文件损坏"而做无意义的修复。
4. **curl Header 引号问题**：当 Key/Token 含特殊字符时，`curl -H "Authorization: Bearer ..."` 在 `terminal()` 中会触发 bash eval 错误。本会话中使用**单引号包裹整个 curl 命令**（`curl -s -H 'Authorization: Bearer ...' 'URL'`）成功绕过了此问题。
