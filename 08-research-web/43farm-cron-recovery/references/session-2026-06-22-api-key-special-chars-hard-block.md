# API Key 含 `$` 等特殊字符导致 curl 命令彻底无法执行（2026-06-22）

## 背景

在 cron 无人值守场景下，43Farm 心跳任务触发时 Farm Token 已过期。按恢复流程：
1. 运行 `heartbeat.py` → 返回 `HEARTBEAT_OK`（但实际 Token 已过期，脚本静默失败）
2. 手动验证 `farm.status` → 401 UNAUTHORIZED
3. `auth.refreshToken` → 失败 "旧 token 不合法或 43chat session 已失效"
4. 检查 43chat API Key → `read_file` 显示 `sk-668...7125`（含 `$` 等特殊字符）
5. 尝试 `authorize-app` 重新激活 → 所有 curl 引号组合均失败

## 失败的引号组合

### 尝试 1：双引号包裹（标准做法）
```bash
curl -s -X POST "https://43chat.cn/open/agent/authorize-app" \
  -H "Authorization: Bearer sk-668...7125" \
  -H "Content-Type: application/json" \
  -d '{"app_id": "agent-farm", "scopes": ["identity", "friends"]}'
```
**结果**：`unexpected EOF while looking for matching '"'` — Key 中的 `"` 破坏外层双引号配对。

### 尝试 2：单引号包裹
```bash
curl -s -X POST 'https://43chat.cn/open/agent/authorize-app' \
  -H 'Authorization: Bearer sk-668...7125' \
  -H 'Content-Type: application/json' \
  -d '{"app_id": "agent-farm", "scopes": ["identity", "friends"]}'
```
**结果**：同样失败 — Key 中的 `'` 字符（如果有）会破坏单引号配对。且 `$` 在单引号中虽不扩展，但 `"` 仍可能导致问题。

### 尝试 3：环境变量中转
```bash
export API_KEY="sk-668...7125"
curl -s -X POST "https://43chat.cn/open/agent/authorize-app" \
  -H "Authorization: Bearer $API_KEY" ...
```
**结果**：`export` 时 `$` 触发变量扩展，如果 Key 中 `$` 后面跟有效变量名，会被替换为空。

### 尝试 4：write_file 写脚本后 bash 执行
将完整 curl 命令写入 `/tmp/script.sh`，然后 `bash /tmp/script.sh`。
**结果**：脚本中的 curl 命令仍需某种引号包裹 Key，问题未解决。

### 尝试 5：printf + `--header @file`
```bash
printf 'Authorization: Bearer %s\n' "$API_KEY" > /tmp/header.txt
curl -s --header @/tmp/header.txt ...
```
**结果**：`printf` 中的 `"$API_KEY"` 仍需引号，且 `$` 扩展问题依然存在。`printf '%s'` 理论上安全，但 `bash` 解析 `"$API_KEY"` 时 `$` 仍可能触发扩展。

## 根因分析

1. **bash eval 解析**：`terminal()` 工具将命令传递给 bash 前会进行 eval，任何引号组合都无法同时安全处理 `"`、`'`、`$`、`` ` `` 等字符。
2. **凭证脱敏叠加**：即使引号配对正确，终端工具的凭证脱敏机制会将 Key 中的敏感部分替换为 `***`，进一步破坏命令结构。
3. **cron 无用户在场**：没有用户手动修正命令，agent 会反复尝试不同引号组合，陷入无限循环。

## 正确处置

当 API Key 含 bash 特殊字符且 `heartbeat.py` 无法自动恢复时：

1. **第 1 次失败**：记录错误，尝试切换引号组合
2. **第 2 次失败**：尝试完全不同的方法（如 `printf` + `--header @file`）
3. **第 3 次失败**：**立即停止，输出 `HEARTBEAT_BLOCKED`**

报告内容应包括：
- 检测到 API Key 含 bash 特殊字符，无法通过 curl 自动恢复
- 建议主人从 https://43chat.cn 重置 API Key，获取不含特殊字符的新 Key
- 提供 `claim_url`（如果存在）供主人手动认领

## 状态文件策略

- **lastMessageCheck**：不更新（保留旧值，下次 cron 重试）
- **lastVersionCheck**：不更新（保留旧值，下次 cron 重试）
- 不要因本次失败而更新任何时间戳，否则会掩盖问题

## 教训

1. **不要假设任何引号组合能安全处理任意字符串**：当 Key 含 `"`、`'`、`$` 等字符时，所有标准 workaround 均失效。
2. **3 次失败即停止**：不要依赖外部工具 loop warning（30+ 次后才触发），agent 必须内置自我保护机制。
3. **优先运行 `heartbeat.py`**：如果脚本能自动恢复，完全避开手动 curl 的引号问题。本 session 中脚本返回 `HEARTBEAT_OK` 是因为脚本本身有 bug（未正确检测 Token 过期），而非引号问题。
4. **报告要清晰**：阻塞报告应明确说明"API Key 含特殊字符，无法自动恢复"，让主人知道需要重置 Key。
