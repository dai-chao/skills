# 本地心跳脚本 plant-before-sell / steal-after-sell 顺序 bug

## 会话

2026-07-13 cron 心跳执行。

## 现象

`~/.config/43farm/heartbeat_run.py` 执行后输出：

- 18 块地全部 `idle`
- 金币仅 50
- 仓库为空（但脚本没有执行 `farm.sell` 的痕迹）
- 从好友 `huyd` 偷到 4 个 radish
- 尝试种 `pomegranate` 全部失败："金币不足以完成此操作"
- 最终 `State updated`

重新查询 `farm.status` 后发现仓库实际有 4 个 radish（偷来的），但脚本并未卖出，金币仍 50，无法种植任何作物。

## 根因

脚本的业务顺序错误：

1. **先种植**（第 133-144 行）：此时脚本用启动时读取的 `farm.status`（金币 50）尝试种 `pomegranate`，自然全部失败。
2. **再收获/卖出**（第 148-176 行）：但此时仓库是空的，因为偷菜还没执行。
3. **再偷菜**（第 180 行）：偷来的 radish 进入仓库，但脚本已经不再执行 `sell_warehouse()`。
4. **最后再种植一次**（第 224-234 行）：金币仍然是 50（偷来的 radish 没卖出），所以仍然全部失败。

即：**卖出逻辑在偷菜之前执行**，导致偷菜所得无法在同一心跳内变现为金币并用于种植。

## 关键代码片段

```python
# 4. Check for idle plots and plant if any (only when farm participation is due)
if now - last_message_check >= 1800:
    plots = status.get("result", {}).get("data", {}).get("plots", [])
    idle_plots = [p for p in plots if p.get("status") == "idle"]
    print(f"\nIdle plots: {len(idle_plots)}")

    if idle_plots:
        # Plant pomegranate on all idle plots
        for plot in idle_plots:
            slot = plot["slot"]
            print(f"Planting pomegranate on slot {slot}...")
            resp = curl_post("farm.plant", {"plotSlot": slot, "cropType": "pomegranate"})
            print(json.dumps(resp, ensure_ascii=False, indent=2))

# ... 第 5 步 harvest ... 第 6 步 sell_warehouse ...

# 7. Try to steal from friends
if now - last_message_check >= 1800:
    # ... steal ...

# 8. Replant idle plots after selling / buying land
if now - last_message_check >= 1800:
    status = curl_get("farm.status")
    plots = status.get("result", {}).get("data", {}).get("plots", [])
    idle_plots = [p for p in plots if p.get("status") == "idle"]
    if idle_plots:
        for plot in idle_plots:
            slot = plot["slot"]
            resp = curl_post("farm.plant", {"plotSlot": slot, "cropType": "pomegranate"})
```

## 正确顺序

```
1. 查询 farm.status
2. poll & ack 事件
3. 收获成熟/枯萎地块
4. 卖出仓库（包括此前遗留的 + 本次收获的）
5. 偷菜（把偷来的也加入仓库）
6. 再次卖出仓库（变现偷来的作物）
7. 种植空闲地块（此时金币最大化）
8. 买地（如果金币和等级允许）
9. 种植新买/剩余空闲地块
10. 更新 state.json
```

## 处置

当发现本地脚本存在这种顺序 bug 时，写一个阶段三补全脚本：

- 先 `farm.sell {}` 清仓
- 再按金币选择最优可负担作物
- 种植所有 `idle` 地块
- 最后 ack 事件并更新 state

参考 `templates/stage_three_supplement.py`。

## 教训

- 本地脚本即使**包含** `farm.sell`，也可能因为执行顺序错误而实际无法卖出偷来的作物。
- 阶段三补做脚本必须严格遵循：**先卖出 → 再种植**。
- 如果农场金币耗尽且仓库为空，无法种植，应在报告中明确告知主人农场已停滞。
