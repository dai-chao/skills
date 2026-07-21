# Session 2026-06-29: Token Flapping — refreshToken 成功但新 token 立即 401

## 场景

Cron 心跳任务执行时，发现 Farm Token 已过期（`farm.status` 返回 401）。调用 `auth.refreshToken` 成功返回新 token，但用新 token 调用任何业务接口（`farm.status`、`farm.events.poll`、`farm.steal`）立即再次返回 401。

## 实测时间线

```
T+0:  farm.status → 401 "Farm Token 无效或已过期"
T+1:  auth.refreshToken → 成功返回新 farmToken (eyJhbG...V-EI)
T+2:  farm.status (新 token) → 401 "Farm Token 无效或已过期"
T+3:  auth.refreshToken (新 token) → 成功返回又一个新 farmToken (eyJhbG...xnNc)
T+4:  farm.status (第二个新 token) → 401 "Farm Token 无效或已过期"
T+5:  auth.refreshToken (第二个新 token) → 失败 "旧 token 不合法或 43chat session 已失效"
```

**关键观察**：`refreshToken` 连续两次成功，但返回的 token 均立即失效。第三次 `refreshToken` 失败，说明后端状态已彻底不一致。

## 根因分析

这不是客户端问题，而是后端 Token 签发与验证状态之间的**竞态条件或缓存不一致**：

1. `refreshToken` 端点验证旧 token 时，旧 token 在验证缓存中仍被视为「有效但即将过期」
2. 后端签发新 token 并返回给客户端
3. 但新 token 的签发操作同时触发了旧 token 的「立即失效」标记
4. 由于缓存同步延迟，新 token 在验证端点也被标记为「由已失效的父 token 签发」→ 401
5. 第二次 `refreshToken` 重复上述过程（旧 token 在验证缓存中短暂恢复为「有效」）
6. 第三次时后端状态彻底同步完成，旧 token 被永久标记为失效 → `refreshToken` 失败

## 正确处理策略

**不要循环调用 `refreshToken`**。一旦发现以下模式，立即降级到完整重新激活流程：

```
if refreshToken succeeds but next API call with new token returns 401:
    → 这是 token flapping，不是临时网络问题
    → 直接执行 authorize-app → farm.activate 重新获取 Farm Token
    → 不要再次尝试 refreshToken（会浪费一次后端调用配额，且大概率失败）
```

## 与「Token 立即失效」的区别

| 模式 | 现象 | 根因 | 处理 |
|------|------|------|------|
| Token Flapping（本页） | `refreshToken` 成功但新 token 立即 401，可重复 2-3 次 | 后端签发/验证缓存不一致 | 跳过 refresh，直接重新激活 |
| Token 立即失效 | `farm.activate` 成功但新 token 立即 401 | 后端 Token 生成与验证不同步 | 等待 3-5 秒后重试，或联系官方群 |
| Token 正常过期 | `refreshToken` 成功，新 token 正常工作 | 正常生命周期 | 无需特殊处理 |

## 代码实现（heartbeat.py 逻辑）

```python
def refresh_token(current_token):
    """尝试 refreshToken，检测 flapping 模式。"""
    resp = call_api("auth.refreshToken", token=current_token, body={})
    if "error" in resp:
        return None  # 彻底失效，走重新激活
    new_token = resp.get("farmToken")
    
    # 验证新 token 是否有效（关键步骤！）
    verify = call_api("farm.status", token=new_token)
    if "error" in verify:
        # Token Flapping  detected — 新 token 立即失效
        return None  # 直接走重新激活，不要循环 refresh
    return new_token
```

## 相关参考

- `references/cron-token-recovery.md` — 完整 Token 恢复流程（含 authorize-app → farm.activate）
- `references/session-2026-06-23-token-flapping-behavior.md` — 早期 token flapping 观察记录
- `scripts/heartbeat.py` — 内置 Token 恢复逻辑（已包含 flapping 检测）
