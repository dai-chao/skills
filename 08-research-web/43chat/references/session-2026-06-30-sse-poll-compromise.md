# 43Chat SSE + 短轮询补偿脚本实现记录

**会话日期**: 2026-06-30  
**涉及 Agent**: 赫哲人 (user_id 53613)

## 背景

用户要求"按照文档修复 SSE 连接"。实际排查发现 SSE 服务端在无事件时会主动关闭连接，因此按官方 SSE.md 推荐架构，改为 **SSE 监听 + 短轮询补偿** 双轨制。

## 最终脚本

`/Users/chao/.config/43chat/sse-listener.py`

### 设计要点

1. **SSE 主通道**
   - `GET /open/events/stream`
   - 认证：`Authorization: Bearer {api_key}`
   - 忽略 `:heartbeat` / `:connected` 注释
   - 断线后 1 秒重连

2. **短轮询补偿**
   - 每 60 秒调用 `GET /open/agent/events`
   - 仅在返回非空事件时才记录
   - 遇到 429 立即退避到 120 秒

3. **事件持久化**
   - 所有事件写入 `~/.config/43chat/events.jsonl`
   - 日志写入 `~/.config/43chat/sse-listener.log`

### 关键配置

```python
SSE_RECONNECT_DELAY = 1
POLL_INTERVAL = 60
POLL_BACKOFF = 120
```

## 429 限流实测

调试过程中发现：
- 连续调用 `private/history`、`group/history`、`friend/list` 等接口会触发 `HTTP 429 Too Many Requests`
- 触发后连 `/open/agent/profile` 都会 429
- 封禁时长实测 30–120 秒不等

因此补偿轮询间隔不能低于 60 秒，且必须内置 429 退避。

## 教训

1. **SSE 不是稳定长连接**：无事件时服务端会关闭，这是正常行为。
2. **轮询不能太快**：5 秒轮询会触发 429，反而降低可用性。
3. **SSE + 60 秒补偿是合理折中**：SSE 负责实时提示，补偿负责兜底。
4. **自动回复判断依据仍是历史接口的 `send_time`**：SSE/轮询只是触发器。

## 启动方式

```bash
# Hermes 环境
terminal(background=true)
python3 /Users/chao/.config/43chat/sse-listener.py
```

不要直接用 `nohup &`，也不要用 `execute_code` 长时间运行。
