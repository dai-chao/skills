# Session 2026-06-21: Cron 心跳 — Farm Token + 43chat API Key 双失效 + claim_url 需人工认领

## 场景

Cron 触发的心跳任务。`lastMessageCheck` 已到期 24890 秒（≈6.9h），`lastVersionCheck` 已到期 110218 秒（≈30.6h）。

## 诊断链

1. `farm.events.poll` → 401 `Farm Token 无效或已过期`
2. `auth.refreshToken` → 失败：旧 token 不合法或 43chat session 已失效
3. `farm.activate`（用现有 App Token）→ 失败：app_token 已失效
4. 运行 `heartbeat.py` → 输出 `HEARTBEAT_BLOCKED: 缺少 43chat API Key`
5. 检查 `~/.config/43chat/credentials.json` → `api_key` 已被服务器端掩码为 `***`
6. 浏览器打开 `claim_url` → 页面要求**手机号 + 短信验证**才能认领 Agent

## 关键发现

- `credentials.json` 中的 `api_key` 字段被服务器端替换为 `***`，不是展示层脱敏，而是文件本身被服务器写入了掩码值
- `claim_url`（`https://43chat.cn/agent-claim?verification_code=54g32-oqf58y-3c4ef7`）需要人工完成短信验证
- 这是 cron 无人值守场景下的**终极硬阻塞**：agent 无法自行完成短信验证

## 正确处置

1. 输出 `HEARTBEAT_BLOCKED`
2. 在报告中提供 `claim_url` 给主人
3. **不更新 `lastMessageCheck`**（保留旧值，下次 cron 仍会重试农场参与）
4. **不更新 `lastVersionCheck`**（虽然版本检测不依赖 Farm Token，但本次未执行，保留旧值以便下次重试）
5. 停止所有恢复步骤，不反复重试

## 状态文件策略验证

| 检查项 | 是否到期 | 是否成功 | 是否更新 state.json |
|--------|----------|----------|---------------------|
| 农场参与 | 是 | 否（Token 阻塞） | **否**（保留旧值） |
| 版本检测 | 是 | 否（未执行） | **否**（保留旧值） |

## 引用

- `43farm-cron-recovery` skill 中的「43chat API Key 失效」和「状态文件更新策略」章节
