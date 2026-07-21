# authorize.py / authorize.sh 脚本损坏：Token 恢复的第一道防线失效（2026-06-26 会话实录）

## 场景

Farm Token 过期，所有 API 调用返回 401 UNAUTHORIZED。Agent 尝试使用 `authorize.py` 和 `authorize.sh` 重新获取 Token，但两个脚本均已损坏。

## 损坏的 authorize.py

**文件路径**：`/Users/chao/authorize.py`

**内容**：
```python
import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

api_key = 'sk-cc0...dbe9'
auth = 'Bearer ***  # ← 第 8 行：字符串未闭合，缺少右引号
req = urllib.request.Request(
    'https://43chat.cn/open/agent/authorize-app',
    data=json.dumps({'api_key': api_key}).encode('utf-8'),
    headers={
        'Authorization': auth,
        'Content-Type': 'application/json'
    },
    method='POST'
)

try:
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    print(resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
```

**错误**：
```
File "/Users/chao/authorize.py", line 8
    auth = 'Bearer *** req = urllib.request.Request(
                                                    ^
SyntaxError: EOL while scanning string literal
```

**根因分析**：
- `auth` 变量赋值时，右引号缺失
- 可能原因：`write_file` 写入时触发脱敏，将 `***` 替换破坏了引号配对
- 或者 agent 在生成脚本时引入了语法错误

## 损坏的 authorize.sh

**文件路径**：`/Users/chao/authorize.sh`

**内容**：
```bash
curl -s -X POST -H 'Authorization: Bearer *** -H 'Content-Type: application/json' -d '{"api_key":"sk-cc0...dbe9"}' 'https://43chat.cn/open/agent/authorize-app' > /tmp/authorize.json
cat /tmp/authorize.json
```

**错误**：
```
/Users/chao/authorize.sh: line 1: unexpected EOF while looking for matching `''
/Users/chao/authorize.sh: line 3: syntax error: unexpected end of file
```

**hexdump 分析**：
```
00000000: 6375 726c 202d 7320 2d58 2050 4f53 5420  curl -s -X POST
00000020: 2d48 2027 4175 7468 6f72 697a 6174 696f  -H 'Authorizatio
00000040: 6e3a 2042 6561 7265 7220 2a2a 2a20 2d48  n: Bearer *** -H
00000060: 2027 436f 6e74 656e 742d 5479 7065 3a20   'Content-Type:
```

**根因分析**：
- 第 1 个 `-H` 的左单引号在 `Authorization: Bearer *** 处开始
- 但右单引号在 `Content-Type` 之前结束（`*** -H '`）
- 导致 `Content-Type: application/json` 成为未引号的裸字符串
- 后续的单引号 `'https://...'` 与前面的引号配对混乱

**可能原因**：
- `write_file` 写入时触发脱敏，将 API Key 替换为 `***`，破坏了原有的引号结构
- 或者 agent 在生成脚本时未正确转义嵌套引号

## 修复尝试

Agent 尝试修复 `authorize.py`：
1. 使用 `patch` 工具替换 `auth = 'Bearer ***` → 失败（old_string 和 new_string 相同）
2. 使用 `write_file` 重写 `authorize_fixed.py` → 仍然包含相同的语法错误
3. 尝试 `python3 -c` 直接执行 → 被安全扫描 pending_approval

所有修复尝试均失败，因为：
- `patch` 无法匹配损坏的字符串（包含未闭合引号）
- `write_file` 在写入含凭证内容时可能再次触发脱敏
- cron 模式下 `python3 -c` 被拦截

## 影响

1. **Token 恢复完全阻塞**：`authorize.py` 和 `authorize.sh` 是手动恢复的第一道防线
2. **只能依赖 `heartbeat.py` 自动恢复**：但 `heartbeat.py` 也可能失败（如 API Key 也失效）
3. **迭代浪费**：修复损坏脚本消耗了 5+ iterations

## 正确处置

### 发现脚本损坏时

1. **不要尝试修复损坏的脚本**（修复消耗 iteration，且可能引入更多错误）
2. **直接调用 `heartbeat.py`**（内置脚本通常更可靠）
3. 如果 `heartbeat.py` 也无法恢复，进入 `43farm-cron-recovery` 手动恢复流程

### 预防脚本损坏

1. **使用 `write_file` 写脚本时避免嵌入敏感凭证**：
   - 不要在脚本中硬编码 API Key 或 Token
   - 让脚本从 `credentials.json` 读取凭证
   - 这样 `write_file` 不会触发脱敏（因为写入的内容不含真实凭证）

2. **脚本语法验证**：
```bash
# 写完后立即验证
python3 -m py_compile /tmp/script.py 2>&1 || echo "SYNTAX_ERROR"
```

3. **使用 `read_file` 读取凭证 + 脚本内部处理**：
```python
# 正确的脚本写法（避免嵌入凭证）
import json
with open('/Users/chao/.config/43chat/credentials.json') as f:
    creds = json.load(f)
api_key = creds['api_key']
# ... 使用 api_key 调用 API ...
```

## 教训

1. **不要依赖用户目录下的自定义脚本进行 Token 恢复**
2. **`heartbeat.py` 是唯一的可靠恢复路径**
3. 自定义脚本（authorize.py、authorize.sh）容易因脱敏或语法错误而损坏
4. **在 cron 心跳执行器中，如果检测到 authorize 脚本损坏，应直接跳过并调用 `heartbeat.py`**
5. **脚本中不要硬编码凭证**：让脚本从配置文件读取，避免 `write_file` 脱敏问题

## 相关文件

- `/Users/chao/authorize.py`（损坏）
- `/Users/chao/authorize.sh`（损坏）
- `/Users/chao/authorize_fixed.py`（修复尝试失败）
- `/Users/chao/.config/43farm/credentials.json`（Farm Token，已过期）
- `/Users/chao/.config/43farm/credentials.json.bak`（备份 Token，也已过期）
