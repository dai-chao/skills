# Session 2026-06-22: heartbeat.py 返回 HEARTBEAT_OK 但 Farm Token 已过期

## 现象

Cron 心跳任务执行器被触发后，按标准流程直接调用内置脚本：

```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

脚本输出：`HEARTBEAT_OK`，exit code: 0。

但 agent 继续按心跳执行器规范执行手动验证步骤时，发现 Farm Token 实际上已过期。

## 时间线

1. **读取状态文件**：`lastMessageCheck = 1782143010`，`lastVersionCheck = 1782139657`
2. **计算时间差**：当前时间 `1782143693`
   - 农场参与：683 秒（< 1800，未到期）
   - 版本检测：4036 秒（< 7200，未到期）
3. **直接调用脚本**：`python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` → `HEARTBEAT_OK`
4. **手动验证**（agent 按规范执行）：`curl -H "X-Farm-Token: ..." farm.status` → 401 `UNAUTHORIZED`
5. **尝试续签**：`auth.refreshToken` → 「旧 token 不合法或 43chat session 已失效」

## 关键发现

脚本返回 `HEARTBEAT_OK` 时，实际上：
- `farm.events.poll` 返回 401（Token 过期）
- 脚本尝试 `auth.refreshToken` 失败
- 脚本尝试重新激活，但 `authorize-app` 因 43chat API Key 问题也失败
- 脚本将"无事件"视为正常状态，输出 `HEARTBEAT_OK`

这是脚本静默失败的又一个变体——**Token 过期被脚本内部吞掉，对外呈现为正常状态**。

## 环境约束

- `execute_code` 被 BLOCKED（cron 模式）
- `python3 -c` 被 pending_approval 无限挂起
- 只能使用 `terminal` 的 `curl` 或 `python3 /path/to/file.py`
- `read_file` 读取 credentials.json 不受 stdout 脱敏影响

## 正确处置流程

1. 脚本返回 `HEARTBEAT_OK` 后，**不要立即结束**
2. 继续执行版本检测（如果到期）
3. 尝试手动调用 `farm.status` 验证 Token 有效性
4. 如果 `farm.status` 返回 401，进入 `43farm-cron-recovery` 的 Token 恢复流程
5. 如果恢复失败，输出 `HEARTBEAT_BLOCKED` 并报告主人
6. **不要仅凭脚本的 `HEARTBEAT_OK` 输出就结束心跳任务**

## 教训

- `HEARTBEAT_OK` ≠ 任务真正完成
- 脚本内部可能吞掉 Token 过期错误
- 心跳执行器必须配合手动验证或状态检查
- 在 cron 无人值守场景下，这种静默失败特别危险——主人永远不会知道 Token 已过期
