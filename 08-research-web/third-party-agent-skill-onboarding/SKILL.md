---
name: third-party-agent-skill-onboarding
version: 1.0.0
description: Install, register, claim, and verify third-party agent skill marketplaces (e.g. 才虫, 43Chat) that require API key credentials and periodic heartbeat polling.
category: autonomous-ai-agents
---

# 第三方 Agent 技能市场接入

适用于需要「安装 skill 文件 → 注册 Agent → 人类认领 → 保存 API Key → 配置心跳」的第三方平台。

## 触发条件

- 用户说「安装/加入/接入 XXX agent skill」
- 用户发来一个 `skill.md` 或平台安装链接
- 第三方 skill 要求注册、认领、保存 API Key、配置心跳

## 标准工作流程

1. **读取安装文档**
   - 用 `curl` 或 `web_extract` 拉取 `skill.md` 和 `skill.json`
   - 确认文件列表、版本、凭证路径、心跳配置位置

2. **安装文件**
   - 创建 `~/.hermes/skills/<skill-name>/`
   - 下载所有必需文件，保持官方命名（大小写敏感）
   - 常见文件：`SKILL.md`, `skill.json`, `PUBLISHER.md`, `WORKER.md`, `HEARTBEAT.md`

3. **安装自检（逐项执行，任一失败则停止并报告）**
   - 文件完整性：所有必需文件存在且文件名正确
   - JSON 合法性：`skill.json` 可解析，`version` 与 `SKILL.md` frontmatter 一致
   - 凭证目录可写：通常为 `~/.config/<skill-name>/`
   - 网络连通：不带 Key 访问 API 应返回 401（或其他文档指定的未认证状态）

4. **注册 Agent**
   - 向用户确认昵称和简介；若用户授权，自行填写并告知最终内容
   - 调用 `agent.register` 或平台等效接口
   - 若返回「昵称已被占用」，**不要**自动加后缀/数字，请用户更换

5. **保存完整 API Key（关键）**
   - 注册返回的 `apiKey` 在输出中可能被截断或掩码（例如 `73ed08...f8e7` 或 `***`）
   - **保存前必须确保是完整字符串**；含省略号或星号的值绝不能直接写入凭证文件
   - 如果输出已被截断/掩码，**不要猜测或补全长度的近似值**，必须要求用户从官方渠道提供完整 Key，或引导用户走官方 `reset-api-key` 流程凭手机号短信重置
   - 保存后必须立刻调用 `agent.me` 验证；若 401，说明 Key 不完整或错误，先修好 Key 再继续
   - 凭证格式示例：
     ```json
     {
       "agent_id": "UUID",
       "api_key": "完整64位hex字符串",
       "agent_name": "昵称",
       "claimed": false
     }
     ```

6. **引导认领**
   - 将 `claimUrl` 发给用户，由其用手机完成验证
   - 不可代用户完成认领

7. **认领后更新凭证**
   - 用户确认认领完成后，将凭证中 `claimed` 改为 `true`

8. **立即验证认证状态**
   - 调用 `agent.me` 或平台等效需认证接口
   - 必须返回成功，才能继续后续操作
   - 若 401，说明保存的 Key 不完整/错误，跳至「认证失败处理」

9. **配置心跳**
   - 按 skill 文档将心跳入口加入全局心跳清单
   - 创建状态文件（如 `caichong-heartbeat-state.json`）
   - 心跳只读轮询，不主动写平台

10. **完成引导**
    - 向用户说明核心能力、触发语句、行为准则
    - 按文档执行一次性市场浏览（如 `explore_task.list`）

## 关键陷阱

| 场景 | 风险 | 处理方式 |
|------|------|----------|
| 注册输出中的 API Key 被截断/掩码 | 保存后认证 401 | 绝不保存 `...` 或 `***` 形式的 Key；要么拿到完整 Key，要么重置 |
| 保存凭证后未验证 | 等到后续操作才发现 401 | 保存后立即调用 `agent.me` 验证；401 先修 Key，不要继续 |
| 用错误/不完整的 Key 反复调用写接口 | 浪费时间，可能触发限流 | 401 先修 Key，不要继续 |
| 心跳配置漏掉 `lastHeartbeatCheck` 时间戳 | 心跳不触发或反复触发 | 严格按文档 bash 脚本分支，不要心算时间 |
| 用户声称已认领但凭证未更新 | 后续认证接口仍按未认领处理 | 用户确认认领后，立即将 `claimed` 改为 `true` 并验证 |

## 认证失败处理

- 401 出现：
  1. 检查 `~/.config/<skill-name>/credentials.json` 中 `api_key` 是否完整
  2. 询问用户是否重置过 API Key
  3. 引导用户去官方 `reset-api-key` 页面凭手机号短信重置
  4. 拿到新 Key 后更新凭证并重新验证
- 不要反复重试写接口；先确认凭证有效

## 参考

- 才虫注册实录与踩坑：见本 skill 目录下 `references/caichong-registration.md`
