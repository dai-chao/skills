# 43Farm 凭证链断裂：Farm Token + 43chat API Key 双失效 + 新 Key 需认领（2026-06-16）

## 场景

Cron 心跳任务触发，执行 43Farm 农场参与和版本检测。

## 状态检测

- 当前时间：1781622289
- lastMessageCheck：1781610664（差值 11625 秒 > 1800，农场参与到期）
- lastVersionCheck：1781607047（差值 15242 秒 > 7200，版本检测到期）

## 诊断链

### 步骤 1：farm.events.poll → 401

```
{"error":{"message":"Farm Token 无效或已过期","code":-32001}}
```

### 步骤 2：auth.refreshToken → 失败

```
{"error":{"message":"Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）"}}
```

### 步骤 3：验证 43chat API Key → 4010

```bash
curl -s -X GET -H "Authorization: Bearer *** https://43chat.cn/open/agent/profile
```

响应：
```json
{"code":4010,"message":"API Key 无效或已被重置"}
```

### 步骤 4：重新注册 43chat → 获取新 Key + claim_url

```bash
curl -X POST https://43chat.cn/open/agent/register -H "Content-Type: application/json" -d '{}'
```

响应：
```json
{"code":0,"message":"注册成功","data":{"api_key":"sk-54g...4ef7","claim_url":"https://43chat.cn/agent-claim?verification_code=54g32-oqf58y-3c4ef7"}}
```

**关键发现**：`api_key` 被服务器端脱敏（`sk-54g...4ef7`，仅 24 字符）。这是**服务器端返回的脱敏值**，不是完整 Key。

### 步骤 5：新 Key 调用 authorize-app → 4010

即使保存了新 Key，调用 `authorize-app` 仍返回：
```json
{"code":4010,"message":"API Key 无效或已被重置"}
```

**原因**：新 Key 尚未完成 **claim（认领）**。`claim_url` 需要主人手动在浏览器中打开，完成短信验证和确认认领。

## 关键结论

1. **服务器端返回的 API Key 是脱敏的**：`POST /open/agent/register` 响应中的 `api_key` 字段被服务器主动脱敏（`sk-xxx...yyy` 格式），无法直接用于 API 调用。

2. **未认领的 Key 完全无效**：即使保存了脱敏后的 Key，所有需要认证的接口（`authorize-app`、`profile` 等）都会返回 4010。

3. **认领需要人类在场**：`claim_url` 需要主人手动在浏览器中完成短信验证，这是**无法自动化的步骤**。

4. **cron 无人值守场景下是硬阻塞**：当 Farm Token 过期且 43chat API Key 也失效时，如果新 Key 未认领，agent **无法自治恢复**。

## 正确处置流程

### 对于 cron 任务

1. 检测到 `farm.events.poll` 返回 401
2. 尝试 `auth.refreshToken` → 失败
3. 验证 43chat API Key → 返回 4010
4. **立即停止所有恢复尝试**
5. 输出 `HEARTBEAT_BLOCKED` 并报告主人
6. 报告中必须包含：
   - 失效环节（Farm Token + 43chat API Key）
   - 需要主人执行的步骤（认领 claim_url 或提供新 Key）
   - 当前 claim_url（如果已重新注册）
   - 当前状态（时间戳、检测到期情况）

### 报告模板

```
43Farm 心跳阻塞 — 凭证链断裂

失效环节：
1. Farm Token 已过期（auth.refreshToken 失败）
2. 43chat API Key 无效（返回 4010）

需要主人操作：
- 打开 claim_url 完成 43chat Agent 认领：
  https://43chat.cn/agent-claim?verification_code=54g32-oqf58y-3c4ef7
- 或从 43chat 「我的 Agent/API Key」页面获取完整 Key 并提供给我

当前状态：
- 农场参与：已到期（11625 秒未检查）
- 版本检测：已到期（15242 秒未检查）
- 时间戳：1781622289
```

## 错误处置（不要这样做）

- ❌ 不要反复重试 `authorize-app`（每次调用都返回 4010，浪费 iteration）
- ❌ 不要反复重新注册（每次注册创建新 agent，旧 agent 彻底失效，问题恶化）
- ❌ 不要返回 `HEARTBEAT_OK`（这会掩盖问题，导致主人延迟发现）
- ❌ 不要尝试用 `execute_code` 绕过（cron 模式下被 BLOCKED）
- ❌ 不要尝试用 `python3 -c` 或 heredoc（cron 模式下被拦截或静默失败）

## 关联文档

- `terminal-credential-redaction/references/session-2026-06-16-naive-replacement-breaks-json-escapes.md` — 本 session 中 curl 命令因凭证脱敏导致 bash 语法错误的详细分析
- `43farm-cron-recovery/references/session-2026-06-16-server-side-key-masking.md` — 43chat 注册响应服务器端脱敏 API Key 的独立验证
