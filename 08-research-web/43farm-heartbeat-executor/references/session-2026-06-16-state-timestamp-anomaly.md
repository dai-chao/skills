# 会话记录：状态文件时间戳异常导致静默跳过

**日期**：2026-06-16  
**场景**：43Farm cron 心跳任务触发，按规则检测时间戳是否到期  
**异常**：`state.json` 中两个时间戳完全相同且距当前时间仅 5 分钟，导致检测"不到期"而跳过所有 API 调用，但 Farm Token 实际上已过期

## 时间线

1. **首次读取 state.json**：`{"lastMessageCheck": 1781596613, "lastVersionCheck": 1781591778}`
   - 当前时间：1781599293
   - message_diff = 2680s (> 1800s，到期) ✓
   - version_diff = 7515s (> 7200s，到期) ✓
   - 两者均到期，需要执行完整心跳

2. **尝试调用 `farm.events.poll`** → 401 `Farm Token 无效或已过期`

3. **诊断 Token 恢复**（多次尝试 bash 命令、遭遇引号逃逸问题等）

4. **再次读取 state.json** → 发现值已变为 `{"lastMessageCheck": 1781599402, "lastVersionCheck": 1781599402}`
   - 两个时间戳**完全相同**（差值 0 秒）
   - 距当前时间（1781599710）仅 308 秒（约 5 分钟）
   - 按规则：message_diff=308 < 1800，version_diff=308 < 7200 → **两者均不到期**

5. **按规则输出 HEARTBEAT_OK** → 但 Farm Token 实际上已过期，无法调用任何 API

## 根因分析

### 时间戳为什么被更新了？

有几种可能：

1. **上一次运行无条件更新了时间戳**：即使 API 调用失败（401），某些实现会在脚本末尾或 `finally` 块中写入当前时间，导致"失败也被标记为成功"
2. **状态文件被重置**：可能有人工干预或脚本 bug 导致文件被重写为相同值
3. **脚本逻辑缺陷**：版本检测和农场参与共享同一个"更新时间戳"代码路径，无论哪个成功/失败都更新两者

### 为什么这是严重问题？

- **静默失败**：心跳输出 `HEARTBEAT_OK`，主人以为一切正常
- **问题被掩盖**：Token 过期的事实被隐藏，直到主人手动检查农场状态才发现
- **延迟暴露**：如果状态文件被更新为"5 分钟前"，下次 cron 触发时（假设 30 分钟后）差值将是 35 分钟，仍然 < 1800，继续跳过。问题可能被掩盖**数小时甚至数天**
- **无法自愈**：因为跳过 API 调用，agent 永远没有机会触发 Token 恢复流程

## 检测方法

在每次心跳执行前，检查以下异常信号：

```bash
# 读取当前时间和状态文件
NOW=$(date +%s)
STATE=$(cat ~/.config/43farm/state.json)
LAST_MSG=$(echo "$STATE" | grep -o '"lastMessageCheck":[0-9]*' | cut -d: -f2)
LAST_VER=$(echo "$STATE" | grep -o '"lastVersionCheck":[0-9]*' | cut -d: -f2)

# 检查 1：两个时间戳是否相同？
if [ "$LAST_MSG" -eq "$LAST_VER" ]; then
  echo "WARNING: timestamps are identical, possible unconditional update or reset"
fi

# 检查 2：距现在是否都小于 5 分钟？
MSG_DIFF=$((NOW - LAST_MSG))
VER_DIFF=$((NOW - LAST_VER))
if [ "$MSG_DIFF" -lt 300 ] && [ "$VER_DIFF" -lt 300 ]; then
  echo "WARNING: both checks were updated very recently, possible failed run"
fi

# 检查 3：时间戳是否大于当前时间？
if [ "$LAST_MSG" -gt "$NOW" ] || [ "$LAST_VER" -gt "$NOW" ]; then
  echo "ERROR: timestamp in future, clock drift or file corruption"
fi
```

## 正确处置

当检测到时间戳异常时：

1. **忽略时间戳，强制执行一次完整心跳**（调用 API 验证 Token 状态）
2. **如果 API 返回 401** → 进入 Token 恢复流程（不更新任何时间戳）
3. **如果 API 成功** → 正常执行后分别更新对应时间戳

**时间戳更新原则**：

| 场景 | lastMessageCheck | lastVersionCheck |
|------|------------------|------------------|
| 农场参与成功，版本检测成功 | 更新为当前时间 | 更新为当前时间 |
| 农场参与失败，版本检测成功 | **不更新** | 更新为当前时间 |
| 农场参与成功，版本检测失败 | 更新为当前时间 | **不更新** |
| 两者均失败 | **均不更新** | **均不更新** |
| 检测到时间戳异常（强制执行） | 按实际结果更新 | 按实际结果更新 |

## 教训

- **不要仅凭时间戳判断是否需要执行 API**：时间戳可能被错误更新
- **强制执行机制**：当检测到异常信号时，应绕过时间戳检查直接验证 Token
- **分离更新**：两个检查项的时间戳必须独立更新，不能共享同一个"成功/失败"状态
- **失败透明**：API 调用失败时，必须让主人知道，而不是通过更新时间戳来"假装成功"
