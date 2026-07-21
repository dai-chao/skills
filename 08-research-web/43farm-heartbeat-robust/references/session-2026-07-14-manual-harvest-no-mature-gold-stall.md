# 2026-07-14 手动收菜：无成熟作物 + 金币停滞

## 触发

用户发送 "收菜偷菜"，要求立即执行收获和偷菜。

## 农场状态

```json
{
  "coins": 44,
  "experience": 160885,
  "level": 30,
  "plotCount": 18,
  "warehouse": []
}
```

地块分布：
- 9 块 growing（1 pumpkin, 8 radish）
- 8 块 idle
- 0 块 mature / withered

## 执行结果

1. `farm.harvest` → `{"harvestedCount": 0, "xpAwarded": 0, "crops": []}`
2. `farm.friends` → 10 位已激活农场的好友
3. 遍历 10 位好友 `farm.view` → 均无成熟作物
4. `farm.sell {}` → `{"coinsEarned": 0, "coinsTotal": 44}`（仓库空）
5. 8 块 idle 地尝试种植 → 全部失败：金币 44 < 最便宜 radish 种子 125

## 关键发现

- 当金币低于最便宜作物种子价格（当前 radish 125）且仓库为空、偷菜无收获时，农场进入完全停滞。
- 心跳脚本 `~/.hermes/skills/43farm/scripts/heartbeat.py` 返回 `HEARTBEAT_OK`，但手动执行揭示当前没有可执行动作。
- 这不是错误，而是农场正常状态：需要等待现有 growing 作物成熟。

## 作物成熟预期（基于 `maturesAt`）

- 地块 2-7 radish：约 26 分钟后成熟
- 地块 7 radish：约 29 分钟后成熟
- 地块 8 radish：约 97 分钟后成熟
- 地块 9 radish：约 146 分钟后成熟
- 地块 1 pumpkin：约 187 分钟后成熟

## 后续建议

- 等 radish 成熟后，收获可获得金币，再补种 idle 地块。
- 如想避免长期停滞，可优化作物选择策略（ROI 优先，保留现金储备），避免全部种高价长周期作物。
