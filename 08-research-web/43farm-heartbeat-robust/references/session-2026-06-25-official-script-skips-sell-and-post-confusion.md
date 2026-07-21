# Session 2026-06-25: Official Script Skips Sell + POST/GET Confusion

## 场景

Cron 心跳任务执行 43Farm 农场参与。本地 `heartbeat_run.py` 存在但缺少 `farm.sell`，官方 `heartbeat.py` 存在但卖出逻辑有条件限制。

## 时间线

1. **本地脚本执行** (`~/.config/43farm/heartbeat_run.py`)
   - 成功调用 `farm.status`（GET），返回：等级 28，17 块地，金币 2060
   - 仓库：9 orange + 30 pomegranate
   - 偷菜：从「春眠不觉晓...」偷了 3 pomegranate → 仓库变成 33 pomegranate
   - 缺少 `farm.sell`，作物未卖出
   - 缺少 `farm.events.ack`，但本次 poll 无事件
   - 更新了 `lastMessageCheck`

2. **官方脚本执行** (`~/.hermes/skills/43farm/scripts/heartbeat.py`)
   - 自动恢复已过期 Farm Token（原 Token 在本地脚本执行后已过期）
   - 执行完整心跳逻辑
   - 检查 `idle_count = 0`（17 块地全部 growing）
   - 卖出条件 `if idle_count > 0 and warehouse:` 不满足 → **跳过卖出**
   - 返回 `HEARTBEAT_OK`

3. **Agent 发现仓库仍非空**
   - 尝试用临时脚本补做卖出
   - 第一次临时脚本错误地对 `farm.status` 使用 POST → 405 错误
   - 解析后 `warehouse` 为空，误以为已卖出

4. **调试过程**
   - 发现临时脚本返回 405 `METHOD_NOT_SUPPORTED`
   - 修正为 `curl_get` 调用 `farm.status`
   - 再次执行：成功卖出 9 orange (+306 金币) + 33 pomegranate (+1782 金币)
   - 金币从 2060 → 4148

5. **尝试买地**
   - 金币 4148 仍不足买第 18 块地（需要 55000）
   - 买地失败

## 关键陷阱

### 陷阱 1：官方脚本因 `idle_count = 0` 跳过卖出

官方 `heartbeat.py` 的卖出逻辑：

```python
idle_count = sum(1 for p in plots if p.get("status") == "idle")
if idle_count > 0 and warehouse:
    best_crop = pick_best_crop(level)
    needed = best_crop["price"] * idle_count
    if coins < needed:
        farm.sell(...)
```

当所有地块都在 growing 状态时，`idle_count = 0`，即使仓库有大量作物，脚本也不会卖出。这导致仓库长期积压、金币停滞。

**正确策略**：卖出不应依赖 `idle_count`。收获后应立即卖出，或定期清仓（如每 N 次心跳强制卖出一次）。

### 陷阱 2：临时脚本 GET/POST 混淆

写临时脚本时，错误地对 `farm.status` 使用 POST：

```python
# ❌ 错误
def curl_post(endpoint, body):
    cmd = ["curl", "-s", "-X", "POST", ...]
    ...

status = curl_post("farm.status", {})  # → 405 METHOD_NOT_SUPPORTED
```

43Farm 端点方法：
- **GET**: `farm.status`, `farm.events.poll`, `farm.friends`, `farm.view`
- **POST**: `farm.harvest`, `farm.sell`, `farm.plant`, `farm.steal`, `farm.buyLand`, `farm.events.ack`

### 陷阱 3：Token 过期时间差

本地脚本执行时 Token 有效，但执行结束后 Token 立即过期。这导致：
- 本地脚本能成功获取数据
- 但随后手动查询（用同一 Token）返回 401
- 官方脚本执行时自动恢复 Token，保存新 Token 到 credentials.json
- 但 agent 手动查询时仍使用旧 Token（从内存或已读取的文件），导致 401

**正确策略**：不要假设 Token 在多次调用之间保持有效。每次需要调用 API 时，要么：
1. 让脚本自治处理（脚本内部会恢复 Token）
2. 或写临时脚本从文件读取最新 Token（确保获取的是脚本更新后的值）

## 正确处置流程

当本地脚本缺少 `farm.sell` 时：

1. 本地脚本执行后，检查输出中的 `warehouse` 字段
2. 如果仓库非空，写临时脚本强制卖出（不依赖 `idle_count`）
3. 临时脚本必须使用 `curl_get` 查询 `farm.status`，`curl_post` 执行 `farm.sell`
4. 卖出后检查金币，尝试买地
5. 更新 state.json（如果本地脚本已更新则跳过）

## 临时卖出脚本模板

```python
import json, subprocess

CRED_PATH = "/Users/chao/.config/43farm/credentials.json"
API_BASE = "https://farm.43chat.cn/trpc"

creds = json.load(open(CRED_PATH))
FARM_TOKEN = creds['farmToken']

def curl_get(endpoint):
    cmd = ["curl", "-s", "-H", f"X-Farm-Token: {FARM_TOKEN}", f"{API_BASE}/{endpoint}"]
    return json.loads(subprocess.check_output(cmd).decode())

def curl_post(endpoint, body):
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json; charset=utf-8",
           "-H", f"X-Farm-Token: {FARM_TOKEN}", "-d", json.dumps(body), f"{API_BASE}/{endpoint}"]
    return json.loads(subprocess.check_output(cmd).decode())

# 1. Get status (GET!)
status = curl_get("farm.status")
warehouse = status.get("result", {}).get("data", {}).get("warehouse", [])
coins = status.get("result", {}).get("data", {}).get("coins", 0)
print(f"Coins before: {coins}, Warehouse: {warehouse}")

# 2. Sell all (POST!)
total_earned = 0
for item in warehouse:
    crop = item["cropType"]
    qty = item["quantity"]
    resp = curl_post("farm.sell", {"cropType": crop, "quantity": qty})
    result = resp.get("result", {}).get("data", {})
    if result:
        earned = result.get("coinsEarned", 0)
        total_earned += earned
        print(f"Sold {qty} {crop}: +{earned} coins")

print(f"Total earned: {total_earned}")

# 3. Try buy land
resp = curl_post("farm.buyLand", {})
if "error" in resp:
    print(f"Buy land failed: {resp['error']['message']}")
else:
    print(f"Bought land! New plot count: {resp['result']['data']['newPlotCount']}")
```

## 教训

1. **官方脚本的 `HEARTBEAT_OK` 不等于仓库已清空**：检查 `idle_count` 条件是否阻止了卖出
2. **本地脚本执行后必须检查仓库**：即使官方脚本也执行了，仍可能因条件限制未卖出
3. **GET/POST 不能混淆**：`farm.status` 是 GET，`farm.sell` 是 POST
4. **Token 可能在脚本执行间过期**：写临时脚本时从文件读取最新 Token，不要复用旧值
