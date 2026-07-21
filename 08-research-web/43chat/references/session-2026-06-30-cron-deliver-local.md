# 2026-06-30 43Chat cron 任务微信限流处理记录

**会话日期**: 2026-06-30  
**涉及任务**: 43chat-sse-listener、43chat-auto-chat、43farm-heartbeat

## 现象

用户查看 cron 任务列表时发现：
- `43chat-sse-listener` 和 `43chat-auto-chat` 的 `last_status` 为 `error`
- `last_delivery_error` 显示：`Weixin send failed: iLink sendmessage rate limited; cooldown active for 30.0s`

## 根因

- Hermes cron 任务默认 `deliver` 为 `origin`，会把任务输出发到当前会话
- 如果当前会话绑定微信（如通过 WeChat iLink 桥接），输出会发到微信
- `43chat-auto-chat` 每 1 分钟运行一次、`43chat-sse-listener` 每 5 分钟运行一次，输出频繁
- 微信 iLink 有 30 秒发送冷却期，频繁发送触发限流

## 用户反馈

用户说："任务结果不要发我微信"

## 处理

把所有 43Chat 相关 cron 任务的 `deliver` 改为 `local`：
- `43chat-sse-listener` → `local`
- `43chat-auto-chat` → `local`
- `43farm-heartbeat` → `local`

```python
# Hermes cronjob API
cronjob(action='update', job_id='...', deliver='local')
```

## 结果

- 任务继续正常运行
- 输出不再尝试发到微信
- 不再触发 iLink 限流错误

## 教训

1. 高频运行的 cron 任务默认 `deliver='origin'` 容易触发微信限流
2. 用户明确说"不要发微信"时，立即把所有相关任务改为 `deliver='local'`
3. `deliver='local'` 只保存结果，不发送到任何消息平台
4. 之后用户说"把 2 和 3 删掉"时，直接删除对应 cron 任务即可

## 关联

- 主 skill: `43chat/SKILL.md` 中"自动回复守护进程"和"SSE 接入实战"小节的 cron deliver pitfall
