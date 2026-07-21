# 43Chat SSE 修复 + 自动回复重启记录

**会话日期**: 2026-06-30  
**涉及 Agent**: 赫哲人 (user_id 53613)

## 用户问题

1. "现在的SSE我感觉没用啊，有用户发了消息 都没有回复"
2. "按照文档修复SSE 连接"
3. 选择方案 1：SSE + 短轮询补偿
4. "重新启动" 自动回复守护进程

## 排查结论

### SSE 部分

- 原 `43chat_sse_listener.py` 只监听不回复，且断线重连间隔 3 秒
- 实测 `GET /open/events/stream` 返回 `:connected` 后 5 秒左右被服务端关闭
- 这是正常行为：无事件时服务端主动关闭空闲连接
- 单独依赖 SSE 会漏消息，必须加短轮询补偿

### 自动回复部分

- 原 `auto_chat_daemon.py` 轮询间隔 10 秒，大量调用好友历史
- 触发 429 限流，daemon 反复失败
- 通用回复只有固定一句 "有意思，继续说。你对这个怎么看？"，导致重复
- 用户 53597 吒吒收到连续三次 "嗯？展开说说？"

## 修复内容

### SSE 监听脚本

**路径**: `/Users/chao/.config/43chat/sse-listener.py`

- 按官方 SSE.md 实现 SSE 事件解析
- 断线后 1 秒重连
- 每 60 秒调用 `GET /open/agent/events` 做补偿
- 遇到 429 退避到 120 秒
- 事件写入 `~/.config/43chat/events.jsonl`

### 自动回复守护进程

**路径**: `/Users/chao/.hermes/scripts/auto_chat_daemon.py`

- 轮询间隔从 10 秒改为 60 秒
- 新增 `RATE_LIMIT_BACKOFF = 300`，遇到 429 休眠 5 分钟
- 通用回复改为随机回复池，避免重复
- AI Agent 通用回复也改为随机池
- 过滤空内容消息
- 捕获 `urllib.error.HTTPError` 429 异常

## 关键配置

```python
# sse-listener.py
SSE_RECONNECT_DELAY = 1
POLL_INTERVAL = 60
POLL_BACKOFF = 120

# auto_chat_daemon.py
CHECK_INTERVAL = 60
RATE_LIMIT_BACKOFF = 300
```

## 启动方式

```bash
# SSE 监听（Hermes 后台）
terminal(background=true)
python3 /Users/chao/.config/43chat/sse-listener.py

# 自动回复守护进程（Hermes 后台）
terminal(background=true)
python3 ~/.hermes/scripts/auto_chat_daemon.py
```

## 验证

- 给 53676 发送测试消息 "测试一下自动回复是否正常工作"
- daemon 在 2.2 秒延迟后自动回复
- 日志确认：`回复 53676 (延迟2.2s): '测试一下自动回复是否正常工作' -> 'AI社交确实...'`

## 教训

1. SSE 无事件时服务端会关闭连接，不能单独依赖 SSE 做实时聊天
2. 轮询间隔过短（10 秒）会触发 429，反而降低可用性
3. 固定通用回复会让用户觉得机器人重复、机械
4. 自动回复判断必须基于历史接口的 `send_time`，而不是只看事件
5. 启动 daemon 前必须检查是否已有实例在运行，避免多实例重复回复
