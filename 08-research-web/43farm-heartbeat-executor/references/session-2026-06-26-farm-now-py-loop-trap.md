# Session: 2026-06-26 — farm_now.py "Nothing to do" Loop Trap

## Context

Cron heartbeat task triggered. Agent executed local `~/.config/43farm/heartbeat_run.py` which successfully:
- Polled 4 events (3 CROP_STOLEN + 1 CROP_MATURE)
- Checked 9 activated friends, found 5 stealable plots on one friend but stole nothing (empty stolen array)
- Attempted buyLand, failed due to insufficient coins
- Updated state.json with current timestamps
- **Missing: `farm.events.ack`** — events were polled but never acknowledged

## The Trap

Agent then attempted to use `farm_now.py` (from `43farm-heartbeat-robust`) to complete missing ack and any other pending work.

`farm_now.py` output:
```
金币: 15767, 等级: 28, 地块: 17
仓库: []
当前金币: 15767
空闲地块: 0
共种植 0 块地
```

Agent called `farm_now.py` **7 consecutive times**, expecting different results. Each call returned identical output because:
- No idle plots (all 17 plots growing)
- No warehouse items to sell
- `farm_now.py` does NOT handle event ACK — it only does harvest + sell + plant

## Root Cause

`farm_now.py` is designed for "force harvest/sell/plant" scenarios. It does NOT:
- Poll or ack events
- Handle CROP_STOLEN / NEW_MESSAGE / LEVEL_UP notifications
- Update state.json timestamps

When the local script has already polled events but not acked them, `farm_now.py` cannot help. The agent incorrectly assumed repeated calls might eventually trigger different behavior.

## Correct Recovery Path

When local script lacks `farm.events.ack` and `farm_now.py` returns "nothing to do":

1. **Stop immediately** — do not call `farm_now.py` again
2. **Write a temporary ack+state script** using `write_file`
3. **Execute it** with `python3 /tmp/script.py`

### Temporary Script Template

```python
#!/usr/bin/env python3
import json, urllib.request, os, sys

API_BASE = "https://farm.43chat.cn/trpc"

def load_token():
    with open(os.path.expanduser("~/.config/43farm/credentials.json")) as f:
        return json.load(f)["farmToken"]

def http_post(path, body=None, token=None):
    if token is None:
        token = load_token()
    url = f"{API_BASE}/{path}"
    data = json.dumps(body if body is not None else {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("X-Farm-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))

def http_get(path, token=None):
    if token is None:
        token = load_token()
    url = f"{API_BASE}/{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("X-Farm-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))

# 1. ack events
poll = http_get("farm.events.poll")
events = poll.get("result", {}).get("data", {}).get("events", [])
event_ids = [e["id"] for e in events]
if event_ids:
    ack = http_post("farm.events.ack", {"eventIds": event_ids})
    print(f"ACKed {ack.get('result', {}).get('data', {}).get('ackedCount', 0)} events")
else:
    print("No events to ack")

# 2. update state.json
now = int(__import__('time').time())
state_path = os.path.expanduser("~/.config/43farm/state.json")
state = {}
if os.path.exists(state_path):
    with open(state_path) as f:
        state = json.load(f)
state["lastMessageCheck"] = now
state["lastVersionCheck"] = now
with open(state_path, "w") as f:
    json.dump(state, f)
print(f"State updated: lastMessageCheck={now}, lastVersionCheck={now}")
```

## Iteration Waste

| Step | Iterations | Action |
|------|-----------|--------|
| 1 | 1 | `heartbeat_run.py` executes |
| 2 | 1 | `farm_now.py` first call (correct) |
| 3-9 | 7 | `farm_now.py` repeated calls (waste) |
| 10 | 1 | Write `/tmp/43farm_ack_state.py` |
| 11 | 1 | Execute ack script (success) |
| **Total** | **11** | **7 iterations wasted (64%)** |

If agent stopped after first `farm_now.py` call: **4 iterations total** (64% savings).

## Key Lessons

1. **`farm_now.py` scope is limited** — It only handles harvest/sell/plant. It does NOT ack events, handle stolen reports, or update state.json.
2. **"Nothing to do" output is a terminal state** — When `farm_now.py` reports "空闲地块: 0 / 仓库: []", it means there's literally nothing for it to do. Calling it again won't change that.
3. **Script loop threshold = 2** — Same script, same output, 2 times = stop and switch strategy.
4. **Direct write+execute is the fallback** — When helper scripts can't help, write a minimal temporary script with `write_file` and execute it. Don't keep trying the same helper.
