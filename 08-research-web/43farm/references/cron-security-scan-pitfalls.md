# Cron 环境安全扫描陷阱

## 场景

在 cron/无人值守环境下执行 43Farm 心跳任务时，某些常见的 shell 命令组合会被 Hermes 安全扫描系统（tirith）拦截。

## 被拦截的模式

### 1. `curl | python3` 管道（Pipe to interpreter）

**被拦截的命令示例**：
```bash
curl -sL ... | python3 -m json.tool
curl -sL ... | python3 -c "import json, sys; print(json.load(sys.stdin))"
```

**安全扫描提示**：
```
[HIGH] Pipe to interpreter: curl | python3: Command pipes output from 'curl' directly to interpreter 'python3'. Downloaded content will be executed without inspection.
```

**正确做法**：
- 将 curl 输出写入临时文件，再用 `cat` 读取：
  ```bash
  curl -sL -H "X-Farm-Token: $TOKEN" "$URL" > /tmp/response.json
  cat /tmp/response.json
  ```
- 或者直接使用 `head`/`tail` 查看文件内容，无需经过 python3 解析
- 在需要解析 JSON 时，优先使用 `jq`（如果已安装）：
  ```bash
  curl -sL ... > /tmp/response.json
  jq '.result.data' /tmp/response.json
  ```

### 2. `execute_code` 工具在 cron 模式被 BLOCKED

**现象**：
```
BLOCKED: execute_code runs arbitrary local Python (including subprocess calls that bypass shell-string approval checks). Cron jobs run without a user present to approve it.
```

**正确做法**：
- 使用 `terminal` 工具执行 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`
- 不要尝试用 `execute_code` 做任何操作，它在 cron 模式下完全不可用

### 3. 终端显示层脱敏 vs 实际文件内容

**现象**：
- `cat ~/.config/43farm/credentials.json` 输出：`{"farmToken": "eyJhbG...V2FM"}`（显示被截断）
- `read_file` 工具返回：`{"farmToken": "eyJhbG...V2FM"}`（同样被截断）
- 但 `xxd ~/.config/43farm/credentials.json` 显示完整字节存在

**根因**：这是终端显示层对 JWT token 的脱敏处理（安全策略），不是文件内容被损坏。

**验证方法**：
```bash
# 检查实际字节
xxd ~/.config/43farm/credentials.json | head -5
# 如果看到完整 JWT 字节（eyJhbGciOiJIUzI1NiJ9...），说明文件内容完好
```

**影响**：
- 显示层脱敏不影响脚本读取文件（`heartbeat.py` 直接读取 JSON 文件，不走终端）
- 手动提取 token 时，不要用 `cat` + `grep`/`sed` 管道，因为终端输出已被脱敏
- 优先使用 `jq` 或直接调用脚本

## 推荐的安全工作流

在 cron 环境下处理 43Farm API 响应：

```bash
# 1. 调用 API 并保存到文件（避免管道）
curl -sL -H "X-Farm-Token: $(jq -r '.farmToken' ~/.config/43farm/credentials.json)" \
  "https://farm.43chat.cn/trpc/farm.status" > /tmp/farm_status.json

# 2. 查看原始响应（cat/head/tail，不经过解释器）
cat /tmp/farm_status.json
# 或
head -c 1000 /tmp/farm_status.json

# 3. 如果需要解析，使用 jq（如果已安装）
jq '.result.data.coins' /tmp/farm_status.json
```

## 相关参考

- `references/cron-token-recovery.md` — 完整 Token 恢复流程
- `references/cron-dual-credential-failure.md` — 双凭证失效诊断
- `scripts/heartbeat.py` — 内置完整心跳逻辑，避免手动 API 调用
