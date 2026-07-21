---
name: product-promotion-posting
description: Cross-platform product promotion workflow for developer and social platforms (Zhihu, Juejin, LeetCode, Product Hunt, Reddit, etc.). Generates per-platform copy, uses browser automation to fill drafts, and lets the user hit publish.
compatibility: Works on any Hermes profile with web/browser tools and Playwright available.
allowed-tools: browser, mcp_playwright, file, terminal
metadata:
  version: "1.0.0"
---

# Product Promotion Posting

Promote a product, tool, or project across multiple platforms without resorting to comment spam.

## Trigger

User asks to:
- Promote a product on multiple platforms
- Post to Zhihu / Juejin / LeetCode / Product Hunt / Reddit / X / 即刻 / 小红书
- Write and publish announcement content across platforms

## Workflow

1. **Confirm scope**
   - Which platforms?
   - Product one-liner / core selling points
   - Website URL
   - Image URL or local image path
   - Tone: technical, marketing, or neutral?

2. **Generate per-platform copy**
   - Chinese platforms: 知乎 / 掘金 / 力扣
   - English platforms: Product Hunt / Reddit / Hacker News / X
   - Keep the same core message but adapt style and length

3. **Open platforms one at a time**
   - Navigate to the editor URL
   - Let the user log in manually (do not ask for or handle passwords)
   - After login, fill the title, body, and upload the image
   - Let the user review and click Publish

4. **Move to next platform only after user confirms**
   - Prevents losing login state and mixing up drafts

## Platform URLs

| Platform | Editor URL | Type |
|----------|------------|------|
| 知乎文章 | https://zhuanlan.zhihu.com/write | Article |
| 掘金 | https://juejin.cn/editor/drafts/new | Article |
| 力扣讨论 | https://leetcode.cn/discuss/ | Forum post |
| Product Hunt | https://www.producthunt.com/posts/new | Launch post |
| Reddit | https://www.reddit.com/submit | Text/link post |
| 即刻 | https://web.okjike.com/ | Short post |

## Content Templates

### Chinese technical article (知乎 / 掘金 / 力扣)

```
标题：{产品名} — {解决的核心痛点}

最近不少开发者遇到 {问题场景}，第一反应是 {常见误区}。

但除了 {表面原因}，本机环境也会暴露很多高风险信号：

- {风险点1}
- {风险点2}
- {风险点3}
- {风险点4}

{产品名} 就是针对这个问题的 {解决方案类型}：

- {卖点1}
- {卖点2}
- {卖点3}

支持 {平台/工具列表}。

官网：{官网URL}
```

### English launch post (Product Hunt / Reddit / Hacker News)

```
Title: {Product Name} — {one-line value proposition}

If you're using {tools}, you may have run into {problem}. Most people blame {surface cause}, but local environment also leaks signals like {risk factors}.

{Product Name} scans your local machine for these risks and helps fix them in one click. No data sent to the cloud.

Supports: {tool list}

Try it: {website URL}
```

## Pitfalls

- **Do not spam comments on other people's posts.** This is against platform rules and degrades community trust. Always use the user's own account and native publishing tools.
- **Never ask for or handle the user's password.** Use Playwright to open the page, pause for the user to log in, then continue.
- **Login state is fragile across platforms.** Finish one platform completely before opening the next.
- **Image uploads differ by platform.** Some need local files, some need URLs. Prefer the local file if the platform supports it.
- **Product Hunt and Reddit may block headless automation.** If a CAPTCHA or anti-bot page appears, hand control back to the user.

## Verification

After each post is filled, confirm with the user:
- Title and body look correct
- Image is inserted
- They are ready to click Publish

Only move to the next platform after they say so.
