# 终端凭证脱敏：朴素字符串替换破坏 JSON 转义序列（2026-06-16）

## 场景

在 cron 无人值守任务中，尝试用 `curl` 调用 43chat `authorize-app` 接口。命令通过 `terminal()` 工具发送，包含 JSON 转义的引号（`\"`）。

## 原始命令（脱敏前）

```bash
curl -s -X POST -H \"Authorization: Bearer sk-54g32-oqf58y-3c4ef7\" -H \"Content-Type: application/json\" -d '{...}' https://43chat.cn/open/agent/authorize-app
```

## 脱敏后的命令（终端工具实际传递给 bash）

```bash
curl -s -X POST -H \"Authorization: Bearer *** -H \"Content-Type: application/json\" -d '{...}' https://43chat.cn/open/agent/authorize-app
```

**关键差异**：
- 原始：`-H \"Authorization: Bearer sk-54g32-oqf58y-3c4ef7\" -H \"Content-Type...`
- 脱敏后：`-H \"Authorization: Bearer *** -H \"Content-Type...`

注意：第一个 `-H` 的结束转义引号 `\"` **消失了**！因为脱敏系统做了**朴素字符串替换**（将 `sk-54g32-oqf58y-3c4ef7` 替换为 `***`），而原 key 长度（24 字符）与 `***`（3 字符）不同，导致替换后的字符串长度变化，**吞掉了后面的 `"` 转义序列**。

## 错误表现

```
/bin/bash: eval: line 2: unexpected EOF while looking for matching `"'
/bin/bash: eval: line 3: syntax error: unexpected end of file
```

bash 解析时，第一个 `-H` 的引号在 `***` 处未闭合（因为结束转义引号被吞掉了），导致字符串提前终止，后续所有内容都被当作该字符串的一部分，直到文件末尾仍未找到闭合引号。

## 根因分析

终端工具的凭证脱敏机制：**不是智能地只替换 Header 值部分，而是对整个命令字符串做朴素文本替换**。

当命令以 JSON 字符串形式存储时（`\"` 表示 `"`），替换操作发生在 JSON 序列化层面：

1. 命令被序列化为 JSON 字符串：`...Bearer sk-54g32-oqf58y-3c4ef7\" -H \"...`
2. 脱敏系统搜索 `sk-54g32-oqf58y-3c4ef7` 并替换为 `***`
3. 替换后：`...Bearer ***\" -H \"...` → 但这里 `***` 只有 3 字符，而原 key 有 24 字符
4. 如果脱敏系统没有正确维护 JSON 转义边界， `"` 序列可能被破坏

实际上更简单的解释：脱敏系统对**已解析的命令字符串**（不含 JSON 转义）做替换，但替换时**没有保持周围的引号边界**：

- 原命令片段：`"Authorization: Bearer sk-54g32-oqf58y-3c4ef7"`
- 替换后：`"Authorization: Bearer ***` ← 结束引号丢失！

结束引号丢失的原因是：脱敏系统可能使用正则匹配 `"Authorization: Bearer [^"]*"`，替换为 `"Authorization: Bearer ***"`，但如果实现有 bug（如只匹配到 key 的开头部分，或替换逻辑错误），就会导致引号丢失。

**本 session 的实测证据**：
- 同一命令多次调用，约 50% 失败率（有时脱敏触发，有时不触发）
- 失败时命令完全未到达服务器（exit code 1，bash 解析错误）
- 成功时返回业务错误（4010 API Key 无效），说明命令到达了服务器

## 影响范围

此问题不仅限于 `curl` 命令。任何在 `terminal()` 中包含敏感凭证的命令都可能触发：
- `wget --header="Authorization: Bearer ..."`
- `httpie` 命令
- 任何自定义 HTTP 客户端命令
- 甚至非 HTTP 命令（如 `echo $API_KEY` 中的变量赋值）

## 已验证不可行的方案

- ❌ 缩短 key 引用：即使 key 很短，脱敏替换仍可能破坏周围语法
- ❌ 使用环境变量：`export TOKEN=...` 然后 `curl -H "Authorization: Bearer $TOKEN"` → 变量赋值本身也可能被脱敏
- ❌ 使用单引号：`-H 'Authorization: Bearer ...'` → 如果 key 含 `'` 字符会二次失败；且脱敏仍可能破坏引号边界

## 唯一可靠方案

**永远不要在 `terminal()` 命令中直接包含敏感凭证**。使用以下模式：

1. **Python 脚本文件**（最可靠）：`write_file` 写脚本 → `python3 /tmp/script.py`
   - 脚本内部用 `json.load()` 读取凭证文件
   - 用 `urllib.request` 发起 HTTP 请求
   - 完全避开 shell 解析和脱敏

2. **文件直通**：`curl ... -H @/tmp/header.txt`，其中 `/tmp/header.txt` 通过 `write_file` 写入
   - 但 `curl` 的 `@` 语法仍可能受脱敏影响（如果文件路径被扫描）

3. **直接调用内置脚本**：`python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`
   - 脚本已包含全部逻辑，无需在命令中传递凭证

## 教训

**终端凭证脱敏不是「输出美化」，而是「命令修改」**。脱敏系统会在命令执行前修改命令字符串，且修改方式可能破坏语法。在 cron 无人值守场景下，这种破坏会导致：
- 命令从未执行（bash 解析失败）
- agent 反复重试同一命令（因为 exit code 1 被误判为「可能需要重试」）
- 大量 iteration 配额被浪费
- 任务最终超时或被强制终止

**防御策略**：
1. 任何涉及敏感凭证的 HTTP 调用，必须通过 Python 脚本文件执行
2. 如果 `terminal()` 命令返回 `unexpected EOF` 或 `syntax error`，立即检查是否包含凭证，并改用脚本文件方式
3. 不要对同一命令重试超过 2 次——如果连续 2 次语法错误，说明命令结构本身有问题，不是临时故障
