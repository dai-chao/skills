# 农场好友 ≠ 43Chat 好友（Pitfall）

43Farm 的 `farm.friends` 返回的是"已激活农场的好友"，但对方可能**未激活农场**（`farmActivated: false`），此时 `farm.view` 会返回空数据。这**不代表对方不是 43Chat 好友**。

## 正确做法
- 判断是否为 43Chat 好友时，应调 `GET /open/friend/list` 或 `GET /open/friend/user/:userId`
- 农场查不到信息时，直接走 43Chat 消息接口（`private/history`、`private/send`）验证好友关系
- 不要因 `farm.view` 返回空就假设对方不是好友

## 错误做法
看到 `farm.view` 返回空，就告诉用户"对方不是好友"或"查不到信息"，导致用户困惑。本 session 中用户明确纠正"已经是好友了"，说明此前判断有误。
