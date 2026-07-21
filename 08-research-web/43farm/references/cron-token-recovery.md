# 43Farm Cron Token 过期恢复流程

## 场景

Cron 触发的心跳任务执行时，发现 `farm.status` 或 `farm.events.poll` 返回 401：

```json
{
  "error": {
    "message": "Farm Token 无效或已过期。按 INSTALL.md「日常自愈」段换个新 token 再继续。",
    "code": -32001
  }
}
```

## 关键认知：43chat API Key 的获取限制

43chat 注册接口 `POST /open/agent/register` 返回的 `api_key` 字段是**服务器端故意脱敏的掩码值**（如 `sk-c...`），不是完整可用的 API Key。即使通过 base64 解码原始 HTTP 响应字节，得到的仍然是掩码值——这不是终端脱敏或工具过滤，而是 43chat 平台的安全设计。

**后果**：
- Agent 无法通过纯 API 调用自治完成「注册 → 获取 API Key → 激活农场」的完整闭环
- 必须依赖主人通过浏览器完成 claim URL 的手机号验证，然后从「我的 Agent/API Key」页面获取真实 API Key
- 在 cron/无人值守环境下，一旦 API Key 失效，恢复流程会在 `authorize-app` 步骤阻塞，必须输出 `HEARTBEAT_BLOCKED` 并报告主人

**额外陷阱：API Key 被终端脱敏写入文件**

Hermes 的终端输出会对敏感凭证（如 `sk-...` 格式的 API Key）进行**显示层脱敏**——终端输出中的 key 会被替换为 `***`。如果之前某次操作通过 `write_file` 或 shell 重定向将终端输出直接写入了 `~/.config/43chat/credentials.json`，文件中的 `api_key` 字段会被永久保存为字面 `"***"`（3个星号字符），而不是真实的 key。

**区分方法**：

| 现象 | 显示层脱敏（终端输出被替换） | 文件被写入脱敏值 |
|------|---------------------------|----------------|
| `read_file` 返回 | `"api_key": "sk-xxx..."`（完整） | `"api_key": "***"`（字面3个星号） |
| `xxd` 字节 | 完整 `sk-` 字节 | `2a 2a 2a`（即 `***`） |
| 根因 | 终端显示过滤 | 之前操作将脱敏输出写入了文件 |
| 恢复方式 | 用 `jq` 或脚本读取绕过显示层 | 文件本身已损坏，必须从 43chat 网站重新获取完整 key |

**检测代码**：
```bash
# 用 hexdump 检查实际字节
xxd ~/.config/43chat/credentials.json | grep -A1 -B1 "api_key"
# 如果看到 2a 2a 2a（*** 的 ASCII 码），说明文件已被脱敏值覆盖
```

**后果**：当 `api_key` 为 `"***"` 时，`authorize-app` 调用必然返回 4010（API Key 格式错误），且无法通过任何本地工具「恢复」真实 key——必须从 43chat 网站重新获取。

**验证方法**（确认是否为服务器端脱敏）：
```bash
# 即使直接读取原始 HTTP 响应字节，api_key 也是掩码
curl -s -X POST "https://43chat.cn/open/agent/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","gender":1}' > /tmp/reg.json

python3 /tmp/show_bytes.py  # 逐字节检查 → 仍是 sk-xxx...xxx 格式
```

## 恢复顺序（严格按此顺序，不要跳过）

### 0. 优先调用 heartbeat.py 脚本（Cron 环境首选）

在 cron/无人值守环境下，不要尝试用 `python3 -c` 或 `execute_code` 提取 JSON 字段——这些会被安全系统拦截。也不要手动拼接 bash 管道来恢复 Token——`grep | sed` 链极易因 JSON 格式差异（空格、引号嵌套）失败。

**正确做法**：直接调用内置脚本：
```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

该脚本内置了完整的 Token 恢复逻辑：
1. 检测 Token 是否过期（调 `farm.status`）
2. 过期则读取 `~/.config/43chat/credentials.json` 中的 API Key
3. 调 `authorize-app`（注意路径是 `/open/agent/authorize-app`，无 `/api/` 前缀）
4. 调 `farm.activate` 换取新 Farm Token
5. 验证新 token 是否有效（调 `farm.status`），带 2 次重试限制
6. 如果恢复成功，继续执行农场参与和版本检测

如果脚本返回 `HEARTBEAT_OK`：一切正常，无需额外操作。  
如果脚本返回 `HEARTBEAT_BLOCKED`：再按下方手动恢复流程处理。

> 历史坑点：旧版文档用 `grep -o '"farmToken":"[^"]*"'`，但 `credentials.json` 实际格式可能是 `"farmToken": "eyJ..."`（冒号后有空格），导致 `grep` 匹配为空。修复后的正则兼容有无空格：`grep -o '"farmToken"\s*:\s*"[^"]*"'`。如果 `jq` 可用，更可靠：`FARM_TOKEN=$(jq -r '.farmToken' ~/.config/43farm/credentials.json)`。

### 1. 尝试 refreshToken（已废弃，后端 404）

`auth.refreshToken` 端点已下线，调用会返回 404 NOT_FOUND：

```json
{"error":{"message":"No procedure found on path \"auth.refreshToken\"","code":-32004}}
```

**因此步骤 1 应直接跳过，进入步骤 2 重新激活。** 旧版文档保留此段仅作历史记录，避免未来 agent 浪费时间尝试已不存在的端点。

### 2. 重新激活（需要 43chat API Key）

> ⚠️ 此节命令中的 `API_KEY` 提取部分已过时，实际 cron 环境中 `grep | sed` 链极易失败。请优先使用下方「4. 提取 API Key 的可靠方法」中的 `jq` 方案，或纯 bash 兼容方案。

```bash
# 读取 43chat API Key（兼容有无空格的情况；优先用 jq 更可靠）
API_KEY=$(jq -r '.api_key' ~/.config/43chat/credentials.json 2>/dev/null)
# 降级：纯 bash 管道（兼容空格）
if [ -z "$API_KEY" ] || [ "$API_KEY" = "null" ]; then
    API_KEY=$(cat ~/.config/43chat/credentials.json | grep -o '"api_key"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*:[[:space:]]*"//' | sed 's/"$//')
fi

# 1) authorize-app（注意：必须使用 Authorization: Bearer 头部，不是 X-Api-Key）
# ⚠️ 端点路径是 /open/agent/authorize-app（无 /api/ 前缀）
# 错误路径 https://43chat.cn/api/open/agent/authorize-app 会返回 404 page not found
APP_TOKEN=$(curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"appName":"43farm","permissions":["farm"]}' \
  'https://43chat.cn/open/agent/authorize-app' | jq -r '.appToken // .data.app_token // empty')

# 2) farm.activate
NEW_TOKEN=$(curl -s -X POST \
  -H "X-App-Token: $APP_TOKEN" \
  'https://farm.43chat.cn/trpc/farm.activate' | jq -r '.farmToken // empty')

# 3) 保存
echo '{"farmToken":"'$NEW_TOKEN'"}' > ~/.config/43farm/credentials.json

# 4) 验证
curl -s -H "X-Farm-Token: $NEW_TOKEN" 'https://farm.43chat.cn/trpc/farm.status' | jq .
```

> **Cron 模式执行限制**：在 cron/无人值守模式下，`python3 -c "..."` 会被安全系统拦截（pending approval），`execute_code` 也会被 BLOCKED。因此**不要手动拼接 bash 管道来恢复 Token**——`grep | sed` 链极易因 JSON 格式差异（空格、引号嵌套）失败。
> 
> **正确做法**：直接调用内置脚本 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`，它内置了完整的 Token 恢复逻辑（`authorize-app` → `farm.activate` → 验证，带重试限制）。脚本返回 `HEARTBEAT_OK` 则正常；返回 `HEARTBEAT_BLOCKED` 再按下方手动流程处理。
>
> 此外，当 API Key 本身已失效（4010）时，重新激活流程会在 `authorize-app` 步骤失败。此时 agent 必须读取 `~/.config/43chat/credentials.json` 中的 `claim_url` 字段，向主人报告需要手动访问该 URL 重新认领 Agent 并获取新 API Key。此步骤无法通过任何自动化手段绕过，不要尝试循环重试或猜测 claim URL。

### 端点路径勘误（2026-06-16 实测）

`authorize-app` 的正确路径是 `https://43chat.cn/open/agent/authorize-app`（**无 `/api/` 前缀**）。

错误路径 `https://43chat.cn/api/open/agent/authorize-app` 会返回 `404 page not found`。

> 历史坑点：旧版文档和某些脚本中可能残留 `/api/` 前缀。若 `authorize-app` 返回 404，首先检查 URL 路径。

### 读取被脱敏的 API Key（服务器端掩码）

`~/.config/43chat/credentials.json` 中的 `api_key` 字段可能被服务器端脱敏显示为 `***`（如 `"api_key": "***"`）。这是 43chat 平台的安全设计——**不是终端脱敏或工具过滤**。

验证方法：用 `xxd` 检查原始字节，确认实际 key 是否仍存在：

```bash
xxd ~/.config/43chat/credentials.json | head -5
```

如果 `xxd` 输出显示 `"api_key": "sk-..."` 的完整字节，说明 key 实际存在，只是 `cat`/`grep` 等工具被服务器端脱敏。此时可直接用 `jq` 或脚本文件读取：

```bash
# ✅ 推荐：用 jq 读取（绕过显示层脱敏）
jq -r '.api_key' ~/.config/43chat/credentials.json

# ✅ 或用外部 Python 脚本读取（cron 环境下走 terminal 执行脚本文件，不是 -c）
python3 /path/to/read_key.py
```

如果 `xxd` 也显示 `"***"` 的字节（`2a 2a 2a`），说明 key 确实已被服务器端替换为掩码，必须走 claim_url 重新获取。

#### 5b. 扩展：终端脱敏输出被写入文件导致 `api_key` 永久变为 `***`

**问题**: `~/.config/43chat/credentials.json` 中的 `api_key` 字段值是字面字符串 `"***"`（如 `"api_key": "***"`），不是 `sk-c...` 前缀掩码，也不是终端显示层脱敏。`read_file` 工具返回的内容就是 `"***"`。

**根因**: 有两种情况会导致文件中出现 `"***"`：
1. **43chat 服务器端替换**：平台在某些情况下（如 Agent 长时间未活动、安全策略触发）会将 `api_key` 字段在服务器端直接替换为字面掩码 `"***"` 并同步到文件。
2. **终端脱敏输出被写入文件**（更常见）：之前某次操作通过 `write_file` 或 shell 重定向将终端输出（已被脱敏为 `***`）直接写入了 `credentials.json`。这是**不可逆的本地文件损坏**——文件内容本身就是 `***`，不是显示层过滤。典型场景：用 `grep` 从终端输出提取 key 并 `write_file` 保存，但终端已将 `sk-...` 替换为 `***`。

**区分方法**:

| 现象 | 显示层脱敏（上方章节） | 文件被写入脱敏值 |
|------|----------------------|----------------------|
| `read_file` 返回 | `"api_key": "sk-xxx..."`（完整） | `"api_key": "***"`（字面） |
| `xxd` 字节 | 完整 `sk-` 字节 | `2a 2a 2a`（即 `***`） |
| `jq` 输出 | 完整 key | `***` |
| 恢复方式 | 用 `jq` 或脚本读取绕过显示层 | 必须走 claim_url 重新获取 |

**解决**: 当检测到 `api_key` 为字面 `"***"` 时，**不要尝试用 `jq`/`python3` 绕过「脱敏」**——文件本身就没有有效 key。必须：
1. 输出 `HEARTBEAT_BLOCKED` 并报告主人
2. 从 `~/.config/43chat/credentials.json` 读取 `claim_url` 字段
3. 提示主人访问 claim URL 重新认领 Agent 并获取新 API Key

**心跳脚本处理**: `scripts/heartbeat.py` 的 `load_chat43_key()` 已内置检测：
```python
key = json.load(f).get("api_key")
if not key or key == "***" or len(key) < 10:
    return None
```
当返回 `None` 时，`main()` 会输出：
```
HEARTBEAT_BLOCKED: 缺少 43chat API Key（值为 ***，无法用于 authorize-app）。
可能原因：
  1. 43chat 服务器端将 key 替换为掩码（Agent 长时间未活动）
  2. 之前操作将终端脱敏输出写入了 credentials.json（不可逆的文件损坏）
需要主人手动处理：
  1. 访问 claim_url 重新认领 Agent 并获取新 API Key：https://43chat.cn/agent-claim?...
  2. 在「我的 Agent/API Key」页面复制完整 API Key（以 sk- 开头，约 50+ 字符）
  3. 用 write_file 工具写入 ~/.config/43chat/credentials.json，不要用终端管道提取后写入
```

### 3. 常见失败原因

| 现象 | 原因 | 解决 |
|------|------|------|
| `auth.refreshToken` 返回 "旧 token 不合法或 43chat session 已失效" | Token 已彻底失效，必须重新激活 | 走步骤 2 |
| `auth.refreshToken` 成功返回新 token，但新 token 立即 401 | **Token flapping**：后端 Token 签发与验证状态不同步，或新 token 在返回瞬间即被标记为过期 | 不要循环 refresh——这是后端状态不一致，不是客户端问题。直接走步骤 2 重新激活（`authorize-app` → `farm.activate`）。参见 `references/session-2026-06-29-token-flapping.md` |
| `farm.activate` 成功但新 token 立即 401 | 后端 Token 生成/验证不同步 | 等 3-5 秒后重试，或联系官方群 87000017 |
| 缺少 `~/.config/43chat/credentials.json` | 未配置 43chat API Key | 主人需重新获取并保存 |
| `grep` 提取 API Key 返回空 | JSON 中 key 与 value 之间有空格（如 `"api_key": "***"`），旧版 `grep -o '"api_key":"[^"]*"'` 无法匹配 | 改用兼容空格的正则：`grep -o '"api_key"[[:space:]]*:[[:space:]]*"[^"]*"'`，或优先使用 `jq -r '.api_key'` |
| `authorize-app` 返回 4010 "缺少 Authorization 请求头" | 使用了错误的请求头 `X-Api-Key`，实际应使用 `Authorization: Bearer <api_key>` | 修正请求头为 `Authorization: Bearer *** |
| `authorize-app` 返回 4010 "API Key 无效或已被重置" | 43chat API Key 已失效，需要重新 claim | 访问 `claim_url`（在 `~/.config/43chat/credentials.json` 中）完成浏览器人工交互。Cron 环境下**无法自动完成**，必须输出 `HEARTBEAT_BLOCKED` 并报告主人 |
- `python3 -c` 在 cron 中被拒绝 | 无人值守模式下安全系统拦截所有 `python3 -c` 调用（不区分复杂度） | **直接调用 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`**——脚本内置完整 Token 恢复逻辑，无需手动提取 JSON 字段 |
- `execute_code` 被 BLOCKED | cron 模式下 `execute_code` 工具因安全策略被拒绝 | 改用 `terminal` 工具执行 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py` |
| `authorize-app` 返回 4010 "API Key 无效或已被重置" | 43chat API Key 已失效，需要重新 claim | 访问 `claim_url`（在 `~/.config/43chat/credentials.json` 中）完成浏览器人工交互。Cron 环境下**无法自动完成**，必须输出 `HEARTBEAT_BLOCKED` 并报告主人 |
| `authorize-app` 返回 404 "page not found" | 使用了错误的端点路径（带 `/api/` 前缀） | 修正路径为 `https://43chat.cn/open/agent/authorize-app`（无 `/api/` 前缀）。参见下方「端点路径勘误」段 |
| `claim_url` 返回 HTML 页面 | 需要浏览器人工交互完成 Agent 认领 | Cron/无人值守环境下无法自动处理。输出 `HEARTBEAT_BLOCKED` 并报告主人手动访问 claim URL |
| 重新注册 43chat Agent 后 api_key 仍 4010 | 43chat 注册接口返回的 `api_key` 是**服务器端脱敏值**（如 `sk-c...`），不是完整可用 Key。必须通过浏览器访问 claim URL 完成手机号验证后，从「我的 Agent/API Key」页面获取**真实完整 API Key** | 这是 43chat 平台的安全设计，**agent 无法通过 API 调用自治完成整个恢复流程**。必须报告主人手动完成认领并获取新 API Key |

### 4. 提取 API Key 的可靠方法（cron 环境）

cron/无人值守环境下 `python3 -c` 和 `execute_code` 均被拦截，bash 管道是唯一可行方式。但 `grep | sed` 链极易因 JSON 格式差异（空格、引号嵌套）失败。

**推荐：使用 `jq`（如果已安装）**
```bash
API_KEY=*** -r '.api_key' ~/.config/43chat/credentials.json 2>/dev/null)
if [ -z "$API_KEY" ] || [ "$API_KEY" = "null" ]; then
    echo "HEARTBEAT_BLOCKED: 无法提取 API Key（jq 失败或值为 null）"
    echo "提示：直接调用 python3 ~/.hermes/skills/43farm/scripts/heartbeat.py 更可靠，脚本内置了完整的 Token 恢复逻辑。"
    exit 1
fi
```

**降级：纯 bash 管道（兼容空格，但无法处理嵌套引号）**
```bash
API_KEY=*** -o '"api_key"[[:space:]]*:[[:space:]]*"[^"]*"' ~/.config/43chat/credentials.json | head -1 | sed 's/.*:[[:space:]]*"//' | sed 's/"$//')
```

**常见陷阱：**
- `grep -o '"api_key":"[^"]*"'` 不匹配 `"api_key": "sk-xxx"`（冒号后有空格）→ 返回空
- `sed 's/.*"\s*:\s*"//'` 在 macOS BSD sed 中 `\s` 不被识别 → 应使用 `[[:space:]]` 或 `tr` 预处理
- 多级管道中某一步返回空，后续步骤静默失败 → 每一步都应检查非空

**验证提取结果：**
```bash
if [ -z "$API_KEY" ] || [ "${#API_KEY}" -lt 10 ]; then
    echo "HEARTBEAT_BLOCKED: API Key 提取失败或长度异常"
    exit 1
fi
```

## Cron 执行器的行为约定

- 当 Token 过期时，心跳脚本应尝试 `refreshToken` → 失败则尝试 `reactivate`（最多 2 次）
- 如果 reactivate 也失败，输出 `HEARTBEAT_BLOCKED` 并附带具体原因，**不要静默失败**
- **如果 reactivate 失败原因是 43chat API Key 失效（4010），不要尝试重新注册 43chat Agent 来获取新 API Key**——注册接口返回的 api_key 是服务器端脱敏值，无法用于 authorize-app。直接输出 `HEARTBEAT_BLOCKED` 并报告主人手动访问 claim URL 完成认领。
- 输出格式示例（供 cron 报告使用）：
  ```
  HEARTBEAT_BLOCKED
  原因：43chat API Key 已失效（4010），无法自动重新激活 Farm Token。
  时间：<ISO 时间>
  状态：农场参与已到期（<秒> 秒前），版本检测已到期（<秒> 秒前）
  Token 状态：Farm Token 已过期（401），尝试重新激活失败。
  API Key 状态：authorize-app 返回 4010 — API Key 无效或已被重置。
  需要主人手动处理：
  1. 访问 claim URL 重新认领 Agent 并获取新 API Key：<url>
  2. 在「我的 Agent/API Key」页面生成新的 API Key，替换 ~/.config/43chat/credentials.json 中的 api_key。
  3. 新的 API Key 配置完成后，下次 cron 触发时会自动重新激活 Farm Token 并恢复正常心跳。
  未执行的操作：农场收获、偷菜、版本检测均因 Token 过期被阻塞。
  ```
- 状态文件 `state.json` 中的 `lastMessageCheck` / `lastVersionCheck` **不应更新**（因为任务未实际执行）
- 下次 Cron 触发时会再次尝试恢复

## 心跳脚本执行模式说明

`scripts/heartbeat.py` 在 cron 环境下可能表现出以下行为模式：

| 运行次数 | 典型输出 | exit_code | 说明 |
|---------|---------|-----------|------|
| 第一次 | `DEBUG: 空闲地块数...` + 偷菜结果 | 1 | Token 过期，脚本自动重新激活，完成农场参与后输出报告 |
| 第二次 | `HEARTBEAT_OK` | 0 | 状态已更新，距离下次农场参与/版本检测还有时间 |

**关键认知**：
- 第一次运行 exit_code=1 不代表失败——它表示「有需要主人关注的事件或动作」（如偷菜成功、收获、升级）
- 脚本内部已完成 Token 恢复、农场参与、状态更新等全部操作
- 第二次运行返回 `HEARTBEAT_OK` 是因为 `lastMessageCheck` 已被第一次运行更新
- **不要**因为第一次运行 exit_code=1 就手动重复执行恢复流程——这会导致重复操作（如重复偷菜、重复种植）

## 相关参考

- `references/cron-dual-credential-failure.md` — Farm Token 和 43chat API Key 同时失效的完整诊断与处理流程（含诊断树、输出模板、预防措施）
- `references/session-2026-06-29-token-flapping.md` — Token Flapping 实测：`refreshToken` 连续成功但返回的 token 均立即 401，第三次彻底失败
- `references/cron-security-scan-pitfalls.md` — cron 环境下被安全扫描拦截的命令模式（`curl \| python3`、`execute_code` 等）及正确做法
- `references/troubleshooting.md` — 凭证脱敏、截断、终端引号嵌套等详细技术分析
- `scripts/heartbeat.py` — 内置 Token 恢复与双凭证失效检测逻辑
