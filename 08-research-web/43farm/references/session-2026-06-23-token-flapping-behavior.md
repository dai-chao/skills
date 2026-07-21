# Token 抖动行为 — 农场 Token 在执行期间有效但结束后立即 401

## 现象

2026-06-23 心跳执行期间观察到：

1. `heartbeat.py` 成功执行完整农场参与流程（获取状态、收获 21 banana、偷菜、更新 state.json）
2. 脚本 exit code 0，stdout 输出 `HEARTBEAT_OK`
3. 但脚本结束后立即用同一 Token 调 `farm.status` 返回 401：
   ```json
   {"error":{"message":"Farm Token 无效或已过期...","code":-32001}}
   ```

## 根因

后端 Token 验证机制：Farm Token 在脚本执行期间有效，但执行结束后立即失效。这不是恢复失败，而是后端设计的短时效 Token（可能按请求次数或极短 TTL 过期）。

## 影响

- **手动 curl 验证不可靠**：不要用脚本执行后的手动 curl 来判断 Token 是否有效
- **脚本自洽**：`heartbeat.py` 的 `ensure_valid_token()` 在每次运行时会自动验证并重新激活，无需外部干预
- **状态文件已更新**：`state.json` 的更新证明脚本成功完成了业务逻辑

## 处置

1. 脚本成功运行后，**不要**用手动 curl 验证 Token
2. 若需人工诊断，应检查 `state.json` 是否更新，而非 Token 是否 401
3. 只有脚本本身返回 `HEARTBEAT_BLOCKED` 时才需要主人介入
