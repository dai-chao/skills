#!/usr/bin/env python3
"""重新激活农场 Token

用法：python3 ~/.hermes/skills/43farm-heartbeat-robust/scripts/activate_farm.py

场景：
- farm.status 返回 401，Token 过期
- 43chat API Key 被重置后需要重新激活
- 自动完成 authorize-app → farm.activate → 验证 全流程

注意：此脚本读取 ~/.config/43chat/credentials.json 中的 api_key，
      如果 api_key 被服务器掩码为 ***，则激活失败，需要主人手动更新 Key。
"""
import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")
CHAT_PATH = os.path.expanduser("~/.config/43chat/credentials.json")


def http_request_safe(path, method="GET", data=None, headers=None, token=None):
    url = f"{API_BASE}/{path}" if not path.startswith("http") else path
    req_headers = dict(headers or {})
    if token:
        req_headers["X-Farm-Token"] = token
    if data is not None:
        req_headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_body = {"error": str(e)}
        return False, err_body
    except Exception as e:
        return False, {"error": str(e)}


def load_chat43_key():
    if not os.path.exists(CHAT_PATH):
        return None
    try:
        with open(CHAT_PATH, "r") as f:
            key = json.load(f).get("api_key")
    except Exception:
        return None
    if not key or key == "***" or len(key) < 10:
        return None
    return key


def save_token(token):
    os.makedirs(os.path.dirname(CRED_PATH), exist_ok=True)
    with open(CRED_PATH, "w") as f:
        json.dump({"farmToken": token}, f)


def main():
    api_key = load_chat43_key()
    if not api_key:
        print("ERROR: 缺少 43chat API Key 或 Key 已被服务器掩码为 ***")
        print(f"  请检查 {CHAT_PATH}")
        print("  如果 api_key 是 ***，需要主人手动更新为完整 Key")
        return 1

    # 1. authorize-app
    ok, auth = http_request_safe(
        "https://43chat.cn/open/agent/authorize-app",
        method="POST",
        data={"app_id": "agent-farm", "scopes": ["identity", "friends"]},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    if not ok or auth.get("code") != 0:
        print(f"authorize-app 失败: {auth}")
        return 1

    app_token = auth["data"]["app_token"]
    print(f"app_token 获取成功")

    # 2. farm.activate
    ok, activate = http_request_safe(
        "farm.activate",
        method="POST",
        data={},
        headers={"X-App-Token": app_token},
    )
    if not ok:
        print(f"farm.activate 失败: {activate}")
        return 1

    new_token = activate.get("farmToken")
    if not new_token:
        print(f"farm.activate 未返回 token: {activate}")
        return 1

    print(f"新 token 获取成功 (长度 {len(new_token)})")
    save_token(new_token)

    # 3. 验证
    ok_verify, status = http_request_safe("farm.status", token=new_token)
    if ok_verify:
        farm = status["result"]["data"]
        print(f"验证成功！金币: {farm['coins']}, 等级: {farm['level']}, 地块: {len(farm.get('plots', []))}")
        return 0
    else:
        print(f"验证失败: {status}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
