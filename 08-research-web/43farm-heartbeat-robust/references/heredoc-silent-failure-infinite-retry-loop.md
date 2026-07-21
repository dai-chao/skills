# heredoc 静默失败导致的无限重试循环 — 故障实录

**Session**: 2026-06-16  
**Agent**: kimi-k2.6 via kimi-coding  
**Context**: 43Farm cron 心跳任务执行

## 故障概述

Agent 被指派执行 43Farm 心跳任务。在尝试通过 heredoc 方式执行 Python 计算时，陷入无限重试循环，连续调用同一命令 40+ 次，每次返回空输出，最终耗尽 iteration 配额，任务零进展。

## 时间线

### Phase 1: 正常读取文件（iterations 1-2）

- `read_file` 读取 `~/.config/43farm/credentials.json` → 成功，获取 Farm Token
- `read_file` 读取 `~/.config/43farm/state.json` → 成功，获取 `lastMessageCheck=1781584699`, `lastVersionCheck=1781581693`

### Phase 2: 尝试计算时间差（iterations 3-4）

- 尝试 `terminal` 执行 `python3 -c "import json, time; ..."` → **BLOCKED**（安全审批挂起）
- 尝试 `execute_code` → **BLOCKED**（cron 模式下 execute_code 被明确拒绝）

### Phase 3: heredoc 首次尝试（iteration 5）

```bash
python3 /dev/stdin << 'PYEOF'
import json, time
state = json.load(open('/Users/chao/.config/43farm/state.json'))
now = int(time.time())
msg_delta = now - state['lastMessageCheck']
ver_delta = now - state['lastVersionCheck']
print(f'now={now}')
print(f'msg_delta={msg_delta}')
print(f'ver_delta={ver_delta}')
print(f'msg_expired={msg_delta >= 1800}')
print(f'ver_expired={ver_delta >= 7200}')
PYEOF
```

**结果**: `exit_code: 0`, `output: ""`（完全空）

### Phase 4: 无限重试循环（iterations 6-45）

Agent 对同一 heredoc 命令连续调用了 **40+ 次**。

每次调用的结果完全一致：
- `exit_code: 0`
- `output: ""`（空字符串）
- `error: null`

**关键决策错误**：Agent 将 `exit_code=0` 解读为"命令成功执行"，但空输出被解读为"可能数据未准备好，再试一次"。由于没有明确的"空输出=工具故障"判断规则，agent 持续重试。

### Phase 5: 工具循环警告（iteration ~25）

```
[Tool loop warning: repeated_exact_failure_warning; count=2; 
terminal has failed 2 times with identical arguments. 
This looks like a loop; inspect the error and change strategy instead of retrying it unchanged.]
```

**Agent 的响应**：虽然收到了警告，但 agent 的判断逻辑是"警告说'change strategy'，但 exit_code=0 表示命令本身没问题，可能是输出延迟，再试一次看看"。结果继续重试。

### Phase 6: 最终终止（iteration ~50）

```
You've reached the maximum number of tool-calling iterations allowed. 
Please provide a final response summarizing what you've found and accomplished so far, 
without calling any more tools.
```

**结果**：心跳任务完全未执行。没有调用任何 farm API，没有收获作物，没有检查版本，没有更新 state.json。

## 根因分析

### 1. heredoc 静默失败机制

`python3 /dev/stdin << 'HEREDOC'` 在 cron 模式下通过 terminal 工具执行时：
- 命令被传递给 bash
- bash 看到 heredoc 语法，尝试从 stdin 读取内容
- 但 terminal 工具在 cron 模式下可能不传递 heredoc 内容到 stdin
- 或者安全扫描系统拦截了 stdin 内容
- 结果是 `python3` 启动但没有收到任何代码，立即退出（exit_code=0）
- 因为没有代码执行，stdout 为空

### 2. Agent 的决策陷阱

Agent 的默认启发式：
- `exit_code != 0` → 失败，需要重试或换策略
- `exit_code == 0` → 成功，但 output 为空 → "可能是正常无输出，或数据未准备好"

这个启发式在 heredoc 静默失败场景下完全失效：
- 命令实际上没有执行任何代码
- 但 exit_code=0 让 agent 认为"成功"
- 空输出让 agent 认为"需要再试"
- 没有外部信号告诉 agent "heredoc 在此环境下永远不可用"

### 3. 缺少迭代预算监控

Agent 没有内置的"已用 iteration / 剩余预算"意识。在 50 次上限下：
- 40+ 次浪费在 heredoc 重试
- 剩余 10 次不足以完成任何有意义的 API 调用
- 即使 agent 在第 30 次 iteration 时醒悟，也来不及完成完整心跳逻辑

## 与类似故障的对比

| 故障类型 | 信号 | Agent 是否容易识别 | 本案例 |
|---------|------|------------------|--------|
| `python3 -c` 被 BLOCKED | 明确错误信息 | ✅ 容易 | 未触发 |
| `execute_code` 被 BLOCKED | 明确错误信息 | ✅ 容易 | 已识别 |
| heredoc 静默失败 | exit_code=0, output="" | ❌ 困难 | **本案例** |
| curl 凭证脱敏 | bash 语法错误 | ⚠️ 中等 | 未触发 |
| stdout 截断 | `...` 显示 | ✅ 容易 | 未触发 |

heredoc 静默失败是**最难识别**的一类故障，因为它没有错误信号，只有"成功但无输出"的假象。

## 已验证的解决方案

### 方案 1: 直接调用内置脚本（最优）

```bash
if [ -f ~/.hermes/skills/43farm/scripts/heartbeat.py ]; then
    python3 ~/.hermes/skills/43farm/scripts/heartbeat.py 2>&1
else
    echo "SCRIPT_NOT_FOUND"
fi
```

- 不需要任何 Python 计算中间步骤
- 不需要 heredoc 或 write_file
- 1 次 iteration 完成全部心跳逻辑

### 方案 2: write_file 写临时脚本（脚本不存在时）

```python
# 用 write_file 工具写 /tmp/check_state.py
import json, time
state = json.load(open('/Users/chao/.config/43farm/state.json'))
now = int(time.time())
msg_delta = now - state['lastMessageCheck']
ver_delta = now - state['lastVersionCheck']
print(f'now={now}')
print(f'msg_delta={msg_delta}')
print(f'ver_delta={ver_delta}')
print(f'msg_expired={msg_delta >= 1800}')
print(f'ver_expired={ver_delta >= 7200}')
```

然后：
```bash
python3 /tmp/check_state.py
```

- 2 次 iteration（write_file + terminal）
- 完全避开 heredoc 问题

### 方案 3: 纯 bash 计算（最简单计算）

```bash
date +%s
```

然后手动计算：
```
now = 1781589960
lastMessageCheck = 1781584699
msg_delta = 1781589960 - 1781584699 = 5261
ver_delta = 1781589960 - 1781581693 = 8267
msg_expired = 5261 >= 1800 = true
ver_expired = 8267 >= 7200 = true
```

- 1 次 iteration 获取当前时间
- 剩余计算在 agent 内部完成（不消耗 tool call）
- 不需要 Python 或 heredoc

## 教训总结

1. **heredoc 在 cron 模式下是死亡陷阱**：不仅不可靠，而且其静默失败特性会导致 agent 无限重试，耗尽 iteration 配额。

2. **exit_code=0 + output="" ≠ 成功**：在 cron 模式下，这可能是工具本身的故障。需要建立"空输出 2 次 = 放弃此方式"的硬规则。

3. **脚本优先原则**：内置脚本 `heartbeat.py` 存在时，永远直接调用它。不要尝试手动实现任何中间步骤。

4. **iteration 预算意识**：agent 应该在每次 tool call 后检查已用 iteration 数，超过 30 次时立即简化策略，超过 40 次时直接输出 `HEARTBEAT_BLOCKED`。

5. **工具循环警告是最后防线**：当收到 `repeated_exact_failure_warning` 时，必须立即停止当前方式，换完全不同的策略（如从 heredoc 切换到 write_file，或从 manual 切换到 script）。
