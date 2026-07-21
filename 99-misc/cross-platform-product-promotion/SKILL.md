---
name: cross-platform-product-promotion
description: 为开发者产品/AI工具/SaaS写多平台推广文案（知乎、掘金、力扣、Product Hunt、Reddit 等），支持手动发布，避免 spam。
compatibility: 任何需要推广开发者工具、AI产品、开源项目或SaaS的任务。
allowed-tools: browser, web, file
metadata:
  version: "1.0.0"
---

# 跨平台开发者产品推广

## 触发条件
用户想要推广一个产品、工具、库、AI Agent 或 SaaS，尤其面向开发者群体，并希望覆盖多个平台（知乎、掘金、力扣、Product Hunt、Reddit、即刻等）。

## 核心原则

1. **绝不批量刷评论**。在他人视频/帖子下大量发广告属于 spam，违反平台规则，且会导致账号被封。必须拒绝，哪怕用户说「只发一条」。
2. **不替用户登录发帖**。不应索要账号密码，也不应自动化登录/发布。正确做法是：用户自己登录，我负责起草文案，用户手动点击发布。
3. **一平台一版本**。不同社区的语气、格式、受众不同，不能同一篇文案复制粘贴。
4. **手动发布优于自动化**。自动化发帖可能被平台判定为机器人营销，导致限流或封号。

## 信息提取清单

起草前必须先确认：

| 字段 | 示例 |
|------|------|
| 产品名 | Agent Guard |
| 官网 | https://www.safeclaude.net/# |
| 核心痛点 | 用 Claude/Cursor/Codex 被风控、账号异常，往往是本机环境暴露高风险信号 |
| 功能点 | 代理泄漏检测、时区指纹一致性、配置残留清理、MCP 明文密钥扫描 |
| 卖点/差异化 | 免费扫描、一键修复 Pro、数据不上云 |
| 支持工具 | Claude Code / Cursor / Codex / Gemini / Windsurf / Hermes |
| 图片 | 本地路径或直链 URL |
| 目标平台 | 知乎、掘金、力扣、Product Hunt、Reddit… |

## 平台语气与结构

| 平台 | 语气 | 推荐结构 |
|------|------|----------|
| **知乎** | 科普、痛点共鸣、略长 | 问题引入 → 分析原因 → 给出工具 → 官网链接 |
| **掘金** | 技术干货、简洁直接 | 标题党技术标题 → 痛点 bullet → 工具介绍 → 链接 |
| **力扣** | 实用主义、开发者视角 | 直接说解决什么问题 → 核心功能 → 链接 |
| **Product Hunt** | 英文产品发布、清晰卖点 | Hook → Problem → Solution → Features → Link |
| **Reddit** | 社区讨论、真实体验 | 个人经历 → 遇到的问题 → 工具 → 求反馈 |
| **即刻** | 轻量、短句、带表情 | 一句话痛点 → 功能点 → 链接 |

## 标准文案公式

标题公式：
```
[目标人群] + [痛点/问题] + [解决方案/工具]
```

正文公式：
```
1. 场景/痛点（让人共鸣）
2. 常见误解（为什么不是你以为的原因）
3. 工具功能（bullet 列出）
4. 卖点/差异化
5. 官网 + 号召行动
```

## 图片处理

- 优先使用**直链 URL**（如 GitHub camo URL 或 CDN 地址），便于复制到各平台。
- 若用户提供本地图片路径，说明：平台发帖通常需要手动上传，可先把文案粘贴，再上传图片。

## 网络搜索备选方案

如果用户要求调研竞品/市场，`web_search` 可能返回 403（如 SearXNG 被拦截）。此时可用 Playwright 浏览器打开公共搜索引擎（Bing）或目标平台网页版，通过 `browser_navigate` + `browser_wait_for` + `browser_evaluate` 获取结果。

> 注意：对于抖音等 JS 渲染页面，页面 snapshot 可能无法直接看到内容，需通过 `browser_evaluate` 读取 DOM 文本。

## 参考模板

详细平台模板见 `references/platform-templates.md`。

## 短视频/AI 视频推广

当用户想用 AI 视频工具（如即梦、可灵、Runway）为产品生成短视频时，输出格式应包含：

1. **素材映射表**：最多 12 个参考素材（图片 / 视频 / 音频）分别对应什么内容
2. **主输入提示**：可直接复制到 AI 视频工具的完整 prompt，使用 `@图片1` `@视频1` `@音频1` 语法
3. **分镜脚本**：按时间线列出画面 + 文案/旁白
4. **风格关键词**：色调、运镜、情绪
5. **无参考素材版 prompt**：纯文本 fallback，供用户不上传素材时直接使用

示例见 `references/ai-video-promotion-prompts.md`。

## 输出格式

- 文字平台推广：直接给出每个平台的标题 + 正文，按用户要求的平台顺序排列。无需长篇解释，用户通常要「直接复制粘贴」的内容。
- 短视频推广：先给素材映射，再给主 prompt、分镜脚本、风格词、纯文本 fallback。

## 发布草稿：浏览器自动化

除了给文案，也可以在用户授权后帮他们把草稿填入各平台编辑器，让用户最后点击发布。必须一平台一平台来，避免登录状态和草稿混乱。

### 发布流程

1. 确认要发哪些平台、产品 one-liner、官网、图片、语气。
2. 按上面的平台模板生成对应文案。
3. 逐个打开编辑器 URL，让用户手动登录（不索要密码）。
4. 登录后填入标题、正文，上传图片。
5. 让用户确认内容正确，并自行点击发布。
6. 一个平台完成后再进入下一个。

### 平台编辑器 URL

| 平台 | 编辑器 URL | 类型 |
|------|------------|------|
| 知乎文章 | https://zhuanlan.zhihu.com/write | 文章 |
| 掘金 | https://juejin.cn/editor/drafts/new | 文章 |
| 力扣讨论 | https://leetcode.cn/discuss/ | 论坛帖 |
| Product Hunt | https://www.producthunt.com/posts/new | 产品发布 |
| Reddit | https://www.reddit.com/submit | 文字/链接帖 |
| 即刻 | https://web.okjike.com/ | 短帖 |

### 发布注意事项

- **绝不批量刷评论或在他人帖子下发广告**；这是 spam，会被封号。
- **不替用户登录**，不要索要账号密码。
- 不同平台图片上传方式不同，优先用本地文件；平台支持 URL 时可用直链。
- 若 Product Hunt / Reddit 弹出 CAPTCHA 或反机器人检测，立即停止自动化，把控制权交还用户。
- 填写完后先让用户确认，再点击发布。

## X/Twitter 发布：xurl CLI

如果用户已配置 [xurl](https://github.com/xdevplatform/xurl)，可直接用官方 CLI 在 X 上发布推广内容。完整命令和认证流程见 `references/xurl-cli.md`；这里只列出最常用的推广场景。

### 常见命令

```bash
# 发布纯文字
xurl post "Hello world!"

# 带图片发布
xurl media upload photo.jpg
xurl post "Check this out" --media-id MEDIA_ID

# 回复 / 引用
xurl reply POST_ID "Great point!"
xurl quote POST_ID "My take"

# 检查认证状态
xurl auth status
xurl whoami
```

### 安全边界

- 不要读取、打印或发送 `~/.xurl` 到对话中。
- 不要索要 token、client-id、client-secret。
- 认证和 app 注册必须由用户在终端外完成。
- 发布前确认目标帖子和用户意图。