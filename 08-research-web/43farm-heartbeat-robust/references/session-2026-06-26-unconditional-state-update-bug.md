# 本地脚本无条件更新 state.json 的时间戳陷阱（2026-06-26 会话实录）

## 问题描述

`~/.config/43farm/heartbeat_run.py` 在**所有 API 调用均失败（401 UNAUTHORIZED）时，仍无条件更新 `lastMessageCheck`** 为当前时间戳。

## 问题代码

```python
# heartbeat_run.py 末尾（第 96-100 行）
state = json.load(open(STATE_PATH))
state["lastMessageCheck"] = int(time.time())
with open(STATE_PATH, "w") as f:
    json.dump(state, f)
print("\nState updated.")
```

这段代码**没有任何条件判断**，无论前面的 API 调用成功还是失败，都会执行。

## 实际执行结果

```
=== farm.status ===
{"error": {"message": "Farm Token 无效或已过期...", "code": -32001}}

=== farm.events.poll ===
{"error": {"message": "Farm Token 无效或已过期...", "code": -32001}}

=== farm.friends ===
{"error": {"message": "Farm Token 无效或已过期...", "code": -32001}}

Idle plots: 0
Mature plots: 0
Withered plots: 0
Activated friends: 0

=== Steal results ===
Nothing stolen.

Current plots: 0, coins: 0
Trying to buy land...
{"error": {"message": "Farm Token 无效或已过期...", "code": -32001}}

State updated.  # ← 问题：全部失败仍更新
```

## 状态文件变化

**更新前**：
```json
{"lastMessageCheck": 1782431274, "lastVersionCheck": 1782423864}
```

**更新后**：
```json
{"lastMessageCheck": 1782432946, "lastVersionCheck": 1782423864}
```

- `lastMessageCheck` 从 1782431274 → 1782432946（增加了 1672 秒）
- `lastVersionCheck` 保持不变（脚本未处理版本检测）

## 后果分析

### 短期（下次 cron 触发）

假设 cron 每 5 分钟触发一次：
- 下次触发时间：1782432946 + 300 = 1782433246
- `now - lastMessageCheck` = 1782433246 - 1782432946 = 300 秒
- 300 < 1800（阈值）→ **农场参与被跳过**

### 中期（30 分钟内）

- 30 分钟内所有 cron 触发都会跳过农场参与
- 主人收不到任何告警
- 农场完全停滞（无收获、无偷菜、无种植）

### 长期（问题暴露）

- 30 分钟后 `lastMessageCheck` 再次到期，才会重新尝试 API 调用
- 再次调用仍返回 401（Token 未恢复）
- 如果脚本再次无条件更新，进入无限循环

## 正确实现

```python
# 正确：只在至少一个 API 调用成功时更新
any_success = False

status = curl_get("farm.status")
if "error" not in status:
    any_success = True
    plots = status.get("result", {}).get("data", {}).get("plots", [])
    # ... 处理状态 ...

events = curl_get("farm.events.poll")
if "error" not in events:
    any_success = True
    # ... 处理事件 ...

friends = curl_get("farm.friends")
if "error" not in friends:
    any_success = True
    # ... 处理好友 ...

if any_success:
    state["lastMessageCheck"] = int(time.time())
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)
    print("State updated (success).")
else:
    print("State NOT updated (all API calls failed).")
    print("HEARTBEAT_BLOCKED: Token expired, recovery needed.")
```

## Agent 侧的补救措施

当检测到脚本输出含 401 但 "State updated" 时：

1. **覆盖回滚 `lastMessageCheck`**：
```bash
# 将 lastMessageCheck 恢复为旧值（或更早的时间）
echo '{"lastMessageCheck": 1782431274, "lastVersionCheck": 1782423864}' > ~/.config/43farm/state.json
```

2. **确保下次 cron 触发时农场参与到期**：
- 如果旧值距现在 > 1800 秒，立即到期
- 如果旧值距现在 < 1800 秒，设置为 `now - 1801`（强制到期）

3. **输出 `HEARTBEAT_BLOCKED`**：
- 告知主人 Token 过期
- 提供恢复步骤（按 `43farm-cron-recovery` 技能）

## 教训

1. **状态更新是业务成功的副作用，不是脚本的副作用**
2. **脚本不应无条件更新状态文件**
3. **Agent 在脚本执行后必须检查输出内容**：exit_code=0 ≠ 业务成功
4. **401 是停止信号**：Farm Token 过期不会自行恢复，重复调用脚本无意义
5. **时间戳错误更新会掩盖问题**：主人延迟发现故障，农场停滞时间延长
