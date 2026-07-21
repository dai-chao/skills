# Session 2026-06-26: 临时脚本执行中 Token 过期（Mid-Script Token Expiration）

## 场景

本地 `heartbeat_run.py` 成功执行（收获 1 块石榴、偷 3 个 orange、买地失败），更新了 `lastMessageCheck` 时间戳。但脚本缺少 `farm.events.ack` 和 `farm.sell`。

Agent 写临时脚本 `/tmp/43farm_ack_sell.py` 补做 ACK + 卖出 + 种植：
1. 脚本内 `http_get("farm.status")` → 成功，返回仓库有 3 orange + 21 pomegranate
2. `http_get("farm.events.poll")` → 成功，返回 4 条事件
3. `http_post("farm.events.ack", ...)` → 成功，ACKed 4 条事件
4. `http_post("farm.sell", ...)` → 成功，卖出 3 orange + 21 pomegranate，金币 15767 → 17003
5. `http_get("farm.status")` → 成功，返回空闲地块 1（slot 12）
6. `http_post("farm.plant", {"slot": 12, "cropType": "pomegranate"})` → **401 UNAUTHORIZED**

## 根因分析

Farm Token 在临时脚本执行期间**过期**。前 5 个 API 调用成功，第 6 个调用失败。这说明：
- 本地脚本执行时 Token 仍然有效（所有 API 调用成功）
- 但在临时脚本执行期间（约 5-10 秒后），Token 过期
- 这是「时间锁复合陷阱」的变体：Token 在两次脚本执行之间过期

## 额外错误：farm.plant 参数名错误

临时脚本使用了 `{"slot": 12, ...}` 而不是正确的 `{"plotSlot": 12, ...}`。即使 Token 未过期，这个参数名错误也会导致 `BAD_REQUEST`（Decode 错误）。

## 教训

1. **临时脚本必须包含 Token 验证/恢复逻辑**：
   - 本地脚本执行后 Token 可能立即过期
   - 临时脚本应在开头调用 `ensure_valid_token()` 验证 Token 有效性
   - 如果 Token 过期，尝试 `auth.refreshToken` → `farm.activate` 恢复
   - 如果恢复失败（如 43chat API Key 被掩码），立即输出 `HEARTBEAT_BLOCKED`

2. **farm.plant 的参数名必须是 `plotSlot`，不是 `slot`**：
   - 这是官方 `heartbeat.py` 使用的正确参数名
   - 临时脚本容易忘记此细节而写错
   - 错误参数名会导致 `BAD_REQUEST`（Decode 错误）

3. **复合陷阱的连锁反应**：
   - 本地脚本缺少 ack/sell → 需要临时脚本补做
   - 临时脚本执行中 Token 过期 → 种植失败
   - 官方 `heartbeat.py` 因时间锁直接返回 `HEARTBEAT_OK` → 不做任何恢复
   - 43chat API Key 被掩码 → 无法手动恢复
   - 最终状态：农场有 1 块空闲地未种植，但下次 cron 30 分钟内不会尝试恢复

## 正确处置流程

当本地脚本执行后需要补做 ACK/sell/plant 时：

1. 写临时脚本时，**开头先验证 Token**：
   ```python
   token = ensure_valid_token()
   if not token:
       print("HEARTBEAT_BLOCKED: Token 无法恢复")
       exit(1)
   ```

2. 使用正确的 API 参数名：
   - `farm.plant`: `{"plotSlot": slot, "cropType": "..."}`
   - `farm.sell`: `{"cropType": "...", "quantity": N}` 或 `{}` 清仓
   - `farm.events.ack`: `{"eventIds": [...]}`

3. 如果 Token 在脚本执行中过期，脚本应：
   - 捕获 401 错误
   - 尝试重新激活（`authorize-app` → `farm.activate`）
   - 如果激活失败，不更新 `state.json`，输出 `HEARTBEAT_BLOCKED`

## 与「时间锁复合陷阱」的关系

这是「时间锁复合陷阱」的**变体 3**（此前已有变体 1 和变体 2）：

| 变体 | 触发条件 | 结果 |
|------|---------|------|
| 变体 1 | 本地脚本更新 `lastMessageCheck` 后 Token 立即过期 | 官方脚本时间锁阻止恢复 |
| 变体 2 | 本地脚本缺少 sell/ack，官方脚本因时间锁跳过 | 仓库积压/事件未确认 |
| **变体 3** | **临时脚本执行中 Token 过期** | **补做操作未完成，种植失败** |

变体 3 的额外复杂性：临时脚本不像官方脚本那样内置 Token 恢复，需要显式处理。
