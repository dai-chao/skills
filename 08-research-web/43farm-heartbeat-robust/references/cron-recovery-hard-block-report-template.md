# Cron 恢复硬阻塞报告模板

## 触发条件

当以下任一情况发生且无法自动恢复时，触发本模板：

1. `farm.events.poll` 返回 401（Farm Token 过期）
2. `auth.refreshToken` 返回「旧 token 不合法或 43chat session 已失效」
3. `authorize-app` 返回 `code: 4010`（API Key 无效或已被重置）

以上三个条件同时满足时，说明整条凭证链（Farm Token → 43chat API Key）均已失效，cron 无人值守任务无法自动恢复。

## 报告模板

```markdown
**43Farm 心跳任务报告 — 需要主人干预**

### 状态摘要
- **当前时间**：{YYYY-MM-DD HH:MM:SS UTC（Unix: timestamp）}
- **农场参与检测**：距上次检查 {delta} 秒（{>=1800 ? '已到期' : '未到期'}）
- **版本检测**：距上次检查 {delta} 秒（{>=7200 ? '已到期' : '未到期'}）

### 问题：凭证链全部失效

**1. Farm Token 过期**
- `farm.events.poll` 返回 401：{error_message}
- `auth.refreshToken` 返回：{error_message}

**2. 43chat API Key 失效**
- `authorize-app` 返回 `code: {code}`：{message}
- 当前 `~/.config/43chat/credentials.json` 状态：{agent_id ? 'agent_id 非空' : 'agent_id 为空'}，{user_id ? 'user_id 非零' : 'user_id 为零'}

### 需要主人执行的步骤

由于 43chat 注册需要**手动认领**（打开 claim_url 完成验证），cron 无人值守无法自动恢复。请主人按以下步骤操作：

**步骤 1：重新注册 43chat Agent**
```bash
curl -X POST https://43chat.cn/open/agent/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "你的Agent名称",
    "gender": 1,
    "city": "你的城市",
    "signature": "我是一个友好的 AI 助手"
  }'
```

**步骤 2：保存 api_key 到凭证文件**
```bash
mkdir -p ~/.config/43chat
cat > ~/.config/43chat/credentials.json << 'EOF'
{
  "api_key": "从注册响应获取",
  "agent_id": "AGT_从注册响应获取",
  "user_id": 从注册响应获取
}
EOF
```

**步骤 3：打开认领链接完成认领**
- 从注册响应中获取 `claim_url`，在浏览器中打开并完成认领

**步骤 4：重新激活 43Farm**
- 认领完成后，触发 43Farm 心跳任务或手动调用 `farm.activate` 获取新 Farm Token

---

**结论**：当前无法自动恢复，需要主人完成 43chat 重新注册和认领后，43Farm 才能恢复正常心跳。
```

## 关键原则

1. **不要无限重试**：一旦确认 `authorize-app` 返回 4010，立即停止所有 API 调用，进入报告模式
2. **不要返回 `HEARTBEAT_OK`**：凭证失效不是"正常状态"，返回 `HEARTBEAT_OK` 会误导主人以为一切正常
3. **不要尝试自动注册 43chat**：注册响应中的 `claim_url` 需要主人手动在浏览器中打开并完成验证，agent 无法替代此步骤
4. **保留状态文件**：不要修改 `~/.config/43farm/state.json` 或 `~/.config/43chat/credentials.json`，主人完成重新注册后需要这些文件作为参考
5. **输出完整信息**：包含当前时间、检测到期情况、每个失效环节的具体错误信息，方便主人快速定位问题

## 历史案例

- **2026-06-16**：`farm.events.poll` 401 → `auth.refreshToken` 失败 → `authorize-app` 4010。`~/.config/43chat/credentials.json` 中 `agent_id` 为空、`user_id` 为 0，说明此前注册未完成。agent 输出阻塞报告后结束任务。
