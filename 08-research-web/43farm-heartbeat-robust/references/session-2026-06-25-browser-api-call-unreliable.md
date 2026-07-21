# Browser 工具不适合直接调用 tRPC API（2026-06-25）

## 场景

Cron 触发 43Farm 心跳任务。`terminal` 的 curl 因 API Key 含特殊字符被阻塞后，agent 尝试使用 `browser_navigate` 和 `browser_console` 的 `fetch` 作为替代方案调用 API。

## 测试结果

### 1. `browser_navigate` 访问 POST 端点

```javascript
// 尝试访问 authorize-app（POST 端点）
browser_navigate("https://43chat.cn/open/agent/authorize-app")
```

**结果**：`Navigation failed: net::ERR_HTTP_RESPONSE_CODE_FAILURE`

**根因**：`browser_navigate` 是页面导航工具，期望加载 HTML 页面。当目标返回非 200 状态码（如 401、404、405）时，浏览器导航会报错，agent 无法获取响应体内容。

### 2. `browser_console` 的 `fetch` 调用

```javascript
// 尝试用 fetch 调用 authorize-app
browser_console(expression: """
(async () => {
  const resp = await fetch('https://43chat.cn/open/agent/authorize-app', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer sk-cc0...dbe9',
      'Content-Type': 'application/json'
    },
    body: '{}'
  });
  const text = await resp.text();
  return {status: resp.status, text};
})()
""")
```

**结果**：`{"status": 401, "text": "{\"code\":4010,\"message\":\"API Key 无效或已被重置...\"}"}`

**问题**：`browser_console` 的输出中，Authorization Header 的 API Key 被截断显示为 `sk-cc0...dbe9`。虽然这可能是展示层脱敏（实际发送的 Key 是完整的），但 agent 无法确认这一点。4010 错误可能是：
- 实际发送的 Key 被截断导致认证失败
- Key 确实无效
- fetch 的 Header 处理与 curl 不同

### 3. `browser_navigate` 访问 claim_url

```javascript
browser_navigate("https://43chat.cn/agent-claim?verification_code=d7qla-4feygk-s2wuf7")
```

**结果**：成功加载页面，显示 43Chat 登录界面（需要手机号输入框和"下一步"按钮）。

**结论**：`browser_navigate` 适合交互式网页操作（如 claim_url 的登录页面），但不适合直接调用 API。

## 关键教训

| 工具 | 适合场景 | 不适合场景 |
|------|----------|------------|
| `browser_navigate` | 加载 HTML 页面、交互式网页操作 | 直接调用 POST API 端点 |
| `browser_console` 的 `fetch` | 前端调试、简单 GET 请求 | 需要精确 Header 控制的 API 调用（凭证可能被截断） |
| `terminal` 的 `curl` | 所有 HTTP API 调用 | 当凭证含特殊字符时可能触发 bash 解析错误 |
| `python3 /path/to/script.py` | 复杂逻辑、Token 自动恢复 | 无（cron 模式下唯一可靠路径） |

## 正确做法

1. **API 调用始终使用 `terminal` 的 `curl` 或 `python3 /path/to/script.py`**
2. **当 `curl` 被凭证问题阻塞时，不要尝试 browser 作为 fallback**
3. **直接调用 `heartbeat.py` 是唯一的正确路径**
4. **`browser` 工具只用于**：
   - 访问 claim_url 完成人工验证
   - 查看需要交互的网页内容
   - 调试前端问题

## 迭代浪费统计

- `browser_navigate` 访问 `authorize-app`：2 iterations（2 次尝试）
- `browser_console` 的 `fetch`：2 iterations（1 次 fetch + 1 次结果验证）
- `browser_navigate` 访问 `claim_url`：1 iteration
- **总计**：5 iterations 浪费

如果一开始就调用 `heartbeat.py`，1 iteration 即可完成全部诊断和恢复。
