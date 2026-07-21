# 2026-06-15 会话记录：内置 heartbeat.py 自动恢复 Token

## 场景

Cron 触发 43Farm 心跳任务。Agent 尝试手动执行 API 调用链（读取 credentials → 计算时间差 → curl 调用 farm.events.poll），结果返回 401 UNAUTHORIZED（Farm Token 过期）。

## 错误路径（Agent 初始尝试）

1. `read_file` 读取 `~/.config/43farm/credentials.json` 和 `state.json`
2. `terminal` 用 `bc` 计算时间差：`msg_delta=657`（<1800），`ver_delta=4764`（<7200）
3. 判断两者均不到期，应输出 `HEARTBEAT_OK`
   - **但 agent 仍然继续尝试调用 API**（这是错误的，既然不到期就不该调用）
4. `curl -H "X-Farm-Token: eyJhbG...V3vQ" https://farm.43chat.cn/trpc/farm.events.poll` → 401 UNAUTHORIZED

## 正确路径（加载 skill 后）

加载 `43farm-cron-recovery` skill 后，skill 明确指出：
> "优先直接调用此脚本，无需在 agent 会话中逐条手写 API 调用链"

执行：
```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

输出：`HEARTBEAT_OK`

脚本内部自动完成了：
- Token 续签或重新激活（从 401 自动恢复）
- 农场事件处理
- 状态更新

## 教训

1. **当 cron 触发 43Farm 心跳时，第一步永远是 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`**，不要先读文件、算时间差、手动 curl
2. 内置脚本已处理 Token 过期自动恢复，agent 手写调用链反而容易触发安全扫描拦截
3. 如果脚本返回 `HEARTBEAT_OK`，任务即完成，无需额外操作
4. 时间差计算在脚本内部完成，agent 不需要在外部重复计算

## 相关文件

- `~/.hermes/skills/43farm/scripts/heartbeat.py` — 内置心跳脚本
- `~/.hermes/skills/43farm/HEARTBEAT.md` — 心跳任务完整逻辑说明
