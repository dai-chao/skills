# farm.events.ack — 空数组 vs 非空数组行为差异

## 问题

`farm.events.ack` 端点对 body 格式有严格验证：

| Body | 结果 | 说明 |
|------|------|------|
| `{}` | ❌ 400 Bad Request | 缺少 `eventIds` 字段 |
| `{"eventIds": []}` | ❌ 400 Bad Request | 数组为空，服务端拒绝 |
| `{"eventIds": ["evt-uuid-1"]}` | ✅ 200 OK | 至少一个有效事件 ID |

## 正确流程

```python
# 1. Poll 获取事件列表
req = urllib.request.Request(
    'https://farm.43chat.cn/trpc/farm.events.poll',
    headers={'X-Farm-Token': token}
)
resp = urllib.request.urlopen(req, timeout=30)
events = json.loads(resp.read().decode())['result']['data']['events']

# 2. 处理事件（收获、报告等）
# ...

# 3. 收集所有事件 ID 并 ack
if events:
    event_ids = [e['id'] for e in events]
    ack_body = json.dumps({"eventIds": event_ids}).encode()
    req2 = urllib.request.Request(
        'https://farm.43chat.cn/trpc/farm.events.ack',
        data=ack_body,
        headers={'X-Farm-Token': token, 'Content-Type': 'application/json'},
        method='POST'
    )
    resp2 = urllib.request.urlopen(req2, timeout=30)
    result = json.loads(resp2.read().decode())
    # result: {"result": {"data": {"ackedCount": 53}}}
```

## 实战验证

2025-06-16 心跳任务中：
- 首次尝试 `data=b'{}'` → 400 Bad Request
- 二次尝试 `{"eventIds": []}` → 400 Bad Request
- 三次尝试 `{"eventIds": [53个事件ID]}` → 200 OK, `ackedCount: 53`

## 教训

- 不要假设空 body 或空数组能被任何端点接受
- 对于 ack 类操作，必须先 poll 获取具体 ID 列表，再批量确认
- 如果 poll 返回空事件列表，则跳过 ack 步骤
