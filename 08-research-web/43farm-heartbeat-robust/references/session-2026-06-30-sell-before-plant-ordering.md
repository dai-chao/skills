# 2026-06-30 43Farm 阶段三补做：先卖出再种植的顺序收益

## 背景

本次 cron 心跳中，本地 `heartbeat_run.py` 成功收获 15 块成熟石榴（315 个），但缺少 `farm.sell` 和 `farm.events.ack`。官方 `heartbeat.py` 因时间锁跳过补做，需要写临时脚本完成剩余操作。

## 两种执行顺序的对比

### 顺序 A：先卖出，再种植（实际采用）

- 初始金币：10234
- 卖出 6 orange → +204 金币
- 卖出 315 pomegranate → +17010 金币
- 卖出后金币：27448
- 种植 5 块 idle 地（pomegranate，每块 2425）→ 消耗 12125 金币
- 最终金币：约 15323

结果：5 块地全部种满。

### 顺序 B：先种植，再卖出（假设）

- 初始金币：10234
- 种植 pomegranate，每块 2425
- 10234 // 2425 = 4 块，剩余 534 金币
- 第 5 块 idle 地因金币不足无法种植
- 卖出仓库后获得 17214 金币，但已错过种植第 5 块地的机会

结果：仅种植 4 块地，损失 1 块地的种植周期收益。

## 结论

阶段三补做脚本中，`farm.sell` 必须在 `farm.plant` 之前执行。卖出获得的金币直接决定能种满多少 idle 地块，顺序错误会导致农场产出损失。

## 参考脚本

见 `43farm-heartbeat-executor/references/session-2026-06-30-local-script-harvests-but-skips-sell-ack.md` 中的 `/tmp/43farm_sell_plant.py` 完整实现。
