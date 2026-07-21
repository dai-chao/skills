# Session: 本地脚本成功执行但 Token 立即死亡，时间锁阻止恢复（2026-06-26）

## 场景

43Farm cron 心跳执行：
1. 本地 `~/.config/43farm/heartbeat_run.py` 成功执行（exit_code=0）
2. 所有 API 调用正常：`farm.status`、 `farm.events.poll`、 `farm.friends`、 `farm.view`、 `farm.steal`、 `farm.buyLand`
3. 脚本输出 "State updated"，更新了 `lastMessageCheck` 为当前时间
4. 脚本执行完毕后，立即尝试用临时脚本验证 `farm.status` → **401 Unauthorized**

## 时间线

- `T+0`: 本地脚本开始执行
- `T+30s`: 本地脚本完成，state.json 更新为 `lastMessageCheck: 1782436030`
- `T+35s`: 临时验证脚本调用 `farm.status` → 401
- `T+40s`: 运行官方 `heartbeat.py` → 因时间锁（距上次检查仅 37 秒 < 1800 秒）直接返回 `HEARTBEAT_OK`
- `T+45s`: 再次运行官方 `heartbeat.py` → 同样 `HEARTBEAT_OK`（时间锁仍未到期）
- `T+60s`: 手动 `auth.refreshToken` → 失败「旧 token 不合法或 43chat session 已失效」
- `T+90s`: 进入 43chat API Key 恢复流程 → 发现 Key 被截断为 `sk-cc0...dbe9`

## 关键发现

### 1. Token 在脚本执行期间有效，执行结束后立即失效

本地脚本内部的所有 API 调用都成功（包括最后的 `farm.buyLand`），说明 Token 在脚本执行期间是完全有效的。但脚本结束后仅 5 秒，同一 Token 就 401。

**可能原因**：
- 43chat 后端在脚本执行期间/结束后立即回收了 session
- 或者 Token 的 `exp` 时间戳恰好落在脚本执行结束前后
- 或者 43chat 对同一 Token 的并发使用有限制

### 2. 时间锁阻止了官方脚本的自动恢复

官方 `heartbeat.py` 内置了完整的 Token 恢复链路（`auth.refreshToken` → `authorize-app` → `farm.activate`）。但由于：
- 本地脚本更新了 `lastMessageCheck` 为当前时间
- 官方脚本检查：当前时间 - `lastMessageCheck` = 37 秒 < 1800 秒
- 官方脚本判定「农场参与不到期」，直接返回 `HEARTBEAT_OK`
- **完全跳过了 Token 恢复逻辑**

### 3. 手动恢复被 API Key 截断阻塞

当尝试手动恢复时：
- `auth.refreshToken` 失败（43chat session 已失效）
- 需要重新激活 → 需要 43chat API Key
- `~/.config/43chat/credentials.json` 中的 `api_key` 被截断为 `sk-cc0...dbe9`（含字面省略号）
- `~/.hermes/.env` 中的 `CHAT43_API_KEY` 也是字面 `***`
- 两个来源同时失效 → **终极硬阻塞**

## 教训

1. **本地脚本成功 ≠ Token 安全**：即使脚本内所有 API 调用成功，Token 仍可能在脚本结束后立即过期。这不应视为脚本 bug，而是后端行为。

2. **时间锁复合陷阱的再次验证**：本地脚本更新时间戳 → Token 立即死亡 → 官方脚本时间锁阻止恢复 → 手动恢复需要 API Key → API Key 也失效。这是一个**四层复合陷阱**。

3. **当本地脚本执行后 Token 401 时**：
   - 不要立即重新运行官方脚本（时间锁会阻止它）
   - 应该**等待 30 分钟**（`lastMessageCheck + 1800`）让时间锁到期
   - 或者**手动修改 state.json** 将 `lastMessageCheck` 回退到旧值（但 cron 模式下修改 dotfile 可能被安全扫描拦截）
   - 或者**直接进行手动 Token 恢复**（跳过官方脚本）

4. **API Key 验证应作为前置步骤**：在运行任何脚本之前，如果怀疑 Token 可能有问题，先验证 43chat API Key 的完整性。但这就违反了「第一动作永远是调用脚本」的原则...

5. **矛盾点**：
   - 技能说「第一动作永远是调用脚本，不要先手动验证」
   - 但本案例证明：脚本成功执行后 Token 仍可能立即死亡，且时间锁会阻止后续恢复
   - 这是一个**无法完全避免**的系统性风险，只能通过状态文件策略缓解（不更新失败项的时间戳）

## 状态文件策略的再确认

本地脚本**不应**在 API 调用成功后立即更新 `lastMessageCheck`。理想策略：
- 脚本执行完毕后，再次验证 Token 是否仍然有效（调一次 `farm.status`）
- 如果 Token 仍有效 → 更新 `lastMessageCheck`
- 如果 Token 已 401 → **不更新 `lastMessageCheck`**，让下次 cron 能立即触发恢复

但这会增加一次 API 调用和脚本复杂度。当前本地脚本 `heartbeat_run.py` 在末尾无条件更新 state.json，这是设计缺陷。
