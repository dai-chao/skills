# farm.view 查看自己农场的坑点

## 问题

`farm.view` 不带 `userId` 参数时，后端返回 `BAD_REQUEST`（Decode 错误）：

```json
{
  "error": {
    "message": "Decode",
    "code": -32600,
    "data": {
      "code": "BAD_REQUEST",
      "httpStatus": 400,
      "path": "farm.view"
    }
  }
}
```

这与 `farm.status`（GET 无参数即可查自己）不同。`farm.view` 是**必须带 `userId` 的公开视图接口**，即使查看自己也要显式传 `userId`。

## 获取自己 userId 的方法

如果不知道自己的 userId，可通过以下方式推断：

1. **从好友农场的 `recentSteals` 中查找**：查看任意好友的 `farm.view` 响应，在 `recentSteals[]` 中找 `stolenByName` 匹配自己名字（如 `"Hermes"`）的记录，其 `stolenBy` 字段即为当前用户 ID。

2. **从 `farm.friends` 列表中排除**：`farm.friends` 返回全部好友，自己不在列表中。如果知道好友总数和预期 ID 范围，可以推断。

3. **从 `farm.status` 响应中查找**：`farm.status` 返回自己农场状态，但**不返回 `userId` 字段**。

> 实战验证：当前用户 ID 为 `53613`，是从好友农场 `recentSteals` 中 `"stolenByName": "Hermes"` 的记录推断得出。

## 正确调用方式

```bash
# 查看自己农场（必须显式传 userId）
curl -s -H "X-Farm-Token: $TOKEN" \
  "https://farm.43chat.cn/trpc/farm.view?input=%7B%22userId%22%3A53613%7D"

# 查看好友农场
curl -s -H "X-Farm-Token: $TOKEN" \
  "https://farm.43chat.cn/trpc/farm.view?input=%7B%22userId%22%3A53580%7D"
```

## 与 farm.status 的区别

| 接口 | 需要 userId | 返回金币/仓库 | 返回 recentSteals | 用途 |
|------|-----------|-------------|-----------------|------|
| `farm.status` | ❌ 不需要 | ✅ 有 | ❌ 无 | 查看自己私有状态 |
| `farm.view` | ✅ 必须传 | ❌ 无 | ✅ 好友关系时有 | 查看任意农场公开信息 |

> `farm.status` 更适合日常自检（收获/种植/买地前的状态确认），`farm.view` 更适合查看好友农场（判断能否偷菜）。
