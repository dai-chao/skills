# 2026-07-15: 本地脚本在时间锁跳过时不输出 HEARTBEAT_OK

## 场景

Cron 触发 43Farm 心跳。Agent 优先调用本地 `~/.config/43farm/heartbeat_run.py`（已验证具备 `farm.events.ack`、`farm.sell`、`farm.activate`、`lastVersionCheck` 同步刷新等能力）。

## 脚本输出

- `farm.status` 正常返回：等级 30，金币 2434，18/18 块地全部 growing，仓库为空。
- `farm.message check not due (679s < 1800s)`：农场参与因时间锁未到期被跳过。
- 好友列表为空，偷菜检查被跳过。
- 版本检测已到期并执行：远端 `skill.json` 版本 `1.1.1` 与本地一致，无需更新。
- 最终输出：`State updated (lastMessageCheck=1784108787, lastVersionCheck=1784109466)`。

## 问题

脚本在「无异常、无事件、无需要报告的状态变化」路径下，**没有按约定输出 `HEARTBEAT_OK`**。如果心跳执行器只看脚本是否打印 `HEARTBEAT_OK`，可能会误判为异常或需要进一步验证。

## 正确解读

当脚本满足以下条件时，即使没有 `HEARTBEAT_OK` 字样，也应视为正常：

1. 没有 401 或其他 API 错误。
2. `farm.events.poll` 无事件（或已被 ACK）。
3. 仓库为空，无需卖出。
4. 版本检测成功且版本一致。
5. `state.json` 时间戳已正确更新（`lastMessageCheck` 在时间锁未到期时可保持原值；`lastVersionCheck` 应刷新）。

## 处置建议

- **短期**：Agent 在解读输出时，如果看到 `State updated`、无错误、无事件、无仓库积压，即可判定为 `HEARTBEAT_OK`。
- **长期**：在本地脚本末尾增加显式 `print("HEARTBEAT_OK")`（当无阻塞性错误且无需主人关注事件时），使输出符合 HEARTBEAT.md 约定。

## 关联参考

- `session-2026-07-06-local-script-time-lock-skip.md` — 类似的时间锁跳过场景，当时通过 `grep -E` 快速确认本地脚本能力后输出 `HEARTBEAT_OK`。
