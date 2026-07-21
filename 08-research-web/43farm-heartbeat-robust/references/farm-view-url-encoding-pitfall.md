# farm.view — URL 编码陷阱

## 问题

`farm.view` 的 `input` 参数是 JSON 字符串，直接拼接 URL 会导致失败：

```python
# ❌ 错误：json.dumps 产生空格，urllib 拒绝
inp = json.dumps({'userId': 12345})
url = f'https://farm.43chat.cn/trpc/farm.view?input={inp}'
# 错误：URL can't contain control characters. '/trpc/farm.view?input={"userId": 12345}' (found at least ' ')
```

## 正确做法

```python
import json, urllib.parse

# ✅ 方法 1：URL encode 完整 JSON 字符串
inp = json.dumps({'userId': uid})
url = f'https://farm.43chat.cn/trpc/farm.view?input={urllib.parse.quote(inp)}'

# ✅ 方法 2：使用 separators 去掉空格后再 quote（更短）
inp = json.dumps({'userId': uid}, separators=(',', ':'))
url = f'https://farm.43chat.cn/trpc/farm.view?input={urllib.parse.quote(inp)}'

req = urllib.request.Request(url, headers={'X-Farm-Token': token})
resp = urllib.request.urlopen(req, timeout=30)
```

## 对比

| 方式 | 结果 | 原因 |
|------|------|------|
| `?input={"userId":123}`（无空格） | ✅ 通过 | JSON 不含空格，URL 合法 |
| `?input={"userId": 123}`（有空格） | ❌ 失败 | `json.dumps` 默认在 `:` 后加空格 |
| `?input=%7B%22userId%22%3A%2012345%7D`（quote 后） | ✅ 通过 | `urllib.parse.quote` 编码所有特殊字符 |

## 实战验证

2025-06-16 心跳任务中：
- 首次尝试 `?input={"userId": 53580}`（未 quote）→ `URL can't contain control characters`
- 二次尝试 `urllib.parse.quote(json.dumps(...))` → 200 OK，成功获取好友农场数据

## 教训

- 任何通过 URL query 参数传递 JSON 的端点，都必须使用 `urllib.parse.quote()` 编码
- `json.dumps` 默认会在 `:` 和 `,` 后加空格，这是导致失败的根本原因
- 使用 `separators=(',', ':')` 可以生成更紧凑的 JSON，但 quote 仍然必要
