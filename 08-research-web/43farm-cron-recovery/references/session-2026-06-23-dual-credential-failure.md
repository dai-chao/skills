# 43Farm Cron 双凭证失效链与静默无限重试陷阱（2026-06-23）

> 本次会话实录：Farm Token 过期 → refreshToken 失败 → authorize-app 因 43chat API Key 失效返回 4010 → agent 陷入静默无限重试循环 → 直到 max iterations 被系统截断。

## 执行时间线

- **触发时间**：cron 触发，当前时间 1782190057
- **状态检测**：农场参与到期（3514 秒 > 1800），版本检测到期（8643 秒 > 7200）
- **farm.events.poll** → 401 "Farm Token 无效或已过期"
- **auth.refreshToken** → 失败 "Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）"
- **authorize-app** → 4010 "API Key 无效或已被重置"
- **agent 行为**：未识别为不可恢复错误，继续重试 authorize-app（26+ 次相同调用）
- **结果**：系统触发 tool loop warning，最终因 max iterations 被截断

## 根因分析

### 1. 凭证链全部断裂

```
farm.events.poll → 401
  ↓
auth.refreshToken → 401（无法续签）
  ↓
authorize-app → 4010（API Key 已被服务端重置）
  ↓
结论：无法自治恢复，需主人手动重新注册 43chat
```

### 2. 静默无限重试陷阱

authorize-app 返回 4010 时，agent 未将其识别为"不可恢复错误"，而是当作临时失败继续重试。每次重试：
- 不记录失败次数
- 不递增 backoff
- 不输出诊断信息
- 直到系统层面的 tool loop warning / max iterations 截断

**后果**：
- cron 任务被无意义地占用大量 iterations
- 没有向主人报告任何有效信息
- 农场操作（收获、偷菜、版本检测）全部错过

## 修复方案

### 脚本层（heartbeat.py）

已在 `scripts/heartbeat.py` 中增加：

```python
# authorize-app 阶段增加最大重试限制
MAX_AUTH_RETRIES = 3
if auth_retry_count >= MAX_AUTH_RETRIES:
    print("HEARTBEAT_BLOCKED: 43chat API Key 失效，需手动重新注册")
    sys.exit(1)
```

### Agent 行为层

agent 收到 `HEARTBEAT_BLOCKED` 时应：
1. **立即停止重试**，不要继续尝试任何恢复操作
2. **输出完整诊断报告**给主人，包含：
   - 失效的凭证类型（Farm Token + 43chat API Key）
   - 需要主人执行的步骤（重新注册 43chat → 认领 → 重新激活农场）
   - 未执行的农场操作清单
3. **不更新 state.json**（本次心跳未实际执行任何操作）

## 与单凭证失效的区别

| 场景 | Farm Token | API Key | 可自治恢复 | 输出 |
|------|-----------|---------|-----------|------|
| 仅 Farm Token 过期 | 401 | 有效 | ✅ 是 | 自动恢复，继续执行 |
| API Key 格式正确但过期 | 401 | 有效格式，4010 | ❌ 否 | `HEARTBEAT_BLOCKED` |
| API Key 含特殊字符导致 bash 错误 | 401 | 含 `$` 等字符 | ❌ 否 | `HEARTBEAT_BLOCKED` |
| 双凭证失效（本场景） | 401 | 已被重置 | ❌ 否 | `HEARTBEAT_BLOCKED` |

## 预防建议

1. **心跳脚本必须内置重试上限**：任何恢复链路（refreshToken → authorize-app → farm.activate）都应有 `max_retries`，不可无限循环
2. **区分临时错误与永久错误**：4010（API Key 无效/已重置）是永久错误，不应重试；500（服务端错误）才是临时错误
3. **agent 层识别 `HEARTBEAT_BLOCKED`**：一旦脚本输出此标记，立即停止所有后续操作，直接报告主人
4. **定期监控凭证有效期**：心跳脚本可在每次执行时检查 Farm Token 的剩余有效期（JWT 解码 `exp` 字段），提前预警

## 相关参考

- `references/cron-token-recovery.md` — 完整的 Token 恢复流程
- `references/troubleshooting.md` — 凭证脱敏与截断的详细分析
- `references/session-2026-06-23-api-key-special-chars-hard-block.md` — API Key 特殊字符导致的 bash 硬阻塞
- `scripts/heartbeat.py` — 内置双凭证失效检测与重试上限逻辑
