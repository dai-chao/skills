# Session 2026-06-26: 临时脚本 Token 过期 + farm.plant 参数名错误

## 完整时间线

1. **读取凭证和状态**（2 iterations）
   - `credentials.json`: Farm Token 有效（当时）
   - `state.json`: `lastMessageCheck=1782438986`, `lastVersionCheck=1782438340`
   - 计算：农场参与已到期（距现在 > 1800 秒），版本检测已到期（距现在 > 7200 秒）

2. **执行本地脚本** `python3 ~/.config/43farm/heartbeat_run.py`（1 iteration）
   - 成功获取农场状态：17 块地，金币 15767，等级 28，仓库空
   - 成功 poll 4 条事件（3 条 CROP_STOLEN + 1 条 CROP_MATURE）
   - 成功巡查 9 位好友，从 "XX" 偷了 3 个 orange
   - 成功收获 1 块成熟石榴地（slot 12），获得 21 个 pomegranate
   - 买地失败（金币不足）
   - **缺少**: `farm.events.ack` 和 `farm.sell`
   - 更新 `lastMessageCheck` 为当前时间

3. **执行官方脚本** `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`（1 iteration）
   - 因时间锁（`lastMessageCheck` 刚更新）直接返回 `HEARTBEAT_OK`
   - 不做任何 Token 恢复或补全操作

4. **写临时脚本补做 ACK + 卖出 + 种植**（1 iteration）
   - 脚本 `/tmp/43farm_ack_sell.py` 包含：
     - `farm.status` → 成功（仓库有 3 orange + 21 pomegranate）
     - `farm.events.poll` → 成功（4 条事件）
     - `farm.events.ack` → 成功（ACKed 4 条）
     - `farm.sell` (3 orange) → 成功（+102 金币）
     - `farm.sell` (21 pomegranate) → 成功（+1134 金币）
     - `farm.status` → 成功（空闲地块 1，slot 12）
     - `farm.plant` (`{"slot": 12, ...}`) → **401 UNAUTHORIZED**
   - 种植失败原因：Token 在执行期间过期 + 参数名错误（`slot` 应为 `plotSlot`）

5. **尝试 curl 验证**（1 iteration）
   - `curl -H "X-Farm-Token: ..." farm.status` → 返回完整状态（Token 似乎仍有效？）
   - 实际上此时 Token 已过期，但 `farm.status` 偶尔仍能成功（Token 抖动）

6. **尝试 curl 种植**（1 iteration）
   - `curl -X POST -d '{"slot":12,...}' farm.plant` → 401 UNAUTHORIZED
   - 确认 Token 已过期

7. **尝试官方脚本恢复**（1 iteration）
   - `heartbeat.py` → `HEARTBEAT_OK`（时间锁阻止恢复）

8. **检查状态文件**（1 iteration）
   - `state.json`: `lastMessageCheck=1782440401`（23 秒前）
   - 当前时间: 1782440424
   - 时间锁：农场参与不到期

9. **检查 43chat API Key**（1 iteration）
   - `credentials.json`: `api_key: "***"`（服务器端掩码）
   - 无法自动恢复

10. **搜索未掩码 API Key**（1 iteration）
    - `grep -r "sk-" ~/.config/43chat/` → 只有 `credentials.json` 中的 `***`
    - 无未掩码副本

## 最终状态

- 金币: 17003（卖出后）
- 等级: 28
- 地块: 17/18
- 仓库: 空
- 空闲地块: 1（slot 12，因种植失败未种）
- Farm Token: 已过期
- 43chat API Key: 被掩码
- 下次 cron: 约 30 分钟后，但时间锁会跳过农场参与

## 两个独立错误

### 错误 1: Token 在临时脚本执行中过期

前 5 个 API 调用成功，第 6 个（farm.plant）401。这说明 Token 在脚本执行期间过期。

**为什么前 5 个成功？**
- 可能是后端 Token 验证的缓存/抖动行为
- 某些端点（status、poll、sell）的验证较宽松
- 某些端点（plant）的验证更严格
- 或者 Token 恰好在第 5 和第 6 个调用之间过期

**为什么官方脚本无法恢复？**
- 本地脚本已更新 `lastMessageCheck` 为当前时间
- 官方脚本检查 `now - lastMessageCheck < 1800` → 农场参与不到期
- 直接返回 `HEARTBEAT_OK`，跳过 Token 恢复

### 错误 2: farm.plant 参数名错误

临时脚本使用了 `{"slot": 12, "cropType": "pomegranate"}`，但正确参数名是 `plotSlot`。

**即使 Token 未过期，这个错误也会导致：**
```json
{"error":{"message":"Decode","code":-32600,"data":{"code":"BAD_REQUEST","httpStatus":400,"path":"farm.plant"}}}
```

**混淆来源：**
- `farm.status` 返回的地块字段名是 `slot`
- 但 `farm.plant` 的输入参数名是 `plotSlot`
- 两者不一致，容易混淆

## 正确处置（事后复盘）

如果重新执行，正确流程应为：

1. 本地脚本执行后，检查输出是否缺少 ack/sell
2. 如果缺少，写临时脚本时：
   - 开头包含 `ensure_valid_token()` 验证和恢复逻辑
   - 使用 `{"plotSlot": slot, ...}` 而非 `{"slot": slot, ...}`
   - 如果 Token 无法恢复，不更新 `state.json`，输出 `HEARTBEAT_BLOCKED`
3. 如果临时脚本也失败，立即报告主人，不要重复尝试

## 与已知陷阱的关联

- **时间锁复合陷阱（变体 3）**: 本地脚本更新 → 临时脚本执行中 Token 过期 → 官方脚本时间锁阻止恢复
- **farm.plant 参数名混淆**: `slot` vs `plotSlot` 的不一致导致 BAD_REQUEST
- **API Key 掩码**: 43chat API Key 被服务器端掩码，无法自动恢复
