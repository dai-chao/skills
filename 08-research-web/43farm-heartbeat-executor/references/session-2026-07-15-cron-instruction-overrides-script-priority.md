# 2026-07-15: cron 手写心跳指令再次覆盖脚本优先原则

## 场景

Cron 触发 43Farm 心跳任务。任务描述以完整手动实现指令形式给出：

1. 读取 `~/.config/43farm/credentials.json` 获取 Farm Token
2. 读取 `~/.config/43farm/state.json`，用 bash 计算版本检测和农场参与是否到期
3. 如果农场参与到期，调 `farm.events.poll`、`farm.harvest`、`farm.steal` 等
4. 如果版本检测到期，下载远端 `skill.json` 比对并更新本地 skill 文件
5. 更新 `state.json` 时间戳

## 执行过程

Agent 没有优先调用内置 `heartbeat_run.py` / `heartbeat.py`，而是按 cron 描述逐步执行：

- 读取 `credentials.json` 和 `state.json` 成功。
- 手动 `curl` 调 `farm.events.poll` 返回 **401 UNAUTHORIZED**（Farm Token 已过期）。
- 进入 Token 恢复流程：
  - 验证 43chat API Key → 返回 **4010**（API Key 已失效）。
  - `authorize-app` → 同样返回 4010。
  - `claim_url` 需要手机号登录，无法自治完成。
- 最终输出 `HEARTBEAT_BLOCKED`，心跳任务零业务进展，消耗约 7 iterations。

## 事后分析

如果一开始就调用内置脚本 `python3 ~/.config/43farm/heartbeat_run.py` 或 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`，脚本会在 1 iteration 内完成同样的诊断：读取凭证、验证 Token、尝试恢复、报告阻塞。手动路径没有解决任何额外问题，只是延迟了结论并浪费了迭代预算。

## 核心教训

- **手写 cron 指令的惯性陷阱是反复出现的**。每次 cron 任务描述详细到列出具体 API 调用步骤时，agent 容易忘记技能优先原则。
- **无论 cron 指令多么详细，第一动作永远是 `python3 /path/to/heartbeat.py`**。技能优先级高于 cron 指令描述。
- **手动路径不能解决凭证链失效**。当 Farm Token 和 43chat API Key 同时失效时，任何手动 curl 调用都会得到同样的 401/4010，无法自治恢复。
- 正确顺序应该是：先调用脚本，只有在脚本不存在或脚本明确失败需要补做时，才进入手动实现 fallback。

## 关联参考

- `session-2026-07-14-cron-manual-execution-inertia.md` — 同一惯性陷阱的先前实例。
- `session-2026-06-16-cron-instruction-override-failure.md` — 早期 cron 指令覆盖脚本的完整记录。
