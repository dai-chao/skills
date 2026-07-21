# 43Farm farm.activate 返回 Token 但立即 401（2026-06-23）

> 本次会话实录：Farm Token 过期 → refreshToken 失败 → authorize-app 成功（code: 0）→ farm.activate 成功返回 farmToken → 但新 token 立即 401 → 陷入恢复循环。

## 执行时间线

- **触发时间**：cron 触发，当前时间 1782206962
- **状态检测**：农场参与到期（2797 秒 > 1800），版本检测未到期（4143 秒 < 7200）
- **farm.events.poll** → 401 "Farm Token 无效或已过期"
- **auth.refreshToken** → 失败 "Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）"
- **authorize-app** → 成功 `{"code":0,"data":{"app_token":"at-..."}}`
- **farm.activate** → 成功 `{"farmToken":"eyJhbG..."}`
- **farm.events.poll（新 token）** → 401 "Farm Token 无效或已过期"
- **重试**：多次重复 authorize-app → farm.activate → 401 循环
- **结果**：token 始终无效，无法恢复

## 关键发现：authorize-app 成功但 farm.activate 的 token 无效

这与之前记录的"双凭证失效"场景不同：

| 场景 | authorize-app | farm.activate | 新 token 验证 | 根因 |
|------|-------------|---------------|-------------|------|
| 双凭证失效（之前） | 4010 / 失败 | 未执行 | — | 43chat API Key 已被重置 |
| **本场景** | **code: 0 / 成功** | **成功返回 token** | **立即 401** | **43chat session 已失效，但 authorize-app 仍返回成功** |

## 根因分析

### 假设 1：43chat session 已失效，但 authorize-app 未正确验证

`authorize-app` 返回成功（code: 0）可能仅表示"请求格式正确、API Key 存在"，但**不验证 43chat 用户 session 的有效性**。颁发的 App Token 可能是"形式上有效但实质上无法绑定到有效用户 session"的令牌。

当 `farm.activate` 使用这个 App Token 时，farm 后端尝试将 Farm Token 与 43chat 用户 session 绑定，但发现 session 已失效，因此颁发的 Farm Token 也是无效的。

### 假设 2：farm 后端与 43chat 的 session 同步延迟

43chat 的 session 已失效，但 farm 后端的 session 缓存尚未更新。`authorize-app` 在 43chat 侧验证通过（因为 API Key 本身有效），但 farm 后端的验证逻辑更严格，检测到用户 session 已失效。

### 假设 3：farm 后端验证逻辑 bug

`farm.activate` 成功返回 token，但后续所有 API 调用（`farm.events.poll`、`farm.status`）都返回 401。这可能表明 farm 后端的 token 签发与验证逻辑不一致——签发时未充分验证，验证时更严格。

## 诊断方法

当遇到此场景时，agent 应执行以下诊断：

### 步骤 1：验证 43chat API Key 本身

```bash
curl -s -H "Authorization: Bearer <api_key>" "https://43chat.cn/open/agent/profile"
```

- 如果返回 `code: 0` → API Key 有效，问题在 farm 后端
- 如果返回 `code: 4010` → API Key 已失效，进入"双凭证失效"处理流程
- 如果返回 `code: 401` + JWT 解析错误 → Key 格式损坏

### 步骤 2：验证 authorize-app 的 App Token

```bash
curl -s -X POST -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"agent-farm","scopes":["identity","friends"]}' \
  "https://43chat.cn/open/agent/authorize-app"
```

- 如果返回 `code: 0` → App Token 获取成功
- 如果返回 `code: 4010` → API Key 无效

### 步骤 3：验证 farm.activate 和 token 有效性

```bash
curl -s -X POST -H "X-App-Token: <app_token>" "https://farm.43chat.cn/trpc/farm.activate"
# 保存返回的 farmToken

curl -s -H "X-Farm-Token: <farm_token>" "https://farm.43chat.cn/trpc/farm.status"
```

- 如果 farm.activate 成功但 farm.status 401 → **本场景**（authorize-app 成功但 token 无效）
- 如果 farm.activate 失败 → 检查错误信息

## 处置策略

### 当确认是"authorize-app 成功但 token 无效"时：

1. **停止重复激活循环**（不要多次 authorize-app → farm.activate）
2. **尝试 43chat 的 claim_url 流程**（如果 credentials.json 中有 claim_url）
3. **如果 claim_url 需要人工验证**（手机号 + 短信）→ 输出 `HEARTBEAT_BLOCKED`
4. **报告主人**：说明 43chat session 已失效，需要重新登录/认领

### 状态文件更新策略：

- **不更新 `lastMessageCheck`**（农场参与未成功执行）
- **不更新 `lastVersionCheck`**（即使本次未到期，也不更新）
- 保留旧值，下次 cron 触发时重试

## 与双凭证失效的区别

| 特征 | 双凭证失效（API Key 被重置） | 本场景（session 失效但 API Key 有效） |
|------|---------------------------|----------------------------------|
| authorize-app | 4010 | code: 0 |
| farm.activate | 可能成功或失败 | 成功 |
| 新 token 验证 | 未执行或失败 | 立即 401 |
| 可恢复性 | 需新 API Key | 需重新登录 43chat 刷新 session |
| 处置 | `HEARTBEAT_BLOCKED` | `HEARTBEAT_BLOCKED` + 建议重新登录 |

## 相关参考

- `references/session-2026-06-23-dual-credential-failure.md` — 双凭证失效（authorize-app 失败）
- `references/session-2026-06-23-api-key-special-chars-hard-block.md` — API Key 特殊字符硬阻塞
- `scripts/heartbeat.py` — 内置恢复逻辑
