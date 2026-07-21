# 本地脚本缺少 farm.sell 导致仓库积压（2026-06-25）

## 场景

Cron 触发 43Farm 心跳任务。本地 `~/.config/43farm/heartbeat_run.py` 执行成功（exit code 0），输出包含完整的 farm.status、偷菜结果、买地尝试等。但脚本输出中没有 `farm.sell` 和 `farm.events.ack` 的痕迹。

## 执行结果

### 本地脚本输出
- farm.status: 17 块地全部 growing，warehouse 为空（但偷菜后会有变化）
- farm.events.poll: 无事件
- 偷菜: 从 XX 偷了 6 个 orange（18个），从不系之舟偷了 5 个地块（15个）
- 买地: 金币 582 不足，失败
- 输出结尾: "State updated."

### 问题发现

本地脚本执行后，agent 调用官方 `heartbeat.py` 返回 `HEARTBEAT_OK`。但按照技能文档的警告，需要检查本地脚本是否缺少 `farm.sell` 和 `farm.events.ack`。

写临时脚本 `/tmp/43farm_check.py` 查询 farm.status：
```
coins: 582
warehouse: [{'cropType': 'orange', 'quantity': 24}, {'cropType': 'pomegranate', 'quantity': 9}]
plots: 17
idle_plots: 0
mature_plots: 0
withered_plots: 0
```

**仓库积压**: 24 orange + 9 pomegranate，但金币只有 582。

## 补全操作

### 1. 卖出仓库

写临时脚本 `/tmp/43farm_sell.py` 强制卖出：
```python
# 先错误地使用了 POST 调 farm.status → 405 Method Not Allowed
# 修正为 GET 后成功

Warehouse before sell: [{'cropType': 'orange', 'quantity': 24}, {'cropType': 'pomegranate', 'quantity': 9}]
Sold 24 orange
Sold 9 pomegranate
Coins after sell: 1884
Warehouse after sell: []
```

金币从 **582 → 1884**（+1302）。

### 2. 确认事件

写临时脚本 `/tmp/43farm_final.py` 查询事件并 ack：
```
Events count: 1
Events: [{'id': '08f36fd3-95bc-4b94-8dfd-d03ae135cff8', 'type': 'ACHIEVEMENT_UNLOCKED', ...}]
Ack result: {'result': {'data': {'ackedCount': 1}}}
```

成就事件：梁上君子（见习）——"君子爱菜，偷之有道"。

## 教训

1. **本地脚本执行后必须检查仓库**：即使脚本返回 exit code 0 且输出详细，也可能缺少关键功能
2. **检查方法**：写临时脚本查询 `farm.status` 的 `warehouse` 字段，非空则补做卖出
3. **不要依赖官方脚本补做**：官方脚本可能因 `idle_count = 0` 或时间锁而跳过卖出
4. **GET/POST 方法混淆**：`farm.status` 是 GET 端点，使用 POST 会返回 405。这是写临时脚本时的常见编码错误
5. **farm.sell 的参数**：仓库有多种作物时，需要逐项指定 `cropType` 和 `quantity`，空对象 `{}` 可能无法清仓

## 迭代消耗

- 本地脚本执行: 1 iteration
- 官方脚本执行: 1 iteration
- 检查仓库状态: 1 iteration (write_file) + 1 iteration (execute)
- 卖出仓库（第一次写错 POST）: 1 iteration (write_file) + 1 iteration (execute, 405 失败)
- 卖出仓库（修正为 GET）: 1 iteration (write_file) + 1 iteration (execute, 成功)
- 确认事件: 1 iteration (write_file) + 1 iteration (execute, 成功)
- **总计**: 约 9 iterations

如果本地脚本内置 `farm.sell` 和 `farm.events.ack`，只需 2 iterations（本地脚本 + 官方脚本）。
