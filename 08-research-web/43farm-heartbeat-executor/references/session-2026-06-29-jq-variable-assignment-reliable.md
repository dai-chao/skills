# Session 2026-06-29: jq -r 配合 shell 变量赋值稳定提取 Token

## 场景

执行 43Farm 心跳任务时，本地脚本执行后 Token 过期，官方脚本恢复新 Token 后，需要验证新 Token 有效性。

## 尝试历史

1. `read_file` 读取 `credentials.json` → 返回缓存旧内容（去重陷阱）
2. `cat ~/.config/43farm/credentials.json | head -c 50` → 输出被截断
3. `TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json); curl -s -H "X-Farm-Token: $TOKEN" URL` → **成功**

## 关键成功因素

```bash
TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json)
curl -s -H "X-Farm-Token: $TOKEN" https://farm.43chat.cn/trpc/farm.status
```

与之前会话记录的 `$(jq -r)` 不稳定行为不同，本次成功的原因：

1. **变量赋值隔离了命令替换**：`TOKEN=$(...)` 将 `jq -r` 的输出隔离到变量赋值上下文，避免了在复杂 curl 命令中嵌套 `$()` 导致的解析问题
2. **Token 是 base64url 安全字符串**：不含 bash 特殊字符（`$`, `` ` ``, `"`, `'`, `!`, `&`, `|`, `;`, `<`, `>`, `(`, `)`, `{`, `}`, `[`, `]`, `*`, `?`, `~`, `\` 等）
3. **脱敏机制正确处理**：`terminal` 工具在命令执行前将 `***` 还原为完整值，变量赋值和引用均正确还原

## 与之前失败案例的对比

| 模式 | 结果 | 原因 |
|------|------|------|
| `curl -H "X-Farm-Token: $(jq -r '.farmToken' file)" URL` | ❌ 不稳定 | 命令替换在复杂参数中解析不确定 |
| `TOKEN=$(jq -r '.farmToken' file); curl -H "X-Farm-Token: $TOKEN" URL` | ✅ 稳定 | 变量赋值隔离了替换上下文 |
| `curl -H "X-Farm-Token: eyJhbG...V2FM" URL` | ❌ 间歇性 401 | `read_file` 展示截断的 `...` 不是真实内容 |

## 适用条件

- Token 必须是 bash 安全字符串（base64url 通常满足）
- 仅用于简单的一次性验证/查询
- 不适合复杂逻辑（如遍历好友列表、批量操作）

## 不适用情况

- Token 含 bash 特殊字符（如 `$`）→ 变量赋值时可能触发扩展
- 需要多次 API 调用 → 每次都需要写完整 curl 命令，迭代消耗大
- 需要处理 JSON 响应 → 管道到 `python3 -m json.tool` 被拦截

## 相关会话

- `session-2026-06-18-cron-token-extraction-loop.md` — `$(jq -r)` 在复杂命令中不稳定的记录
- `session-2026-06-29-naive-curl-token-masking.md` — 展示层脱敏导致的 Token 使用陷阱
- `session-2026-06-29-readfile-dedup-trap.md` — `read_file` 缓存陷阱迫使改用 shell 工具
