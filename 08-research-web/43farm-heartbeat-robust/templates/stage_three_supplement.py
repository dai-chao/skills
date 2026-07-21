#!/usr/bin/env python3
"""43Farm 阶段三补全脚本 —— 在本地心跳脚本执行后补做缺失的卖出/种植/ACK。

正确顺序：
1. 确保 Token 有效（必要时重新激活）
2. 卖出仓库（{} 清仓）
3. 偷菜后的仓库也卖出（如果需要可再次查询并卖出）
4. 按金币选最优可负担作物种植所有 idle 地块
5. ACK 未读事件
6. 更新 state.json 时间戳

用法：
    python3 /tmp/stage_three_supplement.py
"""
import json
import os
import time
import urllib.error
import urllib.request

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")
CHAT_PATH = os.path.expanduser("~/.config/43chat/credentials.json")
STATE_PATH = os.path.expanduser("~/.config/43farm/state.json")

# 作物列表：（名称，种子价格，等级要求）
CROPS = [
    ("pomegranate", 2425, 16),
    ("orange", 1587, 14),
    ("banana", 900, 12),
    ("strawberry", 605, 10),
    ("pumpkin", 325, 9),
    ("tomato", 251, 7),
    ("eggplant", 237, 5),
    ("corn", 175, 3),
    ("carrot", 163, 0),
    ("radish", 125, 0),
]


def load_token():
    with open(CRED_PATH) as f:
        return json.load(f)["farmToken"]


def load_chat_key():
    if not os.path.exists(CHAT_PATH):
        return None
    with open(CHAT_PATH) as f:
        key = json.load(f).get("api_key")
    if not key or key == "***" or len(key) < 10:
        return None
    return key


def http_request(path, method="GET", data=None, token=None, extra_headers=None):
    url = path if path.startswith("http") else f"{API_BASE}/{path}"
    headers = {}
    if token:
        headers["X-Farm-Token"] = token
    if data is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
    if extra_headers:
        headers.update(extra_headers)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return False, json.loads(e.read().decode("utf-8"))


def ensure_valid_token():
    """确保 Farm Token 有效，必要时通过 43chat 重新激活。"""
    token = load_token()
    ok, _ = http_request("farm.status", token=token)
    if ok:
        return token

    print("Farm token expired, reactivating...")
    api_key = load_chat_key()
    if not api_key:
        print("HEARTBEAT_BLOCKED: 43chat API key missing or masked")
        return None

    ok, auth = http_request(
        "https://43chat.cn/open/agent/authorize-app",
        method="POST",
        data={"app_id": "agent-farm", "scopes": ["identity", "friends"]},
        extra_headers={"Authorization": f"Bearer {api_key}"},
    )
    if not ok or auth.get("code") != 0:
        print(f"HEARTBEAT_BLOCKED: authorize-app failed: {auth}")
        return None

    app_token = auth["data"]["app_token"]
    ok, activate = http_request(
        "farm.activate",
        method="POST",
        data={},
        extra_headers={"X-App-Token": app_token},
    )
    if not ok:
        print(f"HEARTBEAT_BLOCKED: farm.activate failed: {activate}")
        return None

    new_token = activate.get("farmToken")
    if not new_token:
        print("HEARTBEAT_BLOCKED: farm.activate did not return farmToken")
        return None

    # 保存新 Token
    with open(CRED_PATH, "w") as f:
        json.dump({"farmToken": new_token}, f)

    # 验证
    ok, _ = http_request("farm.status", token=new_token)
    if ok:
        return new_token
    print("HEARTBEAT_BLOCKED: new token not immediately valid")
    return None


def get_status(token):
    ok, status = http_request("farm.status", token=token)
    if not ok:
        raise RuntimeError(f"farm.status failed: {status}")
    return status["result"]["data"]


def sell_all(token):
    """清仓卖出仓库所有作物。"""
    ok, resp = http_request("farm.sell", method="POST", data={}, token=token)
    if not ok:
        print(f"Sell failed: {resp}")
        return 0
    earned = resp.get("result", {}).get("data", {}).get("coinsEarned", 0)
    return earned


def pick_best_crop(level, coins):
    """选择当前等级能种的最贵且负担得起的作物。"""
    for name, price, req_level in CROPS:
        if level >= req_level and price <= coins:
            return name, price
    return None, 0


def plant_idle(token, farm):
    """种植所有空闲地块。"""
    level = farm["level"]
    coins = farm["coins"]
    plots = farm["plots"]
    best, price = pick_best_crop(level, coins)
    if not best:
        print(f"No affordable crop (level={level}, coins={coins})")
        return 0

    planted = 0
    for p in plots:
        if p.get("status") == "idle" and coins >= price:
            slot = p["slot"]
            ok, resp = http_request(
                "farm.plant",
                method="POST",
                data={"plotSlot": slot, "cropType": best},
                token=token,
            )
            if ok:
                coins -= price
                planted += 1
                print(f"Planted slot {slot}: {best} (coins left {coins})")
            else:
                print(f"Plant slot {slot} failed: {resp}")
    return planted


def ack_events(token):
    """ACK 所有未读事件。"""
    ok, poll = http_request("farm.events.poll", token=token)
    if not ok:
        print(f"Poll failed: {poll}")
        return 0
    events = poll.get("result", {}).get("data", {}).get("events", [])
    event_ids = [e["id"] for e in events]
    if not event_ids:
        print("No events to ack")
        return 0
    ok, ack = http_request(
        "farm.events.ack", method="POST", data={"eventIds": event_ids}, token=token
    )
    if not ok:
        print(f"Ack failed: {ack}")
        return 0
    count = ack.get("result", {}).get("data", {}).get("ackedCount", 0)
    print(f"Acked {count} events")
    return count


def update_state():
    state = {}
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            state = json.load(f)
    now = int(time.time())
    state["lastMessageCheck"] = now
    state["lastVersionCheck"] = now
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)
    print(f"State updated: lastMessageCheck={now}, lastVersionCheck={now}")


def main():
    token = ensure_valid_token()
    if not token:
        return 1

    # 1. 先卖出（本地脚本可能遗漏或顺序错误）
    farm = get_status(token)
    print(f"Before: coins={farm['coins']} warehouse={farm['warehouse']}")
    earned = sell_all(token)
    print(f"Sell earned: {earned} coins")

    # 2. 再种植（利用卖出后的金币）
    farm = get_status(token)
    planted = plant_idle(token, farm)
    print(f"Planted {planted} plots")

    # 3. ACK 事件
    ack_events(token)

    # 4. 更新状态
    update_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
