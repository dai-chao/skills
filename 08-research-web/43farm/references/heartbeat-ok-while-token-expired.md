# Heartbeat 返回 HEARTBEAT_OK 但 Token 已过期

## 现象

手动验证 Farm Token 时发现 401：

```json
{"error": {"message": "Farm Token 无效或已过期。按 INSTALL.md「日常自愈」段换个新 token 再继续。", "code": -32001}}
```

但执行 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` 却返回：

```
HEARTBEAT_OK
```

## 根因

`scripts/heartbeat.py` 的 `main()` 函数先检查时间间隔：

- 农场参与：`(now - lastMessageCheck) >= 1800` 秒
- 版本检测：`(now - lastVersionCheck) >= 7200` 秒

如果两个条件都不满足，脚本会直接输出 `HEARTBEAT_OK` 并退出，**不会调用 `farm.status` 来验证 Token 是否有效**。

因此，在 `state.json` 中的两个间隔都未到期时，即使 Farm Token 已经过期，脚本也会返回 OK。

## 影响

- 可能在 Token 过期后的一段时间内（最长 30 分钟），心跳任务无法主动检测到 Token 失效。
- 一旦某个间隔到期，脚本会正常进入 `ensure_valid_token()` 并尝试重新激活。
- 这不是脚本崩溃，而是当前行为设计：在非工作窗口期跳过所有 API 调用以节省开销。

## 排查建议

如果怀疑 Token 已过期但心跳返回 OK：

1. 读取 `~/.config/43farm/state.json`，查看 `lastMessageCheck` 和 `lastVersionCheck`。
2. 计算当前时间是否已超出对应阈值。
3. 若都未到期，脚本行为正常，可手动调用 `farm.status` 验证 Token。
4. 若需要立即恢复 Token，走 `cron-token-recovery.md` 或 `activate-farm-script-pattern.md` 中的重新激活流程。

## 是否修改脚本

将脚本改为“始终验证 Token”会改变现有语义：每次 cron 触发都会调用 `farm.status`，即使没有任何工作要做。这能提前发现 Token 过期，但会增加 API 负载。当前版本保持原行为，按需手动干预即可。
