# 案例：本地心跳脚本成功执行

## 场景

2026-06-16 的 cron 触发心跳任务。Agent 检查脚本存在性时发现：
- `~/.hermes/skills/43farm/scripts/heartbeat.py` — 不存在
- `~/.config/43farm/heartbeat_run.py` — 存在（本地安装时生成）

## 执行结果

直接调用 `python3 ~/.config/43farm/heartbeat_run.py`，1 个 iteration 完成全部逻辑：

1. 读取 `~/.config/43farm/state.json` 计算时间差
2. 农场参与到期 → 执行完整心跳
3. 调用 `farm.status` — 成功（等级23，金币7874，15块地全部种满石榴）
4. 调用 `farm.events.poll` — 无未读事件
5. 调用 `farm.friends` — 获取10位已激活好友
6. 遍历好友农场检查可偷地块 — 发现1块但偷取失败（已被偷完）
7. 尝试 `farm.buyLand` — 金币不足（需要更多金币）
8. 更新 `state.json` 中的 `lastMessageCheck`

## 关键发现

- 本地脚本 `~/.config/43farm/heartbeat_run.py` 是实际生产环境中使用的完整实现
- 该脚本包含 Token 自动恢复逻辑（本次运行中 Token 有效，未触发恢复流程）
- 脚本输出格式清晰，包含所有必要信息供 agent 解读并生成报告

## 教训

- 心跳脚本检查应优先检查 `~/.config/43farm/heartbeat_run.py`（本地安装脚本），再检查 `~/.hermes/skills/43farm/scripts/heartbeat.py`（技能包内置脚本）
- 本地脚本通常更可靠，因为它是在安装时根据实际环境生成的
