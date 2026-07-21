#!/usr/bin/env python3
"""独立偷菜脚本 - 不检查时间锁，直接扫描好友并偷菜

用法：python3 ~/.hermes/skills/43farm-heartbeat-robust/scripts/steal_now.py

场景：
- 用户说"偷菜"但心跳脚本因 1800s 时间锁返回 HEARTBEAT_OK
- 用户想额外偷一轮，不等待 cron 周期
- 需要快速查看谁家有成熟作物可偷

注意：此脚本不更新 state.json，不收获/种植/卖出，只做偷菜。
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")


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


def check_friends(token):
    ok, data = http_request_safe("farm.friends", token=token)
    if not ok:
        return []
    friends_data = data.get("result", {}).get("data", [])
    if isinstance(friends_data, dict):
        friends = friends_data.get("friends", [])
    else:
        friends = friends_data
    targets = []
    for f in friends:
        if not f.get("farmActivated"):
            continue
        uid = f.get("userId") or f.get("id")
        if uid is None:
            continue
        name = f.get("name") or f"User {uid}"
        inp = json.dumps({"userId": uid}, separators=(",", ":"))
        ok2, view = http_request_safe(
            f"farm.view?input={urllib.parse.quote(inp)}", token=token
        )
        if not ok2:
            continue
        plots = view.get("result", {}).get("data", {}).get("plots", [])
        mature = [p for p in plots if p.get("status") == "mature"]
        if mature:
            targets.append({"userId": uid, "name": name, "mature": len(mature)})
    return targets


def try_steal(token, user_id):
    ok, data = http_request_safe(
        "farm.steal", method="POST", data={"userId": user_id}, token=token
    )
    if not ok:
        return None, data.get("error", {}).get("message", str(data))
    return data.get("result", {}).get("data", {}).get("stolen", []), None


def main():
    token = load_token()
    if not token:
        print("TOKEN_FAIL: 无法读取 ~/.config/43farm/credentials.json")
        return 1

    ok, _ = http_request_safe("farm.status", token=token)
    if not ok:
        print("TOKEN_INVALID: Farm Token 已过期，需要重新激活")
        return 1

    targets = check_friends(token)
    print(f"可偷好友: {len(targets)}")
    for t in targets:
        print(f"  {t['name']} (id={t['userId']}) - {t['mature']} 块成熟")

    stolen_any = False
    for t in targets:
        stolen, err = try_steal(token, t["userId"])
        if stolen:
            items = ", ".join(f"{s['cropType']} x{s['amount']}" for s in stolen)
            print(f"从 {t['name']} 偷了: {items}")
            stolen_any = True
        elif err:
            print(f"偷 {t['name']} 失败: {err}")

    if not stolen_any:
        print("没偷到任何菜")

    return 0


if __name__ == "__main__":
    sys.exit(main())
