# farm.view URL 编码陷阱：curl 直接拼接 JSON 参数

## 问题

在手动实现偷菜逻辑时，直接拼接 JSON 到 URL 会导致 curl 失败：

```bash
# ❌ 错误：未编码的 JSON 含空格和特殊字符
curl -s "https://farm.43chat.cn/trpc/farm.view?input={\"userId\": 53580}"
# curl: (3) URL using bad/illegal format or missing URL
```

## 根因

`json.dumps({"userId": user_id})` 产生的字符串包含空格（`{"userId": 53580}`），curl 将空格视为 URL 非法字符。

## 修复

使用 `urllib.parse.quote` 对 JSON 字符串编码：

```python
import urllib.parse
view = curl_get(f"farm.view?input={urllib.parse.quote(json.dumps({'userId': user_id}))}")
# 结果：farm.view?input=%7B%22userId%22%3A%2053580%7D
```

## 脚本中的正确处理

官方 `heartbeat.py` 脚本已正确处理此编码。手动实现时才暴露此问题。

## 相关参考

- `43farm-heartbeat-robust/references/farm-view-url-encoding-pitfall.md` — 更详细的 URL 编码说明（使用 urllib.request）
- `43farm-heartbeat-executor/references/session-2026-06-16-cron-instruction-override-failure.md` — 本问题的会话上下文
