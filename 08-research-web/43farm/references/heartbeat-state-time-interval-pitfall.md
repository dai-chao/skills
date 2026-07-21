# 43Farm 心跳脚本 — 时间间隔陷阱

## 问题

heartbeat.py 主函数第 520-522 行：

```python
if not msg_due and not ver_due:
    print("HEARTBEAT_OK")
    return 0
```

`msg_due = (now - last_msg) >= 1800`，即**30 分钟**才执行一次农场操作。

用户之前设置的是 10 分钟 cron，但脚本硬编码了 30 分钟间隔。当用户手动执行或 cron 触发时，如果时间间隔不足 30 分钟，脚本直接返回 `HEARTBEAT_OK`，**跳过所有收获/种植/偷菜操作**。

## 表现

用户说「收菜偷菜」，脚本返回 `HEARTBEAT_OK`，但农场没有任何操作。用户质问：「X的农场有成熟的怎么不偷」。

## 根因

`state.json` 中的 `lastMessageCheck` 时间戳控制了执行频率。即使 cron 每 10 分钟触发，脚本内部 30 分钟的节流阀导致实际农场操作频率远低于预期。

## 解决

### 方案 A：强制立即执行（手动场景）

```bash
# 清零时间戳，强制 msg_due = true
rm -f ~/.config/43farm/state.json
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

或修改 `state.json`：
```bash
echo '{"lastMessageCheck": 0, "lastVersionCheck": 9999999999}' > ~/.config/43farm/state.json
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

### 方案 B：调整 cron 间隔匹配脚本（不推荐）

把 cron 改成 30 分钟，但这样失去了密集监控的意义。

### 方案 C：修改脚本间隔（需要用户决定）

把脚本第 517 行的 `1800` 改成 `600`（10 分钟），与用户 cron 一致。

## 额外陷阱：`lastVersionCheck` 被设为极大值导致版本检测永不触发

如果 `state.json` 中的 `lastVersionCheck` 被错误设为极大值（如 `9999999999`），则 `(now - lastVersionCheck)` 为负数，永远小于 7200，版本检测永远不会执行。

**典型场景**：某次手动恢复时为了「跳过版本检测」而故意将 `lastVersionCheck` 设为极大值，但忘记恢复。或者 state.json 被错误写入未来时间戳。

**检测**（cron 环境中 python3 -c 被安全扫描阻止，使用纯 bash 替代）：
```bash
# 检查 lastVersionCheck 是否为极大值
NOW=$(date +%s)
LAST_VER=$(cat ~/.config/43farm/state.json | grep -o '"lastVersionCheck":[0-9]*' | cut -d: -f2)
DELTA=$((NOW - LAST_VER))
echo "lastVersionCheck=$LAST_VER now=$NOW delta=$DELTA"
```

**修复**：将 `lastVersionCheck` 设为合理的历史时间戳（如 0 或当前时间）。在 cron 环境中使用 Write 工具直接写入修正后的 `state.json`：
```json
{"lastMessageCheck": 0, "lastVersionCheck": 0}
```
或设为刚好超过阈值：将 `lastVersionCheck` 设为当前时间戳减 7201。

> **脚本已内置防护**：`scripts/heartbeat.py` 从 v1.1.0+ 起在 `main()` 中增加了 sanity check：若 `lastVersionCheck > now + 86400`（超过未来 1 天），则强制视为 `ver_due = True`，自动恢复版本检测。但仍建议手动修复 state.json，避免每次心跳都触发不必要的版本检测。

## 额外陷阱：`HEARTBEAT_OK` 不等于「Token 有效」

脚本返回 `HEARTBEAT_OK` 仅表示「时间间隔未到期，本次跳过操作」。它**不会**验证 Farm Token 是否仍然有效。如果 Token 在两次心跳之间过期，脚本会连续多次返回 `HEARTBEAT_OK`，直到某个间隔真正到期时才会调用 API 并发现 401。

**表现**：用户手动测试 API 发现 401，但心跳脚本持续输出 `HEARTBEAT_OK`，造成「一切正常」的假象。

**根因**：脚本的节流设计（30 分钟农场参与、120 分钟版本检测）是为了避免频繁调用 API。Token 有效性检查只在「有实际工作要做」时才执行。

**解决**：
- 这是预期行为，无需修复脚本。若需强制检查，清零 state.json 时间戳即可：
  ```bash
  echo '{"lastMessageCheck": 0, "lastVersionCheck": 0}' > ~/.config/43farm/state.json
  python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
  ```
- 若希望脚本在每次运行时都快速验证 token（牺牲一点效率），可修改 `main()` 在 `msg_due`/`ver_due` 都为 false 时仍调一次 `farm.status`（轻量查询）来提前发现过期。

## 额外陷阱：Cron 终端 Python 执行陷阱

在 cron 任务中通过 `terminal` 工具执行 Python 时，`python3 -c` 和 `cat | python3` 会被安全扫描阻止，`python3 /dev/stdin << 'HEREDOC'` 可能返回空输出。详见 `references/cron-terminal-python-execution-pitfall.md`。

**推荐**：简单计算用纯 bash（`date +%s`、`grep -o`、`cut`），复杂逻辑用 agent 侧 Read 工具读取后在上下文中处理。

## 教训

1. 用户说「收菜偷菜」时，**先检查 state.json 时间戳**，如果时间太近导致脚本会跳过，先清零再执行
2. 不要假设脚本返回 `HEARTBEAT_OK` 就等于操作完成——可能是空转
3. 如果用户频繁手动触发，state 文件会不断被刷新，cron 反而更难触发实际操作
4. **检查 `lastVersionCheck` 是否为极大值**——这会导致版本检测永远跳过，即使 farm token 已过期也不会尝试恢复
