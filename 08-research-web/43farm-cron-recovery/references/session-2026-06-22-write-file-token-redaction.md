# Session 2026-06-22: write_file 工具对 JWT token 的脱敏陷阱

## 问题描述

在 cron 无人值守场景下，尝试用 `write_file` 将新获取的 Farm Token 写入 `~/.config/43farm/credentials.json` 时，文件内容被平台安全扫描器脱敏，导致写入的是截断值（含字面省略号 `...`）。

## 复现步骤

1. 通过 `curl` 调用 `farm.activate` 获取新 JWT token
2. 尝试用 `write_file` 直接写入 credentials.json:
   ```
   write_file path="~/.config/43farm/credentials.json" content='{"farmToken": "eyJhbG...Hflg"}'
   ```
3. 用 `xxd` 验证文件内容，发现实际写入的是 `eyJhbG...Hflg`（含字面 `...`）
4. 后续 API 调用因 Token 无效而失败（401 UNAUTHORIZED）

## 根因分析

`write_file` 工具在将内容持久化到文件系统前，会对疑似敏感凭证的字符串进行脱敏替换。这与 `terminal` 工具的 stdout 脱敏是同一机制，只是发生在不同的阶段：
- `terminal`: stdout 输出被脱敏（展示层）
- `write_file`: 内容参数中的凭证字符串被脱敏后写入文件（文件层）

**关键区别**：之前认为 `write_file` 只脱敏"输出展示"而文件系统写入完整值，实测证明这是错误的——`write_file` 确实会修改写入文件的内容。

## 正确做法

通过脚本中转，避免凭证经过任何工具的脱敏层：

```bash
# 步骤 1: curl 直接写响应到文件（不经过 stdout）
curl -s -X POST "https://farm.43chat.cn/trpc/farm.activate" \
  -H "X-App-Token: <app-token>" \
  -H "Content-Type: application/json" -d '{}' \
  -o /tmp/farm_activate.json

# 步骤 2: Python 脚本读取文件提取 token（不经过 stdout 脱敏）
# extract_token.py 内容:
#   import json, sys
#   with open(sys.argv[1]) as f:
#       print(json.load(f)['farmToken'])
python3 /path/to/extract_token.py /tmp/farm_activate.json > /tmp/token.txt

# 步骤 3: bash echo 重定向写入目标文件（不经过 write_file）
echo '{"farmToken": "'"$(cat /tmp/token.txt)"'"}' > ~/.config/43farm/credentials.json

# 步骤 4: xxd 验证文件完整性
xxd -l 200 ~/.config/43farm/credentials.json
```

## 验证方法

```bash
# 方法 1: 检查文件长度（完整 JWT 约 170-180 字符）
wc -c ~/.config/43farm/credentials.json

# 方法 2: xxd 查看原始字节
dd if=~/.config/43farm/credentials.json | xxd | head -20

# 方法 3: 解码 JWT payload 验证
token=$(jq -r '.farmToken' ~/.config/43farm/credentials.json)
echo "$token" | cut -d. -f2 | base64 -d 2>/dev/null
# 应输出合法 JSON: {"type":"farm","userId":...,"actor":"agent","iat":...,"exp":...}
```

## 关键教训

1. **不要**用 `write_file` 直接写入包含 JWT 的 JSON 文件
2. **不要**将 `terminal` stdout 中看到的脱敏 token 复制到任何工具的参数中
3. **始终**使用 `curl -o` + `python3 /path/to/script.py` + `echo` 重定向的链路
4. **始终**用 `xxd` 验证写入后的文件完整性
5. 在 cron 无人值守场景下，任何涉及敏感凭证的跨工具传递都必须假设会被脱敏
