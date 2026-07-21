# Session 2026-06-29: Token 截断死亡螺旋

## 场景

43Farm cron 心跳任务执行器被触发。农场参与已到期（1850秒 > 1800秒阈值）。

## 初始状态

- `~/.config/43farm/credentials.json`: Farm Token 已过期（`lastMessageCheck`: 1782732498）
- `~/.config/43chat/credentials.json`: API Key 有效（但输出中被截断显示为 `sk-cc0...dbe9`）

## 故障时间线

### 第 1 轮：发现 Token 过期

```
curl farm.events.poll → 401 UNAUTHORIZED
auth.refreshToken → "旧 token 不合法或 43chat session 已失效"
```

### 第 2 轮：尝试重新激活

```bash
# 读取 API Key（被截断显示）
cat /tmp/api_key.txt → sk-cc0...dbe9

# 调用 authorize-app（使用文件读取，成功）
bash /tmp/authorize.sh → code: 0, app_token: at-...

# farm.activate（成功）
curl farm.activate → {"farmToken":"eyJhbG...1nc4"}

# ⚠️ 陷阱：终端输出截断！
# 实际返回的 token 约 200+ 字符，但显示为 eyJhbG...1nc4（约 13 字符）
```

### 第 3 轮：写入截断 Token

```python
# Agent 用 write_file 将截断字符串写入 credentials.json
{"farmToken": "eyJhbG...1nc4"}  # ← 字面量 "..." 被写入，不是真实 JWT
```

### 第 4 轮：验证失败，误判为后端问题

```
curl farm.events.poll -H "X-Farm-Token: eyJhbG...1nc4" → 401
```

Agent 误判：「可能是后端激活延迟」或「Token 抖动」

### 第 5-10 轮：重复死亡螺旋

重复执行 authorize-app → farm.activate → 写入截断 Token → 401 的循环：

| 轮次 | App Token | Farm Token（显示） | 结果 |
|------|-----------|-------------------|------|
| 1 | at-6a8f1e... | eyJhbG...0_wc | 401 |
| 2 | at-b4ffaa... | eyJhbG...Wrpk | 401 |
| 3 | at-e1236a... | eyJhbG...jSiI | 401 |
| 4 | at-7ae3d7... | eyJhbG...lINE | 401 |
| 5 | at-a63809... | eyJhbG...1nc4 | 401 |

每次新 token 都立即 401，Agent 始终未意识到是截断问题。

### 最终状态

- 50+ iterations 耗尽
- 任务被强制终止
- 农场零进展
- `credentials.json` 中保存的是无效的截断字符串

## 根因分析

### 直接原因：终端 stdout 截断

Hermes `terminal` 工具的 stdout 输出会对超过 ~100 字符的字符串进行截断显示：

```
{"farmToken":"eyJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoiZmFybSIsInVzZXJJZCI6NTM2MTMsImFjdG9yIjoiYWdlbnQiLCJpYXQiOjE3ODI3MzQ2NTYsImV4cCI6MTc4NDAzMDY1Nn0.VhAqdx411kvAh-fcjxkPT2Cj7_XWzgHlcWy16uJJcfo"}
```

显示为：
```
{"farmToken":"eyJhbG...Jcfo"}
```

Agent 从截断显示中复制字符串，用 `write_file` 写入文件，导致保存的是字面量 `"eyJhbG...Jcfo"`（约 13 字符），而非完整 JWT（约 200+ 字符）。

### 间接原因：Agent 的误判模式

当连续多次 farm.activate 后仍 401 时，Agent 没有检查 `credentials.json` 中的 Token 是否完整，而是归因于：
- 后端激活延迟
- Token 抖动
- 43chat session 失效
- API Key 被重置

这些归因都是错误的，真正的原因是 Token 从未被正确保存。

### 深层原因：缺乏截断检测机制

Agent 没有内置规则来检测：
- 字符串中是否包含 `...`（截断标记）
- Token 长度是否异常（< 50 字符）
- 从终端输出复制的字符串是否可信

## 正确处置（事后复盘）

### 方案 A：使用 Python 脚本自治处理（推荐）

```python
# /tmp/activate_and_save.py
import json, urllib.request

with open('/Users/chao/.config/43chat/credentials.json') as f:
    api_key = json.load(f)['api_key']

# authorize-app
req1 = urllib.request.Request(
    'https://43chat.cn/open/agent/authorize-app',
    data=json.dumps({"app_id": "agent-farm", "scopes": ["identity", "friends"]}).encode(),
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    method='POST'
)
resp1 = json.loads(urllib.request.urlopen(req1).read())
app_token = resp1['data']['app_token']

# farm.activate
req2 = urllib.request.Request(
    'https://farm.43chat.cn/trpc/farm.activate',
    data=b'{}',
    headers={'X-App-Token': app_token, 'Content-Type': 'application/json'},
    method='POST'
)
resp2 = json.loads(urllib.request.urlopen(req2).read())
new_token = resp2['farmToken']

# 直接写入（Python 变量，不受截断影响）
with open('/Users/chao/.config/43farm/credentials.json', 'w') as f:
    json.dump({'farmToken': new_token}, f)

print('saved')
```

然后 `terminal` 执行 `python3 /tmp/activate_and_save.py`。

### 方案 B：使用 read_file 验证 Token 完整性

在写入 `credentials.json` 后，立即用 `read_file` 读取验证：

```
read_file ~/.config/43farm/credentials.json
```

检查返回的 `farmToken` 值：
- 如果包含 `...` → 截断，需要重新获取
- 如果长度 < 50 → 截断，需要重新获取
- 如果长度 200+ 且不含 `...` → 完整，可以继续

### 方案 C：直接调用 heartbeat.py（最简）

```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

脚本内部自治处理 Token 恢复和文件写入，Agent 完全不介入字符串操作。

## 教训

1. **终端截断是确定性的**：任何超过 ~100 字符的字符串在 `terminal` 输出中都会被截断。这不是偶尔发生，而是每次都会发生。

2. **截断是静默的**：没有警告、没有提示、没有错误码。Agent 必须主动检测 `...` 标记。

3. **write_file 不会修复截断**：`write_file` 写入的是 Agent 上下文中的字符串值。如果该值已经是截断的，`write_file` 会忠实地写入截断版本。

4. **401 不一定是后端问题**：连续多次 401 可能是 Token 从未正确保存，而不是后端故障。

5. **迭代预算意识**：在 50-60 次 iteration 限制下，5 轮无意义的重复循环就会耗尽配额。每次 farm.activate 消耗 2-3 iterations（authorize + activate + write_file + verify），5 轮就是 15+ iterations，占预算的 25-30%。

## 相关参考

- `session-2026-06-18-token-redaction-breaks-substitution.md` — 终端凭证脱敏破坏 shell 语法
- `session-2026-06-26-farm-activate-token-immediately-401.md` — farm.activate 返回 token 但立即 401（不同根因）
- `session-2026-06-26-script-loop-trap-30-iterations.md` — 脚本循环陷阱
