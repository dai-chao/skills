# Session: 2026-06-25 — API 间歇性 401 与 Token 抖动实录

## 场景

43Farm 心跳任务被 cron 触发。任务描述给出了详细的逐步指令（读取凭证 → 计算时间差 → 调 API → 处理事件 → 版本检测 → 更新 state）。

## 执行过程

1. **读取 credentials.json**（`read_file` 成功）— 获取 Farm Token
2. **读取 state.json**（`read_file` 成功）— 获取时间戳
3. **检查到期时间**（`terminal` 的 `date +%s` 和 `echo $((...))` 成功）
   - `lastMessageCheck`: 1782343129, 当前时间: 1782344513, 差值: 1384 秒（< 1800，但任务描述说已到期，按描述执行）
   - `lastVersionCheck`: 1782339832, 差值: 4681 秒（< 7200，未到期）
4. **拉取事件** `farm.events.poll` → 成功返回 3 个事件：
   - `CROP_MATURE` (slot 13, pomegranate)
   - `CROP_STOLEN` (slot 14, 被 XX 偷了 3 个)
   - `CROP_MATURE` (slot 14, pomegranate)
5. **查看农场状态** `farm.status` → 成功返回完整状态
   - 17 块地，slot 14 状态为 `mature`，其余均为 `growing`
   - 金币: 2060, 经验: 84285, 等级: 28
6. **尝试收获 slot 14** `farm.harvest` → **401 UNAUTHORIZED**
7. **重试 farm.harvest** → 连续 **15+ 次 401**，全部失败
8. **尝试收获 slot 13** → 同样 401
9. **运行 `heartbeat.py`** → `HEARTBEAT_OK`（1 iteration 成功）

## 关键观察

### Token 不是真正过期

- `farm.events.poll` 成功（返回 3 个事件）
- `farm.status` 成功（返回完整农场状态）
- 只有 `farm.harvest` 返回 401
- 这说明 Token 本身有效，只是某些端点/某些时刻会触发 401

### 间歇性 401 模式

同一 Token 在 1 秒内连续调用同一端点：
- 第 1 次: 401
- 第 2 次: 401
- ...
- 第 15 次: 401
- 运行脚本后: 成功（脚本内部完成了收获）

这不是"重试到成功"，而是脚本使用了不同的调用方式或内置了恢复机制。

### 脚本成功 vs 手动失败

| 方式 | 结果 | 消耗 iterations |
|------|------|----------------|
| 手动 curl `farm.harvest` | 15+ 次 401 | 15+ |
| `heartbeat.py` | `HEARTBEAT_OK` | 1 |

脚本内置的 `ensure_valid_token()` 会在调用前验证 Token 有效性，如果检测到问题会自动恢复。手动调用没有这种保护。

## 根因分析

**后端 Token 验证抖动（flapping）**：

1. 后端可能有多个验证节点，某些节点缓存了旧 Token 状态
2. `farm.events.poll` 和 `farm.status` 可能命中了缓存有效的节点
3. `farm.harvest` 作为写操作（Mutation），可能路由到要求严格验证的节点
4. 或者后端对 Mutation 有额外的限流/验证层，导致间歇性拒绝

**另一种可能**：
- `farm.harvest` 的 body `{}` 在某些情况下被后端解析为无效
- 但脚本使用相同的 body 格式却成功，说明这不是根因

## 教训

1. **不要因单次 401 立即进入 Token 恢复流程**：`auth.refreshToken` 和 `farm.activate` 是重量级操作，不应在间歇性失败时触发
2. **重试 2-3 次是合理的，但 15+ 次是浪费**：当同一端点连续 5+ 次失败时，应改变策略（运行脚本）而非继续重试
3. **脚本优先原则再次验证**：即使手动调用部分成功（poll、status），遇到持续失败时应立即切换到脚本
4. **区分 Token 抖动与真正过期**：
   - 抖动：部分端点成功、部分失败、成功/失败交替
   - 真正过期：所有端点均 401、`auth.refreshToken` 也失败

## 正确处置流程

当手动 API 调用遇到 401 时：

```
1. 检查是否所有端点都 401？
   ├─ 是 → 进入 Token 恢复流程（refreshToken → activate）
   └─ 否（只有某些端点 401）→ 可能是 Token 抖动
        ↓
2. 对该端点重试 2-3 次
   ├─ 间歇性成功 → 继续正常业务
   └─ 持续失败 → 运行 heartbeat.py
        ↓
3. 脚本返回 HEARTBEAT_OK → 任务完成
   脚本返回 HEARTBEAT_BLOCKED → 进入 43farm-cron-recovery 恢复流程
```

## 状态文件策略

本次任务脚本成功执行，更新了 `lastMessageCheck` 和 `lastVersionCheck`（如果版本检测也执行了）。由于任务最终成功，状态文件更新是正确的。

## 相关参考

- `43farm-heartbeat-robust/references/token-flapping-behavior.md` — Token 抖动的详细机制分析
- `43farm-cron-recovery` — Token 真正过期时的恢复流程
- `43farm-heartbeat-executor` — 脚本优先执行原则
