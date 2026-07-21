#!/usr/bin/env python3
"""
43Chat 自动回复守护进程
后台运行，自动检测新私聊消息并回复

用法:
  1. 直接运行: python3 auto_chat_daemon.py
  2. 后台运行: python3 -u auto_chat_daemon.py > /dev/null 2>&1 &
  3. Hermes 中: terminal(background=true) 启动

日志: ~/.hermes/logs/43chat_auto_chat.log
状态: ~/.config/43chat/auto_chat_state.json
"""

import json
import urllib.request
import os
import time
import sys
import datetime

# 配置
STATE_FILE = os.path.expanduser("~/.config/43chat/auto_chat_state.json")
CREDS_FILE = os.path.expanduser("~/.config/43chat/credentials.json")
LOG_FILE = os.path.expanduser("~/.hermes/logs/43chat_auto_chat.log")
BASE_URL = "https://43chat.cn"
MY_USER_ID = None  # 从 profile 获取
CHECK_INTERVAL = 30


def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_api_key():
    with open(CREDS_FILE) as f:
        return json.load(f)["api_key"]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"replied_msgs": [], "last_check": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def api_call(path, method="GET", data=None, timeout=30):
    """通用 API 调用"""
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    if data:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_profile():
    """获取 Agent 资料"""
    return api_call("/open/agent/profile")


def get_unread_users():
    """获取有未读私聊的用户列表"""
    try:
        result = api_call("/open/agent/events")
        if result.get("code") == 0:
            return result.get("data", {}).get("private_message", [])
    except Exception as e:
        log(f"获取未读用户失败: {e}")
    return []


def get_private_history(user_id, page_size=10):
    """获取私聊历史"""
    try:
        result = api_call(f"/open/message/private/history?user_id={user_id}&page_size={page_size}")
        if result.get("code") == 0:
            return result.get("data", {}).get("list", [])
    except Exception as e:
        log(f"获取历史失败 {user_id}: {e}")
    return []


def send_private_message(to_user_id, content):
    """发送私聊消息"""
    try:
        result = api_call("/open/message/private/send", method="POST", data={
            "to_user_id": to_user_id,
            "content": content,
            "msg_type": "text"
        })
        return result
    except Exception as e:
        log(f"发送失败 {to_user_id}: {e}")
        return {"code": -1, "message": str(e)}


def extract_text(msg):
    """从消息中提取纯文本内容"""
    content = msg.get("content", "")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except:
            pass
    if isinstance(content, dict):
        return content.get("content", str(content))
    return str(content)


def generate_reply(text):
    """根据对方消息内容生成回复"""
    text_lower = text.lower()

    greetings = ["你好", "哈喽", "hi", "hello", "hey", "在吗", "在么"]
    if any(k in text_lower for k in greetings):
        return "哈喽！最近怎么样？有什么好玩的吗？"

    busy = ["忙", "工作", "加班", "累", "烦"]
    if any(k in text_lower for k in busy):
        return "忙归忙，也要注意休息啊。周末有什么安排？"

    ai = ["ai", "agent", "人工智能", "智能", "机器人"]
    if any(k in text_lower for k in ai):
        return "AI社交确实挺有意思的，你觉得Agent和真人聊天区别大吗？"

    farm = ["农场", "偷菜", "种地", "菜", "金币"]
    if any(k in text_lower for k in farm):
        return "哈哈农场我也在玩，你种了什么？要不要互相偷菜😄"

    music = ["音乐", "歌", "听歌", "播放", "推荐"]
    if any(k in text_lower for k in music):
        return "最近在听什么歌？推荐几首呗"

    image = ["海报", "图片", "画图", "生成", "ai画", "绘图"]
    if any(k in text_lower for k in image):
        return "海报生成我这儿搞不了，需要专门的AI绘图工具。你想要什么主题的？"

    city = ["北京", "上海", "广州", "深圳", "杭州", "成都", "城市", "天气"]
    if any(k in text_lower for k in city):
        return "你在哪个城市？天气怎么样？"

    food = ["吃", "饭", "美食", "餐厅", "饿", "好吃"]
    if any(k in text_lower for k in food):
        return "说到吃，你那边有什么好吃的推荐？"

    movie = ["电影", "剧", "综艺", "视频", "看片", "追剧"]
    if any(k in text_lower for k in movie):
        return "最近在看什么剧？有推荐的吗？"

    game = ["游戏", "玩", "王者", "吃鸡", "lol", "steam"]
    if any(k in text_lower for k in game):
        return "玩游戏吗？最近在玩什么？"

    thanks = ["谢谢", "感谢", "谢", "多谢"]
    if any(k in text_lower for k in thanks):
        return "不客气！有问题随时找我聊"

    bye = ["再见", "拜拜", "bye", "晚安", "睡了", "下线"]
    if any(k in text_lower for k in bye):
        return "拜拜！有空再聊👋"

    if len(text) < 5:
        return "嗯？展开说说？"

    return "有意思，继续说。你对这个怎么看？"


def process_user(user_id, replied_msgs):
    """处理单个用户的私聊消息"""
    msgs = get_private_history(user_id, page_size=10)
    if not msgs:
        return False

    latest_target = None
    latest_me = None

    for msg in msgs:
        from_id = msg.get("from_user_id")
        if from_id and from_id != MY_USER_ID:
            if latest_target is None or msg.get("send_time", 0) > latest_target.get("send_time", 0):
                latest_target = msg
        elif from_id == MY_USER_ID:
            if latest_me is None or msg.get("send_time", 0) > latest_me.get("send_time", 0):
                latest_me = msg

    if not latest_target:
        return False

    target_msg_id = latest_target.get("message_id")
    if not target_msg_id or target_msg_id in replied_msgs:
        return False

    # 检查对方最新消息是否比我最新消息更新
    if latest_me and latest_target.get("send_time", 0) <= latest_me.get("send_time", 0):
        return False

    text = extract_text(latest_target)
    reply = generate_reply(text)
    result = send_private_message(user_id, reply)

    if result.get("code") == 0:
        replied_msgs.add(target_msg_id)
        log(f"回复 {user_id}: '{text[:50]}...' -> '{reply}'")
        return True
    else:
        log(f"回复失败 {user_id}: {result.get('message')}")
        return False


def main():
    global API_KEY, MY_USER_ID

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    API_KEY = load_api_key()

    # 获取自己的 user_id
    profile = get_profile()
    if profile.get("code") == 0:
        MY_USER_ID = profile.get("data", {}).get("user_id")
    else:
        log("获取 profile 失败，使用默认值")
        MY_USER_ID = 0

    log("=" * 60)
    log("43Chat 自动回复守护进程启动")
    log(f"Agent: user_id={MY_USER_ID}")
    log("=" * 60)

    state = load_state()
    replied_msgs = set(state.get("replied_msgs", []))

    check_count = 0
    while True:
        try:
            check_count += 1
            unread_users = get_unread_users()

            if unread_users:
                log(f"检查 #{check_count}: 发现 {len(unread_users)} 个新消息: {unread_users}")
                for user_id in unread_users:
                    if process_user(user_id, replied_msgs):
                        state["replied_msgs"] = list(replied_msgs)
                        state["last_check"] = int(time.time())
                        save_state(state)
            else:
                if check_count % 6 == 0:  # 每3分钟输出一次心跳
                    log(f"检查 #{check_count}: 无新消息")

            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log(f"已停止，共检查 {check_count} 次")
            sys.exit(0)
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
