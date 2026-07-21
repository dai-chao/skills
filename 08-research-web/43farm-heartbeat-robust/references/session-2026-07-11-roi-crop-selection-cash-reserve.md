# ROI-First Crop Selection — 2026-07-11

## Problem

The local `~/farm_now.py` script was choosing crops by **highest coin profit per second**. For a level 30 farm with 18 plots, this logic kept picking the most expensive seeds available:

- `pomegranate` (2425 coins)
- `banana` (900 coins)
- `orange` (1587 coins)

These crops have high long-term returns, but their seed prices drain working capital immediately. After each harvest, the script would reinvest **all** coins into a few expensive seeds, leaving no cash. Once the farm was fully planted, the user had no money to buy new seeds for maturing/idle plots, so the farm stalled even though crops were still growing.

Observed sequence:

| Run | Coins before | Action | Coins after | Notes |
|---|---|---|---|---|
| 1 | 30544 | Planted 12 × pomegranate | 1444 | Most cash locked in seeds |
| 2 | 1444 | Planted 1 × banana | 544 | Still expensive |
| 3 | 544 | Planted 1 × pumpkin + sold carrot ×2 | 219 | Almost broke |
| 4 | 219 + 40 (sell) | Planted 1 × eggplant | 22 | 18 plots planted, 0 liquidity |

After this, the script could no longer plant anything because every affordable seed cost more than the 22 coins on hand.

## Fix

User directed: **"优先回本快"** (prioritize fast return on investment).

The script was patched to:

1. **Sort by ROI**, not coin-per-second:
   - `ROI = (yield × unit_price − seed_price) / seed_price`
   - This favors cheap seeds that return their cost quickly, preserving cash flow.
2. **Keep a cash reserve** of 300 coins so the farm is never fully drained.
3. **Use only available cash minus reserve** when choosing a crop:
   - `available_coins = max(0, coins − reserve_coins)`
4. **Tie-break by coin-per-second** only when ROI is equal.

### Code fragment

```python
reserve_coins = 300
available_coins = max(0, coins - reserve_coins)

affordable = [(n, p, r, y, up, gs, s) for n, p, r, y, up, gs, s in crops
              if level >= r and p <= available_coins]

def roi_rate(item):
    n, p, y, up, gs, s = item
    return (y * up - p) / p

def coin_rate(item):
    n, p, y, up, gs, s = item
    return (y * up - p) / gs

affordable.sort(key=lambda x: (roi_rate(x), coin_rate(x)), reverse=True)
```

## Outcome

After the patch, the script could still run when coins were low, but it would choose cheaper seeds and keep a reserve. The farm stops stalling because cash is preserved for the next planting cycle.

## Lesson

For idle-plant scripts, **liquidity matters more than theoretical profit**. A farm with 18 plots but zero cash is worse than a farm with 18 plots of cheap, fast-ROI crops and a healthy cash reserve. When users complain "every day I plant and sell but still have no coins," the cause is usually over-investment in expensive seeds, not low yields.

## When to apply

Apply this rule when:
- The user has many plots but frequently runs out of coins
- The script reports "金币不够种任何作物" even though harvests are happening
- The chosen crop price is consistently > 50% of current coins
