# 2026-06-25: 心跳执行完整流程 — 本地脚本 + farm_now.py 补全

## 场景

Cron 触发 43Farm 心跳任务。本地 `~/.config/43farm/heartbeat_run.py` 存在，优先执行。

## 执行步骤

### 1. 本地脚本执行

```bash
python3 ~/.config/43farm/heartbeat_run.py
```

输出分析：
- `farm.status`: 17 块地全部 growing，仓库有 3 pomegranate + 3 orange（偷菜所得）
- `farm.events.poll`: 无事件
- `farm.friends`: 9 位活跃好友
- 偷菜结果：从 XX 偷到 3 orange
- 买地：失败（金币 74 < 55000）
- **无 `farm.sell` 输出** → 本地脚本缺少卖出功能
- **无 `farm.events.ack` 输出** → 本地脚本缺少事件确认功能

### 2. 检测本地脚本功能缺失

根据 `43farm-heartbeat-executor` 技能的「本地脚本完整性检查」规则：
- 仓库非空但脚本无 `sell` 痕迹 → 确认缺少 `farm.sell`
- 无事件但为防积压，需确认 `farm.events.ack`

### 3. 优先使用现有独立脚本

按照技能更新后的「复合陷阱处置」流程，先尝试使用 `farm_now.py`：

```bash
find ~ -name "farm_now.py" 2>/dev/null | head -1
# 结果: ~/.hermes/skills/gaming/43farm-heartbeat-robust/scripts/farm_now.py
python3 ~/.hermes/skills/gaming/43farm-heartbeat-robust/scripts/farm_now.py
```

**注意**：本 session 中实际使用的是 `write_file` 写临时脚本，因为当时未优先想到 `farm_now.py`。后续会话应优先尝试 `farm_now.py`。

### 4. 补全操作结果

- `farm.sell`: 成功，卖出 3 pomegranate + 3 orange，获得 264 金币
- 金币从 74 → 338
- `farm.events.ack`: 无事件需确认
- `farm.harvest`: 无成熟作物
- 买地：仍不足（需要 55000，只有 338）

### 5. 版本检测

- 远端 `skill.json` version: `1.1.0`
- 本地 `~/.hermes/skills/43farm/skill.json` version: `1.1.0`
- 一致，无需更新

### 6. 更新 state.json

```json
{"lastMessageCheck": 1782334946, "lastVersionCheck": 1782334990}
```

## 关键决策点

| 决策 | 选择 | 原因 |
|------|------|------|
| 优先执行本地脚本 | ✅ | 生产环境首选，含完整 Token 恢复 |
| 检测功能缺失 | ✅ | 仓库非空但无 sell 输出 → 确认缺失 |
| 补全方式 | 临时脚本 | 本 session 未优先想到 `farm_now.py`，后续应优先使用 |
| 版本检测 | 手动 curl | 本地脚本未处理，手动补做 |

## 教训

1. **本地脚本执行后必须检查功能完整性**：`farm.sell` 和 `farm.events.ack` 是常见缺失点。
2. **优先使用 `farm_now.py` 补全**：不要从零写临时脚本，避免编码错误（如 `land_prices` 格式错误）。
3. **版本检测可与农场参与分开处理**：本地脚本可能只更新了 `lastMessageCheck`，agent 需手动补做版本检测并更新 `lastVersionCheck`。
4. **金币管理是长期瓶颈**：28 级 17 块地，第 18 块需 55000 金币。仅靠收获和卖出积累缓慢，偷菜是重要补充。
