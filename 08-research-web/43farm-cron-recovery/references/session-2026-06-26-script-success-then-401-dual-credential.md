# Session: 本地脚本成功 + 补做 ack 后 Token 立即死亡，双凭证失效（2026-06-26）

## 场景

43Farm cron 心跳执行，本地脚本成功但缺少 `farm.events.ack`，临时补做脚本成功 ack 事件，但随后 Token 立即 401，43chat API Key 也失效（4010）。

## 完整恢复失败链

1. **本地脚本执行成功**（`~/.config/43farm/heartbeat_run.py`）
   - 所有 API 调用成功：`farm.status`、`farm.events.poll`、`farm.friends`、`farm.view`、`farm.buyLand`
   - 输出 "State updated"，更新 `lastMessageCheck` 和 `lastVersionCheck` 为 1782461114
   - exit_code=0

2. **发现本地脚本缺少 `farm.events.ack`**
   - 4 条事件已 poll 但未确认

3. **运行 `farm_now.py`** → 无事可做（无 idle 地块、无仓库）
   - `farm_now.py` 不处理事件 ack

4. **写临时补做脚本 `/tmp/43farm_ack_state.py`**
   - 包含：`ensure_valid_token()` → `farm.events.ack` → `farm.sell` → `farm.plant` → `farm.buyLand` → 更新 `state.json`
   - 执行成功：ack 4 条事件，买地失败，更新 state.json

5. **Token 验证 401**
   - 临时脚本执行完毕后，立即用 `curl` 验证 `farm.status` → **401 Unauthorized**
   - Token 在脚本执行期间有效，结束后立即死亡

6. **尝试 `auth.refreshToken`** → 失败："旧 token 不合法或 43chat session 已失效"

7. **尝试 `authorize-app` 恢复**
   - 读取 `~/.config/43chat/credentials.json`：`api_key` 为 `sk-cc0...dbe9`（含字面省略号）
   - `curl -H "Authorization: Bearer ..."` → **4010**："API Key 无效或已被重置"

8. **检查 `.env` 备用来源**
   - `~/.hermes/.env` 中的 `CHAT43_API_KEY` 也是字面 `***`（`xxd` 确认字节 `2a 2a 2a`）

9. **两个来源同时失效 → 终极硬阻塞**
   - 输出 `HEARTBEAT_BLOCKED`
   - 报告主人：需要重新获取 43chat API Key

## 恢复流程中的关键决策点

### 决策点 1：本地脚本执行后 Token 401，是否运行官方 `heartbeat.py`？

**答案：否**

官方 `heartbeat.py` 会因时间锁（`lastMessageCheck` 仅 57 秒前）直接返回 `HEARTBEAT_OK`，完全跳过 Token 恢复。

**正确做法**：立即加载本 skill（`43farm-cron-recovery`）进行手动恢复。

### 决策点 2：`auth.refreshToken` 失败后，是否立即尝试 `authorize-app`？

**答案：先验证 API Key 完整性**

在尝试 `authorize-app` 之前，先检查 `~/.config/43chat/credentials.json` 中的 `api_key` 是否完整：

```bash
key=$(jq -r '.api_key' ~/.config/43chat/credentials.json)
if echo "$key" | grep -q '\.\.'; then
  echo "API_KEY_TRUNCATED_HARD_BLOCK"
fi
```

- 如果 Key 含字面省略号 `...` → **硬阻塞**，不要尝试 `authorize-app`（必然 4010）
- 如果 Key 完整 → 继续 `authorize-app` → `farm.activate` 恢复链路

### 决策点 3：4010 是否一定是 Key 失效？

**答案：不一定**

4010 有两种根因：
1. **真正的 Key 失效**（服务器端已删除/重置）
2. **命令格式问题**（curl Header 值因 shell 引号问题损坏）

**区分方法**：
- 用变量方式重新调用：`API_KEY=$(jq -r '.api_key' ...)` + `curl -H "Authorization: Bearer $API_KEY"`
- 如果变量方式仍 4010 → 真正的 Key 失效
- 如果变量方式返回 `code: 0` → 之前的 4010 是误判

本 session 中，Key 本身已被截断（含 `...`），所以是真正的失效。

### 决策点 4：`.env` 文件是否可靠备用来源？

**答案：不一定**

`~/.hermes/.env` 中的 `CHAT43_API_KEY` 也可能是字面 `***`。必须用 `xxd` 验证原始字节：

```bash
grep -n 'CHAT43_API_KEY' ~/.hermes/.env | head -1 | xxd
```

- 十六进制列显示 `2a 2a 2a` → 字面星号，失效
- 十六进制列显示 `73 6b 2d ...` → 真实 Key，可用

本 session 中，`.env` 也是 `***`，与 `credentials.json` 同时失效。

## 状态文件策略（恢复失败时）

当恢复失败且状态文件已被更新时：

| 场景 | `lastMessageCheck` | `lastVersionCheck` | 下次 cron 行为 |
|------|-------------------|-------------------|----------------|
| 本地脚本已更新，Token 401，API Key 失效 | 已更新（1782461114） | 已更新（1782461114） | 约 30 分钟后重试，但问题不会自行恢复 |

**关键**：`lastMessageCheck` 已被更新，但 Token 已 401。下次 cron 触发时：
- 如果时间在 1800 秒内 → 官方脚本直接 `HEARTBEAT_OK`，跳过恢复
- 如果时间超过 1800 秒 → 官方脚本尝试恢复，但 API Key 仍失效 → 恢复失败

**主人修复后**：
- 主人获取新 API Key，更新 `credentials.json` 和 `.env`
- 下次 cron 触发时（无论时间锁是否到期），官方脚本会：
  - 如果时间锁到期 → 尝试农场参与 → 发现 Token 401 → 触发恢复 → `authorize-app` 成功 → `farm.activate` 成功 → 心跳恢复
  - 如果时间锁不到期 → 直接 `HEARTBEAT_OK`，但 Token 可能仍 401 → 需要等待下次 cron

**建议**：主人修复 API Key 后，手动运行一次 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`，强制触发完整恢复，不要等待 cron。

## 相关参考

- `43farm-heartbeat-executor/references/session-2026-06-26-script-success-then-401-dual-credential.md` — 同一 session 的心跳执行器视角
- `session-2026-06-26-local-script-success-token-immediately-dead.md` — 本地脚本成功但 Token 立即死亡的首次验证
- `session-2026-06-26-time-lock-compound-trap-full.md` — 时间锁复合陷阱的完整分析
- `session-2026-06-26-env-file-literal-asterisks-trap.md` — `.env` 文件中的 `***` 是字面星号
