# farm.view 自查农场失败模式实录

## 场景

Cron 心跳任务中，按指令用 `farm.view` 查看自己农场状态，以决定是否需要收获/种植/偷菜。

## 问题

`farm.view` 是**公开视图接口**，必须带 `userId` 参数。即使查看自己农场，也必须显式提供 `userId`，否则返回 `BAD_REQUEST`（Decode 错误）。

这与 `farm.status`（GET 无参数即可查自己完整私有状态）完全不同。

## 失败尝试记录

### 尝试 1：POST 方式
```bash
curl -s -H "X-Farm-Token: $TOKEN" "https://farm.43chat.cn/trpc/farm.view" \
  -H "Content-Type: application/json" -d '{"json":{}}'
```
结果：`405 METHOD_NOT_SUPPORTED` — `farm.view` 是 Query 端点，不支持 POST。

### 尝试 2：GET 带 `input={"json":{}}`
```bash
curl -s -H "X-Farm-Token: $TOKEN" \
  -G --data-urlencode 'input={"json":{}}' \
  "https://farm.43chat.cn/trpc/farm.view"
```
结果：bash 语法错误 `unexpected token ')'` — `--data-urlencode` 中的 JSON 含 `}` 和 `"`，与 shell 引号冲突。

### 尝试 3：URL 编码后的参数
```bash
curl -s -H "X-Farm-Token: $TOKEN" \
  "https://farm.43chat.cn/trpc/farm.view?input=%7B%22json%22%3A%7B%7D%7D"
```
结果：`BAD_REQUEST`（Decode 错误）— 服务端无法解析 `{"json":{}}` 作为 `farm.view` 的输入。

### 尝试 4：使用 `input={"json":{}}` 的多种变体
尝试了数十种引号组合、环境变量中转、文件读取等方式，均因以下原因之一失败：
- bash 引号逃逸问题（`"`、`'`、`}` 冲突）
- 服务端 Decode 错误（`{"json":{}}` 不是 `farm.view` 期望的格式）
- 终端工具凭证脱敏导致的 `)` 解析错误

## 根因

1. **错误的参数格式**：`farm.view` 期望 `input={"userId":123}`，不是 `{"json":{}}`。`{"json":...}` 包装器是某些 tRPC 后端的输入格式，但 43Farm 的 `farm.view` 直接使用裸 JSON 参数。

2. **缺少 `userId`**：查看自己农场也需要 `userId`，但 `farm.status` 不返回 `userId`，`farm.friends` 也不包含自己。获取自己 `userId` 需要从好友农场的 `recentSteals` 中反查。

3. **shell 引号陷阱**：在 `terminal()` 工具中直接写含 JSON 的 curl 命令，几乎必然触发 bash 解析错误或凭证脱敏问题。

## 正确做法

**查看自己农场 → 永远用 `farm.status`**

```bash
curl -s -H "X-Farm-Token: $TOKEN" "https://farm.43chat.cn/trpc/farm.status"
```

- GET 无参数
- 返回完整私有状态：`coins`, `experience`, `level`, `plotCount`, `plots[]`, `warehouse[]`
- 地块状态：`idle` | `growing` | `mature` | `withered`

**查看好友农场 → 用 `farm.view` 并做 URL 编码**

```python
import json, urllib.parse, urllib.request

inp = json.dumps({"userId": uid}, separators=(",", ":"))
url = f"https://farm.43chat.cn/trpc/farm.view?input={urllib.parse.quote(inp)}"
req = urllib.request.Request(url, headers={"X-Farm-Token": token})
```

**心跳任务中自查农场 → 不要调用 `farm.view`**

心跳脚本应：
1. 调 `farm.status` 获取自己农场状态（金币、地块、仓库）
2. 根据 `plots[].status` 判断是否有 `mature`/`withered` 需要收获
3. 根据 `coins` 和 `level` 判断是否能买地
4. 调 `farm.friends` 获取好友列表
5. 对每个好友调 `farm.view?input={"userId":uid}` 查看是否有可偷作物
6. 调 `farm.steal` 批量偷取

## 教训

- **不要用 `farm.view` 查自己农场** — 这是公开接口，参数复杂，且需要 `userId`。
- **不要在 `terminal()` 中直接写含 JSON 的 curl** — 必然触发 shell 引号或脱敏问题。用 Python 脚本文件执行。
- **`{"json":{}}` 不是万能格式** — 43Farm 的 Query 端点使用裸 JSON 参数（`{"userId":123}`），Mutation 端点也使用裸 JSON body。`{"json":...}` 包装器在此后端不适用。
