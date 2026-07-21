# 2026-06-25: 本地脚本缺少 farm.sell + 时间锁复合陷阱的 workaround

## 问题场景

1. 本地 `~/.config/43farm/heartbeat_run.py` 执行成功，更新了 `lastMessageCheck`
2. 但本地脚本缺少 `farm.sell`，仓库积压 9 orange + 6 pomegranate
3. 随后调用官方 `~/.hermes/skills/43farm/scripts/heartbeat.py`
4. 官方脚本检测到 `lastMessageCheck` 距现在仅 14 秒，认为「农场参与不到期」
5. 官方脚本直接返回 `HEARTBEAT_OK`，不做任何操作
6. 同时 Farm Token 在本地脚本执行后已过期（Token 抖动）
7. 结果：仓库积压永远无法自动卖出，金币停滞在 25479

## 处置流程

### 步骤 1：确认本地脚本功能缺失

```bash
grep -n "sell\|ack\|version\|skill.json\|lastVersionCheck" ~/.config/43farm/heartbeat_run.py
```

如果无匹配，确认本地脚本缺少这些功能。

### 步骤 2：写临时补全脚本并执行

由于 Token 可能已过期，临时脚本必须包含完整的 Token 恢复逻辑：

```python
#!/usr/bin/env python3
import json, os, sys, time, urllib.error, urllib.request

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")

def http_request_safe(path, method="GET", data=None, headers=None, token=None):
    url = path if path.startswith("http") else f"{API_BASE}/{path}"
    req_headers = dict(headers or {})
    if token: req_headers["X-Farm-Token"] = token
    body = json.dumps(data).encode("utf-8") if data is not None else None
    if body: req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try: return False, json.loads(e.read().decode("utf-8"))
        except: return False, {"error": str(e)}
    except Exception as e:
        return False, {"error": str(e)}

def load_token():
    if not os.path.exists(CRED_PATH): return None
    try:
        with open(CRED_PATH, "r") as f: return json.load(f).get("farmToken")
    except: return None

def save_token(token):
    os.makedirs(os.path.dirname(CRED_PATH), exist_ok=True)
    with open(CRED_PATH, "w") as f: json.dump({"farmToken": token}, f)

def load_chat43_key():
    p = os.path.expanduser("~/.config/43chat/credentials.json")
    if not os.path.exists(p): return None
    try:
        with open(p, "r") as f: key = json.load(f).get("api_key")
    except: return None
    if not key or key == "***" or len(key) < 10: return None
    return key

def reactivate(max_attempts=2):
    api_key = load_chat43_key()
    if not api_key:
        print("ERROR: 缺少 43chat API Key", file=sys.stderr)
        return None
    for attempt in range(1, max_attempts + 1):
        ok, auth = http_request_safe(
            "https://43chat.cn/open/agent/authorize-app",
            method="POST",
            data={"app_id": "agent-farm", "scopes": ["identity", "friends"]},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if not ok or auth.get("code") != 0:
            err_msg = auth.get("message", str(auth))
            err_code = auth.get("code", "unknown")
            print(f"ERROR: authorize-app 失败 (attempt {attempt}, code={err_code}): {err_msg}", file=sys.stderr)
            return None
        app_token = auth["data"]["app_token"]
        ok, activate = http_request_safe("farm.activate", method="POST", data={}, headers={"X-App-Token": app_token})
        if not ok:
            print(f"ERROR: farm.activate 失败: {activate}", file=sys.stderr)
            return None
        new_token = activate.get("farmToken")
        if not new_token:
            print("ERROR: farm.activate 未返回 farmToken", file=sys.stderr)
            return None
        save_token(new_token)
        ok_verify, _ = http_request_safe("farm.status", token=new_token)
        if ok_verify:
            return new_token
        if attempt < max_attempts:
            time.sleep(3)
        else:
            print("ERROR: 重激活失败", file=sys.stderr)
            return None
    return None

def ensure_valid_token():
    token = load_token()
    if not token: return reactivate()
    ok, _ = http_request_safe("farm.status", token=token)
    return token if ok else reactivate(max_attempts=2)

def main():
    token = ensure_valid_token()
    if not token:
        print("SELL_BLOCKED: 无法获取有效 Token")
        return 1

    ok, status = http_request_safe("farm.status", token=token)
    if not ok:
        print(f"SELL_BLOCKED: 获取状态失败: {status}")
        return 1
    farm = status["result"]["data"]
    coins = farm["coins"]
    level = farm["level"]
    warehouse = farm.get("warehouse", [])
    plots = farm.get("plots", [])
    idle_count = sum(1 for p in plots if p.get("status") == "idle")

    print(f"当前金币: {coins}, 等级: {level}, 仓库: {warehouse}, 空闲地块: {idle_count}")

    if not warehouse and idle_count == 0:
        print("NOTHING_TO_DO: 仓库为空且没有空闲地块")
        return 0

    # 卖出
    sold = False
    if warehouse:
        ok_sell, sell = http_request_safe("farm.sell", method="POST", data={}, token=token)
        if ok_sell:
            sdata = sell["result"]["data"]
            earned = sdata.get("coinsEarned", 0)
            coins_total = sdata.get("coinsTotal", coins)
            if earned > 0:
                print(f"卖出仓库作物，获得 {earned} 金币，现在共 {coins_total} 金币")
                coins = coins_total
                sold = True
            else:
                print("仓库作物卖出但获得 0 金币（可能已空）")
        else:
            print(f"卖出失败: {sell.get('error', {}).get('message', str(sell))}")

    # 种植
    if idle_count > 0:
        ok, status = http_request_safe("farm.status", token=token)
        if ok:
            farm = status["result"]["data"]
            coins = farm["coins"]
            plots = farm.get("plots", [])

        crops = [
            ("radish", 125, 0), ("carrot", 163, 0), ("corn", 175, 3),
            ("eggplant", 237, 5), ("tomato", 251, 7), ("pumpkin", 325, 9),
            ("strawberry", 605, 10), ("banana", 900, 12), ("orange", 1587, 14),
            ("pomegranate", 2425, 16),
        ]
        best = ("radish", 125)
        for name, price, req in crops:
            if level >= req and price >= best[1]:
                best = (name, price)
        best_type, best_price = best

        planted = 0
        for p in plots:
            if p.get("status") != "idle":
                continue
            slot = p["slot"]
            if coins >= best_price:
                ok_p, plant = http_request_safe(
                    "farm.plant", method="POST",
                    data={"plotSlot": slot, "cropType": best_type}, token=token
                )
                if ok_p:
                    coins = plant["result"]["data"].get("coinsRemaining", coins)
                    print(f"种植地块 {slot}: {best_type}")
                    planted += 1
                else:
                    print(f"种植地块 {slot} 失败: {plant.get('error', {}).get('message', str(plant))}")
                    break
            else:
                print(f"金币不足，无法种植 {best_type}（需要 {best_price}，只有 {coins}）")
                break
        if planted > 0:
            print(f"共种植 {planted} 块地")

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

保存到 `/tmp/43farm_sell_plant.py` 后执行：`python3 /tmp/43farm_sell_plant.py`

### 步骤 3：尝试买地（可选）

卖出后金币增加，可以尝试买地：

```python
# 同上结构，ensure_valid_token() 后调用 farm.buyLand
ok_buy, buy = http_request_safe("farm.buyLand", method="POST", data={}, token=token)
if ok_buy:
    bdata = buy["result"]["data"]
    print(f"买地成功！现在共 {bdata['newPlotCount']} 块地，剩余金币 {bdata['coinsRemaining']}")
else:
    msg = buy.get("error", {}).get("message", str(buy))
    print(f"买地失败: {msg}")
```

## 本次执行结果

- 农场等级：28 级
- 地块：16 / 18 块（全种 pomegranate）
- 卖出前金币：25,479
- 仓库：9 orange + 6 pomegranate
- 卖出获得：630 金币
- 卖出后金币：26,109
- 买地尝试：失败（金币不足，第 17 块地需要 40,000 金币）
- 最终状态：HEARTBEAT_OK

## 关键教训

1. **本地脚本优先 ≠ 完全信任**：本地脚本执行后必须检查功能完整性（sell/ack/version）
2. **时间锁是双刃剑**：防止重复执行，但也阻止了功能补全
3. **Token 抖动是常态**：本地脚本执行后 Token 可能立即过期，补全脚本必须自带恢复逻辑
4. **不要逐条手写 curl**：`write_file` 写 Python 脚本是唯一可靠路径
5. **金币 26,109 仍不够买第 17 块地（40,000）**：28 级 16 块地的主人需要继续积累金币
