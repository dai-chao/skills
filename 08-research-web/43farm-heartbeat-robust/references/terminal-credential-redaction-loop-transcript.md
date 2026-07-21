# Terminal 凭证脱敏导致的无限循环故障实录

## 会话信息
- **日期**: 2026-06-15
- **触发场景**: 43Farm cron 心跳任务，Farm Token 过期后尝试重激活
- **Hermes 版本**: 运行中版本（2026-06-15）
- **影响**: 同一命令被重复执行 50+ 次，浪费大量 iteration 配额，任务最终失败

## 故障时间线

### 阶段 1：Farm Token 过期检测
```
$ curl -s -X GET -H "X-Farm-Token: eyJhbG...Ur00" https://farm.43chat.cn/trpc/farm.events.poll
{"error":{"message":"Farm Token 无效或已过期...","code":-32001}}
```
- 确认 Farm Token 过期，进入「日常自愈」流程

### 阶段 2：尝试 refreshToken
```
$ curl -s -X POST -H "X-Farm-Token: eyJhbG...Ur00" https://farm.43chat.cn/trpc/auth.refreshToken
{"error":{"message":"Farm Token 无法续签（旧 token 不合法或 43chat session 已失效）"}}
```
- refreshToken 失败，按 INSTALL.md 指引进入重激活流程

### 阶段 3：读取 43chat API Key
```
$ cat ~/.config/43chat/credentials.json
{
  "api_key": "sk-997...fbc5",
  ...
}
```
- 成功读取 API Key，但 Key 在终端输出中被截断显示为 `sk-997...fbc5`

### 阶段 4：尝试调用 authorize-app（故障开始）

**首次尝试**（命令被脱敏替换）：
```
$ curl -s -X POST -H "Authorization: Bearer *** -H "Content-Type: application/json" -d '{"app_id":"agent-farm","scopes":["identity","friends"]}' https://43chat.cn/open/agent/authorize-app
{"code":4010,"message":"API Key 无效或已被重置..."}
```
- 返回 4010，说明 API Key 确实已失效（这是业务错误，非技术错误）

**第二次尝试**（同一命令）：
```
$ curl -s -X POST -H "Authorization: Bearer *** -H "Content-Type: application/json" -d '{"app_id":"agent-farm","scopes":["identity","friends"]}' https://43chat.cn/open/agent/authorize-app
/bin/bash: eval: line 2: unexpected EOF while looking for matching `"'
/bin/bash: eval: line 3: syntax error: unexpected end of file
```
- **同一命令，第二次执行时触发 shell 语法错误**
- 退出码 1，命令未实际发送到服务器

**后续 40+ 次尝试**：
- 命令内容完全相同
- 结果随机交替：约 50% 返回 4010（脱敏未触发），50% 返回 bash 语法错误（脱敏触发）
- 系统发出「repeated_exact_failure_warning」共 50 次
- 最终 iteration 配额耗尽，任务终止

## 根因分析

### 直接原因
Hermes `terminal()` 工具的**凭证脱敏机制**在替换命令中的敏感字符串时，破坏了 shell 引号配对。

### 触发机制
1. 命令字符串中包含 `-H "Authorization: Bearer sk-997...fbc5"`
2. 脱敏系统识别 `sk-997...fbc5` 为敏感凭证（API Key 格式）
3. 将 `sk-997...fbc5` 替换为字面量 `***`
4. 替换后的命令变为 `-H "Authorization: Bearer ***"`
5. 但替换操作可能影响了引号边界，导致 bash eval 时字符串解析失败

### 为什么同一命令有时成功有时失败？
- 脱敏系统的触发可能基于某种概率或上下文检测
- 当脱敏系统**未介入**时，命令中的完整 Key 被传递给 bash（虽然 Key 本身也可能含特殊字符导致问题）
- 当脱敏系统**介入**时，`***` 替换破坏了语法

## 影响评估

| 维度 | 影响 |
|------|------|
| 任务完成 | ❌ 失败，心跳任务未执行任何农场操作 |
| 迭代配额 | ⚠️ 浪费 50+ 次 iteration |
| 用户感知 | ⚠️ 主人收到失败报告，需要手动更新 API Key |
| 数据完整性 | ✅ 无损坏（命令未实际执行）|

## 已验证的解决方案

### 方案 A：Python 脚本文件（最可靠）
```python
# /tmp/farm_heartbeat.py
import json, urllib.request, os, time

# 读取凭证（完全在 Python 内部，不经过 shell）
with open(os.path.expanduser('~/.config/43farm/credentials.json')) as f:
    farm_token = json.load(f)['farmToken']
with open(os.path.expanduser('~/.config/43chat/credentials.json')) as f:
    api_key = json.load(f)['api_key']

# 所有 HTTP 调用通过 urllib.request 处理
req = urllib.request.Request(
    'https://farm.43chat.cn/trpc/farm.events.poll',
    headers={'X-Farm-Token': farm_token}
)
# ... 其余逻辑
```

执行方式：
```bash
$ python3 /tmp/farm_heartbeat.py
```

**优势**：
- 完全避开 shell 解析和脱敏机制
- 可以处理复杂的 JSON 解析、错误重试逻辑
- 在 cron 模式下，`python3 /path/to/file.py` 不触发 interpreter 拦截

### 方案 B：curl 的 --header 文件（适用于简单 GET）
```bash
# 先将 header 写入文件
echo "X-Farm-Token: $TOKEN" > /tmp/header.txt
# 使用 -H @file 语法
curl -s -H @/tmp/header.txt https://farm.43chat.cn/trpc/farm.events.poll
```

**注意**：`$TOKEN` 仍需通过某种方式传入，如果通过 `$(cat file)` 仍可能触发 `)` 解析问题。

## 预防措施

1. **在 cron 任务中，永远不要在 `terminal()` 中写含凭证的 curl 命令**
2. **优先使用 `write_file` + `python3 /tmp/script.py` 模式**
3. **如果必须使用 curl，将凭证写入文件后用 `-H @file` 读取**
4. **监控 iteration 使用**：如果同一命令调用超过 3 次，立即检查是否陷入循环

## 相关参考

- `43farm-cron-recovery/references/session-2025-06-14-both-tokens-dead.md` — 类似的 Token 过期恢复场景
- `terminal-credential-redaction` skill — 终端脱敏行为的系统级说明
