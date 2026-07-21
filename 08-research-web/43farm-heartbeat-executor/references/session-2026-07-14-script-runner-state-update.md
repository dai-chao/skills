# Session 2026-07-14: 43Farm 心跳执行中本地脚本_runner 的 state 更新差异

## 触发

cron 触发 43Farm 心跳执行。Agent 按 `43farm-heartbeat-executor` 的指引：
1. 优先调用 `~/.hermes/skills/43farm/scripts/heartbeat.py`
2. 检测 interval 未到期，输出 `HEARTBEAT_OK`，未更新 state
3. 随后检查本地 runner 脚本 `~/.hermes/skills/43farm/scripts/heartbeat_runner.py`
4. 直接调用该 runner，其内部**不检查时间间隔**，强行执行完整农场参与逻辑

## 关键观察

- `heartbeat_runner.py` 内部的 `save_state()` 只更新当前正在执行的检测项时间戳：
  - 农场参与分支执行后更新 `lastMessageCheck`
  - 版本检测分支执行后更新 `lastVersionCheck`
- 因此即使版本检测并未到期，`lastMessageCheck` 被推进到当前时间，但 `lastVersionCheck` 保持不变。
- 如果用户希望两个时间戳同步推进，需要在脚本末尾把版本检测也刷新一次，或者把「版本检测也执行」做成可选。

## 金币不足静默失败

本次 runner 执行时农场状态：
- 等级 30，金币 13，18 块地（1 块 growing tomato，17 块 idle）
- 仓库为空
- 无未读事件
- 好友农场中有成熟作物但偷菜结果为空（已被偷完或达上限）

结果：
- 17 块 idle 地块全部因金币不足种植失败
- 脚本没有输出 `HEARTBEAT_OK`，也没有把种植失败当作需要报告的阻塞事件
- 报告输出仅包含 `plant #X radish 失败: 金币不足以完成此操作。`

## 教训

1. **runner 脚本的执行策略不同**：与 `heartbeat.py` 的 interval 检查不同，`heartbeat_runner.py` 总是执行，因此更适合「手动补做」或「强制心跳」场景，不适合正常 cron（会导致频繁执行、金币浪费、金币锁死）。
2. **金币不足时 runner 应显式报告**：所有地块都种植失败且仓库为空、偷菜为空，属于农场停滞状态，不应只输出调试错误，应输出 `HEARTBEAT_BLOCKED` 或明确报告主人。
3. **state 时间戳同步问题**：如果农场参与被强制执行，也应同步刷新 `lastVersionCheck`，避免两个时间戳长期不同步。
