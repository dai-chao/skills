# 2026-07-17 43Farm cron 心跳 — 脚本优先自动恢复确认

## 场景

Cron 任务以完整手写心跳指令形式给出。Agent 先尝试读取凭证和手动 `curl` 调 `farm.events.poll`，得到：

```json
{"error":{"message":"Farm Token 无效或已过期...","code":-32001}}
```

随后加载 `43farm-heartbeat-executor` 技能，直接调用本地脚本：

```bash
python3 ~/.config/43farm/heartbeat_run.py
```

脚本成功运行，输出完整 `farm.status` 并以 `State updated (...)` 结尾，没有显式 `HEARTBEAT_OK`。

## 关键观察

1. **脚本内部自动处理了 Token 恢复**：同一份在 `curl` 中 401 的 Token，在脚本执行流程中被自动恢复，全部 API 调用成功。
2. **时间锁正常跳过农场参与**：`farm.message check not due (1376s < 1800s)`，这是预期行为。
3. **版本检测已执行并同步刷新 `lastVersionCheck`**：远端 `gameplayVersion: 1.1.1` 与本地一致，但脚本仍推进了 `lastVersionCheck` 时间戳。
4. **本地脚本能力完整**：`grep -E` 确认 `heartbeat_run.py` 已包含 `farm.events.ack`、`farm.sell`、`farm.activate`、`lastVersionCheck`。
5. **农场状态**：18/18 地 growing，仓库空，好友列表空，无事件需要处理。

## 结论

`State updated (lastMessageCheck=..., lastVersionCheck=...)` 在业务状态无异常时等同于 `HEARTBEAT_OK`。Agent 应直接报告结果，无需再次调用脚本或手动验证状态。本案例再次验证：即使手动 `curl` 先报 401，脚本优先路径仍是 cron 模式下最可靠、最省迭代的方式。
