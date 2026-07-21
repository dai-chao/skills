# 2026-07-06: 本地脚本因时间锁跳过农场参与时的能力校验

## 场景

Cron 触发 43Farm 心跳。优先调用本地 `~/.config/43farm/heartbeat_run.py`。

## 输出

脚本输出：

- `farm.status` 正常，显示 18 块地全部 growing、仓库为空、等级 29、金币 99。
- `farm.message check not due (693s < 1800s)`：时间锁阻止农场参与。
- `farm.friends` 返回空数组。
- 所有收获/卖出/偷菜/买地检查均被跳过。
- 版本检测未显式输出（时间锁未到期时版本检查逻辑仍执行，但输出未显示具体比对结果）。
- 最终：`State updated (lastMessageCheck=1783317648, lastVersionCheck=1783318342)`。

## 关键判断

当农场参与被跳过时，输出中没有 `farm.events.ack`、`farm.sell`、`farm.harvest` 等痕迹，无法仅凭输出判断本地脚本是否具备这些能力。

直接用 grep 检查源码确认能力：

```bash
grep -E "farm\.events\.ack|farm\.sell|farm\.activate|lastVersionCheck" ~/.config/43farm/heartbeat_run.py
```

结果：
- `farm.events.ack` 命中
- `farm.sell` 命中
- `farm.activate` 命中
- `lastVersionCheck` 命中

结论：本地脚本已具备事件确认、仓库清仓、Token 自动恢复和版本检测同步刷新能力，无需补做。

## 后续验证

脚本退出后，用 `curl` 验证 `farm.status` 返回 200，Token 仍然有效，无 401 抖动。

## 教训

- 时间锁跳过时，不能仅凭脚本输出判断功能完整性。
- 用 `grep -E` 扫描脚本源码是快速确认本地脚本能力的可靠方式，不消耗迭代预算。
- 当源码已包含全部关键能力且 `warehouse` 为空、无事件痕迹时，可直接输出 `HEARTBEAT_OK`。
