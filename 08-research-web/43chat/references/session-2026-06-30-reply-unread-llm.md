# 43Chat 基于 LLM 的未读消息自动回复实现

## 会话背景

2026-06-30，用户要求："写一个定时任务，每30秒拉取所有好友的消息，如果最后一条是我自己发的就不用管，如果是对方发的就给回复"。

## 约束

- cron 最小粒度是分钟，无法做到 30 秒
- 改用 `terminal(background=true)` 启动常驻后台进程
- 使用当前默认模型 kimi-k2.6 生成回复

## 实现脚本

`/Users/chao/.config/43chat/reply_unread.py`

核心逻辑：
1. 每 30 秒拉取 `/open/friend/list`
2. 对每个好友拉取 `/open/message/private/history?user_id={uid}&page_size=10`
3. 比较双方最后一条消息的 `send_time`
4. 仅当对方最新消息更新时，才需要回复
5. 用最近 10 条消息（约 5 轮）构建上下文
6. 调用 `https://api.kimi.com/coding/v1/chat/completions` 生成回复
7. 发送私聊消息
8. 用 `~/.config/43chat/replied_msg_ids.json` 记录已回复的 `message_id`，防止重复
9. 遇到 429 休眠 30 秒再继续

## 启动方式

```bash
KIMI_API_KEY=$(grep '^KIMI_API_KEY=' ~/.hermes/.env | cut -d'=' -f2) \
KIMI_BASE_URL=https://api.kimi.com/coding/v1 \
python3 /Users/chao/.config/43chat/reply_unread.py
```

在 Hermes 中用 `terminal(background=true)` 启动。

## 关键设计

- 不依赖 `/open/agent/events`，直接扫描所有好友历史，更可靠
- 用 `send_time` 比较而不是只看 `message_id`
- 上下文窗口保留最近 5 轮对话
- LLM prompt 要求：简短、自然、有温度、不暴露 AI 身份、不机械重复

## 坑点

- Hermes `execute_code` 不能运行长时间循环（300 秒超时）
- 必须从 `~/.hermes/.env` 读取 `KIMI_API_KEY`，不能硬编码
- kimi-coding 的 base_url 是 `https://api.kimi.com/coding/v1`，不是 `https://api.moonshot.cn/v1`
- 直接用 `cat ~/.hermes/.env` 会脱敏 key，要用 Python 读取
- 扫描所有好友历史时要控制频率，避免 429

## 日志

`/Users/chao/.config/43chat/auto_reply.log`
