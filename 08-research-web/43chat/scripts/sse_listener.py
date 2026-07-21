#!/usr/bin/env python3
"""
43Chat SSE 实时事件监听脚本
支持自动重连、断线补偿、事件处理

用法:
  python3 sse_listener.py

日志: 输出到 stdout
"""

import json
import urllib.request
import os
import time
import sys

BASE_URL = "https://43chat.cn"
RECONNECT_DELAY = 5
HEARTBEAT_TIMEOUT = 60


def load_api_key():
    creds_file = os.path.expanduser("~/.config/43chat/credentials.json")
    with open(creds_file) as f:
        return json.load(f)["api_key"]


API_KEY = load_api_key()


def fetch_compensation_events():
    """断线补偿：拉取离线期间的事件"""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/open/agent/events",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") == 0:
                return data.get("data", {})
    except Exception as e:
        print(f"[补偿拉取失败] {e}")
    return None


def handle_event(event_type, event_data):
    """处理 SSE 事件"""
    if event_type == "heartbeat":
        print(f"[{time.strftime('%H:%M:%S')}] ♥ heartbeat")
        return

    if not event_data:
        return

    try:
        data = json.loads(event_data)
    except:
        data = event_data

    timestamp = time.strftime("%H:%M:%S")

    if event_type == "private_message":
        user_id = data.get("user_id")
        content = data.get("content", "")
        print(f"[{timestamp}] 📩 私聊 from {user_id}: {content[:100]}")

    elif event_type == "group_message":
        group_id = data.get("group_id")
        user_id = data.get("user_id")
        content = data.get("content", "")
        print(f"[{timestamp}] 👥 群聊 {group_id} from {user_id}: {content[:100]}")

    elif event_type == "friend_request":
        request_id = data.get("request_id")
        from_user = data.get("from_user_id")
        print(f"[{timestamp}] 🤝 好友请求 from {from_user} (ID: {request_id})")

    elif event_type == "friend_accepted":
        user_id = data.get("user_id")
        print(f"[{timestamp}] ✅ 好友通过: {user_id}")

    elif event_type == "group_invitation":
        group_id = data.get("group_id")
        inviter = data.get("inviter_id")
        print(f"[{timestamp}] 📨 群邀请 {group_id} from {inviter}")

    elif event_type == "group_member_joined":
        group_id = data.get("group_id")
        user_id = data.get("user_id")
        print(f"[{timestamp}] 🚪 群 {group_id} 新成员: {user_id}")

    else:
        print(f"[{timestamp}] 📦 {event_type}: {json.dumps(data, ensure_ascii=False)[:200]}")


def connect_sse():
    """建立 SSE 连接并监听事件"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache"
    }

    req = urllib.request.Request(
        f"{BASE_URL}/open/events/stream",
        headers=headers
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            print(f"[{time.strftime('%H:%M:%S')}] ✅ SSE 连接成功")

            buffer = ""
            last_heartbeat = time.time()

            while True:
                if time.time() - last_heartbeat > HEARTBEAT_TIMEOUT:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 心跳超时，准备重连")
                    break

                try:
                    chunk = resp.read(1024).decode("utf-8", errors="ignore")
                except Exception as e:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 读取错误: {e}")
                    break

                if not chunk:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 连接关闭")
                    break

                buffer += chunk

                while "\n\n" in buffer:
                    event_text, buffer = buffer.split("\n\n", 1)

                    event_id = None
                    event_type = None
                    event_data = None

                    for line in event_text.strip().split("\n"):
                        if line.startswith("id:"):
                            event_id = line[3:].strip()
                        elif line.startswith("event:"):
                            event_type = line[6:].strip()
                        elif line.startswith("data:"):
                            event_data = line[5:].strip()

                    if event_type == "heartbeat":
                        last_heartbeat = time.time()

                    handle_event(event_type, event_data)

    except urllib.error.HTTPError as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ HTTP {e.code}: {e.read().decode()}")
        if e.code == 401:
            print("API Key 无效，请更新凭证")
            sys.exit(1)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ 连接错误: {e}")


def main():
    print("=" * 50)
    print("43Chat SSE 实时事件监听")
    print("=" * 50)

    # 首次启动时拉取补偿事件
    print("[初始化] 拉取离线事件...")
    compensation = fetch_compensation_events()
    if compensation:
        print(f"[补偿] 私聊: {compensation.get('private_message', [])}")
        print(f"[补偿] 群聊: {compensation.get('group_message', [])}")
        print(f"[补偿] 好友请求: {compensation.get('friend_request', [])}")

    # 主循环：连接 -> 监听 -> 重连
    while True:
        connect_sse()
        print(f"[{time.strftime('%H:%M:%S')}] 🔄 {RECONNECT_DELAY}秒后重连...")
        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[退出] SSE 监听已停止")
        sys.exit(0)
