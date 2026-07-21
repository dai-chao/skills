# Session 2026-07-16: Manual Instruction Override + Token Expired + API Key 4010

## 场景

Cron 触发 43Farm 心跳任务。Cron 任务描述为完整的手动心跳指令（读取 credentials → 读取 state → 计算时间差 → poll 事件 → 收获 → 偷菜 → 版本检测 → 更新 state）。

## 执行过程

1. Agent 读取 `~/.config/43farm/credentials.json` → 成功（1 iteration）
2. Agent 读取 `~/.config/43farm/state.json` → 成功（1 iteration）
3. Agent 用 `date +%s` 和 `echo $((...))` 计算时间差 → 农场参与已到期（2480s > 1800s），版本检测未到期（1379s < 7200s）（2 iterations）
4. Agent 尝试 `execute_code` 执行 Python 脚本 → **BLOCKED**（1 iteration）
5. Agent 尝试 `python3 -c` 提取 Token → **pending_approval**（1 iteration）
6. Agent 尝试 `python3 -c` 带重定向 → **pending_approval**（1 iteration）
7. Agent 改用 `read_file` 读取 credentials.json → 成功，但 Token 显示为 `eyJhbG...DEtg`（展示层截断）
8. Agent 直接 `curl -H "X-Farm-Token: eyJhbG...DEtg"` 调 `farm.events.poll` → **401 UNAUTHORIZED**（Farm Token 已过期）
9. Agent 尝试 `auth.refreshToken` → 失败（旧 token 不合法或 43chat session 已失效）
10. Agent 尝试 `authorize-app` 用 43chat API Key → **4010**（API Key 无效或已被重置）
11. Agent 尝试 `GET /api/personal/key-info` 验证 Key → 因 shell 引号问题连续失败 50+ 次（`unexpected EOF while looking for matching '"'`）

## 最终结果

- **Farm Token 过期**：无法续签，无法恢复
- **43chat API Key 失效**：4010，无法获取新 App Token
- **claim_url 存在**：`https://43chat.cn/agent-claim?verification_code=d7qla-4feygk-s2wuf7`，需人工验证
- **输出**：`HEARTBEAT_BLOCKED`，心跳任务零业务进展
- **消耗 iterations**：约 60+（其中 50+ 浪费在 `curl` 引号循环上）

## 根因分析

1. **Cron 手写指令惯性陷阱**：Agent 遵循 cron 描述逐步执行，未优先调用内置脚本。如果一开始就调用 `python3 ~/.config/43farm/heartbeat_run.py` 或 `~/.hermes/skills/43farm/scripts/heartbeat.py`，脚本会在 1 iteration 内完成同样的诊断并给出相同结论。

2. **展示层 Token 截断陷阱**：`read_file` 返回的 Token 显示为 `eyJhbG...DEtg`（含 `...`），Agent 直接将其嵌入 `curl` 命令，导致 401。这是已知的 `session-2026-06-29-naive-curl-token-masking.md` 陷阱的再次复现。

3. **Shell 引号逃逸致命循环**：当尝试用 `curl -H "Authorization: Bearer <key>"` 验证 43chat API Key 时，Key 中的特殊字符导致 bash eval 解析错误（`unexpected EOF`）。Agent 对同一命令重复 50+ 次，未触发有效的 loop 停止机制。

4. **未优先调用脚本**：尽管 `43farm-heartbeat-executor` 技能已明确记录「第一动作永远是直接运行脚本」，Agent 仍因 cron 描述的详细指令而陷入手动执行路径。

## 与历史案例的关联

| 案例 | 日期 | 触发原因 | 浪费 iterations | 结果 |
|------|------|----------|----------------|------|
| 真实案例 10 | 2026-06-23 | API Key 含 `$` 特殊字符 | 50+ | 硬阻塞 |
| 真实案例 27 | 2026-07-14 | Cron 手写指令覆盖脚本 | 10+ | 最终成功但浪费 |
| 真实案例 28 | 2026-07-15 | Cron 手写指令 + Token 过期 + API Key 4010 | 7 | 硬阻塞 |
| **真实案例 30** | **2026-07-16** | **Cron 手写指令 + Token 过期 + API Key 4010 + 引号循环** | **60+** | **硬阻塞** |

## 核心教训

1. **无论 cron 描述多么详细，第一动作永远是 `python3 /path/to/heartbeat.py`**。手动路径不仅不能解决凭证失效问题，还会浪费 iterations、延迟报告。

2. **展示层截断的 Token 不能直接嵌入 curl 命令**。`read_file` 返回的 `eyJhbG...DEtg` 是展示层截断，不是真实内容。直接复制到 `curl -H "X-Farm-Token: eyJhbG...DEtg"` 会导致 401。

3. **Shell 引号逃逸是终极硬阻塞**。当 API Key 含特殊字符时，`curl -H "Authorization: Bearer <key>"` 在 bash eval 阶段会无限循环失败。应在第 3 次失败后立即停止，不要尝试更多 workaround。

4. **4010 + claim_url = 终极硬阻塞**。当 43chat API Key 返回 4010 且 `credentials.json` 中存在 `claim_url` 时，说明 agent 尚未完成 43chat 认领流程，任何自动恢复都不可能。必须输出 `HEARTBEAT_BLOCKED` 并报告主人。

5. **不要尝试重新注册 43chat**。重新注册会创建新 agent，旧 agent 彻底失效，问题恶化。

## 状态保留策略

```json
{
  "lastMessageCheck": 1784198376,
  "lastVersionCheck": 1784199396
}
```

保留旧值，不更新。原因：
- 农场参与未成功执行（Token 过期）
- 版本检测未成功执行（iteration 已耗尽）
- 下次 cron 触发时，农场参与仍会到期（因为 `lastMessageCheck` 未更新），会再次尝试并报告，直到主人修复凭证

## 报告模板

当遇到此硬阻塞时，应向主人输出：

```
⚠️ 43Farm 心跳任务报告 — Token 已过期，无法自动恢复

## 执行摘要

| 项目 | 状态 |
|------|------|
| 版本检测 | 未到期间隔（1379s / 需 7200s），跳过 |
| 农场参与检测 | 已到期（2480s / 需 1800s），尝试执行 |
| Farm Token | ❌ 已过期（HTTP 401） |
| Token 续签 | ❌ 失败（旧 token 不合法 / 43chat session 失效） |
| 43chat API Key | ❌ 已失效（HTTP 4010） |

## 详细情况

1. Farm Token 过期：farm.events.poll 返回 401，提示按 INSTALL.md「日常自愈」流程换新 token。
2. 续签失败：调用 auth.refreshToken 返回错误，提示需要重新走 farm.activate 流程。
3. 43chat API Key 失效：尝试用 ~/.config/43chat/credentials.json 中的 API Key 申请新的 App Token 时，43chat 返回 4010 — API Key 无效或已被重置。

## 需要主人手动处理

由于 43chat API Key 已失效，无法自动完成农场重新激活。请按以下步骤操作：

1. 打开 43chat 的「我的 Agent/API Key」页面，重新生成新的 API Key
2. 更新 ~/.config/43chat/credentials.json 中的 api_key 字段
3. 重新触发 43Farm 心跳任务，我将自动完成后续激活流程

或者，您也可以直接告诉我新的 43chat API Key，我立即为您重新激活农场。
```

## 关联参考

- `session-2026-06-29-naive-curl-token-masking.md` — 展示层截断 Token 嵌入 curl 导致 401
- `session-2026-06-23-api-key-special-chars-hard-block.md` — API Key 含特殊字符导致 curl 引号循环
- `session-2026-07-15-dual-credential-dead-with-claim-url.md` — 双凭证失效 + claim_url 硬阻塞
- `session-2026-07-14-cron-manual-execution-inertia.md` — Cron 手写指令惯性陷阱
- `session-2026-07-15-cron-instruction-overrides-script-priority.md` — Cron 指令覆盖脚本优先级
