# Session 2026-06-25: 本地脚本更新 time戳后 Token 立即过期

## 场景

Cron 心跳任务触发：
1. 本地 `~/.config/43farm/heartbeat_run.py` 执行成功
2. 脚本输出显示农场状态正常（17 块地全部 growing），仓库有 9 orange
3. 脚本执行了好友巡查和偷菜尝试（竞争失败，stolen: []）
4. 脚本输出 "State updated"，更新了 `lastMessageCheck`
5. 脚本执行结束后，Farm Token 立即过期

## 时间线

- `lastMessageCheck` 更新前：1782363526
- 本地脚本执行时间：约 1782363526-1782363530
- 脚本更新后 `lastMessageCheck`：1782363526（当前时间）
- 随后尝试 `farm.status` → 401 UNAUTHORIZED
- `auth.refreshToken` → 失败（旧 token 不合法）
- `authorize-app` → 成功（API Key 有效）
- `farm.activate` → 成功返回新 token
- 新 token `farm.status` → 401 UNAUTHORIZED（claim_url 未完成硬阻塞）

## 关键问题

本地脚本更新了 `lastMessageCheck` 后，官方 `heartbeat.py` 在随后调用时：
- 检查 `lastMessageCheck` → 距现在仅 8 分钟（< 1800 秒）
- 判定「农场参与不到期」
- 直接返回 `HEARTBEAT_OK`
- 完全跳过 Token 恢复逻辑

这意味着：
1. 如果只有官方脚本运行，Token 过期问题会被时间锁掩盖 30 分钟
2. 主人需要等待 30 分钟后才会再次收到 Token 过期告警
3. 在此期间，农场实际无法进行任何操作（收获、偷菜、卖出）

## 处置

当检测到 Token 过期且恢复失败（硬阻塞）时：
1. 立即报告 `HEARTBEAT_BLOCKED`，不要等待
2. 在报告中明确告知主人：
   - `claim_url` 需要手动完成（浏览器 + 手机号验证）
   - 即使 `lastMessageCheck` 已被更新，问题不会自行恢复
   - 下次 cron 将在约 30 分钟后再次尝试，但结果相同（硬阻塞）
3. 不更新 `lastVersionCheck`（如果版本检测已做则保留）

## 状态文件策略

| 场景 | lastMessageCheck | lastVersionCheck |
|------|------------------|------------------|
| 本地脚本已更新，Token 随后过期 | 已更新（本地脚本） | 视版本检测是否执行 |
| 硬阻塞（claim_url 未完成） | **保留当前值**（不重置） | **保留当前值** |

**不要**为了"让下次 cron 立即重试"而重置 `lastMessageCheck` 为旧值。这会导致 agent 主动篡改状态文件，可能引发更多问题。正确做法是：报告阻塞，让主人修复，下次 cron 自然重试。
