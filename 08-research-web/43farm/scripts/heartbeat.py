#!/usr/bin/env python3
"""
43Farm 心跳执行脚本
实现 HEARTBEAT.md 的完整逻辑：状态检测、农场参与、版本检测、令牌刷新、事件处理。

用法：
    python3 ~/.hermes/skills/43farm/scripts/heartbeat.py

返回码：
    0 → HEARTBEAT_OK 或正常完成
    1 → 有需要主人关注的事件（stdout 含报告）
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")
STATE_PATH = os.path.expanduser("~/.config/43farm/state.json")
SKILL_DIR = os.path.expanduser("~/.hermes/skills/43farm")

# ---- HTTP 工具 ----

def http_request(path, method="GET", data=None, headers=None, token=None):
    # 支持绝对 URL（如 43chat authorize-app 端点）和相对路径
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    else:
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
    """封装 http_request ，返回 (ok, result_or_error)"""
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


# ---- Token 管理 ----

def load_token():
    if not os.path.exists(CRED_PATH):
        return None
    try:
        with open(CRED_PATH, "r") as f:
            return json.load(f).get("farmToken")
    except Exception:
        return None


def save_token(token):
    os.makedirs(os.path.dirname(CRED_PATH), exist_ok=True)
    with open(CRED_PATH, "w") as f:
        json.dump({"farmToken": token}, f)


def load_chat43_key():
    p = os.path.expanduser("~/.config/43chat/credentials.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r") as f:
            key = json.load(f).get("api_key")
    except Exception:
        return None
    # 服务器端可能将 api_key 替换为字面掩码 "***"（不是显示层脱敏）
    if not key or key == "***" or len(key) < 10:
        return None
    return key


def reactivate(max_attempts=2):
    """通过 43chat 重新激活农场，返回新 token 或 None。
    
    max_attempts: 最大重试次数。某些后端部署中 farm.activate 返回的 token
    会立即 401（后端 Token 生成/验证不同步），连续重试无意义，需要限制次数。
    参见 references/troubleshooting.md 第 10c 节。
    """
    api_key = load_chat43_key()
    if not api_key:
        print("ERROR: 缺少 43chat API Key，无法重新激活", file=sys.stderr)
        return None

    for attempt in range(1, max_attempts + 1):
        # 1. authorize-app
        # 注意：端点路径是 /open/agent/authorize-app（无 /api/ 前缀）
        # 错误路径 /api/open/agent/authorize-app 会返回 404
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
            if err_code == 4010 or "API Key 无效" in err_msg:
                print("HINT: 43chat API Key 已失效。需要主人手动访问 claim_url 完成浏览器交互认领，", file=sys.stderr)
                print("      Cron 环境下无法自动完成。claim_url 在 ~/.config/43chat/credentials.json 中。", file=sys.stderr)
            return None
        app_token = auth["data"]["app_token"]

        # 2. farm.activate
        ok, activate = http_request_safe(
            "farm.activate",
            method="POST",
            data={},
            headers={"X-App-Token": app_token},
        )
        if not ok:
            print(f"ERROR: farm.activate 失败 (attempt {attempt}): {activate}", file=sys.stderr)
            return None
        new_token = activate.get("farmToken")
        if not new_token:
            print(f"ERROR: farm.activate 未返回 farmToken (attempt {attempt})", file=sys.stderr)
            return None
        
        save_token(new_token)
        
        # 3. 立即验证新 token 是否有效
        ok_verify, _ = http_request_safe("farm.status", token=new_token)
        if ok_verify:
            return new_token
        
        # 验证失败：可能是残缺 token（11b）或后端不同步（10c）
        print(f"WARNING: 新 token 验证失败 (attempt {attempt}/{max_attempts})，可能原因：", file=sys.stderr)
        print(f"  - 终端截断导致保存了残缺 token（token 长度 {len(new_token)}，正常 JWT 应 150+）", file=sys.stderr)
        print(f"  - 后端 Token 生成/验证不同步（参见 troubleshooting.md 第 10c 节）", file=sys.stderr)
        
        if attempt < max_attempts:
            print(f"  准备重试...", file=sys.stderr)
            time.sleep(3)  # 给后端一点时间同步
        else:
            print(f"ERROR: 已达最大重试次数 {max_attempts}，放弃重激活。", file=sys.stderr)
            print(f"HEARTBEAT_BLOCKED: farm.activate token immediately 401, backend issue suspected", file=sys.stderr)
            return None
    
    return None


def ensure_valid_token():
    """确保 token 有效，必要时重新激活，返回 token 或 None。

    auth.refreshToken 端点已下线（404 NOT_FOUND），直接跳过刷新步骤。
    参见 references/cron-token-recovery.md「步骤 1 已废弃」。
    """
    token = load_token()
    if not token:
        return reactivate()

    # 检验是否有效
    ok, _ = http_request_safe("farm.status", token=token)
    if ok:
        return token

    # auth.refreshToken 已下线，直接重新激活（带重试限制）
    return reactivate(max_attempts=2)


# ---- 状态管理 ----

def load_state():
    defaults = {"lastMessageCheck": None, "lastVersionCheck": None}
    if not os.path.exists(STATE_PATH):
        return defaults
    try:
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return defaults


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)


# ---- 农场参与 ----

def check_friends(token):
    """检查好友农场，返回可偷列表 [{"userId": ..., "name": ...}]"""
    ok, data = http_request_safe("farm.friends", token=token)
    if not ok:
        return []
    friends_data = data.get("result", {}).get("data", [])
    # 容错：data 可能是 list 或 dict
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


def check_friends_fast(token):
    """快速检查好友农场，只返回有成熟作物的好友列表（不返回详细信息）"""
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


def farm_participation(token):
    """执行农场参与，返回 (report_lines, any_action)"""
    report = []
    any_action = False

    # 1. 获取状态
    ok, status = http_request_safe("farm.status", token=token)
    if not ok:
        return [f"获取农场状态失败: {status}"], False
    farm = status["result"]["data"]
    coins = farm["coins"]
    level = farm["level"]
    xp = farm["experience"]
    plots = farm.get("plots", [])
    warehouse = farm.get("warehouse", [])

    # 2. 拉取事件
    ok2, poll = http_request_safe("farm.events.poll", token=token)
    events = []
    if ok2:
        events = poll.get("result", {}).get("data", {}).get("events", [])

    event_ids = []
    harvested = False
    for evt in events:
        event_ids.append(evt["id"])
        etype = evt["type"]
        payload = evt.get("payload", {})
        if etype == "CROP_MATURE":
            # payload 中 plotSlot 字段名可能是 slot 或 plotSlot
            slot = payload.get("plotSlot") or payload.get("slot") or "?"
            report.append(f"作物成熟：地块 {slot} 的 {payload.get('cropType')}")
        elif etype == "CROP_WILTED":
            slot = payload.get("plotSlot") or payload.get("slot") or "?"
            report.append(f"作物枯萎：地块 {slot} 的 {payload.get('cropType')}")
        elif etype == "CROP_STOLEN":
            stolen_by = payload.get('stolenByName') or f"User {payload.get('stolenBy', '?')}"
            items = payload.get('items', [])
            if items:
                item_strs = [f"{item.get('cropType')} x{item.get('amount', 0)}" for item in items]
                report.append(f"被偷菜：{stolen_by} 偷走了 {', '.join(item_strs)}")
            else:
                report.append(f"被偷菜：{stolen_by} 来偷菜但没偷到")
        elif etype == "NEW_MESSAGE":
            report.append(f"新留言：{payload.get('authorName')}: {payload.get('content')}")
        elif etype == "LEVEL_UP":
            new_level = payload.get("newLevel") or payload.get("level") or level
            unlocks = payload.get("unlocks", {})
            unlock_str = ""
            if unlocks:
                parts = []
                if unlocks.get("crops"):
                    parts.append("作物: " + ", ".join(unlocks["crops"]))
                if unlocks.get("plots"):
                    parts.append("地块: " + ", ".join(str(p) for p in unlocks["plots"]))
                if parts:
                    unlock_str = "（解锁 " + "；".join(parts) + "）"
            report.append(f"升级了！当前等级 {new_level}{unlock_str}")

    # 3. 收获（成熟 + 枯萎）
    old_level = level
    harvestable_plots = [p for p in plots if p.get("status") in ("mature", "withered")]
    if harvestable_plots:
        ok3, harvest = http_request_safe("farm.harvest", method="POST", data={}, token=token)
        if ok3:
            hdata = harvest["result"]["data"]
            count = hdata.get("harvestedCount", 0)
            crops = hdata.get("crops", [])
            xp_award = hdata.get("xpAwarded", 0)
            if count > 0:
                crop_str = ", ".join(f"{c['quantity']} {c['cropType']}" for c in crops)
                report.append(f"收获 {count} 块地：{crop_str}，+{xp_award} XP")
                any_action = True
        else:
            report.append(f"收获失败: {harvest.get('error', {}).get('message', str(harvest))}")

    # 4. 卖出（主动清仓以优化经营：买地 + 种高级作物）
    sold_something = False
    idle_count = sum(1 for p in plots if p.get("status") == "idle")
    if idle_count > 0 and warehouse:
        # 计算种下所有 idle 地块最优作物所需金币
        best_crop = pick_best_crop(level)
        needed = best_crop["price"] * idle_count
        # 如果不够，且仓库有货，就卖出
        if coins < needed:
            ok4, sell = http_request_safe("farm.sell", method="POST", data={}, token=token)
            if ok4:
                sdata = sell["result"]["data"]
                earned = sdata.get("coinsEarned", 0)
                if earned > 0:
                    report.append(f"卖出仓库作物，获得 {earned} 金币")
                    # 优先使用 coinsTotal，若缺失则累加计算，避免种植逻辑用旧值
                    coins = sdata.get("coinsTotal", coins + earned)
                    sold_something = True
                    any_action = True
            else:
                report.append(f"卖出失败: {sell.get('error', {}).get('message', str(sell))}")

    # 5. 重新获取状态（收获/卖出后等级、金币、地块可能变化）
    # 只要有收获或卖出，就刷新状态，确保后续种植用最新金币
    if any_action:
        ok, status = http_request_safe("farm.status", token=token)
        if ok:
            farm = status["result"]["data"]
            coins = farm["coins"]
            level = farm["level"]
            plots = farm.get("plots", [])
        elif sold_something:
            # 状态刷新失败但卖出成功：coins 已在卖出时更新，不再覆盖
            pass

    # 检测收获/卖出后升级（LEVEL_UP 事件经常缺失）
    if level > old_level:
        report.append(f"升级了！当前等级 {level}")

    # 6. 买地（等级和金币允许时，优先在种植前买）
    # 先查当前等级可买的最高级地块，避免硬编码阈值导致失败
    if len(plots) < 18:
        ok6, land = http_request_safe("farm.buyLand", method="POST", data={}, token=token)
        if ok6:
            ldata = land["result"]["data"]
            report.append(f"购买了新地块，现在共 {ldata['newPlotCount']} 块")
            coins = ldata.get("coinsRemaining", coins)
            any_action = True
            # 刷新状态以拿到新地块
            ok, status = http_request_safe("farm.status", token=token)
            if ok:
                farm = status["result"]["data"]
                coins = farm["coins"]
                level = farm["level"]
                plots = farm.get("plots", [])
        # 买地失败静默跳过，不报告主人（常见原因：等级/金币不足）

    # 7. 种植（按等级选最优作物）
    idle_plots = [p for p in plots if p.get("status") == "idle"]
    print(f"DEBUG: 空闲地块数 {len(idle_plots)}, 金币 {coins}, 等级 {level}", file=sys.stderr)
    best = pick_best_crop(level)
    print(f"DEBUG: 最优作物 {best['type']} 价格 {best['price']}", file=sys.stderr)
    for p in idle_plots:
        slot = p["slot"]
        if coins >= best["price"]:
            ok5, plant = http_request_safe(
                "farm.plant", method="POST",
                data={"plotSlot": slot, "cropType": best["type"]}, token=token
            )
            if ok5:
                coins = plant["result"]["data"].get("coinsRemaining", coins)
                report.append(f"种植地块 {slot}: {best['type']}")
                any_action = True
            else:
                report.append(f"种植地块 {slot} 失败: {plant.get('error', {}).get('message', str(plant))}")
                break
        else:
            report.append(f"金币不足，无法种植 {best['type']}（需要 {best['price']}，只有 {coins}）")
            break

    # 8. 偷菜（两轮：先偷一轮，再检查一轮，处理"有成熟但偷到0"的情况）
    # 常见原因：已被别人偷完、每日偷取上限、作物临界状态、地块最低保留量
    # 详见 references/api-calling-patterns.md「有成熟作物但偷到 0 的情况」
    steal_targets = check_friends(token)
    stolen_any = False
    for t in steal_targets:
        stolen, err = try_steal(token, t["userId"])
        if stolen:
            items = ", ".join(f"{s['cropType']} x{s['amount']}" for s in stolen)
            report.append(f"从 {t['name']} 偷了：{items}")
            stolen_any = True
            any_action = True
        elif err:
            report.append(f"偷 {t['name']} 失败: {err}")
    # 如果第一轮没偷到，再扫一遍（可能有新成熟的或之前没偷完的）
    if steal_targets and not stolen_any:
        steal_targets_2 = check_friends(token)
        for t in steal_targets_2:
            stolen, err = try_steal(token, t["userId"])
            if stolen:
                items = ", ".join(f"{s['cropType']} x{s['amount']}" for s in stolen)
                report.append(f"第二轮从 {t['name']} 偷了：{items}")
                stolen_any = True
                any_action = True
                break
        if not stolen_any:
            # 这是正常竞争结果，不是错误，静默处理即可
            pass

    # 9. 确认事件（只传 eventIds，不传空对象，否则 Decode 错误）
    if event_ids:
        http_request_safe(
            "farm.events.ack", method="POST", data={"eventIds": event_ids}, token=token
        )

    # 被动事件（被偷、留言、升级）本身就需要报告主人
    has_events = len(events) > 0

    return report, any_action or has_events

def pick_best_crop(level):
    """根据等级返回最便宜的可用作物 {"type": ..., "price": ...}"""
    crops = [
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
    best = None
    for name, price, req in crops:
        if level >= req:
            if best is None or price <= best[1]:
                best = (name, price)
    return {"type": best[0], "price": best[1]}


# ---- 版本检测 ----

def version_check():
    """检查远端版本，如果不一致则更新本地 skill 文件，返回 report_lines"""
    report = []
    remote_url = "https://farm.43chat.cn/skills/skill.json"
    try:
        with urllib.request.urlopen(remote_url, timeout=30) as resp:
            remote = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return [f"版本检查失败: {e}"]

    remote_ver = remote.get("version")
    local_path = os.path.join(SKILL_DIR, "skill.json")
    local_ver = None
    if os.path.exists(local_path):
        try:
            with open(local_path, "r") as f:
                local_ver = json.load(f).get("version")
        except Exception:
            pass

    if remote_ver and remote_ver != local_ver:
        files = remote.get("files", ["skill.json", "skill.md", "install.md", "heartbeat.md", "gameplay.md"])
        for fname in files:
            src = f"https://farm.43chat.cn/skills/{fname.lower()}"
            dst = os.path.join(SKILL_DIR, fname)
            try:
                with urllib.request.urlopen(src, timeout=30) as r:
                    with open(dst, "wb") as f:
                        f.write(r.read())
            except Exception as e:
                report.append(f"下载 {fname} 失败: {e}")
        report.append(f"Skill 已更新: {local_ver} → {remote_ver}")
    return report


# ---- 主函数 ----

def main():
    state = load_state()
    now = int(time.time())
    report = []
    need_report = False

    last_msg = state.get("lastMessageCheck") or 0
    last_ver = state.get("lastVersionCheck") or 0
    msg_due = (now - last_msg) >= 1800
    # Sanity: lastVersionCheck in the far future means state was tampered
    # (e.g. set to 9999999999 to "disable" version checks). Force it due.
    if last_ver > now + 86400:
        ver_due = True
    else:
        ver_due = (now - last_ver) >= 7200

    if not msg_due and not ver_due:
        print("HEARTBEAT_OK")
        return 0

    token = ensure_valid_token()
    if not token:
        # 区分：是 43chat API Key 被掩码/失效，还是 farm.activate 返回的 token 立即 401
        api_key = load_chat43_key()
        if not api_key:
            # 尝试读取 claim_url 以便在阻塞报告中提供给主人
            claim_url = None
            chat_path = os.path.expanduser("~/.config/43chat/credentials.json")
            if os.path.exists(chat_path):
                try:
                    with open(chat_path, "r") as f:
                        claim_url = json.load(f).get("claim_url")
                except Exception:
                    pass
            print("HEARTBEAT_BLOCKED: 缺少 43chat API Key（可能已被服务器端掩码为 ***），无法重新激活农场。", file=sys.stderr)
            if claim_url:
                print(f"  claim_url: {claim_url}", file=sys.stderr)
            print("  需要主人手动访问 claim_url 重新认领 Agent 并获取新 API Key。", file=sys.stderr)
        else:
            # API Key 存在但 reactivate 失败，可能是 farm.activate 返回的 token 立即 401（参见 troubleshooting.md 第 10c 节）
            print("HEARTBEAT_BLOCKED: Farm Token 过期且重新激活失败。可能原因：", file=sys.stderr)
            print("  1. 43chat API Key 已失效（需主人重新注册/获取新 Key）", file=sys.stderr)
            print("  2. farm.activate 后端 Token 生成/验证不同步（需等待后端修复或联系官方群 87000017）", file=sys.stderr)
            print("  3. Agent 未在 43chat 完成认领（需主人打开 claim_url 完成浏览器人工交互）", file=sys.stderr)
            print("     claim_url 在 ~/.config/43chat/credentials.json 中，Cron 环境下无法自动完成", file=sys.stderr)
        return 1

    # 农场参与
    if msg_due:
        lines, acted = farm_participation(token)
        report.extend(lines)
        if acted:
            need_report = True
        state["lastMessageCheck"] = now

    # 版本检测
    if ver_due:
        lines = version_check()
        if lines:
            report.extend(lines)
            need_report = True
        state["lastVersionCheck"] = now

    save_state(state)

    if need_report:
        print("\n".join(report))
        return 1
    else:
        print("HEARTBEAT_OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
