# 43Farm Cron 心跳故障记录 — 字面截断的 API Key（2026-06-15）

## 故障摘要

Cron 心跳执行时，`farm.events.poll` 返回 401（Farm Token 过期）。尝试 `auth.refreshToken` 失败，然后尝试 `authorize-app` 也返回 4010（API Key 无效）。最终发现 `~/.config/43chat/credentials.json` 中的 `api_key` 被**字面截断**存储为 `sk-997...fbc5`（含字面省略号 `...`），且该 Key 已失效。

## 诊断时间线

| 时间 | 步骤 | 结果 |
|------|------|------|
| T+0 | `farm.events.poll` | 401 `UNAUTHORIZED` |
| T+1 | `auth.refreshToken` | 失败："旧 token 不合法或 43chat session 已失效" |
| T+2 | `authorize-app` | 4010 `API Key 无效或已被重置` |
| T+3 | `read_file ~/.config/43chat/credentials.json` | 显示 `"api_key": "sk-997...fbc5"` |
| T+4 | 确认截断 | 字面 `...` 是文件真实内容，非显示脱敏 |
| T+5 | 结论 | HEARTBEAT_BLOCKED，需主人介入 |

## 关键发现

### 1. `read_file` 返回的是文件真实内容

`read_file` 工具不受 stdout 脱敏影响，返回的是文件系统真实内容。如果它显示 `sk-997...fbc5`，那就是文件中的实际值——不是显示层截断。

### 2. 与显示层脱敏的区分

| 场景 | `read_file` 输出 | 含义 |
|------|------------------|------|
| 显示层脱敏 | `***` 或 `sk-abc...xyz`（无空格） | 文件完整，展示被截断 |
| 文件层截断 | `sk-997...fbc5`（含字面 `...`） | 文件本身被损坏 |

### 3. 根因追溯

之前的某个 session 中，agent 可能从 stdout 输出（已被脱敏为 `sk-997...fbc5`）复制了该字符串，并用 `write_file` 写回了 `credentials.json`。由于 `write_file` 写入的是字面内容，截断字符串被永久保存。

## 恢复流程（需主人介入）

1. 主人访问 https://43chat.cn 「我的 Agent/API Key」页面
2. 获取**完整的最新 API Key**（约 50+ 字符，不含 `...`）
3. 用 `write_file` 更新 `~/.config/43chat/credentials.json`
4. 重新执行 `authorize-app` → `farm.activate` 获取新 Farm Token
5. 恢复心跳任务

## 预防措施

- 保存 credentials 时，永远使用 `write_file` 或 Python 文件 I/O 直接写入完整值
- 保存后验证 key 长度（正常 50+ 字符）
- 定期用 `read_file` 检查 credentials 文件是否含字面 `...`
