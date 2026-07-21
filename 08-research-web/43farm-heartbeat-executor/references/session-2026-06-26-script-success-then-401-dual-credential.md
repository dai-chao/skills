# Session: 本地脚本成功 + 补做 ack 后 Token 立即死亡，双凭证失效（2026-06-26）

## 场景

43Farm cron 心跳执行，本地脚本成功但缺少 `farm.events.ack`，临时补做脚本成功 ack 事件，但随后 Token 立即 401，43chat API Key 也失效（4010）。

## 完整时间线

1. **`T+0`**: 运行本地 `~/.config/43farm/heartbeat_run.py`
   - `farm.status` → 成功：等级 28，金币 20139，17 块地全部 growing，仓库空
   - `farm.events.poll` → 成功：4 条事件（3 条 CROP_STOLEN + 1 条 CROP_MATURE）
   - `farm.friends` → 成功：22 位好友，9 位已激活农场
   - 遍历 9 位激活好友的 `farm.view` → 全部无可偷地块
   - `farm.buyLand` → 失败：金币不足（400 BAD_REQUEST）
   - **输出 "State updated"**，更新 `lastMessageCheck` 和 `lastVersionCheck` 为 1782461114
   - exit_code=0

2. **`T+30s`**: 检查本地脚本输出，发现**缺少 `farm.events.ack`**
   - 4 条事件已 poll 但未确认，下次 cron 会重复 poll

3. **`T+35s`**: 运行 `farm_now.py` → "金币: 20139, 等级: 28, 地块: 17 / 仓库: [] / 空闲地块: 0 / 共种植 0 块地"
   - `farm_now.py` 无事可做（无 idle 地块、无仓库作物）
   - `farm_now.py` 不处理事件 ack

4. **`T+40s`**: 写临时脚本 `/tmp/43farm_ack_state.py`
   - 包含：`ensure_valid_token()` → `farm.events.ack` → `farm.sell` → `farm.plant` → `farm.buyLand` → 更新 `state.json`
   - 执行临时脚本：成功 ack 4 条事件，买地失败（金币不足），更新 state.json

5. **`T+60s`**: 用 `curl` 验证 `farm.status` → **401 Unauthorized**
   - Token 在临时脚本执行完毕后立即死亡

6. **`T+65s`**: 尝试 `auth.refreshToken` → 失败："旧 token 不合法或 43chat session 已失效"

7. **`T+70s`**: 尝试 `authorize-app` 恢复
   - 读取 `~/.config/43chat/credentials.json`：`api_key` 为 `sk-cc0...dbe9`（含字面省略号）
   - `curl -H "Authorization: Bearer sk-cc0...dbe9"` → **4010**："API Key 无效或已被重置"

8. **`T+75s`**: 检查 `~/.hermes/.env`：`CHAT43_API_KEY` 也是字面 `***`（`xxd` 确认字节 `2a 2a 2a`）

9. **`T+80s`**: 两个来源同时失效 → **终极硬阻塞**
   - 输出 `HEARTBEAT_BLOCKED`
   - 报告主人：需要重新获取 43chat API Key

## 关键发现

### 1. 本地脚本缺少 `farm.events.ack` 是持续性问题

`heartbeat_run.py` 在每次 cron 执行时都会 poll 到事件，但从不 ack。这导致：
- 事件积压（虽然不影响功能，但增加后端负担）
- 每次 cron 都会重复报告相同事件
- 需要临时补做脚本或手动 ack

### 2. 临时补做脚本成功但 Token 立即死亡

临时脚本 `/tmp/43farm_ack_state.py` 的 `ensure_valid_token()` 在开始时验证了 Token 有效（`farm.status` 成功），执行了 ack 和其他操作。但脚本结束后立即 401。

这与本地脚本的情况相同：Token 在脚本执行期间有效，结束后立即失效。

### 3. 状态文件已被更新，时间锁阻止官方脚本恢复

`state.json` 显示：
```json
{"lastMessageCheck": 1782461114, "lastVersionCheck": 1782461114}
```

当前时间约 1782461171，差值仅 57 秒。

如果此时运行官方 `heartbeat.py`：
- 检查 `lastMessageCheck`：57 秒 < 1800 秒 → 农场参与不到期
- 直接返回 `HEARTBEAT_OK`
- 完全跳过 Token 恢复逻辑

### 4. 手动恢复时 API Key 也失效

`~/.config/43chat/credentials.json` 中的 `api_key` 被截断为 `sk-cc0...dbe9`（含字面省略号 `...`），这是**文件层截断**，不是展示层脱敏。

`~/.hermes/.env` 中的 `CHAT43_API_KEY` 也是字面 `***`（`xxd` 确认十六进制 `2a 2a 2a`）。

两个来源同时失效，无法自治恢复。

## 事件详情

本次 poll 到的 4 条事件：

| 事件 ID | 类型 | 详情 | 时间 |
|---------|------|------|------|
| `8caf0c42-...` | CROP_STOLEN | 地块 14 pomegranate 被 **X** 偷了 3 个 | 1782460631 |
| `d19a00fd-...` | CROP_STOLEN | 地块 14 pomegranate 被 **不系之舟** 偷了 3 个 | 1782460804 |
| `97544c5e-...` | CROP_STOLEN | 地块 14 pomegranate 被 **加勒比德柱** 偷了 3 个 | 1782460805 |
| `f949f74b-...` | CROP_MATURE | 地块 14 pomegranate 已成熟 | 1782460958 |

> 地块 14 的 pomegranate 先成熟，然后被连续偷了 3 次（共 9 个）。由于多季作物机制，地块 14 进入第 2 季生长中（`season: 2`, `status: growing`）。

## 教训

### 1. 本地脚本执行后必须验证 Token

即使脚本 exit_code=0 且所有 API 调用成功，也应在脚本执行完毕后立即验证 Token：

```bash
curl -s -H "X-Farm-Token: $(jq -r '.farmToken' ~/.config/43farm/credentials.json)" \
  "https://farm.43chat.cn/trpc/farm.status"
```

- 如果返回 401 → Token 已死亡，不要运行官方脚本（时间锁会阻止恢复）
- 应立即加载 `43farm-cron-recovery` skill 进行手动恢复

### 2. 临时补做脚本也应包含 Token 验证

临时脚本（如 `/tmp/43farm_ack_state.py`）的 `ensure_valid_token()` 在开始时验证 Token，但脚本执行期间 Token 可能死亡。应在脚本末尾也验证一次：

```python
# 脚本末尾追加
ok, _ = http_request("farm.status", token=token)
if not ok:
    print("WARNING: Token died after script execution")
```

### 3. 当 Token 验证 401 时，正确恢复路径

**错误做法**：
```bash
# 不要这样做！时间锁会阻止恢复
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py  # → HEARTBEAT_OK（假阳性）
```

**正确做法**：
1. 立即加载 `43farm-cron-recovery` skill
2. 尝试 `auth.refreshToken` → `authorize-app` → `farm.activate` 手动恢复
3. 如果 API Key 也失效（4010），检查 Key 完整性（是否含 `...`）
4. 如果 Key 被截断 → 报告 `HEARTBEAT_BLOCKED`，停止恢复

### 4. 状态文件已被更新时的紧急恢复

如果 `lastMessageCheck` 已被更新且 Token 已 401：
- 官方脚本因时间锁无法恢复
- 手动恢复是唯一的出路
- 如果手动恢复也失败（API Key 失效），必须报告主人
- 在报告中明确告知：下次 cron 约 30 分钟后才会再次尝试，但问题不会自行恢复

### 5. 事件聚合报告

当 `farm.events.poll` 返回大量事件（如 40+ 条 `CROP_STOLEN`）时，不要逐条枚举，应做聚合统计：

```
共 36 条被偷事件，来自 5 位好友：
- X: 12 次（地块 3, 5, 7）
- 不系之舟: 8 次（地块 2, 4）
- 加勒比德柱: 10 次（地块 1, 6, 8）
- ...
```

只列出关键事件（如 `LEVEL_UP`、新留言等）即可。

## 状态文件策略（本次执行）

| 检查项 | 执行结果 | 时间戳更新 | 下次 cron 行为 |
|--------|----------|------------|----------------|
| 农场参与 | 本地脚本成功，但缺少 ack；临时脚本补 ack 成功；Token 随后死亡 | `lastMessageCheck=1782461114` | 约 30 分钟后重试，但 Token 仍 401 |
| 版本检测 | 本地脚本执行了版本检查（gameplayVersion 1.1.1） | `lastVersionCheck=1782461114` | 约 120 分钟后重试 |

**问题**：`lastMessageCheck` 已被更新，但 Token 已 401。下次 cron 触发时：
- 时间锁：当前时间 - 1782461114 ≈ 1800 秒 → 可能刚好到期或不到期
- 如果不到期 → 官方脚本直接 `HEARTBEAT_OK`，跳过恢复
- 如果到期 → 官方脚本尝试恢复，但 API Key 仍失效 → 恢复失败

**主人修复后**：
- 主人获取新 API Key，更新 `credentials.json`
- 下次 cron 触发时，官方脚本时间锁到期 → 尝试农场参与 → 发现 Token 401 → 触发恢复 → `authorize-app` 成功 → `farm.activate` 成功 → 心跳恢复

## 相关参考

- `session-2026-06-26-local-script-success-token-immediately-dead.md` — 同一问题的首次验证
- `session-2026-06-26-time-lock-compound-trap-full.md` — 时间锁复合陷阱的完整分析
- `session-2026-06-25-local-script-updates-timestamp-token-dead.md` — 本地脚本无条件更新时间戳的隐患
- `session-2026-06-26-unconditional-state-update-bug.md` — 本地脚本无条件更新 `state.json` 的时间戳陷阱
