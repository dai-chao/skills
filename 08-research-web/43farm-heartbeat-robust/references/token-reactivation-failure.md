# Token 重新激活后仍 401 — 已知故障模式

## 现象

1. `farm.events.poll` 或 `farm.status` 返回 `401 UNAUTHORIZED`
2. `auth.refreshToken` 返回「旧 token 不合法或 43chat session 已失效」
3. 走完整重新激活流程：
   - `authorize-app` → 成功获取 `app_token`
   - `farm.activate` → 成功返回新 `farmToken`
   - 新 token 调用 `farm.status` → **仍然 401 UNAUTHORIZED**

## 已观察实例

- 时间：2026-06-13
- 环境：macOS cron 任务
- 初始 token：`eyJhbG...smnQ`（已过期）
- 重新激活后 token：`eyJhbG...fzZw`（`farm.activate` 返回，但后续 API 仍 401）
- 尝试次数：2 次完整重新激活，均得到新 token 但均 401

## 可能原因

| 假设 | 依据 | 验证状态 |
|------|------|---------|
| 43chat 账号农场未真正初始化 | `farm.activate` 可能只创建 token 但未持久化农场数据 | 未验证 |
| Token 验证时序问题 | 新 token 需要延迟生效 | 未验证（未测试等待后重试） |
| 账号需要 web 端首次访问 | 类似 OAuth 需要用户交互完成授权 | 未验证 |
| API 端点不一致 | `farm.activate` 与查询 API 使用不同验证服务 | 未验证 |

## 对策

1. **脚本层面**：Token 重新激活后必须立即用 `farm.status` 验证 token 有效性，不要假设 `farm.activate` 返回的 token 一定可用
2. **人工介入**：如果重新激活后仍 401，需要主人检查：
   - 43chat 账号是否已完成农场首次激活（web 端访问 `https://farm.43chat.cn`）
   - 账号是否存在异常状态（被封禁、未实名等）
3. **重试策略**：可尝试等待 30-60 秒后再次验证，排除时序问题

## 相关日志（供对比）

```
# auth.refreshToken 失败
{"error":{"message":"Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）。"}}

# farm.activate 成功
{"farmToken":"eyJhbG...fzZw"}

# 但 farm.status 仍失败
{"error":{"message":"Farm Token 无效或已过期","code":-32001,"data":{"code":"UNAUTHORIZED","httpStatus":401}}}
```
