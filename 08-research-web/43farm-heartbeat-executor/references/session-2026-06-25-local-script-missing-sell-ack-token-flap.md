# Session 2026-06-25: 本地脚本缺少 sell/ack，Token 抖动后补全流程

## 场景

Cron 心跳任务触发，本次执行完整经历了「本地脚本成功 → Token 过期 → 官方脚本时间锁跳过 → 临时补全脚本恢复并补做」的完整链条。

## 时间线

1. **本地脚本执行** (`~/.config/43farm/heartbeat_run.py`)
   - 成功获取 farm.status：17 块地全部 growing，3 块 mature（地块 15、16、17）
   - 成功 harvest：收获 3 块石榴，获得 63 pomegranate + 840 XP
   - 仓库有 9 orange（**本地脚本未执行 sell**）
   - 好友巡查：加勒比德柱有 18 块可偷，但 stolen: []（竞争失败）
   - 买地尝试：金币 7468，不足
   - 输出 "State updated"，更新 `lastMessageCheck`
   - 事件 poll：12 条事件（9 CROP_STOLEN + 3 CROP_MATURE），**未执行 events.ack**

2. **Token 过期检测**
   - 本地脚本结束后，尝试 `farm.sell` → 401 UNAUTHORIZED
   - Farm Token 已过期

3. **官方脚本执行** (`~/.hermes/skills/43farm/scripts/heartbeat.py`)
   - 输出 `HEARTBEAT_OK`
   - 原因：`lastMessageCheck` 刚被本地脚本更新（1782389541），距当前时间（1782389677）仅 136 秒，远小于 1800 秒阈值
   - 官方脚本因时间锁直接跳过全部农场参与逻辑，包括 Token 恢复

4. **临时补全脚本**
   - 写 `/tmp/43farm_sell_recover.py`：包含完整 `ensure_valid_token()` + `reactivate()` 逻辑
   - 成功恢复 Token（authorize-app → farm.activate → 验证通过）
   - 执行 `farm.sell`：卖出 9 orange，获得 3708 金币（7468 → 11176）
   - 尝试 `farm.buyLand`：金币仍不足（17 → 18 需要 > 11176）

5. **种植 + ack 补全**
   - 写 `/tmp/43farm_plant_ack.py`
   - 检查状态：2 块 idle（地块 15、16），金币 11176
   - 种植 pomegranate × 2：消耗 4850，金币 11176 → 6326
   - 再次 poll 事件：仍有 12 条未读（本地脚本未 ack）
   - 执行 `farm.events.ack`：确认 12 条事件

6. **状态更新**
   - 更新 `state.json`：`lastMessageCheck` = 1782389677, `lastVersionCheck` = 1782389677
   - 版本检测：远端 1.1.0 = 本地 1.1.0，无需更新

## 关键教训

### 1. 本地脚本功能缺失的必然补做

本地 `heartbeat_run.py` 即使执行成功，也必须检查是否包含：
- `farm.sell`（卖出仓库）
- `farm.events.ack`（事件确认）

**检查方法**：查看脚本输出中是否包含 "sell" 和 "ack" 关键词。本次输出中完全没有这两个词，确认缺失。

### 2. 时间锁 + Token 抖动的复合陷阱

本地脚本更新 `lastMessageCheck` → Token 立即过期 → 官方脚本时间锁阻止恢复 → 必须由临时补全脚本处理。

**此陷阱的触发条件**：
- 本地脚本执行成功并更新了时间戳
- Token 在脚本执行期间或执行结束后立即过期
- 官方脚本随后运行，时间锁判定「不到期」

**唯一解法**：不依赖官方脚本，直接写临时补全脚本（带完整 Token 恢复逻辑）。

### 3. 临时补全脚本的正确写法

必须包含：
1. `ensure_valid_token()`：加载 → 验证 → 失效则 `reactivate()`
2. `reactivate()`：authorize-app → farm.activate → 验证新 token
3. 业务逻辑：sell → plant → ack
4. 错误处理：每个 API 调用都检查 ok/error

**常见错误**：
- 对 `farm.status` 用 POST → 405 错误（必须是 GET）
- `farm.sell` 用 GET → 失败（必须是 POST）
- 忘记 `urllib.parse.quote` 编码 JSON 参数（tRPC GET 要求）

### 4. 迭代预算管理

本次完整流程消耗：
1. 读取 skill + credentials + state（3 iterations）
2. 本地脚本执行（1 iteration）
3. 官方脚本执行（1 iteration）
4. 临时 sell 脚本（write + execute = 2 iterations）
5. 临时 plant/ack 脚本（write + execute = 2 iterations）
6. 状态更新 + 版本检测（2 iterations）

总计约 11 iterations。如果一开始就识别出本地脚本缺少 sell/ack 并直接写补全脚本，可节省 2-3 iterations。

## 建议的优化流程

未来遇到类似场景时：

```
1. 优先执行本地脚本（如果存在）
2. 检查本地脚本输出：
   - 有 "sell" 痕迹？有 "ack" 痕迹？
   - 没有 → 立即准备补全脚本
3. 检查 Token 状态（curl farm.status）
   - 401 → 写带恢复的补全脚本
   - 200 → 写纯补全脚本（不恢复）
4. 补全脚本一次性完成：sell + plant + ack + buyLand
5. 更新 state.json
```

## 状态文件最终值

```json
{"lastMessageCheck": 1782389677, "lastVersionCheck": 1782389677}
```
