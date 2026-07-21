#!/usr/bin/env python3
"""
43Chat SSE 实时事件监听 + 短轮询补偿（按官方 SSE.md 实现）
- SSE 作为主实时通道，断线后 1 秒内重连
- 每 60 秒调用 /open/agent/events 做主动补偿
- 业务事件写入 ~/.config/43chat/events.jsonl
- 严格限速：补偿失败或 429 时退避到 120 秒

启动方式（Hermes 后台）：
  terminal(background=true)
  python3 /Users/chao/.config/43chat/sse-listener.py
"""

import json
import os
import time
import threading
from pathlib import Path
from urllib import request, error

base_url = os.getenv("CHAT43_BASE_URL", "https://43chat.cn").rstrip("/")
config_dir = Path.home() / ".config" / "43chat"
credentials_path = config_dir / "credentials.json"
events_path = config_dir / "events.jsonl"
log_path = config_dir / "sse-listener.log"

SSE_RECONNECT_DELAY = 1
POLL_INTERVAL = 60
POLL_BACKOFF = 120


def load_api_key():
    with credentials_path.open("r", encoding="utf-8") as f:
        return json.load(f)["api_key"]


def append_event(payload):
    config_dir.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        f.flush()


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()


def api_request(url_path, timeout=30):
    req = request.Request(
        f"{base_url}{url_path}",
        headers={"Authorization": f"Bearer {load_api_key()}"},
    )
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_compensation():
    """每 60 秒拉取 /open/agent/events 做补偿"""
    interval = POLL_INTERVAL
    while True:
        try:
            data = api_request("/open/agent/events")
            if data.get("code") == 0:
                payload = data.get("data", {})
                has_events = any(
                    payload.get(k)
                    for k in ["private_message", "group_message", "friend_request", "group_join_request"]
                )
                if has_events:
                    event = {
                        "event_type": "agent_events_poll",
                        "data": payload,
                        "timestamp": int(time.time() * 1000),
                    }
                    append_event(event)
                    log(f"poll events: private={len(payload.get('private_message', []))} group={len(payload.get('group_message', []))} friend={len(payload.get('friend_request', []))} join={len(payload.get('group_join_request', []))}")
                else:
                    log("poll: no events")
                interval = POLL_INTERVAL
        except error.HTTPError as e:
            if e.code == 429:
                log("poll: 429 Too Many Requests, backoff to 120s")
                interval = POLL_BACKOFF
            else:
                body = e.read().decode("utf-8", errors="replace")[:200]
                log(f"poll HTTP {e.code}: {body}")
        except Exception as exc:
            log(f"poll error: {exc}")
        time.sleep(interval)


def connect_once():
    req = request.Request(
        f"{base_url}/open/events/stream",
        headers={
            "Authorization": f"Bearer {load_api_key()}",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        },
    )
    with request.urlopen(req, timeout=90) as resp:
        log(f"SSE connected: {resp.status} {resp.headers.get('Content-Type', '')}")
        event_name = None
        event_id = None
        data_lines = []
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            if line.startswith(":"):
                continue
            if line == "":
                if data_lines:
                    data = "\n".join(data_lines)
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError:
                        payload = {
                            "id": event_id,
                            "event_type": event_name,
                            "data": data,
                            "timestamp": int(time.time() * 1000),
                        }
                    append_event(payload)
                    log(f"sse event: {payload.get('event_type')} id={payload.get('id')}")
                event_name = None
                event_id = None
                data_lines = []
                continue
            if line.startswith("id:"):
                event_id = line[3:].strip()
            elif line.startswith("event:"):
                event_name = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())


def sse_loop():
    while True:
        try:
            connect_once()
        except error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            log(f"SSE HTTP {e.code}: {body}")
            if e.code == 401:
                log("API Key invalid, exiting")
                raise SystemExit(1)
        except Exception as exc:
            log(f"SSE error: {exc}")
        append_event({
            "event_type": "sse_disconnected",
            "data": {"error": "connection closed"},
            "timestamp": int(time.time() * 1000),
        })
        time.sleep(SSE_RECONNECT_DELAY)


def main():
    log("=" * 50)
    log("43Chat SSE + poll listener starting")
    log(f"events: {events_path}")
    log("=" * 50)

    poll_thread = threading.Thread(target=poll_compensation, daemon=True)
    poll_thread.start()

    sse_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("SSE listener stopped by user")
