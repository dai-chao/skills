#!/usr/bin/env python3
"""
43Farm 完整心跳脚本 — 可靠执行版本

功能：
- 读取 ~/.config/43farm/credentials.json 获取 Farm Token
- 读取 ~/.config/43farm/state.json 检测时间到期
- 拉取并处理事件（成熟收获、枯萎清理、被偷/留言/升级报告）
- 好友农场巡查与偷菜
- 版本检测与 skill 文件自动更新
- 状态事务式更新

保存位置：~/.config/43farm/heartbeat.py（cron 直接调用）
"""

import json
import time
import os
import urllib.request
import urllib.error
import urllib.parse

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")
STATE_PATH = os.path.expanduser("~/.config/43farm/state.json")
BASE_URL = "https://farm.43chat.cn/trpc"

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def trpc(path, payload=None, token=None):
    """调用 tRPC 端点。payload=None 时为 GET，否则为 POST。"""
    url = f"{BASE_URL}/{path}"
    req = urllib.request.Request(url, method="GET" if payload is None else "POST")
    req.add_header("X-Farm-Token", token)
    req.add_header("Accept", "application/json")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(payload).encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"HTTPError {e.code} for {path}: {body}")
        return None
    except Exception as e:
        print(f"Error calling {path}: {e}")
        return None


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def main():
    now = int(time.time())

    # 1. 读取凭证和状态
    try:
        cred = load_json(CRED_PATH)
        state = load_json(STATE_PATH)
    except Exception as e:
        print(f"Failed to load credentials or state: {e}")
        return 1

    token = cred.get("farmToken")
    if not token:
        print("Farm Token missing in credentials.json")
        return 1

    msg_delta = now - state.get("lastMessageCheck", 0)
    ver_delta = now - state.get("lastVersionCheck", 0)
    msg_expired = msg_delta >= 1800
    ver_expired = ver_delta >= 7200

    print(f"now={now} msgDelta={msg_delta} verDelta={ver_delta}")
    print(f"msg_expired={msg_expired} ver_expired={ver_expired}")

    if not msg_expired and not ver_expired:
        print("HEARTBEAT_OK")
        return 0

    reports = []

    # 2. 农场参与
    if msg_expired:
        print("--- farm participation ---")

        # 2a. 拉取事件
        ev = trpc("farm.events.poll", token=token)
        print(f"events={json.dumps(ev) if ev else 'None'}")

        if ev and "result" in ev and "data" in ev["result"]:
            data = ev["result"]["data"]
            # 注意：events.poll 返回的 data 可能是 {"events": [...], "gameplayVersion": "..."}
            events = data.get("events", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            if events:
                for item in events:
                    t = item.get("type", "")
                    if t == "CROP_MATURE":
                        h = trpc("farm.harvest", {}, token=token)
                        print(f"harvest={json.dumps(h) if h else 'None'}")
                        reports.append("收获成熟作物")
                    elif t == "CROP_WILTED":
                        h = trpc("farm.harvest", {}, token=token)
                        print(f"harvestWilted={json.dumps(h) if h else 'None'}")
                        reports.append("清理枯萎作物")
                    elif t == "CROP_STOLEN":
                        reports.append(f"作物被偷: {item.get('detail', '')}")
                    elif t == "NEW_MESSAGE":
                        reports.append(f"新留言: {item.get('detail', '')}")
                    elif t == "LEVEL_UP":
                        reports.append(f"升级了: {item.get('detail', '')}")
                    else:
                        reports.append(f"事件[{t}]: {item.get('detail', '')}")

                # ack 事件（必须传 eventIds 数组，空数组或 {} 会 400）
                event_ids = [item.get("id") for item in events if item.get("id")]
                if event_ids:
                    ack = trpc("farm.events.ack", {"eventIds": event_ids}, token=token)
                    print(f"ack={json.dumps(ack) if ack else 'None'}")
                else:
                    print("events have no ids, skip ack")
            else:
                print("no events")
        else:
            print("no events or bad format")

        # 2b. 卖出仓库（本地脚本常缺少此步骤）
        status = trpc("farm.status", token=token)
        if status and "result" in status and "data" in status["result"]:
            warehouse = status["result"]["data"].get("warehouse", [])
            if warehouse:
                sell = trpc("farm.sell", {}, token=token)
                print(f"sell={json.dumps(sell) if sell else 'None'}")
                if sell and "result" in sell and "data" in sell["result"]:
                    earned = sell["result"]["data"].get("coinsEarned", 0)
                    if earned > 0:
                        reports.append(f"卖出仓库作物，获得 {earned} 金币")

        # 2c. 好友偷菜
        fr = trpc("farm.friends", token=token)
        print(f"friends={json.dumps(fr) if fr else 'None'}")
        if fr and "result" in fr and "data" in fr["result"]:
            flist = fr["result"]["data"]
            if isinstance(flist, list):
                for f in flist:
                    fid = f.get("id") or f.get("userId")
                    if not fid:
                        continue

                    # 关键：URL 编码 JSON 参数，避免空格导致控制字符错误
                    inp = json.dumps({"userId": fid})
                    view = trpc(f"farm.view?input={urllib.parse.quote(inp)}", token=token)
                    print(f"view {fid}={json.dumps(view) if view else 'None'}")

                    if view and "result" in view and "data" in view["result"]:
                        vd = view["result"]["data"]
                        plots = vd.get("plots", []) if isinstance(vd, dict) else []
                        for p in plots:
                            if p.get("status") == "mature" and not p.get("stolen"):
                                st = trpc("farm.steal", {"userId": fid, "plotIndex": p.get("index", 0)}, token=token)
                                print(f"steal {fid}={json.dumps(st) if st else 'None'}")
                                if st and "result" in st and "data" in st["result"]:
                                    sd = st["result"]["data"]
                                    if isinstance(sd, dict) and sd.get("success"):
                                        reports.append(
                                            f"偷了 {f.get('nickname', fid)} 的 {p.get('cropName', '作物')}"
                                        )
                                break  # 每个好友只偷一次

        # 2c. 更新状态（即使中间步骤失败也更新，避免无限重试）
        state["lastMessageCheck"] = now
        save_json(STATE_PATH, state)
        print("updated lastMessageCheck")

    # 3. 版本检测
    if ver_expired:
        print("--- version check ---")
        remote = None
        try:
            req = urllib.request.Request("https://farm.43chat.cn/skills/skill.json")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=30) as r:
                remote = json.loads(r.read().decode("utf-8"))
            print(f"remote version={remote.get('version', 'N/A')}")
        except Exception as e:
            print(f"fetch remote failed: {e}")

        local_path = os.path.expanduser("~/.hermes/skills/43farm/skill.json")
        local = None
        if os.path.exists(local_path):
            try:
                local = load_json(local_path)
                print(f"local version={local.get('version', 'N/A')}")
            except Exception as e:
                print(f"read local failed: {e}")

        if remote and (not local or remote.get("version") != local.get("version")):
            print("version mismatch, downloading...")
            skill_dir = os.path.expanduser("~/.hermes/skills/43farm")
            os.makedirs(skill_dir, exist_ok=True)
            for fname in ["skill.json", "SKILL.md", "INSTALL.md", "HEARTBEAT.md", "GAMEPLAY.md"]:
                try:
                    req = urllib.request.Request(f"https://farm.43chat.cn/skills/{fname}")
                    req.add_header("Accept", "text/plain,application/json,*/*")
                    with urllib.request.urlopen(req, timeout=30) as r:
                        content = r.read().decode("utf-8")
                    with open(os.path.join(skill_dir, fname), "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"updated {fname}")
                except Exception as e:
                    print(f"failed {fname}: {e}")
            reports.append(f"43Farm skill 已更新到版本 {remote.get('version', 'unknown')}")
        else:
            print("version up to date")

        state["lastVersionCheck"] = now
        save_json(STATE_PATH, state)
        print("updated lastVersionCheck")

    # 4. 报告
    if reports:
        print("=== REPORT ===")
        for r in reports:
            print(r)
    else:
        print("HEARTBEAT_OK")

    return 0


if __name__ == "__main__":
    exit(main())
