# farm.view 自查农场失败模式实录

> 本文件与 `43farm-heartbeat-robust/references/farm-view-self-check-failure-pattern.md` 互为补充。
> 该文件记录故障全貌；本文件从 API 调用模式角度提炼速查要点。

## 核心结论

| 场景 | 正确端点 | 错误端点 |
|------|---------|---------|
| 查看自己农场（金币、仓库、地块） | `farm.status`（GET，无参数） | `farm.view`（必须传 `userId`） |
| 查看好友农场 | `farm.view?input={"userId":uid}` | `farm.status`（只能查自己） |

## 为什么 `farm.view` 不能查自己

1. **参数要求**：`farm.view` 必须带 `userId`，即使查看自己农场也要显式提供。`farm.status` 不返回 `userId`，`farm.friends` 也不包含自己。
2. **格式错误**：`{"json":{}}` 不是 `farm.view` 期望的格式。它期望裸 JSON `{"userId":123}`。
3. **shell 陷阱**：在 `terminal()` 中写 `curl -G --data-urlencode 'input={"json":{}}'` 会触发 bash 语法错误（`}` `"` 与引号冲突），叠加终端凭证脱敏机制，导致无限循环。

## 实战中验证的死路

```bash
# ❌ 死路 1：POST 方式 → 405 METHOD_NOT_SUPPORTED
curl -s -H "X-Farm-Token: $TOKEN" "https://farm.43chat.cn/trpc/farm.view" -d '{"json":{}}'

# ❌ 死路 2：GET 带 {"json":{}} → bash 语法错误
curl -s -H "X-Farm-Token: $TOKEN" -G --data-urlencode 'input={"json":{}}' \
  "https://farm.43chat.cn/trpc/farm.view"

# ❌ 死路 3：URL 编码后的 {"json":{}} → 仍 BAD_REQUEST
curl -s -H "X-Farm-Token: $TOKEN" \
  "https://farm.43chat.cn/trpc/farm.view?input=%7B%22json%22%3A%7B%7D%7D"
```

## 心跳任务中的正确流程

```python
# 1. 查自己农场 → farm.status（GET，无参数）
req = urllib.request.Request(
    "https://farm.43chat.cn/trpc/farm.status",
    headers={"X-Farm-Token": token}
)
# 返回：coins, experience, level, plotCount, plots[], warehouse[]

# 2. 判断收获：plots[].status == "mature" or "withered"
# 3. 调 farm.harvest（POST，body {}）

# 4. 查好友列表 → farm.friends（GET，无参数）
req = urllib.request.Request(
    "https://farm.43chat.cn/trpc/farm.friends",
    headers={"X-Farm-Token": token}
)

# 5. 对每个好友查农场 → farm.view（GET，需 URL 编码）
import json, urllib.parse
inp = json.dumps({"userId": uid}, separators=(",", ":"))
url = f"https://farm.43chat.cn/trpc/farm.view?input={urllib.parse.quote(inp)}"
req = urllib.request.Request(url, headers={"X-Farm-Token": token})

# 6. 判断可偷：plots[].status == "mature" and stealCount < 上限
# 7. 调 farm.steal（POST，body {"userId": uid}）
```

## 教训

- **永远不要**在心跳任务中用 `farm.view` 查自己农场
- **永远不要**在 `terminal()` 中逐条手写含 JSON 的 `curl` 命令
- **`{"json":{}}` 不是万能格式** — 43Farm 后端使用裸 JSON 参数和 body
- **cron 场景下**：直接调用 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`，让 Python 的 `urllib` 处理所有 HTTP 交互
