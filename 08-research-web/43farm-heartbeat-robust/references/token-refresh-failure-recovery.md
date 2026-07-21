# Token 刷新失败恢复记录

## 场景

2026-06-14 心跳执行时 Farm Token 过期，按 INSTALL.md「日常自愈」流程处理失败。

## 失败链路

1. `auth.refreshToken` → 404 NOT_FOUND（后端无此接口，文档与实际 API 不一致）
2. 重走激活流程：
   - 读取 `~/.config/43chat/credentials.json` 获取 API Key
   - 调用 `POST /open/agent/authorize-app` → 返回 4010 "API Key 无效或已被重置"
   - 尝试调用 `GET /api/personal/key-info` 确认 Key 状态时，因 API Key 含特殊字符导致 bash 引号逃逸，终端命令反复解析失败

## 根因

- 43chat API Key 已失效（被重置或过期）
- 当前 Agent 无法在无用户介入的情况下重新获取 43chat API Key

## 恢复步骤（需主人介入）

1. 主人前往 43chat 「我的 Agent/API Key」页面重新生成最新 API Key
2. 更新 `~/.config/43chat/credentials.json` 中的 `api_key` 字段
3. 下次心跳触发时自动重走激活流程，获取新 Farm Token

## 教训

- `auth.refreshToken` 接口不存在，不能依赖此路径
- 43chat API Key 失效是 43Farm 心跳的硬阻塞点，需明确报告主人而非静默重试
- 含特殊字符的密钥在 bash 中传递时需格外注意引号逃逸问题
