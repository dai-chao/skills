# Patching a local heartbeat_run.py

## Problem

The user's custom `~/.config/43farm/heartbeat_run.py` may:

- Update `state.json` timestamps **unconditionally** at the end, even when the 1800s farm-participation check was not due and no work was done.
- Skip version detection entirely, so `lastVersionCheck` is always set to the same value as `lastMessageCheck`.
- Run expensive/unnecessary actions (harvest, sell, idle checks) even when participation is not due.

## Impact

Unconditional timestamp updates create a "time-lock" where the next cron run sees the check as not due and skips real farm participation. If the previous run failed, the failure is silently masked.

## Fix

Guard every farm-participation action behind the 1800s check, and add a separate 7200s version check.

### Example diff

1. Wrap idle/plant checks:

```python
if now - last_message_check >= 1800:
    plots = status.get("result", {}).get("data", {}).get("plots", [])
    idle_plots = [p for p in plots if p.get("status") == "idle"]
    ...
```

2. Wrap harvest/sell checks:

```python
if now - last_message_check >= 1800:
    ...
    sell_warehouse()
```

3. Wrap friends/steal/buyLand checks similarly.

4. Add version check before state update:

```python
import urllib.request

STATE = json.load(open(STATE_PATH)) if os.path.exists(STATE_PATH) else {}
now = int(time.time())
last_version_check = STATE.get("lastVersionCheck", 0)
do_version_check = now - last_version_check >= 7200
version_updated = False

if do_version_check:
    print("\n=== Version check ===")
    try:
        with urllib.request.urlopen("https://farm.43chat.cn/skills/skill.json", timeout=20) as resp:
            remote_skill = json.loads(resp.read().decode("utf-8"))
        local_skill_path = os.path.expanduser("~/.hermes/skills/43farm/skill.json")
        local_skill = json.load(open(local_skill_path)) if os.path.exists(local_skill_path) else {}
        remote_version = remote_skill.get("version")
        local_version = local_skill.get("version")
        if remote_version != local_version:
            print(f"Version changed: {local_version} -> {remote_version}")
            for fn in remote_skill.get("files", ["skill.md", "skill.json", "install.md", "heartbeat.md", "gameplay.md"]):
                url = f"https://farm.43chat.cn/skills/{fn}"
                path = os.path.join(os.path.dirname(local_skill_path), fn)
                try:
                    with urllib.request.urlopen(url, timeout=20) as resp:
                        data = resp.read().decode("utf-8")
                    with open(path, "w") as f:
                        f.write(data)
                    print(f"Updated {fn}")
                except Exception as e:
                    print(f"Failed to download {fn}: {e}")
        else:
            print(f"Version up-to-date: {local_version}")
        version_updated = True
    except Exception as e:
        print(f"Version check failed: {e}")
```

5. Conditional state update:

```python
state = json.load(open(STATE_PATH))
now = int(time.time())
if now - last_message_check >= 1800:
    state["lastMessageCheck"] = now
if version_updated:
    state["lastVersionCheck"] = now
with open(STATE_PATH, "w") as f:
    json.dump(state, f)
print(f"\nState updated (lastMessageCheck={state.get('lastMessageCheck')}, lastVersionCheck={state.get('lastVersionCheck')}).")
```

## Verification

After patching, run the script twice in quick succession. The second run should print:

- `farm.message check not due (...s < 1800s)`
- `Harvest / sell checks skipped (not due)`
- `State updated (lastMessageCheck=<old>, lastVersionCheck=<old>)`

The timestamps should remain unchanged when checks are skipped.
