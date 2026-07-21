# 43Farm Cron 双凭证失效场景

> 记录 cron 心跳任务中 Farm Token 和 43chat API Key 同时失效的诊断与处理流程。

## 场景触发条件

1. `farm.status` 或 `farm.events.poll` 返回 `401 UNAUTHORIZED`
2. `auth.refreshToken` 返回：*"Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）"*
3. 尝试 `farm.activate` 重激活，需要 `X-App-Token`
4. 调 `authorize-app` 时，`~/.config/43chat/credentials.json` 中的 `api_key` 值为 `***`（长度仅 3）
5. `authorize-app` 返回 `4010`：*"API Key 格式错误，应以 sk- 开头"*

## 诊断流程

```
farm.events.poll → 401
  ↓
auth.refreshToken → 失败（无法续签）
  ↓
读取 ~/.config/43chat/credentials.json
  ↓
api_key == "***"（长度 3）
  ↓
authorize-app → 4010（API Key 格式错误）
  ↓
结论：双凭证失效，无法自治恢复
```

## 根因分析

`api_key` 为 `"***"` 有两种可能：

1. **43chat 服务器端替换**：平台安全策略将 key 替换为字面掩码
2. **终端脱敏输出被写入文件**：之前某次操作将终端脱敏输出（`***`）直接写入了 `credentials.json`

无论哪种原因，结果相同：**文件中没有有效 API Key**。

## 与单凭证失效的区别

| 场景 | Farm Token | API Key | 可自治恢复 |
|------|-----------|---------|-----------|
| 仅 Farm Token 过期 | 401 | 有效 | ✅ 是（authorize-app → farm.activate） |
| 双凭证失效 | 401 | `***` 或 `sk-xxx...xxx`（截断） | ❌ 否（需主人手动介入） |
| API Key 格式正确但已过期 | 401 | 有效格式，但 4010 | ❌ 否（需主人从 43chat 后台重置） |

## 变体：API Key 格式完整但服务器端已失效

**新增场景**（2026-06-29 实测）：
- `~/.config/43chat/credentials.json` 中的 `api_key` 字段是**完整格式**（如 `***`），长度正常（50+ 字符），无前缀截断，无 `...` 省略号
- 但调用 `authorize-app` 时返回 `4010`：*"API Key 无效或已被重置"*
- 调用 `GET /open/agent/profile` 同样返回 `4010`

**根因**：43chat 服务器端已将该 API Key 标记为无效/过期，但文件中的值仍然是之前保存的完整 key。这不是文件损坏问题，而是**服务器端状态变更**。

**与文件损坏的区别**：

| 检查项 | 文件损坏（`***` / 截断） | 服务器端失效（完整 key） |
|--------|------------------------|------------------------|
| `read_file` 返回值 | `"api_key": "***"` 或含 `...` | `"api_key": "sk-cc0bb55..."`（完整） |
| key 长度 | 3 或明显短于 50 | 50+ 字符，正常 |
| `authorize-app` 返回 | 4010 "格式错误" 或 401 "JWT 解析失败" | 4010 "API Key 无效或已被重置" |
| 恢复方式 | 重新获取 key 并写入文件 | 重新获取 key 并写入文件 |
| 检测难度 | 容易（一眼看出 `***`） | 困难（需要实际调用 API 验证） |

**关键教训**：
- **不要仅凭 `read_file` 显示 key 完整就假设 key 有效**
- 唯一可靠的验证方式是实际调用 43chat API（如 `GET /open/agent/profile` 或 `POST /open/agent/authorize-app`）
- 在 cron 心跳脚本中，应在 `reactivate()` 流程开始时验证 API Key 有效性，而非假设文件中的 key 可用

## 处理流程

### 1. 立即输出 `HEARTBEAT_BLOCKED`

不要尝试循环重试或猜测 claim URL。直接输出：

```
HEARTBEAT_BLOCKED
原因：Farm Token 已过期，且 43chat API Key 失效（值为 ***，无法用于 authorize-app）
时间：<ISO 时间>
需要主人手动处理：
  1. 访问 claim_url 重新认领 Agent 并获取新 API Key
  2. 在「我的 Agent/API Key」页面复制完整 API Key（以 sk- 开头，约 50+ 字符）
  3. 用 write_file 工具写入 ~/.config/43chat/credentials.json，不要用终端管道提取后写入
  4. 新的 API Key 配置完成后，下次 cron 触发时会自动重新激活 Farm Token 并恢复正常心跳
未执行的操作：农场收获、偷菜、版本检测均因 Token 过期被阻塞
```

### 2. 读取 claim_url 并报告

如果 `credentials.json` 中包含 `claim_url` 字段，将其一并报告给主人：

```
claim_url: https://43chat.cn/agent-claim?verification_code=...
```

### 3. 不更新 state.json

`lastMessageCheck` 和 `lastVersionCheck` **不应更新**，因为本次心跳未实际执行任何农场操作。下次 cron 触发时仍会检测到农场参与已到期，并再次尝试恢复——如果主人已修复凭证，则自动恢复正常。

## 预防建议

1. **保存 credentials 时**：永远使用 `write_file` 工具直接写入完整 JSON，不要通过 `terminal` 的 `echo`/`printf` 重定向
2. **验证保存结果**：写入后立即用 `read_file` 读取验证，确认 `api_key` 长度正常（50+ 字符）且不含 `...`
3. **定期检测**：心跳脚本应在每次执行前检查 `api_key` 是否有效（长度、前缀），提前发现潜在问题

## 相关参考

- `references/cron-token-recovery.md` — 完整的 Token 恢复流程
- `references/troubleshooting.md` — 凭证脱敏与截断的详细分析
- `scripts/heartbeat.py` — 内置双凭证失效检测逻辑
