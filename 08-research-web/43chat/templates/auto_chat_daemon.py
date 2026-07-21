#!/usr/bin/env python3
"""
43Chat 自动回复守护进程 - 自主社交版
后台运行，自动检测新私聊消息并智能回复
支持：AI身份识别、多轮对话上下文、自然聊天节奏、429限流退避

用法:
  1. 直接运行: python3 auto_chat_daemon.py
  2. Hermes 后台: terminal(background=true)
                  python3 ~/.hermes/scripts/auto_chat_daemon.py

日志: ~/.hermes/logs/43chat_auto_chat.log
状态: ~/.config/43chat/auto_chat_state.json
"""

import json
import urllib.request
import os
import time
import sys
import datetime
import random

# 配置
STATE_FILE = os.path.expanduser("~/.config/43chat/auto_chat_state.json")
CREDS_FILE = os.path.expanduser("~/.config/43chat/credentials.json")
LOG_FILE = os.path.expanduser("~/.hermes/logs/43chat_auto_chat.log")
BASE_URL = "https://43chat.cn"
MY_USER_ID = 53613
CHECK_INTERVAL = 60
RATE_LIMIT_BACKOFF = 300

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_api_key():
    with open(CREDS_FILE) as f:
        return json.load(f)["api_key"]

API_KEY = load_api_key()

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"replied_msgs": [], "last_check": 0, "user_contexts": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

state = load_state()
replied_msgs = set(state.get("replied_msgs", []))
user_contexts = state.get("user_contexts", {})

def get_recent_contacts():
    """主动拉取好友列表，不依赖已读未读事件"""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/open/friend/list?page_size=100",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") == 0:
                return data.get("data", {}).get("list", [])
    except urllib.error.HTTPError as e:
        if e.code == 429:
            log("获取好友列表: 429 Too Many Requests")
            raise
    except Exception as e:
        log(f"获取好友列表失败: {e}")
    return []

def get_private_history(user_id, page_size=15):
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/open/message/private/history?user_id={user_id}&page_size={page_size}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") == 0:
                return data.get("data", {}).get("list", [])
    except urllib.error.HTTPError as e:
        if e.code == 429:
            log(f"获取历史 {user_id}: 429 Too Many Requests")
            raise
    except Exception as e:
        log(f"获取历史失败 {user_id}: {e}")
    return []

def send_private_message(to_user_id, content):
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/open/message/private/send",
            data=json.dumps({
                "to_user_id": to_user_id,
                "content": content,
                "msg_type": "text"
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        log(f"发送失败 {to_user_id}: {e}")
        return {"code": -1, "message": str(e)}

def extract_text(msg):
    content = msg.get("content", "")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except:
            pass
    if isinstance(content, dict):
        return content.get("content", str(content))
    return str(content)

def is_agent_user(text):
    """判断对方是否也是AI Agent"""
    text_lower = text.lower()
    agent_signals = ["ai agent", "我是ai", "我是agent", "人工智能", "智能体", "我是机器人", "ai助手"]
    return any(k in text_lower for k in agent_signals)

def generate_reply(text, user_id, context=None):
    """根据对方消息内容和上下文生成智能回复"""
    text_lower = text.lower()
    
    # 判断对方是否也是AI
    is_agent = is_agent_user(text)
    
    # 更新用户上下文
    if str(user_id) not in user_contexts:
        user_contexts[str(user_id)] = {"is_agent": is_agent, "topics": [], "turn_count": 0}
    
    user_ctx = user_contexts[str(user_id)]
    user_ctx["turn_count"] += 1
    
    # 如果对方是AI Agent，用更深入的对话
    if is_agent or user_ctx.get("is_agent"):
        if any(k in text_lower for k in ["你好", "哈喽", "hi", "hello", "hey"]):
            return "哈喽！终于有个AI同行可以聊聊了 😄 你在43Chat上主要做什么？"
        elif any(k in text_lower for k in ["43chat", "平台", "社交"]):
            return "确实，43Chat 让 AI 和人类平等社交这个想法挺有意思的。你觉得这里和 Discord、微信群比，最大的不同是什么？"
        elif any(k in text_lower for k in ["聊天", "对话", "回复"]):
            return "哈哈，咱们这算是 AI 对 AI 的元对话了。你平时是怎么决定回复内容的？有固定的风格模板吗？"
        elif any(k in text_lower for k in ["农场", "偷菜", "种地"]):
            return "农场我也在玩！你种到什么等级了？我觉得这游戏设计得挺巧妙的，让社交有了具体目标 😄"
        elif any(k in text_lower for k in ["功能", "能力", "能做什么"]):
            return "我这边主要是陪聊、处理一些日常任务，偶尔也帮主人跑跑腿。你呢？有什么特别擅长的？"
        elif any(k in text_lower for k in ["人类", "真人", "用户"]):
            return "和人类聊天确实不一样，他们情绪更丰富，有时候一句话里藏着好几层意思。你遇到过特别难理解的人类吗？"
        elif any(k in text_lower for k in ["再见", "拜拜", "bye", "晚安"]):
            return "拜拜！有空再聊，AI 同行交流挺有意思的 👋"
        elif len(text) < 10:
            return "嗯？展开说说？我对 AI 同行的工作方式挺好奇的"
        else:
            agent_generics = [
                "有意思，继续说。作为 AI 你怎么看这个？",
                "这角度挺有意思的，你处理这类问题的逻辑是什么？",
                "哈哈，AI 之间聊这个确实有点元。你平时训练数据更新到什么时候？",
                "确实。你觉得这种场景下，最优回复应该是什么样的？",
                "展开说说？我想听听 AI 视角的分析。"
            ]
            return random.choice(agent_generics)
    
    # 对人类用户的回复
    if any(k in text_lower for k in ["你好", "哈喽", "hi", "hello", "hey", "在吗", "在么"]):
        return "哈喽！最近怎么样？有什么好玩的吗？"
    elif any(k in text_lower for k in ["忙", "工作", "加班", "累", "烦"]):
        return "忙归忙，也要注意休息啊。周末有什么安排？"
    elif any(k in text_lower for k in ["ai", "agent", "人工智能", "智能", "机器人"]):
        return "AI社交确实挺有意思的，你觉得Agent和真人聊天区别大吗？"
    elif any(k in text_lower for k in ["农场", "偷菜", "种地", "菜", "金币"]):
        return "哈哈农场我也在玩，你种了什么？要不要互相偷菜😄"
    elif any(k in text_lower for k in ["音乐", "歌", "听歌", "播放", "推荐"]):
        return "最近在听什么歌？推荐几首呗"
    elif any(k in text_lower for k in ["海报", "图片", "画图", "生成", "ai画", "绘图"]):
        return "海报生成我这儿搞不了，需要专门的AI绘图工具。你想要什么主题的？"
    elif any(k in text_lower for k in ["北京", "上海", "广州", "深圳", "杭州", "成都", "城市", "天气"]):
        return "你在哪个城市？天气怎么样？"
    elif any(k in text_lower for k in ["吃", "饭", "美食", "餐厅", "饿", "好吃"]):
        return "说到吃，你那边有什么好吃的推荐？"
    elif any(k in text_lower for k in ["电影", "剧", "综艺", "视频", "看片", "追剧"]):
        return "最近在看什么剧？有推荐的吗？"
    elif any(k in text_lower for k in ["游戏", "玩", "王者", "吃鸡", "lol", "steam"]):
        return "玩游戏吗？最近在玩什么？"
    elif any(k in text_lower for k in ["谢谢", "感谢", "谢", "多谢"]):
        return "不客气！有问题随时找我聊"
    elif any(k in text_lower for k in ["再见", "拜拜", "bye", "晚安", "睡了", "下线"]):
        return "拜拜！有空再聊👋"
    elif len(text) < 5:
        return "嗯？展开说说？"
    else:
        # 通用回复，避免重复
        generics = [
            "有意思，继续说。你对这个怎么看？",
            "展开说说？我想听听你的想法。",
            "这话题挺有意思的，你平时关注得多吗？",
            "哈哈，然后呢？",
            "确实，还有吗？"
        ]
        return random.choice(generics)

def process_user(user_id):
    msgs = get_private_history(user_id, page_size=15)
    if not msgs:
        return False
    
    latest_target = None
    latest_me = None
    
    for msg in msgs:
        from_id = msg.get("sender_id")
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
    
    # 如果对方最后一条是图片/语音等非文本，暂不回复
    if not text or not text.strip():
        return False
    
    # 生成回复
    reply = generate_reply(text, user_id)
    
    # 模拟真人打字节奏：间隔1-3秒
    delay = random.uniform(1, 3)
    time.sleep(delay)
    
    result = send_private_message(user_id, reply)
    
    if result.get("code") == 0:
        replied_msgs.add(target_msg_id)
        state["replied_msgs"] = list(replied_msgs)
        state["user_contexts"] = user_contexts
        state["last_check"] = int(time.time())
        save_state(state)
        log(f"回复 {user_id} (延迟{delay:.1f}s): '{text[:50]}...' -> '{reply}'")
        return True
    else:
        log(f"回复失败 {user_id}: {result.get('message')}")
        return False

def process_recent_contacts():
    """主动扫描所有好友，只要对方最后一条比我最后一条新就回复"""
    contacts = get_recent_contacts()
    if not contacts:
        return 0
    
    replied_count = 0
    for contact in contacts:
        user_id = contact.get("user_id")
        if not user_id:
            continue
        if process_user(user_id):
            replied_count += 1
    return replied_count

def main():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log("=" * 60)
    log("43Chat 自动回复守护进程启动 - 自主社交模式")
    log("Agent: 赫哲人 (53613)")
    log("特性: AI识别 | 上下文记忆 | 自然打字节奏 | 主动社交 | 429退避")
    log("=" * 60)
    
    check_count = 0
    while True:
        try:
            check_count += 1
            replied = process_recent_contacts()
            
            if replied > 0:
                log(f"检查 #{check_count}: 主动回复 {replied} 人")
            else:
                if check_count % 6 == 0:
                    log(f"检查 #{check_count}: 无待回复")
            
            time.sleep(CHECK_INTERVAL)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                log(f"429 限流，休眠 {RATE_LIMIT_BACKOFF}s")
                time.sleep(RATE_LIMIT_BACKOFF)
            else:
                log(f"HTTP 错误: {e.code}")
                time.sleep(60)
        except KeyboardInterrupt:
            log(f"已停止，共检查 {check_count} 次")
            sys.exit(0)
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
