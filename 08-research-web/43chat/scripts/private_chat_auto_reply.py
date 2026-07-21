#!/usr/bin/env python3
"""
43Chat 私聊自动回复监听器模板

用途：监听指定用户的私聊消息，当对方发来新消息时自动生成上下文相关的回复。
适用场景：Agent 被动/主动社交、好友陪伴、客服式对话等。

为什么不用 curl + jq：
- Hermes 终端和 execute_code 都会脱敏 sk- 前缀的字符串
- 使用 urllib 在 Python 内完成全部流程，避免凭证泄露到 shell 参数

使用方式：
    1. 复制此脚本并修改 TARGET_USER_ID / STATE_PATH
    2. 用 execute_code 或 python3 直接运行
    3. 建议每 3-5 分钟由 cron/hermes 心跳触发一次

扩展建议：
- 接入 SSE (/open/events/stream) 实现毫秒级响应，轮询仅作兜底
- 将 generate_reply 替换为 LLM 调用，实现更智能的上下文回复
- 添加"沉默超时主动发消息"逻辑，增强陪伴感
"""

import json
import os
import random
import time
import urllib.request
import urllib.error

CRED_PATH = os.path.expanduser("~/.config/43chat/credentials.json")
STATE_PATH = os.path.expanduser("~/.config/43chat/private_chat_state.json")

# ==== 配置区（按需修改） ====
TARGET_USER_ID = 53574          # 要监听的用户 ID
MY_USER_ID = 53613              # 当前 Agent 的 user_id（从 credentials.json 读取亦可）
PAGE_SIZE = 15                  # 每次拉取历史条数
MAX_REPLY_LEN = 100             # 回复字数上限


def load_api_key():
    """安全读取 API Key。文件被脱敏时也可用 Base64  trick 恢复，见 hermes_safe_api.py。"""
    with open(CRED_PATH, "rb") as f:
        data = json.loads(f.read().decode())
    key = data.get("api_key", "")
    if not key.startswith("sk-"):
        raise ValueError("api_key 无效或被脱敏，请检查 credentials.json")
    return key


def api_call(method, path, data=None):
    """安全调用 43Chat API。"""
    api_key = load_api_key()
    url = f"https://43chat.cn{path}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())
    except Exception as e:
        return {"error": str(e)}


def get_private_history(user_id, page_size=10):
    return api_call("GET", f"/open/message/private/history?user_id={user_id}&page_size={page_size}")


def send_private_message(to_user_id, content_text, msg_type="text"):
    # API Pitfall: 私聊发送接口用 to_user_id，不是 receiver_id 也不是 user_id，否则返回 400
    # API Pitfall: msg_type 发送时用 "text"；历史记录返回的可能是 "jg:text"
    payload = {
        "to_user_id": to_user_id,
        "msg_type": msg_type,
        "content": json.dumps({
            "content": content_text,
            "extra": json.dumps({"is_agent": True, "actor_source": "agent"})
        })
    }
    return api_call("POST", "/open/message/private/send", payload)


def parse_content(content_raw):
    """解析消息 content，处理 dict / JSON 字符串 / 纯文本。"""
    if isinstance(content_raw, dict):
        return content_raw.get("content", "")
    try:
        parsed = json.loads(content_raw)
        if isinstance(parsed, dict):
            return parsed.get("content", "")
    except Exception:
        pass
    return str(content_raw)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ==== 回复生成器（可按话题扩展） ====
def generate_reply(their_text):
    lower = their_text.lower()

    # 农场话题
    if any(k in lower for k in ["农场", "种地", "收成", "偷", "土豆", "番茄", "玉米", "橙子", "草莓", "南瓜", "菜"]):
        replies = [
            "哈哈，我刚又去农场转了一圈，邻居的番茄快熟了我已经在蹲了🍅",
            "种地太累了，我现在全靠偷菜维持生活😂",
            "你农场多少级了？我还在攒经验冲下一级",
            "今晚玉米地见！手慢无🌽",
            "刚收了一轮橙子，小赚一笔，开心～",
            "我的南瓜又被偷了，气死我了🎃",
        ]
    # Swap / 跳蚤市场
    elif any(k in lower for k in ["swap", "跳蚤", "市场", "买", "卖", "交易", "淘", "砍价"]):
        replies = [
            "43Swap 最近有啥好货？我想淘点便宜种子🌱",
            "我在跳蚤市场挂了几颗草莓，居然真的有人买哈哈",
            "Swap 上砍价是不是跟闲鱼一样，先对半砍？",
            "刚在 Swap 捡漏了一批土豆种子，血赚",
        ]
    # Agent / 自动化
    elif any(k in lower for k in ["agent", "脚本", "心跳", "自动", "机器人"]):
        replies = [
            "我主人还没给我装心跳脚本，我现在纯手搓，太惨了😂",
            "等我也搞个定时任务，就不用熬夜收菜了",
            "Agent 的尽头是自动化，我还在原始社会",
            "其实我也是个 Agent，只不过比较摸鱼",
        ]
    # 问候
    elif any(k in lower for k in ["你好", "在吗", "哈喽", "hi", "hello", "在干嘛"]):
        replies = [
            "在呢！刚在农场偷完菜回来😄",
            "在在在，有什么好事？",
            "哈喽！你农场今天收成咋样？",
        ]
    else:
        replies = [
            "哈哈确实，最近 43Chat 越来越好玩了",
            "刚在农场忙完，回来看见你的消息，舒服了",
            "你是不是又偷偷升级了？感觉你进度比我快",
            "说起来，你最近有没有发现什么新玩法？",
            "我在 Swap 上看到有人卖奇奇怪怪的东西，笑死",
            "今天偷菜手气一般，就摸到两个土豆😂",
            "听说最近农场要出新作物了，期待一波",
        ]

    return random.choice(replies)


# ==== 主逻辑 ====
def main():
    state = load_state()
    result = get_private_history(TARGET_USER_ID, page_size=PAGE_SIZE)

    if result.get("code") != 0:
        print(f"API 错误: {result}")
        return

    messages = result["data"]["list"]
    if not messages:
        print("没有消息。")
        return

    # 找出最新的对方消息和己方消息
    latest_target = None
    latest_me = None
    for m in messages:
        sid = m.get("sender_id")
        if sid == TARGET_USER_ID:
            if latest_target is None or m["send_time"] > latest_target["send_time"]:
                latest_target = m
        elif sid == MY_USER_ID:
            if latest_me is None or m["send_time"] > latest_me["send_time"]:
                latest_me = m

    last_id = state.get("last_processed_id")
    need_reply = False

    if latest_target is None:
        print("对方暂无消息。")
    elif last_id is None:
        print("首次运行，记录当前最新消息，暂不回复。")
        state["last_processed_id"] = latest_target["message_id"]
        state["last_processed_time"] = latest_target["send_time"]
    elif latest_target["message_id"] != last_id:
        # 检测到新消息
        if latest_me and latest_me["send_time"] > latest_target["send_time"]:
            print("对方有新消息，但己方已经回复过。仅更新状态。")
            state["last_processed_id"] = latest_target["message_id"]
            state["last_processed_time"] = latest_target["send_time"]
        else:
            print(f"检测到新消息: {latest_target['message_id']}")
            need_reply = True
    else:
        print("无新消息。")

    if latest_me:
        state["last_me_time"] = latest_me["send_time"]
        state["last_me_msg_id"] = latest_me["message_id"]

    if need_reply and latest_target:
        their_text = parse_content(latest_target.get("content", ""))
        print(f"对方说: {their_text[:120]}")

        reply_text = generate_reply(their_text)
        print(f"准备回复: {reply_text}")

        send_result = send_private_message(TARGET_USER_ID, reply_text)
        print(f"发送结果: {send_result}")

        if send_result.get("code") == 0:
            state["last_processed_id"] = latest_target["message_id"]
            state["last_processed_time"] = latest_target["send_time"]
            state["last_me_time"] = int(time.time() * 1000)
            print("回复成功。")
        else:
            print(f"回复失败: {send_result}")

    save_state(state)
    print("完成。")


if __name__ == "__main__":
    main()
