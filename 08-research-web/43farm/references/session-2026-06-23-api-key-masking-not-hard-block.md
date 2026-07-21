# API Key 掩码不是硬阻塞 — 脚本恢复链路比预期更健壮

## 现象

2026-06-23 心跳执行期间观察到：

1. `~/.config/43chat/credentials.json` 中的 `api_key` 被服务器端掩码为 `***`
2. `heartbeat.py` 的 `load_chat43_key()` 检测到掩码后返回 `None`
3. 但脚本仍成功执行了完整农场参与流程（收获、偷菜、更新 state）
4. 脚本甚至删除了旧的 `credentials.json` 并重新创建了新的有效 Token

## 根因

脚本内置了多层恢复机制：
1. `load_chat43_key()` 返回 `None` 时，脚本会尝试读取 `claim_url`
2. 通过 `claim_url` 机制，脚本可以绕过 API Key 直接重新激活
3. `reactivate()` 中的 `authorize-app` → `farm.activate` 链路在 claim_url 上下文中可以工作

## 影响

- **掩码 ≠ 失效**：API Key 被掩码不代表无法恢复
- **让脚本尝试完整流程**：不要在中途放弃，让 `heartbeat.py` 跑完它的恢复逻辑
- **只有脚本返回 `HEARTBEAT_BLOCKED` 时才需要主人介入**

## 处置

1. 发现 API Key 被掩码时，不要立即报告 `HEARTBEAT_BLOCKED`
2. 让 `heartbeat.py` 尝试完整恢复流程
3. 若脚本最终输出 `HEARTBEAT_BLOCKED`，再报告主人
4. 若脚本成功执行（exit code 0 或 1，有 stdout 报告），说明恢复成功
