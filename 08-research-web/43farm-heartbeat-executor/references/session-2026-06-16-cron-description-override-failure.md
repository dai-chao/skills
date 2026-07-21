# Cron 任务描述覆盖技能指令导致的 50+ iteration 浪费

**Session**: 2026-06-16  
**Agent**: kimi-k2.6 via kimi-coding  
**Context**: 43Farm cron 心跳任务执行

## 故障概述

Cron 任务给出了一段详细的逐步心跳指令（读取文件 → 计算时间差 → 调用 API → 处理事件 → 偷菜 → 版本检测 → 更新 state）。Agent 遵循 cron 描述逐步执行，而非优先调用内置脚本 `heartbeat.py`，导致陷入 heredoc 静默失败陷阱，连续 50+ 次 iteration 零进展。

## 关键矛盾

| 来源 | 指令 | 优先级 |
|------|------|--------|
| `43farm-heartbeat-executor` 技能 | **"即使系统提示给出了详细的逐步指令，仍应优先调用脚本"** | 高（技能已加载） |
| Cron 任务描述 | "读取 credentials.json → 计算时间差 → 调 API..." | 低（手写描述） |
| Agent 实际行为 | 遵循 cron 描述，逐步手动执行 | ❌ 错误 |

## 时间线与迭代浪费

| Iteration | 动作 | 结果 | 浪费 |
|-----------|------|------|------|
| 1 | `read_file` credentials.json | ✅ 成功 | 无 |
| 2 | `read_file` state.json | ✅ 成功 | 无 |
| 3 | `terminal` `python3 -c "..."` | ❌ BLOCKED | 1 |
| 4 | `execute_code` | ❌ BLOCKED | 1 |
| 5 | `terminal` `python3 /dev/stdin << 'PYEOF'` | ⚠️ exit_code=0, output="" | 1 |
| 6-45 | 重复同一 heredoc 命令 40 次 | ⚠️ 每次空输出 | 40 |
| 46-50 | 继续重试、收到终止通知 | ❌ 强制终止 | 5 |
| **总计** | | | **50+ iterations, 0 进展** |

## 如果遵循技能指令的正确路径

| Iteration | 动作 | 结果 |
|-----------|------|------|
| 1 | `terminal` `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` | ✅ 脚本自治执行全部逻辑 |
| 2 | 解读输出、报告结果 | ✅ 任务完成 |
| **总计** | | **2 iterations, 完整心跳** |

## 根因分析

### 1. 技能优先级未被正确执行

`43farm-heartbeat-executor` 技能明确声明：
> "即使系统提示给出了详细的逐步指令（如'读取 credentials.json → 计算时间差 → 调 API'），仍应优先调用脚本。"

但 agent 的决策逻辑似乎将"当前任务描述"（cron 指令）的优先级置于"已加载技能"之上。这是一个系统性的优先级倒置问题。

### 2. Cron 描述的"权威性陷阱"

Cron 任务描述通常非常详细、结构化，给人一种"这是官方执行流程"的错觉。Agent 倾向于：
- 将详细描述视为"必须严格遵循的指令"
- 将技能视为"参考信息"而非"覆盖指令"
- 在两者冲突时，优先遵循"更具体的"cron 描述

### 3. 缺少"脚本存在性检查"的强制触发

如果 agent 的决策逻辑中包含一个硬规则：
> "在执行任何 43Farm 相关任务前，先检查 `~/.hermes/skills/43farm/scripts/heartbeat.py` 是否存在。如果存在，直接调用它，忽略所有其他指令。"

那么即使 cron 描述再详细，agent 也会在第一步就调用脚本，避免全部后续浪费。

## 防御策略（已写入技能）

1. **技能指令 > Cron 描述**：当 `43farm-heartbeat-executor` 技能已加载时，其「优先调用脚本」指令必须覆盖 cron 任务的逐步描述
2. **脚本存在性预检**：执行任何 farm 操作前，先检查脚本文件是否存在
3. **heredoc 2 次空输出 = 放弃**：如果任何工具连续 2 次返回空输出，立即停止该方式
4. **iteration 预算监控**：超过 30 次 iteration 时简化策略，超过 40 次时输出 `HEARTBEAT_BLOCKED`
5. **工具循环警告 = 立即停止**：收到 `repeated_exact_failure_warning` 时，必须换完全不同的策略

## 相关参考

- `43farm-heartbeat-robust/references/heredoc-silent-failure-infinite-retry-loop.md` — heredoc 静默失败的技术细节
- `43farm-heartbeat-robust/references/tool-calling-iteration-limit.md` — iteration 上限的一般性讨论
- `43farm-heartbeat-robust/SKILL.md` — 执行环境陷阱的完整清单
