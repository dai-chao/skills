# 2026-06-18 会话：43chat API Key 重置与 Farm Token 重新激活

## 背景

用户说"收菜偷菜"，但 `farm.status` 返回 401：`Farm Token 无效或已过期`。

进一步检查：`~/.config/43chat/credentials.json` 中的 `api_key` 已被服务器端掩码为 `***`（长度 3），导致 `authorize-app` 调用失败。

## 用户直接提供新 API Key

用户消息：
> 我在 43Chat 的 API Key 已被重置，请把它更新为：sk-668...7125
> 更新后用新 Key 继续工作，旧 Key 已失效。

## 执行流程

1. **更新 credentials.json**：
   - 使用 `write_file` 工具（或 `mcp_filesystem_write_file`）直接写入 `~/.config/43chat/credentials.json`
   - 格式：`{"api_key": "sk-668...7125", "claim_url": "..."}`
   - 注意：不要通过 `terminal` 工具用 `echo` 或 `cat` 写入——这些经过 shell 解析，可能触发脱敏或编码问题

2. **重新激活 Farm Token**：
   - 调用 `scripts/activate_farm.py`（或手动执行 activate 流程）
   - 流程：`authorize-app`（用新 API Key 获取 app_token）→ `farm.activate`（用 app_token 换 farmToken）→ `farm.status` 验证

3. **执行农场操作**：
   - `scripts/steal_now.py` — 偷菜
   - `scripts/farm_now.py` — 收菜+卖出+种植

## 关键教训

- **用户直接提供新 API Key 时，立即更新 credentials.json 并重新激活**
- **不要问用户"Token 过期怎么办"** — 用户已经给出解决方案（新 Key），直接执行
- **更新 credentials.json 优先使用 `write_file` 工具**，避免 shell 解析问题
- **激活后立即验证**（`farm.status`），确保新 Token 有效

## 脚本参考

- `scripts/activate_farm.py` — 自动完成重新激活全流程
- `scripts/steal_now.py` — 独立偷菜
- `scripts/farm_now.py` — 独立收菜+种植

这些脚本存放于 `~/.hermes/skills/43farm-heartbeat-robust/scripts/` 下。
