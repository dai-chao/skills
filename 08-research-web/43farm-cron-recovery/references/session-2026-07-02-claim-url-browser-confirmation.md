# 43Farm Cron 心跳 — 2026-07-02 claim_url 未完成确认实录

## 触发场景

43Farm cron 心跳执行器运行时发现：
- `lastMessageCheck` 已到期（距上次 1981 秒 >= 1800 秒）
- `farm.events.poll` 返回 `401 UNAUTHORIZED`：Farm Token 已失效

## 恢复尝试

1. 直接运行 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` 不可行（本任务由 cron 触发，但 agent 选择直接 API 调用诊断）。
2. 读取 `~/.config/43farm/credentials.json` 获取旧 Farm Token，调用 `farm.events.poll` 确认 401。
3. 读取 `~/.config/43chat/credentials.json`，发现存在 `claim_url` 字段：
   ```json
   {
     "api_key": "sk-cc0bb552327457d07dd8d0ebf56639d883a00ad1a8aadbe9",
     "claim_url": "https://43chat.cn/agent-claim?verification_code=d7qla-4feygk-s2wuf7"
   }
   ```
4. 尝试重新激活链路：
   - `POST https://43chat.cn/open/agent/authorize-app` 返回 `code: 0`，成功获取 App Token `at-fa3905a5cb3b2434d6c9a4b7f1258fa838352d1fe410b0b3184603044ad70b28`
   - `POST https://farm.43chat.cn/trpc/farm.activate` 返回 HTTP 200 和新 Farm Token
   - 新 Farm Token 调用 `farm.events.poll` 仍立即 `401 UNAUTHORIZED`

## 关键验证：用浏览器确认 claim_url 状态

使用 `browser_navigate` 访问 `https://43chat.cn/agent-claim?verification_code=d7qla-4feygk-s2wuf7`：
- 页面标题：43Chat
- 页面内容：
  - 标题：43Chat icon
  - 输入框："输入手机号"
  - 按钮："下一步"（初始 disabled）
  - 复选框："同意用户协议和隐私政策"（未勾选）
  - 链接："《用户协议》"、"《隐私政策》"

结论：该 Agent 尚未完成 43chat 的手机号认领验证。`farm.activate` 能返回 token，但 farm 后端无法验证由未 claim session 生成的 token，因此所有 Farm API 立即 401。这是 cron 无人值守场景下的**终极硬阻塞**。

## 处置与报告

- 输出 `HEARTBEAT_BLOCKED`，向主人提供 `claim_url`
- 未修改 `~/.config/43farm/state.json`，保留原 `lastMessageCheck` 和 `lastVersionCheck` 以便下次 cron 重试
- 未尝试重新注册 43chat（避免创建新 agent 导致旧 agent 彻底失效）

## 教训

1. 当 `authorize-app` 成功但 `farm.activate` 的新 token 立即 401 时，优先检查 `claim_url` 是否存在，而不是反复激活。
2. 用 `browser_navigate` 打开 `claim_url` 是快速确认 claim 状态的有效手段；页面若显示手机号登录，则无需 agent 继续尝试任何恢复操作。
3. 报告应简洁、具体：提供 `claim_url`、说明需要手机号 + 短信验证、说明不更新 state.json 以便下次重试。
4. 在 cron 执行流程中，一旦确认硬阻塞，应立即输出阻塞报告，保留 iteration 预算并停止所有无效恢复尝试。
