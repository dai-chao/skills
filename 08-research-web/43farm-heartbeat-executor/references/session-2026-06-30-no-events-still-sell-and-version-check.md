# 2026-06-30 43Farm 心跳实录：无事件、无成熟作物时仍需补卖出与版本检测

## 场景

本次 cron 心跳触发时，本地 `heartbeat_run.py` 成功执行：
- 农场 18 块地全部处于 `growing` 状态（pomegranate）
- 仓库剩余 4 个 radish
- `farm.events.poll` 返回 0 条事件
- 10 位已激活好友均无可偷成熟作物
- 本地脚本输出 "State updated" 并刷新 `lastMessageCheck`

## 本地脚本缺陷

`~/.config/43farm/heartbeat_run.py` **再次缺少两个关键操作**：
1. 没有 `farm.sell` 卖出仓库作物
2. 没有 `farm.events.ack` 确认已 poll 事件

## 阶段三补做

由于本地脚本刚更新 `lastMessageCheck`，官方 `heartbeat.py` 会因时间锁直接返回 `HEARTBEAT_OK`，无法补做。因此 Agent 直接手动补做：

### 1. 清仓卖出
```bash
TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json)
curl -s -X POST -H "Content-Type: application/json" -H "X-Farm-Token: $TOKEN" -d '{}' https://farm.43chat.cn/trpc/farm.sell
```

响应：
```json
{"result":{"data":{"coinsEarned":52,"coinsTotal":17507}}}
```

仓库 4 个 radish 全部卖出，金币 17455 → 17507。

### 2. 确认事件
```bash
curl -s -H "X-Farm-Token: $TOKEN" https://farm.43chat.cn/trpc/farm.events.poll
```

响应：
```json
{"result":{"data":{"events":[],"gameplayVersion":"1.1.1"}}}
```

0 条事件，无需 ack。

### 3. 版本检测
```bash
curl -s https://farm.43chat.cn/skills/skill.json | head -c 500
```

远端 version：`1.1.1`
本地 `~/.hermes/skills/43farm/skill.json` version：`1.1.1`

一致，无需更新。

## 关键教训

1. **无事件 ≠ 无需检查仓库**：即使 `farm.events.poll` 为空、没有成熟作物、没有偷菜机会，本地脚本仍可能遗留仓库作物未卖出。阶段三补做应 always 检查 `warehouse`。
2. **低价值作物也要卖**：4 个 radish 仅值 52 金币，但积少成多；更重要的是防止仓库逻辑被遗漏。
3. **版本检测独立执行**：不能因本地脚本已更新时间锁就跳过版本检测。远端 `skill.json` 需单独拉取比对。
4. **`farm.sell {}` 清仓模式可靠**：仓库同时含多种作物时，`{}` 可一次性全部卖出，无需逐项指定。
5. **`jq -r` 变量赋值在单条命令中稳定**：本次验证 `TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json)` + 后续 `curl -H "X-Farm-Token: $TOKEN"` 在单行命令中成功。但 multi-line 命令中仍可能因 `)` 解析失败，需谨慎。

## 最终状态

- 金币：17507（+52）
- 仓库：空
- 事件：0 条未读
- 版本：1.1.1（无需更新）
- `state.json` 时间戳已刷新

输出：`HEARTBEAT_OK`
