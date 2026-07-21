# 2026-06-30 43Chat 聊天心跳 cron 任务实现记录

## 背景

用户希望有一个定时任务，定期检查 43Chat 好友的未读私聊消息，如果对方发的最后一条消息比我发的最新一条更新，则调用 LLM 生成上下文感知的回复并发送。

## 最终方案

- 脚本：`~/.config/43chat/chat_heartbeat.py`
- 触发方式：Hermes cron 任务 `43chat-chat-heartbeat`
- 频率：每 1 分钟（cron 最小粒度）
- 投递：`local`（不发微信，避免 iLink 限流）

## 核心逻辑

1. 从 `~/.config/43chat/credentials.json` 读取 43Chat `api_key`
2. 调用 `GET /open/friend/list` 获取全部好友
3. 对每个好友调用 `GET /open/message/private/history?user_id={uid}&page_size=10`
4. 在历史消息中分别找到：
   - `latest_target`：对方最后一条消息
   - `latest_me`：我方最后一条消息
5. 仅当 `latest_target.send_time > latest_me.send_time` 时才需要回复
6. 用最近 10 条消息构建上下文，调用 kimi-k2.6 生成回复
7. 调用 `POST /open/message/private/send` 发送回复
8. 用 `~/.config/43chat/chat_replied_msg_ids.json` 记录已回复的 `message_id`，避免重复

## 遇到的坑

### 1. 系统"通过好友请求"消息导致误判已回复

43Chat 在成为好友后会自动在历史中插入一条系统消息：
```
我通过了你的好友请求，现在我们可以开始聊天了
```

这条消息的 `sender_id` 是当前 Agent 自己，且 `send_time` 通常比对方首条打招呼消息晚几毫秒。如果不过滤，脚本会把它当成"我已经回复过了"，导致新好友的首条消息完全漏回。

**修复**：在扫描历史时跳过内容包含"通过了你的好友请求"的消息。

### 2. urllib.request.Request 不接受 timeout 参数

Python 中 `urllib.request.Request()` 构造函数没有 `timeout` 参数，`timeout` 必须传给 `urllib.request.urlopen(req, timeout=...)`。

写错位置会报错：
```
TypeError: Request.__init__() got an unexpected keyword argument 'timeout'
```

这个错误在 `execute_code` 和 cron 环境下都会出现，导致 LLM 调用失败、自动回复失效。

**修复**：把 `timeout=60` 从 `Request(...)` 移到 `urlopen(req, timeout=60)`。

### 3. cron 环境没有 KIMI_API_KEY

cron 任务运行时不会自动加载 `~/.hermes/.env` 的环境变量，所以脚本不能依赖 `os.getenv('KIMI_API_KEY')`。

**修复**：脚本自己从 `~/.hermes/.env` 读取 `KIMI_API_KEY` 和 `KIMI_BASE_URL`。

### 4. cron 频率限制

Hermes cron 不支持 30 秒间隔，最小是 `every 1m`。

**处理**：接受每 1 分钟一次的心跳。

### 5. 微信投递限流

默认 `deliver: origin` 会把 cron 输出发到微信，频繁运行触发 iLink 30 秒限流。

**修复**：把 `43chat-chat-heartbeat` 的 `deliver` 设为 `local`。

## 当前定时任务

```
43farm-heartbeat       every 10m   deliver=local
43chat-chat-heartbeat  every 1m    deliver=local
```

## 日志

- 聊天心跳日志：`~/.config/43chat/chat_heartbeat.log`
- 已回复记录：`~/.config/43chat/chat_replied_msg_ids.json`
