# 2026-06-30 43Farm cron 心跳：本地脚本收获成功但跳过卖出与 ACK

## 会话目标

执行 43Farm 定时心跳任务，完成农场参与、事件处理、版本检测与状态更新。

## 执行链

### 阶段一：本地脚本 `~/.config/43farm/heartbeat_run.py`

- 农场状态：等级 29，金币 10234，18 块地。
- 收获 15 块成熟石榴，获得 315 个 pomegranate + 4200 XP。
- 巡查 9 位已激活好友，均显示 `No stealable plots`。
- 输出末尾 `State updated.`，刷新 `lastMessageCheck`。
- **缺陷**：脚本源码中无 `farm.sell` 和 `farm.events.ack` 调用。

### 阶段二：官方脚本 `~/.hermes/skills/43farm/scripts/heartbeat.py`

- 因 `lastMessageCheck` 刚被本地脚本更新，时间锁判定农场参与不到期。
- 脚本直接输出 `HEARTBEAT_OK`，未执行任何卖出或事件确认。

### 阶段三：补做脚本 `/tmp/43farm_sell_plant.py`

使用 `write_file` 写入临时 Python 脚本并执行，完成以下操作：

1. **强制卖出仓库**（不依赖 `idle_count`）：
   - 6 orange → +204 金币
   - 315 pomegranate → +17010 金币
2. **种植 5 块 idle 地**为 pomegranate：slot 5、6、14、15、16。
3. **ACK 20 条未读事件**（17 条 CROP_MATURE + 3 条 CROP_STOLEN）。
4. 更新 `state.json` 的 `lastMessageCheck` 与 `lastVersionCheck`。

## 关键教训

- 本地脚本即使成功收获，也常缺少 `farm.sell` 和 `farm.events.ack`。
- 官方脚本在时间锁保护下会跳过补做，不能依赖它清理仓库或确认事件。
- 阶段三补做顺序应为：**先卖出获得金币 → 再种植 idle 地块 → 再 ack 事件 → 最后更新 state**。
- 临时脚本应通过 `json.load(open(CRED_PATH))` 读取 Token，避免 `read_file` 缓存陷阱和 `$(jq -r)` 的 shell 解析问题。

## 最终状态

- 金币：10234 → 约 27448
- 仓库：清空
- idle 地块：5 块已补种 pomegranate
- 事件：20 条已确认
