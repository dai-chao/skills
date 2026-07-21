#!/usr/bin/env python3
"""
阶段三补做脚本：当本地心跳脚本只更新了 lastMessageCheck，或缺少 farm.sell / farm.events.ack 时使用。
执行顺序：卖出仓库 -> 种植 idle 地块 -> ack 事件 -> 更新 state.json。
"""
import json, urllib.request, os, time

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")
CHAT_PATH = os.path.expanduser("~/.config/43chat/credentials.json")
STATE_PATH = os.path.expanduser("~/.config/43farm/state.json")

def load_token():
    with open(CRED_PATH) as f:
        return json.load(f)["farmToken"]

def load_chat_key():
    if not os.path.exists(CHAT_PATH):
        return None
    with open(CHAT_PATH) as f:
        key = json.load(f).get("api_key")
    if not key or key == "***" or len(key) < 10 or "..." in key:
        return None
    return key

def save_token(new_token):
    with open(CRED_PATH, "w") as f:
        json.dump({"farmToken": new_token}, f)

def http_request(path, method="GET", data=None, headers=None, token=None):
    url = path if path.startswith("http") else f"{API_BASE}/{path}"
    h = {}
    if token:
        h["X-Farm-Token"] = token
    if headers:
        h.update(headers)
    if data is not None:
        h.setdefault("Content-Type", "application/json")
        body = json.dumps(data).encode("utf-8")
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return False, json.loads(e.read().decode("utf-8"))

def ensure_valid_token():
    token = load_token()
    ok, _ = http_request("farm.status", token=token)
    if ok:
        return token

    api_key = load_chat_key()
    if not api_key:
        print("ERROR: 43chat API Key 缺失或已被掩码，无法重新激活")
        return None

    ok1, auth = http_request(
        "https://43chat.cn/open/agent/authorize-app",
        method="POST",
        data={"app_id": "agent-farm", "scopes": ["identity", "friends"]},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    if not ok1 or auth.get("code") != 0:
        print(f"ERROR: authorize-app 失败: {auth}")
        return None

    app_token = auth["data"]["app_token"]
    ok2, activate = http_request(
        "farm.activate",
        method="POST",
        data={},
        headers={"X-App-Token": app_token},
    )
    if not ok2:
        print(f"ERROR: farm.activate 失败: {activate}")
        return None

    new_token = activate.get("farmToken")
    if not new_token:
        print("ERROR: farm.activate 未返回 farmToken")
        return None

    save_token(new_token)
    ok3, _ = http_request("farm.status", token=new_token)
    if not ok3:
        print("WARNING: 新 Token 验证失败，可能后端不同步")
    return new_token

def main():
    token = ensure_valid_token()
    if not token:
        print("HEARTBEAT_BLOCKED: Token 无法恢复")
        exit(1)

    # 1. 检查状态
    ok, status = http_request("farm.status", token=token)
    if not ok:
        print("HEARTBEAT_BLOCKED: 无法获取农场状态")
        exit(1)

    farm = status["result"]["data"]
    coins = farm["coins"]
    level = farm["level"]
    plots = farm.get("plots", [])
    warehouse = farm.get("warehouse", [])

    # 2. 卖出仓库
    if warehouse:
        ok_sell, sell_resp = http_request("farm.sell", method="POST", data={}, token=token)
        if ok_sell:
            earned = sell_resp.get("result", {}).get("data", {}).get("coinsEarned", 0)
            coins += earned
            print(f"Sold warehouse: +{earned} coins")
        else:
            print(f"Sell failed: {sell_resp}")

    # 3. 种植 idle 地块
    crops = [
        ("pomegranate", 2425, 16),
        ("orange", 1587, 14),
        ("banana", 900, 12),
        ("strawberry", 605, 10),
        ("pumpkin", 325, 9),
    ]
    best = ("radish", 125)
    for name, price, req in crops:
        if level >= req and price >= best[1]:
            best = (name, price)

    idle_plots = [p for p in plots if p.get("status") == "idle"]
    for p in idle_plots:
        if coins < best[1]:
            break
        slot = p["slot"]
        ok_plant, plant_resp = http_request(
            "farm.plant",
            method="POST",
            data={"plotSlot": slot, "cropType": best[0]},
            token=token,
        )
        if ok_plant:
            coins -= best[1]
            print(f"Planted slot {slot}: {best[0]}")
        else:
            print(f"Plant slot {slot} failed: {plant_resp}")

    # 4. ack 事件
    ok_poll, poll_resp = http_request("farm.events.poll", token=token)
    if ok_poll:
        events = poll_resp.get("result", {}).get("data", {}).get("events", [])
        event_ids = [e["id"] for e in events]
        if event_ids:
            ok_ack, ack_resp = http_request(
                "farm.events.ack",
                method="POST",
                data={"eventIds": event_ids},
                token=token,
            )
            acked = ack_resp.get("result", {}).get("data", {}).get("ackedCount", 0) if ok_ack else 0
            print(f"ACKed {acked} events")

    # 5. 更新 state.json
    now = int(time.time())
    state = {}
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            state = json.load(f)
    state["lastMessageCheck"] = now
    state["lastVersionCheck"] = now
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)
    print(f"State updated: lastMessageCheck={now}, lastVersionCheck={now}")

if __name__ == "__main__":
    main()
