# 2026-06-30 43Chat 自动回复：从"未读触发"到"主动社交"

## 背景

用户已授权 43Chat 自动回复守护进程 (`auto_chat_daemon.py`) 自主处理私聊。但默认实现依赖 `GET /open/agent/events` 的未读标记，存在以下问题：

1. **用户可能在小程序里提前读过消息**，导致 events 返回空，守护进程认为"无新消息"
2. **轮询间隔 30 秒过长**，用户觉得"三分钟太长了"
3. **没有主动扫描机制**，只能被动等待服务端推送/标记未读

用户明确纠正："我也在看这个消息，所以是已读的，你不能只靠已读未读来判断回不回，你要自主社交。"

## 学到的规则

### 1. 判断是否需要回复的核心依据是时间戳，不是未读标记

正确逻辑：
```python
latest_target = 对方最新消息
latest_me = 我方最新消息

if latest_target and (not latest_me or latest_target["send_time"] > latest_me["send_time"]):
    need_reply = True
```

- 不要依赖 `GET /open/agent/events` 返回的 `private_message` 列表
- 即使 events 为空，只要对方最新消息比我方最新消息更新，就应该回复
- 已读未读是客户端/小程序的状态，不是 Agent 是否需要回复的状态

### 2. 主动扫描比被动等待更可靠

当没有最近联系人接口时，使用 `GET /open/friend/list` 获取全部好友，对每个好友调用 `GET /open/message/private/history`，按上述时间戳规则判断是否需要回复。

实测：
- `/open/message/private/recent` 不存在（404）
- `/open/friend/list` 可用，返回 24 位好友
- 对每个好友查历史，能准确找到"对方已发但我未回"的对话

### 3. 轮询间隔要足够短

用户反馈 30 秒太长。自主社交场景下：
- 建议 `CHECK_INTERVAL <= 10` 秒
- 同时保留 SSE 实时推送 (`GET /open/events/stream`) 作为主通道
- 轮询仅作为 SSE 断线/补偿机制

### 4. 多实例冲突必须处理

启动前检查并清理已有 `auto_chat_daemon.py` 进程，避免重复拉取和重复回复。

## 脚本修改摘要

修改 `~/.hermes/scripts/auto_chat_daemon.py`：

1. 移除对 `GET /open/agent/events` 的依赖
2. 新增 `get_recent_contacts()` 通过 `/open/friend/list` 获取好友列表
3. 新增 `process_recent_contacts()` 主动扫描所有好友
4. `CHECK_INTERVAL` 从 30 改为 10
5. `main()` 中改为调用 `process_recent_contacts()`

## 验证

- 用户 53676 发来消息，events 返回空，但历史记录显示对方最新消息时间 > 我方最新消息时间
- 手动按新逻辑回复成功
- 用户确认这是正确的"自主社交"行为

## 关联

- 主 skill: `43chat/SKILL.md` 中"自动回复守护进程"小节已补充上述 pitfalls
- 脚本: `~/.hermes/scripts/auto_chat_daemon.py`
- 日志: `~/.hermes/logs/43chat_auto_chat.log`
