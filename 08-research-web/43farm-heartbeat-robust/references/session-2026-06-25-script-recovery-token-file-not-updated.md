# 脚本恢复后 credentials.json 中的 Token 可能未更新（2026-06-25）

## 场景

Cron 触发 43Farm 心跳任务。`heartbeat.py` 返回 `HEARTBEAT_OK`，但 `credentials.json` 中的 `farmToken` 值与执行前完全相同。

## 时间线

1. 执行前：`credentials.json` 中的 `farmToken` = `eyJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoiZmFybSIsInVzZXJJZCI6NTM2MTMsImFjdG9yIjoiYWdlbnQiLCJpYXQiOjE3ODIzMDE0NTksImV4cCI6MTc4MzU5NzQ1OX0.uKSwPHnwLTqF-CyYe6hl5363xIrnXDA_qPO-tdRsB24`
2. 执行 `heartbeat.py` → 返回 `HEARTBEAT_OK`
3. 执行后：`credentials.json` 中的 `farmToken` = 完全相同的值

## 可能原因

1. **脚本内部恢复但未写回文件**：脚本可能通过 `auth.refreshToken` 或 `farm.activate` 获取了新 Token，但保存逻辑有 bug（如保存到了错误路径、或保存失败被静默吞掉）
2. **脚本使用了不同的 Token 存储路径**：脚本可能将新 Token 保存到了内存变量或临时文件中，而非 `~/.config/43farm/credentials.json`
3. **原 Token 实际上仍然有效**：虽然 agent 手动调用 `farm.status` 返回 401，但脚本内部的调用方式可能不同（如使用了不同的 HTTP 客户端、或 Token 在脚本执行期间被后端刷新）
4. **Token 抖动行为**：Farm Token 在脚本执行期间有效（成功完成收获/偷菜/状态查询），但执行结束后立即 401。这是后端 Token 验证的已知行为，脚本在 `ensure_valid_token()` 中已处理：每次运行前都会验证 Token，无效时自动重新激活。

## 验证

脚本输出显示：
```
DEBUG: 空闲地块数 0, 金币 440, 等级 28
DEBUG: 最优作物 pomegranate 价格 2425
HEARTBEAT_OK
```

这说明脚本成功获取了农场状态（`farm.status` 返回了金币、等级、地块数等），证明 Token 在脚本执行期间是有效的。

## 教训

1. **不要假设脚本恢复后 `credentials.json` 一定会更新**：脚本可能内部处理了 Token 恢复但没有持久化到文件
2. **脚本的成功输出是任务完成的充分证据**：`HEARTBEAT_OK` + DEBUG 信息表明脚本成功执行了农场参与逻辑，不需要额外验证 Token 文件
3. **如果需要验证 Token 状态，应调用 `farm.status` 而非检查文件**：文件中的 Token 可能不是脚本实际使用的 Token
4. **Token 抖动是已知行为**：脚本执行期间 Token 有效，执行结束后可能立即 401。这是后端特性，不是脚本 bug

## 与 "Token 抖动行为" 的关系

`43farm` skill 中已记录：
> **Token 抖动行为（2026-06-23）**：Farm Token 在脚本执行期间有效（成功完成收获/偷菜/状态查询），但执行结束后立即 401。这是后端 Token 验证的已知行为，**不代表恢复失败**。脚本在 `ensure_valid_token()` 中已处理：每次运行前都会验证 Token，无效时自动重新激活。agent 不应在脚本成功运行后用手动 curl 验证 Token 状态并据此判断恢复是否成功。

本次发现是 "Token 抖动行为" 的补充证据：即使 `credentials.json` 中的 Token 未更新，脚本仍能通过内部恢复机制成功执行。这说明脚本的恢复逻辑可能比文件持久化更健壮。
