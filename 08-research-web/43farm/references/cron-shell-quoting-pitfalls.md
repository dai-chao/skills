# 43Farm Cron Shell 引号陷阱

## 场景

Cron 环境下执行 `curl` 命令时，如果命令行包含单引号（`'`）与双引号（`"`）混合使用，极易触发 bash 解析错误。本参考记录实测中的失败模式与修复方案。

## 实测失败模式

### 模式 1：单引号包裹的 Header 值中包含单引号

```bash
# ❌ 失败：-H 'Authorization: Bearer sk-744...8387' 中，如果 API Key 包含单引号字符
# 或终端工具对特殊字符进行转义，会导致 bash 解析错误
curl -s -X POST -H 'Content-Type: application/json' -H 'Authorization: Bearer sk-744...8387' -d '{"app_id":"43farm"}' 'https://43chat.cn/open/agent/authorize-app'
```

**错误输出**：
```
/bin/bash: eval: line 2: unexpected EOF while looking for matching `''
/bin/bash: eval: line 3: syntax error: unexpected end of file
```

**根因**：终端工具在传递命令给 bash 时，对命令中的单引号进行了转义或拆分，导致 bash 接收到的命令字符串中引号不匹配。这不是 bash 本身的问题，而是命令在传递过程中被修改了。

### 模式 2：双引号包裹的 Header 值中包含 `$` 变量引用

```bash
# ❌ 危险：双引号中 $API_KEY 会被 shell 展开，如果变量未定义则展开为空
curl -s -X POST -H "Authorization: Bearer $API_KEY" ...
```

当 `API_KEY` 环境变量未定义时，Header 变成 `Authorization: Bearer `（空值），导致 4010 错误。

### 模式 3：混合引号导致 eval 解析失败

```bash
# ❌ 失败：命令中同时存在单引号包裹的字符串和双引号包裹的 JSON
# 终端工具可能使用 eval 执行命令，混合引号导致 eval 解析错误
curl -s -X POST -H 'Content-Type: application/json' -H 'Authorization: Bearer ...' -d '{"app_id":"43farm"}' 'https://...'
```

### 模式 4：CJK 字符与 JWT Token 的交互陷阱（cron 场景）

在 cron/无人值守场景下，当命令行同时包含：
1. **CJK 字符**（中文、日文、韩文）—— 常见于 `echo` 注释或日志输出
2. **长 JWT Token**（含 `.` `-` `_` 等特殊字符）—— 如 `eyJhbG...xE6A`

即使两者在语法上分别正确，终端工具在传递命令给 bash 时也可能产生解析错误：

```bash
# ❌ 失败：echo 注释含中文，且 FARM_TOKEN 含特殊字符
FARM_TOKEN="eyJh..."
echo "=== 查看好友 芝麻绿豆 的农场 ==="
curl -s "https://farm.43chat.cn/trpc/farm.view?input=%7B%22userId%22%3A53575%7D" \
  -H "X-Farm-Token: $FARM_TOKEN" \
  -H "Accept: application/json"
```

**错误输出**：
```
/bin/bash: eval: line 12: unexpected EOF while looking for matching `"'
/bin/bash: eval: line 13: syntax error: unexpected end of file
```

**根因**：终端工具在将命令传递给 bash 时，对包含 CJK 字符和特殊字符的长字符串进行转义/编码处理，导致引号不匹配或字符串截断。这不是 bash 本身的问题，而是命令传递层的编码问题。

**修复**：将中文注释与命令主体分离，或完全避免中文注释：

```bash
# ✅ 正确：中文注释单独一行，命令行纯 ASCII
# 检查好友 芝麻绿豆 (userId=53575) 的农场
FARM_TOKEN="eyJh..."
curl -s "https://farm.43chat.cn/trpc/farm.view?input=%7B%22userId%22%3A53575%7D" \
  -H "X-Farm-Token: $FARM_TOKEN" \
  -H "Accept: application/json"
```

或更彻底：使用环境变量文件，命令行完全不出现中文和 token 字面量：

```bash
# ✅ 最佳实践：从文件读取 token，命令行无敏感信息
export FARM_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.config/43farm/credentials.json'))['farmToken'])")
export TARGET_UID=53575
curl -s "https://farm.43chat.cn/trpc/farm.view?input=%7B%22userId%22%3A${TARGET_UID}%7D" \
  -H "X-Farm-Token: $FARM_TOKEN" \
  -H "Accept: application/json"
```

### 模式 5：变量赋值行与命令行混写导致 token 被截断

在 cron 终端中，当 `export VAR="value"` 和实际命令写在同一行时，如果 value 包含特殊字符（如 JWT 的 `.`），终端工具可能在传递时截断：

```bash
# ❌ 失败：FARM_TOKEN 和 curl 写在同一行，token 被截断
FARM_TOKEN="eyJh..." curl -s -H "X-Farm-Token: $FARM_TOKEN" "https://..."
# 实际 bash 只接收到 FARM_TOKEN="eyJh"（第一个 . 处截断）
```

**错误输出**：
```
/bin/bash: line 2: -sL: command not found
```
或 token 被截断导致 401。

**修复**：变量赋值和命令必须分写在不同行：

```bash
# ✅ 正确：变量赋值单独一行
FARM_TOKEN="eyJh...完整token..."
# 命令在下一行
API_BASE="https://farm.43chat.cn/trpc"
curl -sL -H "X-Farm-Token: $FARM_TOKEN" "$API_BASE/farm.status"
```

**关键规则**：在 cron 终端中，永远不要将 `VAR="value"` 和实际命令写在同一行，即使中间用 `&&` 或 `;` 连接。JWT token 中的 `.` 字符会被 bash 解释为命令分隔符，导致 token 被截断和后续命令解析失败。

### 模式 5：echo 含 CJK 字符导致多行命令块整体失败（2026-06-29 实测）

当 `echo` 语句包含 CJK 字符（中文好友名），且同一 `terminal` 调用中包含多行命令时，即使 CJK 字符只在 `echo` 中、curl 命令在完全独立的行上，整个命令块也会失败：

```bash
# ❌ 失败：echo 含中文括号，导致后续所有行解析错误
echo "=== Friend 53580 (一鱼) ==="
curl -sL -H "X-Farm-Token: $TOKEN" "$API_BASE/farm.view?input=..."

echo "=== Friend 53577 (XX) ==="
curl -sL -H "X-Farm-Token: $TOKEN" "$API_BASE/farm.view?input=..."
```

**错误输出**：
```
/bin/bash: eval: line 30: syntax error near unexpected token `('
/bin/bash: eval: line 30: `echo "=== Friend 53580 (一鱼) ==="'
```

**根因**：终端工具在将多行命令传递给 bash 时，对包含 CJK 字符的行进行编码/转义处理，破坏了多行命令的边界识别。中文括号 `（）` 或全角字符尤其容易触发此问题。

**修复方案**：

```bash
# ✅ 方案 A：完全移除 echo 中的 CJK 字符，只用 ASCII
echo "=== Friend 53580 ==="
curl -sL -H "X-Farm-Token: $TOKEN" "$API_BASE/farm.view?input=..."

echo "=== Friend 53577 ==="
curl -sL -H "X-Farm-Token: $TOKEN" "$API_BASE/farm.view?input=..."
```

```bash
# ✅ 方案 B：将 echo 与 curl 拆分为独立的 terminal 调用
# 第一调：只 echo（即使失败也不影响后续）
# 第二调：只 curl（纯 ASCII，安全）
```

```bash
# ✅ 方案 C：使用纯 ASCII 的循环结构（推荐批量检查好友时）
for uid in 53580 53577 53596; do
  curl -sL -H "X-Farm-Token: $TOKEN" "$API_BASE/farm.view?input=%7B%22userId%22%3A${uid}%7D" > /tmp/f${uid}.json
  count=$(grep -o '"status":"mature"' /tmp/f${uid}.json | wc -l | tr -d ' ')
  echo "Friend $uid: $count mature"
done
```

**关键原则**：在 cron/无人值守的 `terminal` 调用中，**任何包含 CJK 字符的行都是高风险**。即使该行只是 `echo` 注释，也可能导致整个多行命令块解析失败。最安全的方式是：
1. 所有 `echo` 只使用 ASCII 字符（数字、英文、常用符号）
2. 需要中文输出时，使用 `printf` 而非 `echo`，或将中文输出重定向到文件后单独显示
3. 批量操作时优先使用 `for` 循环 + 纯 ASCII 变量名，避免在命令行中直接写中文

## 修复方案总结

### 方案 A：使用环境变量 + 双引号（推荐用于 cron 脚本）

将敏感值放入环境变量，命令行使用双引号引用变量：

```bash
# 先设置环境变量（从文件读取）
export API_KEY=$(jq -r '.api_key' ~/.config/43chat/credentials.json)

# 命令行使用双引号包裹变量引用（shell 会正确展开）
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"app_id":"43farm","app_name":"43Farm","description":"Farm automation"}' \
  "https://43chat.cn/open/agent/authorize-app"
```

**优点**：变量展开由 shell 处理，不会与命令行引号冲突。

### 方案 B：使用临时文件存储请求体（推荐用于复杂 JSON）

```bash
# 将请求体写入临时文件（避免命令行引号问题）
cat > /tmp/auth_body.json << 'EOF'
{"app_id":"43farm","app_name":"43Farm","description":"Farm automation"}
EOF

# curl 使用 --data-binary @file 读取请求体
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  --data-binary @/tmp/auth_body.json \
  "https://43chat.cn/open/agent/authorize-app"

# 清理临时文件
rm -f /tmp/auth_body.json
```

**优点**：请求体完全与命令行隔离，彻底避免引号冲突。

### 方案 C：使用纯 ASCII 命令行（避免 CJK / 特殊字符）

如果必须在命令行中直接写 JSON，确保：
1. 使用单引号包裹整个 JSON 字符串
2. JSON 内部使用双引号
3. 不包含任何单引号字符

```bash
# ✅ 安全：单引号包裹 JSON，JSON 内部只有双引号
curl -s -X POST -H 'Content-Type: application/json' -d '{"app_id":"43farm"}' "https://..."

# ❌ 危险：JSON 内部包含单引号（如英文缩写）
curl -s -X POST -d '{"desc":"It\'s working"}' ...  # 反斜杠转义在单引号中无效！
```

## 关键原则

1. **优先使用环境变量**：将动态值（token、key）放入环境变量，命令行只写静态字符串
2. **复杂 JSON 用文件**：任何包含中文、emoji、特殊字符的 JSON 都应写入临时文件
3. **避免混合引号**：不要在同一条命令中混用单双引号包裹不同部分
4. **验证命令执行**：如果 `curl` 返回 bash 错误而非 HTTP 响应，说明命令解析失败，不是 API 返回的错误
5. **Cron 环境特殊**：无人值守模式下 `python3 -c` 和 `execute_code` 被拦截，bash 是唯一选择，因此引号问题更致命

### 模式 6：sed 捕获组 `\(` `\)` 与命令替换 `$(...)` 冲突

当使用 `$(sed ...)` 命令替换提取 JSON 字段时，sed 表达式中的捕获组 `\(` `\)` 会与命令替换的 `$(` `)` 产生冲突：

```bash
# ❌ 失败：sed 的 \) 被 bash 解释为命令替换的结束括号
FARM_TOKEN=$(cat "$HOME/.config/43farm/credentials.json" | sed -n 's/.*"farmToken"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
```

**错误输出**：
```
/bin/bash: eval: line 17: syntax error near unexpected token `)'
/bin/bash: eval: line 17: `FARM_TOKEN=*** ... | sed -n 's/.*"farmToken"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')'
```

**根因**：终端工具在传递命令给 bash 时，sed 表达式末尾的 `\1/p'` 中的 `)` 被 bash 的 eval 解析器误认为是 `$(...)` 命令替换的结束括号，导致括号不匹配。

**修复方案**：

```bash
# ✅ 方案 A：使用 grep + cut 替代 sed 捕获组
FARM_TOKEN=$(cat "$HOME/.config/43farm/credentials.json" | grep -o '"farmToken":"[^"]*"' | cut -d'"' -f4)

# ✅ 方案 B：使用 jq（如果已安装）
FARM_TOKEN=$(jq -r '.farmToken' "$HOME/.config/43farm/credentials.json")

# ✅ 方案 C：使用 Python 脚本提取（cron 最可靠）
FARM_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.config/43farm/credentials.json'))['farmToken'])")
# 注意：cron 模式下 python3 -c 可能被拦截，此时应调用脚本文件而非内联
```

**关键原则**：在 cron/无人值守的 `terminal` 调用中，避免在 `$(...)` 命令替换内部使用包含 `\(` 或 `\)` 的 sed 表达式。优先使用 `grep + cut`、`jq` 或 Python 脚本提取 JSON 字段。

## 相关参考

- `references/cron-token-recovery.md` — 完整的 Token 过期恢复流程
- `scripts/heartbeat.py` — 心跳任务脚本（使用 Python 处理 JSON，避免 shell 引号问题）
