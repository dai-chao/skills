# 工具调用迭代次数上限（iteration limit）

## 问题描述

Hermes 会话存在**最大工具调用迭代次数限制**。当 agent 在单个会话中调用工具（`terminal`、`read_file`、`skill_view` 等）超过阈值时，会话会被强制终止，agent 无法继续执行任何操作。

## 实测行为

- 阈值：约 50-60 次 tool-calling iterations（具体数值可能因配置而异）
- 触发时：系统提示 `You've reached the maximum number of tool-calling iterations allowed`
- 后果：agent 被迫立即输出总结，无法完成剩余任务步骤
- 在 cron 场景下：心跳任务被中断，农场可能错过收获/偷菜时机

## 在 43Farm 心跳任务中的影响

心跳任务涉及多个 API 调用步骤：
1. 读取 credentials.json / state.json（2 次）
2. 计算时间差、判断到期（1-2 次）
3. 拉取事件 poll（1 次）
4. 处理事件（收获、偷菜、买地等，每次 1-2 次）
5. 确认事件 ack（1 次）
6. 查看好友农场（N 次，每个好友 1-2 次）
7. 版本检测（1-2 次）
8. 更新 state.json（1 次）

如果 agent 在步骤中陷入困境（如反复重试失败的命令），很容易在 20-30 次迭代内耗尽配额，导致后续步骤无法执行。

## 已验证的浪费模式

以下行为会快速消耗 iteration 配额，在 cron 心跳中必须避免：

1. **反复重试同一命令**：对失败的 `curl` 命令重试 10+ 次，每次消耗 1 次 iteration
2. **分步执行简单计算**：用 `date +%s` 获取时间，再用 `echo` 计算差值，再用 `echo` 判断条件——3 次 iteration 完成 1 次决策
3. **逐条手写 API 调用**：每个 API 端点用单独的 `terminal` 调用，而不是批量脚本
4. **安全扫描失败循环**：命令触发 `pending_approval` 后反复重试，每次都被拒绝但仍消耗 iteration
5. **heredoc 静默失败循环**：`python3 /dev/stdin << 'EOF'` 返回空输出，agent 误以为命令未执行而重复调用

## 对策

1. **优先使用内置脚本**：`python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` 一次性完成全部逻辑，只消耗 1 次 `terminal` iteration
2. **批量操作**：将多个 API 调用写入一个 Python 脚本，通过 `write_file` + `python3 /tmp/script.py` 执行
3. **避免重复计算**：读取 state.json 后，在一个命令中完成所有时间差计算和条件判断
4. **失败即止损**：如果某个命令连续失败 2 次，立即停止重试，输出 `HEARTBEAT_BLOCKED` 并报告原因
5. **监控迭代使用**：如果已使用超过 30 次 iteration，立即简化剩余流程，优先完成收获和事件 ACK

## 教训

- **不要假设有无限迭代配额**：cron 心跳任务必须在有限步骤内完成
- **脚本优先于手写**：内置脚本是最节省 iteration 的方式
- **失败时立即报告**：`HEARTBEAT_BLOCKED` 比无限重试更负责任
- **heredoc 空输出 ≠ 未执行**：如果命令返回 exit_code 0 但 output 为空，可能是 heredoc 静默失败，不要重复调用
