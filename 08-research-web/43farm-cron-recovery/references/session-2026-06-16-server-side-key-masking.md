# 43chat 注册响应中的 API Key 服务器端脱敏（2026-06-16 验证）

## 现象

当 43chat API Key 失效（返回 4010）时，尝试通过 `POST /open/agent/register` 重新注册获取新 Key。但服务器返回的 `api_key` 字段已被**服务器端脱敏**：

```json
{"code":0,"message":"注册成功","data":{"api_key":"sk-da0...8890","claim_url":"..."}}
```

## 关键验证步骤

### 1. 排除显示层脱敏

使用 `read_file` 工具读取 `/tmp/reg_resp.json`（curl 直接保存到文件，未经过 stdout）：

```
{"api_key":"sk-da0...8890"}
```

`read_file` 返回的是文件系统真实内容，不受 stdout 脱敏影响。结果仍然包含 `...`，说明这是**服务器返回的原始响应**中就有的脱敏。

### 2. 十六进制验证

```bash
hexdump -C /tmp/reg_resp.json
```

输出关键段：
```
00000040  3a 7b 22 61 70 69 5f 6b  65 79 22 3a 22 73 6b 2d  |:{"api_key": "sk-|
00000050  64 61 30 2e 2e 2e 38 38  39 30 22 2c              |da0...8890",    |
```

字节 `2e 2e 2e` 就是 ASCII 的 `...`（三个点号）。这是服务器故意返回的截断值，不是任何中间层的脱敏。

### 3. 旧凭证文件同样被截断

检查 `~/.config/43chat/credentials.json` 的十六进制：

```bash
hexdump -C ~/.config/43chat/credentials.json
```

发现旧 Key 也是 `sk-997...fbc5` 格式（含字面 `...`）。这说明**之前的某个 session 中，agent 从 stdout 复制了脱敏后的字符串并保存回了文件**，导致文件永久损坏。

## 结论

**43chat 服务器在注册响应中故意不返回完整 API Key。** 这是安全设计，防止 API Key 在日志/网络抓包中泄露。

**这意味着：**
- ❌ 无法通过自动注册获取可用的 43chat API Key
- ❌ 无法通过任何 HTTP API 调用获取完整 API Key
- ✅ 唯一获取完整 Key 的方式：主人手动登录 https://43chat.cn 「我的 Agent/API Key」页面复制

## 对 43Farm Cron 恢复流程的影响

当 Farm Token 过期 → `auth.refreshToken` 失效 → 43chat API Key 也失效时，**整个自动恢复链断裂**。Cron 任务必须：

1. 输出 `HEARTBEAT_BLOCKED`
2. 报告主人需要手动获取新 API Key
3. 停止所有重试，不要反复注册（每次注册创建新 agent，旧 agent 彻底失效）

## 诊断技巧：区分显示层脱敏 vs 文件层截断

| 检测方法 | 显示层脱敏 | 文件层截断 |
|----------|-----------|-----------|
| `read_file` 返回含 `...` | 否（返回完整值） | **是**（文件本身含 `...`） |
| `hexdump -C` 看到 `2e 2e 2e` | 否 | **是** |
| `cat file \| base64` 解码后含 `...` | 否 | **是** |
| 文件字节长度 | 正常（~200 字节） | 偏短（~150 字节） |

**关键原则**：`read_file` 工具返回的是文件系统真实内容，不受 stdout 脱敏影响。如果 `read_file` 看到的值包含 `...`，这就是文件中的字面字符，不是显示脱敏。

## 修复流程（需主人介入）

1. 主人访问 https://43chat.cn
2. 进入「我的 Agent/API Key」页面
3. 点击「重置 API Key」，获取新的完整 Key
4. 提供新 Key 后，agent 更新 `~/.config/43chat/credentials.json`
5. 重新执行 `farm.activate` 获取新 Farm Token
6. 恢复心跳任务

## 相关会话

- `session-2026-06-15-cascading-token-failure.md` — 首次发现 4010 错误码和 credentials 文件截断问题
- `session-2026-06-15-literal-truncated-key.md` — 确认文件层截断的检测方法
