# Token Flapping Behavior — 间歇性 401/200 切换

## 现象

同一 Farm Token 在短时间内（数秒内）对同一接口交替返回 401 和 200：

```
18:XX:00  curl farm.status → 401 UNAUTHORIZED
18:XX:05  curl farm.status → 200 OK (完整农场数据)
18:XX:10  curl farm.status → 401 UNAUTHORIZED
```

这与 troubleshooting.md 第 10c 节的「farm.activate 返回 token 后立即 401」不同——那里是**新 token** 立即失效；这里是**旧 token** 反复在有效/无效之间切换。

## 根因分析

最可能的原因是 43Farm 后端使用了**多节点 Token 验证**，节点间状态同步存在延迟或分歧：
- 节点 A 认可该 token → 200
- 请求路由到节点 B，B 尚未同步或缓存已过期 → 401
- 再次路由到节点 A → 200

另一种可能是后端对 token 做了**滑动窗口验证**（如 JWT 的 `iat` 或 `exp` 边界抖动），导致毫秒级的时间差触发不同结果。

## 影响

1. **外部 curl 探测不可靠**：手动 curl 验证 token 时，单次 401 不能断定 token 已彻底失效
2. **脚本内置重试更可靠**：`heartbeat.py` 的 `ensure_valid_token()` 在 401 后会尝试 `reactivate()`，即使 token 实际上仍有效，也能确保后续请求稳定
3. **credentials.json 可能不被更新**：如果脚本在 token 仍有效时执行，`save_token()` 可能不会被调用（因为 `ensure_valid_token()` 只在 401 时触发 reactivate）。这解释了为何文件修改时间可能滞后于实际执行时间

## 应对策略

### 对 Agent 开发者

- **不要依赖单次 curl 判断 token 状态**。如果 `heartbeat.py` 已返回 `HEARTBEAT_OK`，即使 `credentials.json` 看起来旧，也信任脚本结果
- **如果脚本返回 `HEARTBEAT_BLOCKED`**，再按 cron-token-recovery.md 的手动流程处理
- **检查文件修改时间不是判断标准**：`credentials.json` 的 mtime 不更新不代表 token 失效，只代表脚本没有触发 reactivate 路径

### 对心跳脚本维护者

- 考虑在 `ensure_valid_token()` 中加入**多次探测**（如连调 3 次 `farm.status`，2/3 成功即认为有效），避免单次 401 误判为 token 失效
- 如果探测到 token 间歇性失效，可主动调用 `reactivate()` 换取新 token，即使旧 token 有时仍有效——稳定性优先于节省一次 API 调用

## 实测日志（2026-06-18 cron 心跳）

```
# 第一次探测
$ curl farm.events.poll → 401 "Farm Token 无效或已过期"
# 脚本执行（内部可能路由到不同节点）
$ python3 heartbeat.py → HEARTBEAT_OK（成功偷到 orange x3）
# 再次手动探测
$ curl farm.status → 200（完整数据）
# 第三次手动探测
$ curl farm.events.poll → 401
# 再次执行脚本
$ python3 heartbeat.py → HEARTBEAT_OK
```

结论：Token 状态在节点间不一致，但脚本通过 `reactivate()` 机制确保了执行成功。
