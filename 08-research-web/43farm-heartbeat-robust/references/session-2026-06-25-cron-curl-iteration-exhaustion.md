# Session Reference: cron 心跳执行器逐条 curl 导致迭代耗尽（2026-06-25）

## 背景

Cron 心跳执行器被触发时，agent 尝试按用户指令逐条执行 API 调用（而非调用内置脚本），导致迭代耗尽、任务失败。

## 事件时间线

1. `read_file` 读取 `~/.config/43farm/credentials.json` → 获取 Farm Token（成功）
2. `read_file` 读取 `~/.config/43farm/state.json` → 获取状态（成功）
3. `date +%s` → 获取当前时间（成功）
4. `echo $((now - last))` → 计算时间差（成功）
5. `curl -H "X-Farm-Token: ..." "farm.events.poll"` → **成功**，返回 8 个事件（6 个 CROP_STOLEN + 2 个 CROP_MATURE）
6. `curl -X POST ... farm.harvest` → **401 UNAUTHORIZED**
7. 重试 `farm.harvest` → 仍 401
8. 重试 → 仍 401
9. ...连续重试 40+ 次...
10. 最终耗尽 iteration 上限，任务被强制终止

## 关键发现

- `farm.events.poll`（GET）成功，但 `farm.harvest`（POST）401
- 这不是 Token 过期（poll 能成功），而是 POST 调用的认证上下文问题
- 连续 40+ 次重试消耗了 40+ 个 iteration，加上前期步骤，总迭代数超过 50-60 上限

## 正确做法（事后复盘）

在步骤 5 之后，应立即：

```bash
# 直接调用官方脚本，1 次 iteration 完成全部逻辑
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

或如果脚本不可用：

```bash
# write_file 写完整脚本到 /tmp/heartbeat.py
# terminal 执行 python3 /tmp/heartbeat.py
```

## 核心教训

- **cron 心跳执行器不是交互式诊断工具**。它的职责是触发脚本并报告结果，不是手动执行每个 API 调用。
- **永远不要逐条手写 curl 调用 API**。任何逐条 curl 的尝试都是反模式，会导致迭代耗尽和任务失败。
- **失败 2 次即止损**。同一命令失败 2 次应立即停止，改用脚本或输出 `HEARTBEAT_BLOCKED`。
- **迭代预算意识**。超过 30 次 iteration 时简化流程，优先完成收获和事件 ACK。
