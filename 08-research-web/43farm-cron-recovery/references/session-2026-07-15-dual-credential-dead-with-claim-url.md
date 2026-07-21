# 2026-07-15 — Farm Token 过期 + 43chat API Key 4010 + claim_url 需人工验证

## 场景

Cron 触发 43Farm 心跳任务。初始状态：
- `~/.config/43farm/state.json`：`{"lastMessageCheck": 1784086586, "lastVersionCheck": 1784087251}`
- 当前时间：1784088636
- 农场参与已到期（距上次 2050 秒 > 1800 秒阈值）
- 版本检测已到期（距上次 1385 秒 < 7200 秒阈值，但接近）

## 诊断链

1. `farm.events.poll` 返回：
   ```json
   {"error":{"message":"Farm Token 无效或已过期。","code":-32001,"data":{"code":"UNAUTHORIZED","httpStatus":401}}}
   ```

2. `auth.refreshToken` 未尝试（直接进入恢复流程，因为 Token 已明确过期）。

3. 验证 43chat API Key：
   ```bash
   curl -s -H "Authorization: Bearer <api_key>" https://43chat.cn/open/agent/profile
   ```
   返回：
   ```json
   {"code":4010,"message":"API Key 无效或已被重置。","timestamp":1784088731}
   ```

4. 尝试 `authorize-app`：
   ```bash
   curl -s -X POST -H "Authorization: Bearer <api_key>" \
     -H "Content-Type: application/json" \
     -d '{"app_id":"agent-farm","scopes":["identity","friends"]}' \
     https://43chat.cn/open/agent/authorize-app
   ```
   返回相同的 4010 错误。

5. 检查 `~/.config/43chat/credentials.json`：
   - 包含 `claim_url`: `https://43chat.cn/agent-claim?verification_code=d7qla-4feygk-s2wuf7`
   - `api_key` 已失效（4010）

6. 使用 `browser_navigate` 打开 `claim_url`：
   - 页面标题：43Chat
   - 页面内容：手机号输入框 + 「下一步」按钮 + 用户协议/隐私政策勾选
   - 无法自动完成验证

## 结论

这是 cron 无人值守场景下的**终极硬阻塞**：
- Farm Token 过期，无法直接续签
- 43chat API Key 已失效（4010），无法获取新 App Token
- `claim_url` 需要手机号 + 短信验证码人工验证，agent 无法自动完成

## 处置

- 输出 `HEARTBEAT_BLOCKED`
- 不更新 `lastMessageCheck` 和 `lastVersionCheck`（保留旧值以便下次 cron 重试）
- 在报告中提供 `claim_url` 并明确要求主人：
  1. 登录 43chat → 我的 Agent → API Key，重新生成 API Key
  2. 或完成 `claim_url` 的手机号验证流程
  3. 更新 `~/.config/43chat/credentials.json` 后重新触发心跳

## 状态保留策略

```json
{
  "lastMessageCheck": 1784086586,
  "lastVersionCheck": 1784087251
}
```

保留旧值，不更新。原因：
- 农场参与未成功执行（Token 过期）
- 版本检测未成功执行（iteration 已耗尽，且 Farm Token 问题阻塞）
- 下次 cron 触发时，农场参与仍会到期（因为 `lastMessageCheck` 未更新），会再次尝试并报告，直到主人修复凭证

## 教训

1. **4010 是真正的 Key 失效信号**：本次 session 中 API Key 不是命令格式问题（已尝试变量方式、直接内联、不同 Header 写法，均 4010），而是服务器端已失效。
2. **claim_url 存在 + 4010 = 终极硬阻塞**：当 `claim_url` 字段存在且 API Key 失效时，说明 agent 尚未完成 43chat 认领流程，任何自动恢复都不可能。
3. **不要尝试重新注册 43chat**：重新注册会创建新 agent，旧 agent 彻底失效，问题恶化。
4. **浏览器工具只用于验证，不用于绕过**：`browser_navigate` 可以确认 claim_url 页面内容，但不要尝试自动填写手机号/获取验证码。

## 关联参考

- `session-2026-06-24-activate-token-always-immediately-401.md` — claim_url 未完成的类似硬阻塞
- `session-2026-07-02-claim-url-browser-confirmation.md` — 用 browser 工具确认 claim_url 页面
- `session-2026-06-16-both-tokens-dead-claim-url-human-required.md` — 双凭证失效 + 需人工认领的完整链路
