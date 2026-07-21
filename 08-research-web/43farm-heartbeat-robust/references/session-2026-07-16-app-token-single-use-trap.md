# Session 2026-07-16: App Token 单次使用陷阱导致连续激活失败

## 场景

cron 心跳任务中，Farm Token 过期，尝试按 INSTALL.md「日常自愈」流程恢复：
1. `authorize-app` 获取 App Token
2. `farm.activate` 用 App Token 换 Farm Token
3. 验证新 Token

## 实际发生

### 第一次尝试
- `authorize-app` → 成功，App Token `at-2e0200df...`
- `farm.activate` → 成功，Farm Token `eyJhbG...dkSA`
- 保存到 `credentials.json`
- `farm.status` → **401 UNAUTHORIZED**

### 第二次尝试（同一 App Token）
- `farm.activate` → **400 `app_token 已失效或被 43chat 拒绝`**

### 第三次尝试（新 App Token）
- `authorize-app` → 成功，App Token `at-64752961...`
- `farm.activate` → 成功，Farm Token `eyJhbG...zURE`
- 保存到 `credentials.json`
- `farm.status` → **401 UNAUTHORIZED**

### 第四次尝试（新 App Token）
- `authorize-app` → 成功，App Token `at-313155df...`
- `farm.activate` → 成功，Farm Token `eyJhbG...c8TA`
- 保存到 `credentials.json`
- `farm.status` → **401 UNAUTHORIZED**

## 关键发现

1. **App Token 是一次性的**：`farm.activate` 消费后，同一 App Token 再次调用返回 `app_token 已失效`
2. **新 Farm Token 立即 401**：连续 3 次完整流程（新 App Token → 新 Farm Token → 验证）均失败
3. **不是截断问题**：`credentials.json` 中的 Token 长度正常（200+ 字符），不含 `...`
4. **不是后端延迟**：未等待直接验证，但即使等待也可能失败（未测试）

## 与已知陷阱的区别

| 陷阱 | 特征 | 本场景 |
|------|------|--------|
| Token 截断 | Token 含 `...`，长度 < 50 | ❌ Token 完整 |
| 后端激活延迟 | 等待 3-5 秒后成功 | ❓ 未测试等待 |
| claim_url 未完成 | `credentials.json` 有 `claim_url` | ❌ 无 `claim_url` |
| **App Token 单次使用** | 新 Token 立即 401，重复 activate 失败 | ✅ 匹配 |

## 根因推测

- 43chat 的 App Token 设计为一次性使用，`farm.activate` 消费后即失效
- `farm.activate` 返回的 Farm Token 可能因 session 绑定、IP 限制或时间窗口未被后端正确注册
- 连续快速调用可能导致后端状态不一致

## 处置建议

1. `farm.activate` 成功后，**不要立即验证**——等待 5-10 秒
2. 如果首次验证 401，**不要重复 `farm.activate`**（App Token 已失效）
3. 重新走完整流程：`authorize-app` → 新 App Token → `farm.activate` → 等待 5-10 秒 → 验证
4. 连续 3 次完整流程均失败 → 输出 `HEARTBEAT_BLOCKED`，报告主人

## 教训

- App Token 是一次性的，不可复用
- 新 Farm Token 可能需要时间生效，不要立即验证
- 连续 3 次完整激活流程失败 = 系统性问题，停止重试
- 不要尝试用同一 App Token 多次 activate
