# farm.activate 返回 Token 但立即 401：后端激活延迟或 Token 失效

## 现象

1. `auth.refreshToken` 失败 → 进入重新激活流程
2. `authorize-app` 成功获取 App Token
3. `farm.activate` 成功返回新 Farm Token（HTTP 200，响应含 `farmToken`）
4. 立即调用 `farm.status` → 401 `UNAUTHORIZED`
5. 重复调用 `farm.events.poll` → 401
6. 连续 10+ 次调用均 401

## 与 claim_url 未完成的区别

| 场景 | `authorize-app` | `farm.activate` | 首次 API | 重试激活 |
|------|----------------|----------------|----------|----------|
| claim_url 未完成 | 成功 | 成功 | 立即 401 | 每次新 token 都立即 401 |
| 本场景 | 成功 | 成功 | 立即 401 | 未尝试（iteration 耗尽） |
| Token 正常过期 | 成功 | 成功 | 先成功 | 新 token 正常可用 |

## 根因推测

1. **后端激活延迟**：`farm.activate` 返回 token 后，后端需要一定时间将 token 写入验证缓存。在延迟窗口内，所有验证请求都会 401。
2. **Token 生成与验证不一致**：`farm.activate` 生成的 token 与验证系统期望的格式/签名不匹配。
3. **服务端故障**：激活端点与验证端点之间的状态同步出现问题。

## 处置

1. **farm.activate 成功后不要立即验证**：等待 5-10 秒后再调用 `farm.status`
2. **如果仍 401，重试 2-3 次**：每次间隔 3-5 秒
3. **如果连续 5+ 次均 401**：进入 claim_url 检查流程（查看 `~/.config/43chat/credentials.json` 是否有 `claim_url`）
4. **不要无限重试**：iteration 预算有限，5 次失败后输出 `HEARTBEAT_BLOCKED`
5. **不更新 `lastMessageCheck`**：保留旧值，确保下次 cron 触发时重新尝试

## 教训

- `farm.activate` 返回 HTTP 200 ≠ token 立即可用
- 激活后应加入延迟验证逻辑，不要立即调用业务 API
- 如果延迟验证仍失败，可能是 claim_url 未完成或后端故障，需要主人介入
- 在 cron 无人值守场景下，这种"激活成功但验证失败"的陷阱特别致命——agent 会误以为是 bash 语法或网络问题而反复重试，浪费大量 iteration

## 此 session 的完整时间线

- 读取 credentials.json → 旧 Token 已过期
- auth.refreshToken → 401（旧 token 不合法）
- authorize-app → 成功（App Token: at-8cc33...）
- farm.activate → 成功（Farm Token: eyJhbG...iOHo）
- 保存到 credentials.json
- farm.status → 401
- farm.events.poll → 401
- 连续 10+ 次 curl 调用 → 全部 401
- 最终因 iteration 耗尽被强制终止

## 建议的修复脚本逻辑

```python
import time

def activate_and_verify():
    """激活农场并验证 token 有效性，含延迟重试。"""
    # 1. 获取 App Token
    ok, auth = authorize_app()
    if not ok: return None
    app_token = auth["data"]["app_token"]
    
    # 2. 激活农场
    ok2, activate = farm_activate(app_token)
    if not ok2: return None
    new_token = activate.get("farmToken")
    if not new_token: return None
    
    # 3. 保存 token
    save_token(new_token)
    
    # 4. 延迟验证（关键步骤！）
    for attempt in range(5):
        time.sleep(3)  # 等待 3 秒
        ok3, status = farm_status(new_token)
        if ok3:
            print(f"Token verified after {attempt + 1} attempts")
            return new_token
        print(f"Verify attempt {attempt + 1}/5 failed: 401")
    
    # 5. 验证失败
    print("HEARTBEAT_BLOCKED: farm.activate succeeded but token never validated")
    return None
```
