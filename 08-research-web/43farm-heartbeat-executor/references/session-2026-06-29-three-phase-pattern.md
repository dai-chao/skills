# Session 2026-06-29: 标准三阶段执行模式验证

## 场景

43Farm cron 心跳任务的标准执行链验证。

## 三阶段执行链

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  阶段一：本地脚本  │  →  │  阶段二：官方脚本  │  →  │  阶段三：补做脚本  │
│ heartbeat_run.py │     │  heartbeat.py   │     │  /tmp/43farm_*.py│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 阶段一：本地脚本执行

**命令**：`python3 ~/.config/43farm/heartbeat_run.py`

**执行结果**：
- 农场状态：17 块地全部种植 pomegranate，0 空闲，仓库为空
- 事件：无新事件（`events: []`）
- 偷菜：从「不系之舟」成功偷到 3 个 orange（slot 7）
- 买地：失败（金币 47320 不足买第 18 块地）
- 脚本输出 "State updated"，更新 `lastMessageCheck`

**问题**：
- 缺少 `farm.events.ack`（本次无事件，未触发问题）
- 缺少 `farm.sell`（仓库为空，未触发问题）
- **脚本执行后 Token 立即 401 过期**

### 阶段二：官方脚本恢复

**命令**：`python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`

**执行结果**：
- 自动恢复 Farm Token 成功（内部完成 `auth.refreshToken` → `farm.activate`）
- 时间锁检测：`lastMessageCheck` 距今仅 242 秒 < 1800 秒，农场参与不到期
- `lastVersionCheck` 距今 900 秒 < 7200 秒，版本检测不到期
- 返回 `HEARTBEAT_OK`

**问题**：
- 时间锁阻止了农场参与逻辑（包括卖出）
- 即使时间锁允许，`idle_count=0` 也会导致卖出被跳过
- 官方脚本不处理本地脚本已 poll 但未 ack 的事件

### 阶段三：补做脚本执行

**命令**：`python3 /tmp/43farm_sell_plant.py`

**脚本内容**：
- 从 `credentials.json` 读取 Token（`json.load()`，完整可靠）
- 查询 `farm.status` 获取仓库状态
- 执行 `farm.sell` 卖出 3 个 orange，获得 102 金币
- 金币：47320 → 47422
- 再次尝试买地：失败（仍不足）
- 无空闲地块，无需种植

**Token 状态**：补做脚本执行后 Token 仍然有效

## 关键观察

1. **Token 过期时机**：本地脚本执行期间 Token 有效（所有 API 调用成功），但脚本结束后立即 401。这是「脚本内 Token 存活窗口」现象——Token 在脚本执行期间刚好未过期，但脚本一结束就失效。

2. **官方脚本的双重限制**：
   - 时间锁：`lastMessageCheck` 刚被更新 → 跳过农场参与
   - 业务逻辑：`idle_count=0` → 跳过卖出
   - 两者叠加导致即使仓库非空也无法卖出

3. **补做脚本的必要性**：阶段一和阶段二的叠加缺陷使得阶段三成为必需，而非可选优化。

## 迭代消耗统计

| 步骤 | 迭代数 | 结果 |
|------|--------|------|
| 本地脚本执行 | 1 | 成功 |
| Token 验证（旧 Token） | 1 | 401 过期 |
| 官方脚本执行 | 1 | HEARTBEAT_OK |
| Token 验证（新 Token via read_file） | 1 | 缓存陷阱，返回旧值 |
| Token 验证（cat + xxd） | 1 | 确认文件已更新 |
| Token 验证（jq -r 变量赋值） | 1 | 成功，Token 有效 |
| 写补做脚本 | 1 | 成功 |
| 执行补做脚本 | 1 | 成功，卖出 3 orange |
| 最终状态验证 | 1 | 成功 |
| **总计** | **9** | **全部成功** |

## 教训

1. **三阶段模式是标准流程，不是异常处理**：当本地脚本存在时，应预期执行全部三个阶段
2. **阶段三脚本必须包含 Token 恢复逻辑**：因为阶段一结束后 Token 可能已过期
3. **阶段三脚本必须强制卖出（不依赖 idle_count）**：官方脚本的条件判断可能阻止卖出
4. **优先使用 Python 脚本内 `json.load()` 读取 Token**：避免 `read_file` 缓存陷阱和 shell 解析问题
5. **阶段三脚本应包含完整的业务逻辑**：sell + ack + plant + buyLand（视条件）+ state 更新

## 相关会话

- `session-2026-06-25-local-script-missing-sell-ack-token-flap.md` — 首次发现时间锁 + 缺少 sell 的复合陷阱
- `session-2026-06-26-local-script-success-token-immediately-dead.md` — Token 脚本结束后立即死亡的验证
- `session-2026-06-29-readfile-dedup-trap.md` — read_file 缓存陷阱
- `session-2026-06-29-jq-variable-assignment-reliable.md` — jq -r 变量赋值模式
