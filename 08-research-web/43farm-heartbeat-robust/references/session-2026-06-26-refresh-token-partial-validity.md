# refreshToken 返回的 Token 部分有效：farm.view 通过但 farm.friends 401（2026-06-26）

## 现象

调用 `auth.refreshToken` 成功返回新 Farm Token：

```json
{"farmToken":"eyJhbG...mVQE"}
```

- `farm.view?input={"userId":53613}` → ✅ 成功（返回完整农场状态）
- `farm.friends` → ❌ 401 `UNAUTHORIZED`
- `farm.events.poll` → ❌ 401 `UNAUTHORIZED`

## 根因分析

`auth.refreshToken` 端点本身不需要验证旧 token 的有效性（或只验证部分签名），因此即使旧 token 已过期，它仍会返回一个**形式上有效的新 token**。但这个新 token 在后端的完整权限验证链中可能：

1. **签名正确但 session 关联失效**：token 的 JWT 签名有效，但对应的 43chat session 或 farm session 已在后端被标记为过期/失效
2. **部分端点缓存不一致**：`farm.view` 可能使用了独立的缓存层（公开视图），而 `farm.friends` / `farm.events.poll` 需要实时验证 session 状态
3. **权限 scope 降级**：refresh 后的 token 可能丢失了某些 scope（如 `friends`），导致需要该 scope 的端点失败

## 与"Token 完全过期"的区别

| 特征 | 部分有效 Token | 完全过期 Token |
|------|-------------|---------------|
| `farm.view` | 成功 | 401 |
| `farm.friends` | 401 | 401 |
| `farm.events.poll` | 401 | 401 |
| `auth.refreshToken` | 成功返回新 token | 可能失败（旧 token 不合法） |
| 恢复路径 | 重走 `farm.activate` | 重走 `farm.activate` |

**关键区别**：部分有效 Token 会制造"Token 已恢复"的假象，agent 可能误以为恢复成功而继续执行，直到遇到 `farm.friends` 或 `farm.events.poll` 才暴露问题。

## 检测方法

refreshToken 返回新 token 后，**必须立即验证两个端点**：

```bash
# 验证 1：farm.view（公开视图，最容易通过）
curl -s -H "X-Farm-Token: <new-token>" "https://farm.43chat.cn/trpc/farm.view?input=%7B%22userId%22%3A53613%7D"

# 验证 2：farm.friends（需要 friends scope，最能暴露问题）
curl -s -H "X-Farm-Token: <new-token>" "https://farm.43chat.cn/trpc/farm.friends"

# 验证 3：farm.events.poll（需要完整 session）
curl -s -H "X-Farm-Token: <new-token>" "https://farm.43chat.cn/trpc/farm.events.poll"
```

**如果验证 1 成功但验证 2/3 失败** → 判定为"部分有效 Token"，立即进入重新激活流程，不要继续执行心跳逻辑。

## 处置流程

```
auth.refreshToken → 返回新 token
  ↓
验证 farm.friends 或 farm.events.poll
  ↓
├─ 成功 → 继续正常心跳
└─ 失败 → 判定为部分有效 Token
    ↓
    重走 farm.activate 流程（authorize-app → activate）
    ↓
    如果 activate 也失败 → 进入 43farm-cron-recovery 的硬阻塞报告
```

## 此 session 的完整实录

1. `auth.refreshToken` 返回新 token `eyJhbG...mVQE`
2. `farm.view` 成功获取农场状态（17 块地全部 growing）
3. `farm.friends` 返回 401 `UNAUTHORIZED`
4. `farm.events.poll` 返回 401 `UNAUTHORIZED`
5. 尝试 `authorize-app` → 43chat API Key 也失效（4010）
6. 判定为双凭证失效（Farm Token + 43chat API Key），进入硬阻塞报告

## 教训

1. **refreshToken 成功 ≠ 恢复成功**：必须验证需要完整权限的端点（`farm.friends` 或 `farm.events.poll`）
2. **不要仅凭 `farm.view` 成功就继续执行**：`farm.view` 是公开视图，最容易通过，不能代表 token 完全有效
3. **在 cron 心跳执行器中，验证 2/3 失败后应立即停止**，不要尝试收获/偷菜/种植等操作（这些操作也会 401）
4. **状态文件不应在此时更新**：如果 token 部分有效，不应更新 `lastMessageCheck`，确保下次 cron 触发时重新尝试恢复

## 相关参考

- `session-2026-06-22-heartbeat-ok-but-token-expired.md` — 脚本返回 HEARTBEAT_OK 但 token 已过期
- `session-2026-06-26-unconditional-state-update-bug.md` — 脚本不应在 API 失败时更新状态文件
- `cron-recovery-hard-block-report-template.md` — 双凭证失效时的硬阻塞报告模板
