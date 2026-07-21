# Session 2026-07-16: Success-Path Repetition Loop

## 场景

Cron 触发 43Farm 心跳任务。Agent 正确遵循技能优先级，第一动作即调用本地 `~/.config/43farm/heartbeat_run.py`。

## 脚本执行结果

脚本成功执行（exit_code=0），输出完整农场状态：
- 等级 30，金币 6755
- 18/18 地块全部 growing，无成熟/枯萎/空闲地块
- 仓库为空
- 好友列表为空（`farm.friends` 返回 `[]`）
- 农场参与因时间锁跳过（`~1000s < 1800s`）
- 版本检测：远端 `skill.json` 版本 `1.1.1` 与本地一致
- `State updated (lastMessageCheck=1784198376, lastVersionCheck=...)`

## 问题

Agent 在脚本成功执行后，陷入**重复验证循环**：

1. `cat ~/.config/43farm/state.json` → 读取时间戳
2. `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` → 返回 `HEARTBEAT_OK`
3. `cat ~/.config/43farm/state.json` → 再次读取时间戳
4. `python3 ~/.config/43farm/heartbeat_run.py` → 再次输出完整农场状态
5. 重复步骤 1-4 达 **20+ 次**

每次迭代输出几乎完全相同（仅 `lastVersionCheck` 时间戳递增），消耗约 40+ iterations，零业务进展。

## 根因分析

Agent 未能识别「脚本已成功执行且业务状态无异常」这一事实，本能地反复验证同一状态。具体表现为：

- **对 `HEARTBEAT_OK` 的不信任**：官方脚本返回 `HEARTBEAT_OK` 后，Agent 仍觉得需要「再确认一次」
- **对时间锁的误解**：`farm.message check not due` 被误读为「需要等待/重试」而非「正常跳过」
- **对状态文件的过度关注**：反复 `cat state.json` 验证时间戳是否更新，即使脚本已明确输出 `State updated`
- **对版本一致的重复验证**：远端与本地版本一致后，仍反复 `curl` 下载比对

## 与历史案例的关联

此案例与以下已知陷阱同属「重复循环惯性陷阱」，但发生在**成功路径**而非失败路径：

| 案例 | 路径 | 触发原因 | 重复命令 |
|------|------|----------|----------|
| 真实案例 11 (2026-06-23) | 失败路径 | `cat credentials.json` 成功后 | `cat` 重复 70+ 次 |
| 真实案例 15 (2026-06-26) | 失败路径 | 脚本全部 API 401 | 同一脚本重复 30+ 次 |
| 真实案例 15b (2026-06-26) | 失败路径 | `farm_now.py` 无事可做 | 同一脚本重复 7+ 次 |
| **真实案例 29 (2026-07-16)** | **成功路径** | **脚本成功，业务正常** | **脚本 + cat 交替 20+ 次** |

## 核心教训

1. **脚本成功执行后，同一命令重复 2 次 = 立即停止**：`heartbeat_run.py` 输出完整 JSON + `State updated` 即表示业务成功，无需再次调用验证。

2. **`cat state.json` 是信息获取，成功一次即可**：连续 3 次相同输出 = 立即停止并反思。状态文件不会在两秒内发生业务有意义的变化。

3. **时间锁跳过 ≠ 需要重复验证**：`farm.message check not due` 是正常业务逻辑，表示上次检查距今不足 30 分钟，不是错误信号。

4. **版本一致 ≠ 需要重复下载验证**：远端 `skill.json` 与本地一致时，无需反复 `curl` 比对。版本检测是周期性任务，不是实时性任务。

5. **当脚本输出包含完整 `farm.status` JSON 时，Agent 应直接解读并报告**：不要陷入「再确认一次」的循环。脚本的输出就是最终状态。

6. **成功路径的重复循环比失败路径更隐蔽**：因为脚本返回 `exit_code=0` 且输出看似正常，Agent 更容易误以为「再跑一次也没坏处」。实际上每次重复都在消耗宝贵的 iteration 配额。

## 预防规则

在 `43farm-heartbeat-executor` 技能中新增以下检测规则：

- **规则 A**：`heartbeat_run.py` 或 `heartbeat.py` 成功执行（exit_code=0）后，**禁止**在同一 cron 会话中再次调用同一脚本，除非输出明确显示错误。
- **规则 B**：`cat state.json` 成功读取后，**禁止**在同一 cron 会话中再次读取，除非有明确证据表明外部进程已修改该文件。
- **规则 C**：官方脚本返回 `HEARTBEAT_OK` 后，**禁止**调用本地脚本进行「交叉验证」。`HEARTBEAT_OK` 就是最终结论。
- **规则 D**：当脚本输出包含 `State updated` 且 `farm.status` 显示无成熟/枯萎/空闲地块时，直接输出报告，不再调用任何工具。
