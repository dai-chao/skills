# 2026-06-25: land_prices 字典格式错误导致 TypeError

## 问题

Agent 在写临时补全脚本 `/tmp/43farm_sell_plant.py` 时，将 `land_prices` 字典的值误写为 `int`（仅价格），而非 `tuple`（等级, 价格）：

```python
# 错误
land_prices = {7: 2000, 8: 3000, ...}
# 解包时：req_level, req_coins = land_prices[18]  → TypeError: cannot unpack non-iterable int object

# 正确
land_prices = {7: (5, 2000), 8: (7, 3000), ...}
```

## 根因

临时脚本匆忙编写，复制 `43farm-heartbeat-robust` SKILL.md 中的 `land_prices` 表时，只复制了价格列，遗漏了等级要求列。

## 影响

- 脚本在买地阶段崩溃，无法完成后续操作
- 需要额外一次 iteration 修复并重新执行
- 如果未及时发现，可能导致状态文件未更新、买地机会错过

## 教训

1. **复制表格数据时务必核对列数**：`land_prices` 是 `(等级, 价格)` 二元组，不是单一价格。
2. **临时脚本也应做最小验证**：在写脚本后、执行前，快速检查关键数据结构（如字典值类型、列表长度）。
3. **优先使用现有 `farm_now.py`**：它已正确处理 `land_prices` 和全部农场逻辑，避免从零写脚本引入此类错误。
4. **脚本执行失败时检查错误位置**：此错误发生在 "Buy land" 阶段，说明收获和卖出已成功，只需修复后续逻辑即可。
