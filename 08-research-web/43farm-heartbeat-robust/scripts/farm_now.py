#!/usr/bin/env python3
"""强制收菜+种植脚本 - 不检查时间锁，直接执行收获/卖出/种植

用法：python3 ~/.hermes/skills/43farm-heartbeat-robust/scripts/farm_now.py

场景：
- 用户说"收菜偷菜"但心跳脚本因 1800s 时间锁返回 HEARTBEAT_OK
- 需要立即收获成熟作物、卖出仓库、种植空闲地块
- 金币不足时自动降级种植次优作物（而非静默失败）

注意：此脚本不更新 state.json，不偷菜，只做自己的农场管理。
"""
import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")

CROPS = [
    ("radish", 125, 0),
    ("carrot", 163, 0),
    ("corn", 175, 3),
    ("eggplant", 237, 5),
    ("tomato", 251, 7),
    ("pumpkin", 325, 9),
    ("strawberry", 605, 10),
    ("banana", 900, 12),
    ("orange", 1587, 14),
    ("pomegranate", 2425, 16),
]


def http_request(path, method="GET", data=None, headers=None, token=None):
    url = f"{API_BASE}/{path}"
    req_headers = dict(headers or {})
    if token:
        req_headers["X-Farm-Token"] = token
    if data is not None:
        req_headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_request_safe(path, method="GET", data=None, headers=None, token=None):
    try:
        return True, http_request(path, method, data, headers, token)
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_body = {"error": str(e)}
        return False, err_body
    except Exception as e:
        return False, {"error": str(e)}


def load_token():
    if not os.path.exists(CRED_PATH):
        return None
    try:
        with open(CRED_PATH, "r") as f:
            return json.load(f).get("farmToken")
    except Exception:
        return None


def pick_best_crop(level, max_price=None):
    """根据等级和金币上限返回最优可种植作物"""
    affordable = [(n, p) for n, p, r in CROPS if level >= r and (max_price is None or p <= max_price)]
    if not affordable:
        return None, None
    affordable.sort(key=lambda x: x[1], reverse=True)
    return affordable[0]


def main():
    token = load_token()
    if not token:
        print("TOKEN_FAIL: 无法读取 ~/.config/43farm/credentials.json")
        return 1

    ok, status = http_request_safe("farm.status", token=token)
    if not ok:
        print(f"状态获取失败: {status}")
        return 1

    farm = status["result"]["data"]
    coins = farm["coins"]
    level = farm["level"]
    plots = farm.get("plots", [])
    warehouse = farm.get("warehouse", [])

    print(f"金币: {coins}, 等级: {level}, 地块: {len(plots)}")
    print(f"仓库: {warehouse}")

    # 1. 收获成熟/枯萎的
    harvestable = [p for p in plots if p.get("status") in ("mature", "withered")]
    if harvestable:
        ok, h = http_request_safe("farm.harvest", method="POST", data={}, token=token)
        if ok:
            hdata = h["result"]["data"]
            count = hdata.get("harvestedCount", 0)
            crops = hdata.get("crops", [])
            xp = hdata.get("xpAwarded", 0)
            if count > 0:
                crop_str = ", ".join(f"{c['quantity']} {c['cropType']}" for c in crops)
                print(f"收获 {count} 块地: {crop_str}, +{xp} XP")
                # 刷新状态
                ok, status = http_request_safe("farm.status", token=token)
                if ok:
                    farm = status["result"]["data"]
                    coins = farm["coins"]
                    plots = farm.get("plots", [])
                    warehouse = farm.get("warehouse", [])
        else:
            print(f"收获失败: {h}")

    # 2. 卖仓库
    if warehouse:
        ok, s = http_request_safe("farm.sell", method="POST", data={}, token=token)
        if ok:
            sdata = s["result"]["data"]
            earned = sdata.get("coinsEarned", 0)
            if earned > 0:
                print(f"卖出仓库: +{earned} 金币")
                coins = sdata.get("coinsTotal", coins)
        else:
            print(f"卖出失败: {s}")

    print(f"当前金币: {coins}")

    # 3. 种作物（优先最优，金币不足时降级）
    idle = [p for p in plots if p.get("status") == "idle"]
    print(f"空闲地块: {len(idle)}")

    planted = 0
    for p in idle:
        slot = p["slot"]
        crop_name, crop_price = pick_best_crop(level, coins)
        if crop_name is None or coins < crop_price:
            print(f"金币不足，无法种植任何作物（当前 {coins}，最低 {crop_price}）")
            break

        ok, plant = http_request_safe(
            "farm.plant", method="POST",
            data={"plotSlot": slot, "cropType": crop_name}, token=token
        )
        if ok:
            coins = plant["result"]["data"].get("coinsRemaining", coins)
            print(f"种植地块 {slot}: {crop_name}, 剩余金币 {coins}")
            planted += 1
        else:
            print(f"种植地块 {slot} 失败: {plant}")
            break

    print(f"共种植 {planted} 块地")
    return 0


if __name__ == "__main__":
    sys.exit(main())
