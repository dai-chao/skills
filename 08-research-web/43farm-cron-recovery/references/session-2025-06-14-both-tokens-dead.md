# 真实故障记录：Farm Token 与 43chat API Key 同时失效

**日期**：2025-06-14  
**触发方式**：cron 定时心跳任务  
**环境**：macOS, Hermes Agent, kimi-k2.6 / kimi-coding provider

## 故障现象

心跳任务执行时，`farm.events.poll` 返回 401：

```json
{
  "error": {
    "message": "Farm Token 无效或已过期。按 INSTALL.md「日常自愈」段换个新 token 再继续。",
    "code": -32001,
    "data": {
      "code": "UNAUTHORIZED",
      "httpStatus": 401,
      "path": "farm.events.poll"
    }
  }
}
```

## 恢复尝试与失败链

### 步骤 1：尝试 auth.refreshToken

```bash
curl -s -X POST -H "X-Farm-Token: eyJhbG...Ur00" \
  https://farm.43chat.cn/trpc/auth.refreshToken
```

返回：

```json
{
  "error": {
    "message": "Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）。按 INSTALL.md「第二步：激活农场」走一次 farm.activate 拿新 token。"
  }
}
```

### 步骤 2：尝试用 43chat API Key 重新激活

读取 `~/.config/43chat/credentials.json` 中的 `api_key`：

```bash
jq -r '.api_key' ~/.config/43chat/credentials.json
# 输出: sk-997...fbc5  （已脱敏展示）
```

调用 `authorize-app`：

```bash
curl -s -X POST \
  -H "Authorization: Bearer sk-997...fbc5" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"agent-farm","scopes":["identity","friends"]}' \
  https://43chat.cn/open/agent/authorize-app
```

返回：

```json
{
  "code": 4010,
  "message": "API Key 无效或已被重置。请确认 Header 为 Authorization: Bearer sk-xxx...的「我的 Agent/API Key」页面最新生成的 Key；可调用 GET /api/personal/key-info 查看当前 Key 前缀是否匹配。",
  "timestamp": 1781427515
}
```

### 步骤 3：确认 API Key 确实无效

尝试调用 `/api/personal/key-info`：

```bash
curl -s -H 'Authorization: Bearer sk-997...fbc5' \
  -H 'Content-Type: application/json' \
  https://43chat.cn/api/personal/key-info
```

返回：

```json
{
  "code": 401,
  "message": "无效的token: 解析用户Token失败: token contains an invalid number of segments",
  "timestamp": 1781427528
}
```

## 根因

**43chat API Key 已失效**（返回 4010），导致整个恢复链断裂：

1. Farm Token 过期 → 需要重新激活
2. 重新激活需要 43chat API Key → Key 已失效
3. 无法自治恢复（cron 无人值守场景下不能自行注册新 Key）

## 正确处置（cron 无人值守场景）

当检测到 API Key 返回 4010 时：

1. 立即停止所有恢复尝试（不要重试 `authorize-app`，不要重试 `farm.activate`）
2. 输出明确的阻塞标记：`HEARTBEAT_BLOCKED`
3. 在报告中说明：
   - 43chat API Key 已失效（错误码 4010）
   - 需要主人访问 https://43chat.cn 「我的 Agent/API Key」页面重置并获取新 Key
   - 提供新 Key 后，agent 会自动完成 Farm Token 续签和后续农场操作
4. 更新 `state.json` 中的 `lastMessageCheck` 为当前时间（避免下次 cron 立即再次触发相同的失败链）

## 附带问题：shell 引号逃逸循环

在诊断过程中，多次尝试用 `curl -H "Authorization: Bearer ..."` 调用 API，由于 API Key 中的特殊字符与 bash 引号冲突，导致：

```
/bin/bash: eval: line 2: unexpected EOF while looking for matching `"'
/bin/bash: eval: line 3: syntax error: unexpected end of file
```

即使切换单引号/双引号组合也无法解决。这是 `terminal()` 工具 eval 解析的固有限制。

**教训**：在 cron 无人值守场景中，如果脚本不存在，手写 `curl` 命令几乎必然遇到引号问题。唯一可靠路径是：
- 先用 `write_file` 将完整请求写入 `.sh` 脚本文件
- 再用 `bash /tmp/script.sh` 执行
- 或直接用 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`（如果脚本存在）

## 错误码速查

| 接口 | 错误码 | 含义 | 处置 |
|------|--------|------|------|
| `farm.events.poll` | 401 / -32001 | Farm Token 过期 | 尝试 `auth.refreshToken` |
| `auth.refreshToken` | 401 / 错误体 | 旧 token 不合法 | 尝试重新激活 |
| `authorize-app` | 4010 | 43chat API Key 无效 | **HEARTBEAT_BLOCKED**，报告主人 |
| `key-info` | 401 | Token 解析失败 | 确认 Key 格式/长度 |
