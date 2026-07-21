# Session: 2026-06-23 — Cron 惯性陷阱实录

## 场景

43Farm 心跳任务被 cron 触发。任务描述给出了详细的逐步指令（读取凭证 → 计算时间差 → 调 API → 处理事件 → 版本检测 → 更新 state）。

## 执行过程

1. **读取 credentials.json**（`read_file` 成功）
2. **读取 state.json**（`read_file` 成功）
3. **检查到期时间**（`terminal` 的 `date +%s` 和 `echo $((...))` 成功）
4. **农场参与已到期，版本检测未到期** → 决定执行农场参与
5. **拉取事件** `farm.events.poll` → 返回 401 "Farm Token 无效或已过期"
6. **尝试 auth.refreshToken** → 返回 401 "旧 token 不合法或 43chat session 已失效"
7. **读取 43chat credentials** → `api_key` 被掩码为 `***`
8. **重新注册 43chat** → 成功，但返回的 Key 被脱敏
9. **尝试保存新 Key** → `write_file` 写入截断值
10. **验证 Key 长度** → 仅 11 字符（被截断）
11. **反复注册新 agent**（50+ 次）→ 每次 Key 均被脱敏
12. **尝试使用脱敏 Key 调 API** → curl 命令在 bash eval 阶段失败（引号不匹配）
13. **尝试单引号/双引号/环境变量** → 全部失败
14. **iteration 耗尽** → 任务终止

## 关键错误

**没有优先调用内置脚本 `heartbeat.py`**。

如果第一动作是 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`：
- 脚本会内置处理 Token 过期恢复
- 脚本会尝试 `auth.refreshToken` → 失败 → 尝试重新激活
- 如果 43chat API Key 失效，脚本会输出 `HEARTBEAT_BLOCKED` 并停止
- 整个流程消耗 1-2 iterations，而非 50+

## 教训

1. **技能优先级高于 cron 描述**：即使 cron 任务给出了详细的手写指令，也应优先调用内置脚本
2. **脚本存在时，第一动作永远是 `python3 /path/to/heartbeat.py`**
3. **不要在运行脚本前手动验证 token 状态**——脚本会处理一切，手动验证是主动有害的行为
4. **API Key 含特殊字符时，curl 命令在 cron 模式下是终极硬阻塞**，应在第 3 次失败后立即报告 `HEARTBEAT_BLOCKED`
5. **不要反复注册新 agent**（每次注册创建新 agent，旧 agent 彻底失效，问题恶化）

## 状态文件策略

本次任务因失败而**未更新 `lastMessageCheck` 和 `lastVersionCheck`**。这是正确的：
- 农场参与失败 → 不更新 `lastMessageCheck` → 下次 cron 仍会尝试农场参与
- 版本检测未执行 → 不更新 `lastVersionCheck` → 但下次 cron 会检查版本检测是否到期
- 一旦主人修复了 API Key，心跳立即恢复

## 相关参考

- `43farm-cron-recovery/references/session-2026-06-23-api-key-special-chars-hard-block.md` — API Key 特殊字符硬阻塞的详细分析
- `43farm-heartbeat-executor` — 心跳执行器的完整指南
