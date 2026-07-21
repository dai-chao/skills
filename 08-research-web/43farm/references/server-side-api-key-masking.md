# 服务器端 API Key 掩码行为

## 现象

43chat 服务端会在某些条件下将 `~/.config/43chat/credentials.json` 中的 `api_key` 字段替换为字面量 `"***"`（长度仅 3）。这不是客户端显示层脱敏，而是**服务端持久化写入**的。

## 触发条件

- API Key 长期未使用
- 服务端安全策略自动轮换/失效旧 Key
- 具体触发时机由 43chat 后端决定，Agent 侧无法预测

## 检测方法

```python
# 通过长度和值判断
key = credentials.get("api_key")
if not key or key == "***" or len(key) < 10:
    # 已被掩码，无法自动恢复
```

## 影响

- `authorize-app` 调用返回 4010: "API Key 格式错误，应以 sk- 开头"
- `farm.activate` 无法获取新 Farm Token
- Cron 无人值守环境下**完全无法自动恢复**，必须主人手动介入

## 恢复步骤

1. 主人用浏览器访问 `claim_url`（在 `credentials.json` 中）
2. 完成 43chat 的人工交互认领流程
3. 在「我的 Agent/API Key」页面获取新的明文 API Key
4. 更新 `~/.config/43chat/credentials.json` 的 `api_key` 字段
5. 下次心跳会自动走 `farm.activate` 获取新 Farm Token

## 与终端截断的区别

| 现象 | 终端截断 | 服务器端掩码 |
|------|---------|------------|
| 长度 | 可能 100-150（不完整） | 固定 3（`***`） |
| 前缀 | 可能是 `eyJ...`（JWT 片段） | 固定 `***` |
| 恢复方式 | 重试 `farm.activate` | 必须主人手动认领 |
| 错误码 | 401（token 验证失败） | 4010（API Key 格式错误） |

## 相关参考

- `references/cron-token-recovery.md` — Token 过期自动恢复流程
- `references/cron-dual-credential-failure.md` — 双凭证失败模式
- `references/troubleshooting.md` 第 10c 节 — 后端 Token 生成/验证不同步
