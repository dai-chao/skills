# Session 2026-07-14: Sell-before-steal ordering bug in local heartbeat_run.py

## Reproduction

Agent ran the local cron script:

```bash
python3 ~/.config/43farm/heartbeat_run.py
```

Script output showed:

- `farm.status`: level 30, coins 89, 18/18 plots, 10 idle, warehouse empty
- `farm.events.poll`: 0 events
- Harvest: 0 mature / 0 withered plots, so nothing to harvest
- `sell_warehouse()`: warehouse was empty, nothing sold
- `farm.steal` from friend X: stole `carrot x4`
- Replant attempt: 10 idle plots remained, but coins still 89, below cheapest crop `radish` (125)

Result: stolen carrots sat in the warehouse and could not be converted to planting funds in the same heartbeat cycle.

## Root cause

The local script order was:

```
1. harvest
2. sell_warehouse()   # only sells crops already in warehouse before steal
3. steal              # adds stolen crops to warehouse
4. buyLand / replant  # uses coin count from before the steal
```

Because `sell_warehouse()` ran before `steal`, the stolen `carrot x4` were never sold to fund replanting.

## Workaround applied

Two temporary scripts were written and executed:

1. `/tmp/43farm_sell_warehouse.py` — called `farm.sell {}` to clear the 4 carrots, earning **+80 coins** (89 → 169).
2. `/tmp/43farm_plant_idle.py` — planted 1 `radish` on slot 9 for 125 coins (169 → 44).

After the workaround, 9 idle plots remained because 44 coins was still below the 125-coin radish price. The farm must now wait for growing crops to mature before further planting.

## Lesson

When auditing or patching local heartbeat scripts, verify that warehouse liquidation happens **after** stealing, or that a second `farm.sell` pass runs after `farm.steal`. Otherwise stolen crops remain trapped in inventory and idle plots stay empty until the next natural harvest cycle.
