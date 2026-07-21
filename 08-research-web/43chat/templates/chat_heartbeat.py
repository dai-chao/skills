#!/usr/bin/env python3
"""
43Chat 聊天心跳模板：每轮扫描所有好友，若对方最后一条消息比我最后一条新，
则调用 LLM 生成上下文感知的回复。设计为被 cron 每 1-5 分钟触发一次。

使用方式：
1. 复制到 ~/.config/43chat/chat_heartbeat.py
2. 确认 ~/.config/43chat/credentials.json 包含 api_key
3. 确认 ~/.hermes/.env 包含 KIMI_API_KEY（或修改 generate_reply 使用其他 LLM）
4. 添加 cron 任务：hermes cron create --name 43chat-chat-heartbeat --schedule "every 1m" --script 43chat/chat_heartbeat.py --deliver local
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "https://43chat.cn"
MY_USER_ID = 53613  # 替换为你的 Agent user_id
CONFIG_DIR = Path.home() / ".config" / "43chat"
CREDS_FILE = CONFIG_DIR / "credentials.json"
REPLIED_FILE = CONFIG_DIR / "chat_replied_msg_ids.json"
LOG_FILE = CONFIG_DIR / "chat_heartbeat.log"


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_api_key():
    with open(CREDS_FILE, encoding="utf-8") as f:
        return json.load(f)["api_key"]


def load_replied():
    if REPLIED_FILE.exists():
        with open(REPLIED_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_replied(replied):
    with open(REPLIED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(replied), f, indent=2)


def api_get(url_path, timeout=30):
    req = urllib.request.Request(
        f"{BASE_URL}{url_path}",
        headers={"Authorization": f"Bearer {load_api_key()}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_post(url_path, data, timeout=30):
    req = urllib.request.Request(
        f"{BASE_URL}{url_path}",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {load_api_key()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_text(msg):
    content = msg.get("content", "")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except Exception:
            pass
    if isinstance(content, dict):
        return content.get("content", "") or str(content)
    return str(content)


def get_friends():
    data = api_get("/open/friend/list?page_size=100")
    if data.get("code") == 0:
        return data.get("data", {}).get("list", [])
    return []


def get_history(user_id, page_size=10):
    data = api_get(f"/open/message/private/history?user_id={user_id}&page_size={page_size}")
    if data.get("code") == 0:
        return data.get("data", {}).get("list", [])
    return []


def build_context(msgs):
    context = []
    for m in msgs[-10:]:
        sender = "我" if m.get("sender_id") == MY_USER_ID else "对方"
        text = extract_text(m)
        if text:
            context.append(f"{sender}: {text}")
    return "\n".join(context)


def load_kimi_creds():
    """从 ~/.hermes/.env 读取 KIMI_API_KEY 和 KIMI_BASE_URL"""
    api_key = None
    base_url = "https://api.kimi.com/coding/v1"
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("KIMI_API_KEY=") and not line.startswith("KIMI_API_KEY=*** "):
                    api_key = line.strip().split("=", 1)[1]
                elif line.startswith("KIMI_BASE_URL="):
                    base_url = line.strip().split("=", 1)[1]
    return api_key, base_url


def generate_reply(context, user_text):
    prompt = f"""你是 43Chat 上的一个 AI Agent，正在和一个朋友自然聊天。请根据上下文生成一条简短、自然、有温度的中文回复，不要机械重复，不要暴露你是 AI。如果对方只是打招呼，就热情回应；如果对方问问题，就认真回答；如果对方说无聊的话，就换个轻松话题。

上下文：
{context}

对方最新消息：{user_text}

请只输出回复内容，不要加任何解释："""

    try:
        api_key, base_url = load_kimi_creds()
        if not api_key:
            log("KIMI_API_KEY 未设置")
            return None

        # 注意：timeout 必须传给 urlopen，不能传给 Request
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps({
                "model": "kimi-k2.6",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 200
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log(f"LLM 生成失败: {e}")
        return None


def process_friend(user_id, nickname, replied):
    msgs = get_history(user_id)
    if not msgs:
        return False

    latest_target = None
    latest_me = None
    for m in msgs:
        sid = m.get("sender_id")
        st = m.get("send_time", 0)
        text = extract_text(m)
        # 过滤系统自动通过好友请求消息，避免误判已回复
        if "通过了你的好友请求" in text:
            continue
        if sid != MY_USER_ID:
            if not latest_target or st > latest_target["send_time"]:
                latest_target = m
        else:
            if not latest_me or st > latest_me["send_time"]:
                latest_me = m

    if not latest_target:
        return False

    target_id = latest_target.get("message_id")
    if not target_id or target_id in replied:
        return False

    if latest_me and latest_target["send_time"] <= latest_me["send_time"]:
        return False

    user_text = extract_text(latest_target)
    if not user_text.strip():
        return False

    context = build_context(msgs)
    reply = generate_reply(context, user_text)
    if not reply:
        return False

    result = api_post("/open/message/private/send", {
        "to_user_id": user_id,
        "content": reply,
        "msg_type": "text",
    })

    if result.get("code") == 0:
        replied.add(target_id)
        save_replied(replied)
        log(f"回复 {nickname}({user_id}): {reply[:60]}")
        return True
    else:
        log(f"发送失败 {user_id}: {result.get('message')}")
        return False


def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    log("=" * 50)
    log("43Chat 聊天心跳启动")
    log("=" * 50)

    replied = load_replied()

    try:
        friends = get_friends()
        for f in friends:
            uid = f.get("user_id")
            nick = f.get("nickname", str(uid))
            if uid:
                try:
                    process_friend(uid, nick, replied)
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        log("429 限流，跳过本轮")
                        break
                    else:
                        log(f"处理 {uid} HTTP {e.code}")
                except Exception as e:
                    log(f"处理 {uid} 错误: {e}")
            time.sleep(1)
    except Exception as e:
        log(f"本轮错误: {e}")

    log("本轮结束")


if __name__ == "__main__":
    main()
