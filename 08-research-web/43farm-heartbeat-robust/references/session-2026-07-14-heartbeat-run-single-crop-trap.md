# 2026-07-14 本地 heartbeat_run.py 只种单一高价作物的陷阱

## 现象

- 执行 `~/.config/43farm/heartbeat_run.py` 心跳脚本
- 农场状态：等级 30，金币 443，18 块地（3 块 growing radish，15 块 idle），仓库空
- 脚本硬编码所有 idle 地块种 `pomegranate`（2425 金/块）
- 15 块 idle 地全部调用 `farm.plant` 失败，返回 `金币不足以完成此操作`
- 同时无成熟作物、无事件、好友农场无可偷，农场完全停滞

## 根因

脚本缺少作物降级逻辑：

```python
# 原脚本中的问题代码
for plot in idle_plots:
    slot = plot["slot"]
    print(f"Planting pomegranate on slot {slot}...")
    resp = curl_post("farm.plant", {"plotSlot": slot, "cropType": "pomegranate"})
```

金币不足以购买高价种子时，应该种植能负担的最优作物（如 `radish` 125 金），而不是让所有地块空着。

## 修复

在 `heartbeat_run.py` 中增加作物选择函数：

```python
CROP_LIST = [
    ("radish", 125, 0, 11.0),
    ("tomato", 251, 7, 12.8),
    ("corn", 175, 3, 12.1),
    ("strawberry", 605, 10, 19.2),
    ("orange", 1587, 14, 24.1),
    ("pomegranate", 2425, 16, 17.7),
    ("banana", 900, 12, 15.0),
    ("eggplant", 237, 5, 10.6),
    ("pumpkin", 325, 9, 10.5),
    ("carrot", 163, 0, 7.9),
]

def pick_best_crop(coins, level):
    """Choose the fastest-payback crop we can afford and grow, keeping 300 coins reserve if possible."""
    for crop, price, req_level, _ in CROP_LIST:
        if level >= req_level and coins >= price + 300:
            return crop, price
    # Fallback: plant whatever we can afford even if it breaks reserve
    for crop, price, req_level, _ in CROP_LIST:
        if level >= req_level and coins >= price:
            return crop, price
    return None, 0
```

然后在两个种植位置（初始 idle 种植、卖出/买地后补种）都调用 `pick_best_crop(coins, level)`，并更新剩余金币。

## 额外注意：临时补做脚本也要用相同逻辑

本次会话中，临时补做脚本 `/tmp/43farm_plant_now.py` 仍使用"最高价值作物"逻辑，结果只种了 1 块 `pumpkin`（325 金）就花光大部分金币，剩余 118 金无法继续种植。这说明主脚本修复后，临时脚本也必须同步使用降级逻辑，否则补做阶段仍会造成金币浪费。

## 结果

- 修复后的 `heartbeat_run.py` 语法校验通过
- 因时间锁已刷新，重新运行脚本时正确跳过了农场参与
- 当前农场：1 块 pumpkin + 3 块 radish growing，14 块 idle，118 金币
- 农场仍因金币不足停滞，但这是正常游戏状态，需等待现有作物成熟收获

## 相关技能

- `43farm-heartbeat-robust` 主 SKILL.md 已新增"本地 heartbeat_run.py 只种植单一高价作物的陷阱"章节
