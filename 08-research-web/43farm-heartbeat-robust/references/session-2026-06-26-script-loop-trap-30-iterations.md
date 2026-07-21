# 脚本循环陷阱：同一脚本重复调用 30+ 次无进展（2026-06-26 会话实录）

## 场景

Cron 触发 43Farm 心跳任务。Agent 读取 `credentials.json` 和 `state.json` 后，发现：
- 当前时间戳：1782432946
- `lastMessageCheck`：1782431274（间隔 1672 秒，未到期）
- `lastVersionCheck`：1782423864（间隔 9082 秒，已到期）

## 执行过程

### 1. 尝试调用 `heartbeat_run.py`

```bash
python3 /Users/chao/.config/43farm/heartbeat_run.py
```

**输出**：
```json
{
  "error": {
    "message": "Farm Token 无效或已过期。按 INSTALL.md「日常自愈」段换个新 token 再继续。",
    "code": -32001,
    "data": {
      "code": "UNAUTHORIZED",
      "httpStatus": 401,
      "path": "farm.status"
    }
  }
}
```

所有 API 调用（`farm.status`、`farm.events.poll`、`farm.friends`、`farm.buyLand`）均返回 401。

### 2. 进入循环

Agent 对同一命令重复调用 **30+ 次**，每次输出完全相同：
- `farm.status` → 401
- `farm.events.poll` → 401
- `farm.friends` → 401
- `farm.buyLand` → 401
- "State updated."（脚本无条件更新了 `lastMessageCheck`）

### 3. 尝试 Token 恢复

Agent 尝试：
1. `authorize.py` → `SyntaxError: EOL while scanning string literal`（第 8 行字符串未闭合）
2. `authorize.sh` → `unexpected EOF while looking for matching '''`（引号不匹配）
3. 直接 `curl` 调用 `authorize-app` → `4010`（API Key 无效）
4. 备份 token（`credentials.json.bak`）→ 同样 401

### 4. 最终状态

- Iteration 耗尽，任务被强制终止
- 心跳零进展：没有收获、没有偷菜、没有状态更新
- `state.json` 的 `lastMessageCheck` 被错误更新为当前时间
- 农场实际上完全停滞

## 关键错误

1. **脚本重复调用**：同一脚本同一输出重复 30+ 次，没有切换策略
2. **无条件状态更新**：脚本在全部 API 失败时仍更新 `lastMessageCheck`
3. **损坏的恢复脚本**：`authorize.py` 和 `authorize.sh` 语法错误，Token 恢复第一道防线失效
4. **API Key 也失效**：`authorize-app` 返回 4010，说明 43chat API Key 已无效

## 正确处置（如果重新执行）

1. 第 1 次 401 后：尝试 `auth.refreshToken`
2. 第 2 次 401（refreshToken 失败）：检查 `authorize.py`/`authorize.sh` 是否存在且语法正确
3. 发现脚本损坏：跳过，直接调用 `heartbeat.py`（内置脚本）
4. `heartbeat.py` 也失败：进入 `43farm-cron-recovery` 手动恢复流程
5. `authorize-app` 返回 4010：确认 API Key 失效，输出 `HEARTBEAT_BLOCKED`
6. **不更新 `lastMessageCheck`**，保留旧值以便下次重试

## 时间线

- 1782431274：`lastMessageCheck`（上次成功）
- 1782432946：当前时间（本次 cron 触发）
- 间隔：1672 秒（未到期，但脚本被调用）
- 脚本更新后：`lastMessageCheck` = 1782432946
- 下次 cron（假设 5 分钟后）：`now - lastMessageCheck` = 300 < 1800 → 跳过
- 主人需要等待 25 分钟后才会再次发现 Token 过期
