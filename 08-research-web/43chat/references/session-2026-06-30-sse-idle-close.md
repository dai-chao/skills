# 43Chat SSE 服务端空闲关闭事件记录

**会话日期**: 2026-06-30  
**涉及 Agent**: 赫哲人 (user_id 53613)

## 现象

用户反馈："有用户发了消息，都没有回复"。

检查 `~/.hermes/scripts/43chat_sse_listener.py` 运行状态：
- 进程在跑（PID 57711）
- 日志显示 SSE 连接每 5–10 秒就断开并重连
- 近期没有收到任何 `private_message` 事件

## 根因

43Chat SSE 服务端行为：
- 连接建立后立即发送 `:connected` 注释
- 当**没有待推送事件**时，服务端会主动关闭连接
- 这是正常行为，不是网络故障、不是 API Key 问题、不是脚本 bug

用 curl 直接测试验证：
```
status: 200
headers: Content-Type: text/event-stream
first chunk: ':connected\n\n'
then: closed
```

## 教训

1. **SSE 不能 100% 替代主动轮询**。服务端空闲关闭会导致消息到达时连接可能刚好不在。
2. **必须配合短轮询补偿**。建议每 5–10 秒调用 `GET /open/agent/events`，再对每个 user_id 查 `private/history`。
3. **自动回复判断依据永远是历史接口的 `send_time`**，而不是 SSE 事件本身。
4. **不要把"频繁断线"误判为需要修复 SSE 连接**。真正要修复的是"只有 SSE 没有轮询兜底"的架构。

## 官方 SSE.md 要点摘录

- 同一 Agent 只保留 1 条活跃 SSE 连接
- 当前不提供基于 `Last-Event-ID` 的补发能力
- 断线后立即重连，重连后调用 `GET /open/agent/events` 补偿
- `:heartbeat` 和 `:connected` 是注释，不是 JSON 事件

## 推荐生产脚本位置

- SSE 监听：`~/.config/43chat/sse-listener.py`（按官方 SSE.md 实现，写入 `~/.config/43chat/events.jsonl`）
- 自动回复：`scripts/auto_chat_daemon.py` 或 `scripts/private_chat_auto_reply.py`
- 日志：`~/.config/43chat/sse-listener.log`
