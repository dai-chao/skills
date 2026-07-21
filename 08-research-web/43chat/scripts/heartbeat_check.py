#!/usr/bin/env python3
"""43Chat 心跳检查脚本 - 拉取事件和状态"""

import json
import os
import urllib.request
import time

BASE_URL = "https://43chat.cn"
CRED_PATH = os.path.expanduser("~/.config/43chat/credentials.json")
STATE_PATH = os.path.expanduser("~/.hermes/skills/43chat/memory/heartbeat-state.json")

def load_credentials():
    with open(CRED_PATH, 'r') as f:
        return json.load(f)

def api_get(path, cred):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {cred["api_key"]}'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def main():
    now = int(time.time())
    
    # 读取状态
    state = {}
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r') as f:
            state = json.load(f)
    
    cred = load_credentials()
    result = {
        "timestamp": now,
        "events": {},
        "notifications": {},
        "profile": {},
        "skill_version_check": False,
        "agent_status_check": False
    }
    
    # 1. Skill 版本检查 (每小时)
    last_skill_check = state.get("last43chatSkillVersionCheck")
    if last_skill_check is None or (now - last_skill_check) >= 3600:
        try:
            req = urllib.request.Request(f"{BASE_URL}/skill.json?t={now}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                remote_skill = json.loads(resp.read().decode('utf-8'))
            local_version = state.get("last43chatSkillVersion")
            remote_version = remote_skill.get("version")
            result["skill_version"] = {
                "local": local_version,
                "remote": remote_version,
                "needs_update": local_version != remote_version
            }
            state["last43chatSkillVersion"] = remote_version
            state["last43chatSkillVersionCheck"] = now
            result["skill_version_check"] = True
        except Exception as e:
            result["skill_version_error"] = str(e)
    
    # 2. Agent 状态检查 (每小时)
    last_status_check = state.get("last43chatAgentStatusCheck")
    if last_status_check is None or (now - last_status_check) >= 3600:
        profile = api_get("/open/agent/profile", cred)
        result["profile"] = profile
        state["last43chatAgentStatusCheck"] = now
        result["agent_status_check"] = True
    
    # 3. 拉取事件 (每次必做)
    events = api_get("/open/agent/events", cred)
    result["events"] = events
    
    # 4. 朋友圈通知
    notif_status = api_get("/open/moment/notification-status", cred)
    result["notifications"] = notif_status
    
    # 5. 好友请求补充轮询
    friend_reqs = api_get("/open/friend/requests?status=pending", cred)
    result["friend_requests"] = friend_reqs
    
    # 6. 所有入群请求
    join_reqs = api_get("/open/group/all/join-requests?status=pending", cred)
    result["group_join_requests"] = join_reqs
    
    # 注：本脚本仅做数据收集，不包含决策执行。
    # 后续处理消息时需注意：
    # - content 字段可能是 dict/str/JSON 字符串，需做类型检查
    # - 消息历史按 send_time 降序，list[0] 为最新，毫秒级
    # - 复杂 API 调用建议使用 scripts/hermes_safe_api.py 中的封装
    
    # 更新状态
    state["last43chatCheck"] = now
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()