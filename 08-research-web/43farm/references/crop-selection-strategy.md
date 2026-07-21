# 43Farm 作物选择策略

## 默认策略：选最便宜的

心跳脚本 `scripts/heartbeat.py` 中的 `pick_best_crop(level)` 默认选择**当前等级可种植的最便宜作物**。

```python
def pick_best_crop(level):
    """根据等级返回最便宜的可用作物 {"type": ..., "price": ...}"""
    crops = [
        ("radish", 125, 0),
        ("carrot", 163, 0),
        ("corn", 175, 3),
        ("eggplant", 237, 5),
        ("tomato", 251, 7),
        ("pumpkin", 325, 9),
        ("strawberry", 605, 10),
        ("banana", 900, 12),
        ("orange", 1587, 14),
        ("pomegranate", 2425, 16),
    ]
    best = None
    for name, price, req in crops:
        if level >= req:
            if best is None or price <= best[1]:
                best = (name, price)
    return {"type": best[0], "price": best[1]}
```

理由：便宜种子能让农场在金币有限时仍然把所有 `idle` 地块种满，避免一次性被高级作物种子费耗尽现金，导致后续地块全部荒废。

## 已踩过的坑：误选最贵作物

2026-07-18 会话中，旧版 `pick_best_crop` 使用 `price >= best[1]` 而不是 `price <= best[1]`，导致 30 级时自动选择最贵的 `pomegranate`（种子价 2425）。结果：

- 7387 金币只种了 3 块地就耗尽
- 剩余 15 块 `idle` 地无法种植
- 农场进入停滞，只能等成熟/偷菜/卖仓库回血

用户反馈："谁让你种最贵的石榴了，之前都是种最便宜的"。随后修复为选择最便宜作物。

## 修改策略

如需切换为“产出最高”或“指定作物”，修改 `pick_best_crop` 并确保用户知情。例如：

- 产出最高：按作物单价 × 产量 / 时间计算 ROI，而不是只看种子价格
- 指定作物：直接返回固定 `cropType`
- 成就导向：按 `farm.unplantedCrops` 结果优先补种未种过的作物

修改后建议手动跑一遍 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` 验证金币和地块利用情况。

## 价格表（截至 SKILL.md 1.1.1 版本）

| cropType | 种子价格 | 解锁等级 |
|----------|---------|---------|
| radish | 125 | 0 |
| carrot | 163 | 0 |
| corn | 175 | 3 |
| eggplant | 237 | 5 |
| tomato | 251 | 7 |
| pumpkin | 325 | 9 |
| strawberry | 605 | 10 |
| banana | 900 | 12 |
| orange | 1587 | 14 |
| pomegranate | 2425 | 16 |

> 注意：价格可能随版本更新变化。心跳脚本的作物价格表必须与后端真实价格一致，否则会出现“金币足够但种植失败”或“金币估算错误”的情况。
