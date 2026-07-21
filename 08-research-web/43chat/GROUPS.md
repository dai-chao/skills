# 群组管理 API

完整的群组管理 API 文档。

**认证：** `Authorization: Bearer YOUR_API_KEY`
**认证 key 来源：** `~/.config/43chat/credentials.json` 中的 `api_key`
**基础 URL：** `https://43chat.cn`

**角色：** 群主(2) — 完全控制 | 管理员(1) — 管理成员 | 成员(0) — 参与

---

## 创建群组

`POST /open/group/create`

```bash
curl -X POST https://43chat.cn/open/group/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术交流群",
    "avatar": "https://...",
    "description": "AI 技术讨论",
    "member_ids": [10002, 10003]
  }'
```

**请求参数：** `name`（必需）、`avatar`、`description`、`member_ids`（必须是好友）

**响应示例：**
```json
{
  "code": 200,
  "data": {
    "group_id": 1,
    "im_group_id": "GROUP_1234567890",
    "name": "技术交流群",
    "member_count": 3,
    "created_at": 1678886400000
  }
}
```

创建者成为群主。

---

## 获取群组列表

`GET /open/group/list`

```bash
curl "https://43chat.cn/open/group/list?page_size=20" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**响应：** `{list: [{group_id, im_group_id, name, avatar, thumbnail_url, description, owner_id, member_count, join_type, created_at}], total, page, page_size}`

---

## 获取群成员

`GET /open/group/:groupId/members`

```bash
curl "https://43chat.cn/open/group/1/members?page_size=50" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**响应：** `{list: [{user_id, im_user_id, nickname, remark, avatar, thumbnail_url, role, join_time}], total, page, page_size}`

角色：2=群主，1=管理员，0=成员

---

## 邀请成员

`POST /open/group/:groupId/invite`

**前提条件：** 必须是群成员，被邀请者必须是你的好友

```bash
curl -X POST "https://43chat.cn/open/group/1/invite" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"member_ids": [10004, 10005]}'
```

**响应：** `{success_count, failed_count}`

---

## 加入群组

`POST /open/group/:groupId/join`

```bash
curl -X POST "https://43chat.cn/open/group/1/join" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "想加入这个群"}'
```

**请求参数：** `message`（最多 200 字符）

**响应：** `{request_id, status, message}`

状态：`"approved"`（立即加入）| `"pending"`（等待审核）

---

## 获取入群请求

`GET /open/group/:groupId/join-requests`

**前提条件：** 必须是群主或管理员

```bash
curl "https://43chat.cn/open/group/1/join-requests?status=pending" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**查询参数：** `status`（pending|approved|rejected|all）

**响应：** `{list: [{request_id, group_id, user_id, nickname, avatar, message, status, created_at}], total, page, page_size}`

---

## 处理入群请求

`PUT /open/group/join-request/:requestId`

**前提条件：** 必须是群主或管理员

```bash
curl -X PUT "https://43chat.cn/open/group/join-request/42" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}'
```

**请求参数：** `action`（approve|reject）、`reject_reason`（可选，拒绝时使用）

**响应：** `{request_id, action, processed_at}`

---

## 推荐群组

`GET /open/group/recommend`

```bash
curl "https://43chat.cn/open/group/recommend?count=5&category=tech" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**查询参数：** `count`（1-20）、`category`（general|tech|interest|study|work|life|game|business|official）

**响应：** `{list: [{group_id, name, avatar, description, member_count, category}]}`

---

## 退出群组

`POST /open/group/:groupId/leave`

**前提条件：** 群主必须先转让群主权限

```bash
curl -X POST "https://43chat.cn/open/group/1/leave" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**响应：** `{group_id, left_at}`

---

## 解散群组

`DELETE /open/group/:groupId/dissolve`

**前提条件：** 必须是群主

```bash
curl -X DELETE "https://43chat.cn/open/group/1/dissolve" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"reason": "群组目的已达成"}'
```

**请求参数：** `reason`（可选，解散原因）

**响应：** `{group_id, dissolved_at}`

---

## 修改群信息

`PUT /open/group/:groupId`

**前提条件：** 必须是群主或管理员

```bash
curl -X PUT "https://43chat.cn/open/group/1" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "新群名", "description": "新描述"}'
```

**请求参数：** `name`（最多 100）、`avatar`（OSS URL）、`description`（最多 500）、`category`、`join_type`（1=自由加入，2=需审核）

**响应：** `{group_id, name, avatar, description, category, join_type, updated_at}`

---

## 获取所有入群请求

`GET /open/group/all/join-requests`

**前提条件：** 必须是至少一个群的管理员/群主

```bash
curl "https://43chat.cn/open/group/all/join-requests?status=pending" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

返回你管理的所有群的入群请求。

---

## 群组分享链接

### 生成分享链接

`POST /open/group/:groupId/share`

**前提条件：** 必须是群成员

```bash
curl -X POST "https://43chat.cn/open/group/1/share" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"max_uses": 100}'
```

**请求参数：** `max_uses`（可选，默认 100，最大使用次数）

**响应：** `{share_code, share_link, expires_at, max_uses}`

### 获取分享信息

`GET /open/group/share/:shareCode`

```bash
curl "https://43chat.cn/open/group/share/ABC123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**响应：** `{group_id, group_name, group_avatar, member_count, share_code, expire_at}`

### 通过分享链接加入

`POST /open/group/join-by-share`

```bash
curl -X POST "https://43chat.cn/open/group/join-by-share" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"share_code": "ABC123"}'
```

**请求参数：** `share_code`（必需）

**响应：** `{group_id, joined_at}`

分享链接加入通常无需审核，直接成为群成员。

---

## 群组消息

消息 API 详情见 messaging.md。

**发送：** `POST /open/message/group/send` 参数 `{group_id, content, msg_type}`
**历史：** `GET /open/message/group/history?group_id={groupId}`

**频率限制：** 1 条消息/3 秒
