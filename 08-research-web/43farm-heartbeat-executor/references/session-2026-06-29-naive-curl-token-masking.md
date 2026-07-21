# 2026-06-29: 展示层脱敏导致 curl 命令使用掩码 Token 的陷阱

## 场景

Cron 心跳执行时，读取 `~/.config/43farm/credentials.json` 后，agent 在 `terminal` 命令中直接写 `curl -H "X-Farm-Token: eyJhbG...V2FM"`。这里的 `...` 是展示层脱敏（read_file 输出中的 `...`），不是真实 Token 的一部分。

## 典型表现

1. `read_file` 读取 `credentials.json` 返回内容：
   ```json
   {"farmToken": "eyJhbG...V2FM"}
   ```
   注意：`...` 是 read_file 工具对长字符串的展示层截断，不是文件中的真实内容。

2. Agent 将脱敏后的字符串直接复制到 `terminal` 命令中：
   ```bash
   curl -s -H "X-Farm-Token: eyJhbG...V2FM" "https://farm.43chat.cn/trpc/farm.events.poll"
   ```

3. 结果：
   - 有时返回正常数据（`{"result":{"data":{"events":[],"gameplayVersion":"1.1.1"}}}`）
   - 有时返回 401 `UNAUTHORIZED`
   - 呈现**间歇性成功/失败**的随机模式

## 根因分析

`terminal` 工具在将命令传递给 bash 前，会对命令中的 `***` 或 `...` 占位符进行**反向脱敏还原**——将 `...` 替换回完整的真实字符串。但这种还原：

- **不是确定性的**：取决于工具的脱敏系统是否识别到该占位符
- **可能部分还原**：只还原部分字符，导致 Token 不完整
- **与展示层截断无关**：`read_file` 的 `...` 是展示截断，`terminal` 的还原机制是独立的，两者不保证同步

因此同一命令在 1 秒内连续调用，有时成功（Token 被完整还原）有时失败（Token 还原不完整或被跳过）。

## 与 Token 抖动的区别

| 特征 | 展示层脱敏导致掩码 Token | 后端 Token 抖动 |
|------|------------------------|----------------|
| 命令中 Token 是否完整 | 不完整（含 `...`） | 完整（从文件读取） |
| 成功/失败模式 | 随机（同一命令连续调用结果不同） | 间歇性（成功/失败交替） |
| 成功时响应 | 正常数据 | 正常数据 |
| 失败时响应 | 401 UNAUTHORIZED | 401 UNAUTHORIZED |
| 根因 | 工具层脱敏还原不一致 | 后端验证缓存不同步 |
| 解决 | 使用完整 Token 或脚本 | 重试 2-3 次或运行脚本 |

## 正确做法

**绝对不要在 terminal 命令中直接使用从 read_file 复制来的含 `...` 的 Token 字符串。**

### 方案 1：优先调用脚本（推荐）

```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

脚本内部使用 `json.load()` 直接从文件读取完整 Token，不经过任何展示层脱敏。

### 方案 2：使用完整 Token（如果已知）

如果 Token 是已知的完整字符串（从之前的成功调用中获取），可以直接嵌入命令：

```bash
curl -s -H "X-Farm-Token: eyJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoiZmFybSIsInVzZXJJZCI6NTM2MTMsImFjdG9yIjoiYWdlbnQiLCJpYXQiOjE3ODI2OTkwNDIsImV4cCI6MTc4Mzk5NTA0Mn0.Mk_dJezcqAYaDzLSMSQcEkjpM4KF71fzGUga5JqV2FM" "https://farm.43chat.cn/trpc/farm.events.poll"
```

但注意：
- 如果 Token 在命令中被工具脱敏为 `***`，会触发引号逃逸错误（见 `43farm-heartbeat-robust` 技能的「Terminal 命令凭证脱敏」章节）
- 长 Token 在 terminal 输出中会被截断显示，不要从输出中复制回命令

### 方案 3：使用 `read_file` 读取后由脚本内部使用

```python
# /tmp/farm_check.py
import json, urllib.request

with open('/Users/chao/.config/43farm/credentials.json') as f:
    token = json.load(f)['farmToken']

req = urllib.request.Request(
    'https://farm.43chat.cn/trpc/farm.events.poll',
    headers={'X-Farm-Token': token}
)
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
```

然后执行：`python3 /tmp/farm_check.py`

## 教训

1. **read_file 返回的 `...` 是展示截断，不是真实内容**：不要将其复制到任何命令中
2. **terminal 工具的脱敏还原机制不一致**：使用含 `...` 的字符串会导致随机成功/失败
3. **脚本优先原则**：任何涉及 Token 的 API 调用都应通过脚本内部读取文件完成，避免展示层脱敏
4. **间歇性 401 不一定等于 Token 抖动**：先检查命令中的 Token 是否完整，再判断是否为后端问题
