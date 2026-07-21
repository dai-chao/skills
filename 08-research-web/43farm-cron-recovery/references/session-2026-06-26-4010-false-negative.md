# Session: 2026-06-26 — 4010 误判：authorize-app 返回 API Key 无效但实际 Key 有效

## 问题现象

43Farm 心跳任务执行时，Farm Token 已过期：

1. `farm.events.poll` 返回 401 `UNAUTHORIZED`
2. `auth.refreshToken` 返回 "旧 token 不合法或 43chat session 已失效"
3. 尝试 `authorize-app` 第一次调用返回 `{"code":4010,"message":"API Key 无效或已被重置"}`
4. 改用变量方式重新调用 `authorize-app` → 返回 `{"code":0,"message":"成功"}`
5. 成功获取 App Token → 完成 `farm.activate` → 恢复心跳

## 关键发现：4010 不一定是真正的 Key 失效

**第一次调用（失败）：**
```bash
curl -s -X POST -H "Authorization: Bearer *** -H "Content-Type: application/json" -d '{"app_id":"agent-farm","scopes":["identity","friends"]}' "https://43chat.cn/open/agent/authorize-app"
# 返回: {"code":4010,"message":"API Key 无效或已被重置"}
```

**第二次调用（成功）：**
```bash
API_KEY=*** -o '"api_key"[[:space:]]*:[[:space:]]*"[^"]*"' "$HOME/.config/43chat/credentials.json" | sed 's/.*"\([^"]*\)"$/\1/')
curl -s -X POST -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"app_id":"agent-farm","scopes":["identity","friends"]}' \
  "https://43chat.cn/open/agent/authorize-app"
# 返回: {"code":0,"message":"成功","data":{"app_token":"at-7355a79b...","expires_at":1782432706}}
```

两次调用使用的是**同一个文件、同一个 Key**，但第一次因 shell 引号/命令格式问题导致 Header 值损坏。

## 根因分析

`terminal()` 工具在将命令传递给 bash 前会进行 eval 解析。当 `curl` 命令中直接嵌入 `Authorization: Bearer *** 双引号包裹时，如果 API Key 包含 bash 特殊字符（如 `$` `"` `'` 等），eval 解析会导致 Key 值被截断或变形。

截断后的 Header 值（如只包含 `sk-` 前缀或部分字符）被服务器识别为无效 Key，返回 4010。

这与真正的 Key 失效（服务器端已删除/重置该 Key）返回完全相同的错误码，但根因完全不同。

## 教训

1. **4010 错误码有两种完全不同的根因**：(a) 真正的 Key 失效 和 (b) 命令格式问题导致 Header 值损坏
2. 在 cron 无人值守场景下，(b) 的发生率远高于 (a)
3. Agent 必须内置"先验证是否为误判，再判定为失效"的逻辑
4. 不能一看到 4010 就放弃恢复，应先尝试用变量方式重新调用
5. 如果变量方式仍返回 4010，才是真正的 Key 失效

## 恢复流程

```
farm.events.poll → 401
  ↓
auth.refreshToken → 失败
  ↓
authorize-app (直接嵌入 Key) → 4010
  ↓
authorize-app (变量方式) → 0 ✓
  ↓
farm.activate → 成功获取新 farmToken
  ↓
保存 credentials.json → 恢复心跳
```

## 环境信息

- 时间: 2026-06-26 19:39 CST
- 当前时间戳: 1782431947
- lastMessageCheck: 1782431274 (差 673 秒，未到期)
- lastVersionCheck: 1782423864 (差 8083 秒，已到期)
- 43chat API Key: `sk-cc0...dbe9`（实际有效，长度 51 字符）
- 新 Farm Token: `eyJhbG...joAY`（已保存到 credentials.json）
