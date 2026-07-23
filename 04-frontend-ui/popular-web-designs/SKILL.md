---
name: popular-web-designs
title: Popular Web Designs · 品牌设计模板
description: >
  74 real-brand DESIGN.md design systems (Stripe, Linear, Vercel, Starbucks, Nike, Tesla…).
  Use whenever the user wants UI/pages that look like a known brand, asks for 「像 X 一样」「X 风格」
  「build like Stripe/Linear/…」, landing/dashboard/marketing pages with a brand aesthetic,
  or wants to drop a DESIGN.md into a project. Always load templates/<brand>.md before coding.
  Source: VoltAgent/awesome-design-md (MIT). Keywords: 设计, UI, ui, 样式, 风格, 界面, UI设计, 品牌设计, 设计系统, DESIGN.md, design, style, styling, css, brand UI.
license: MIT
metadata:
  author: local
  upstream: https://github.com/VoltAgent/awesome-design-md
  synced_at: 2026-07-23
  template_count: 74
---

# Popular Web Designs（品牌 DESIGN.md 库）

来自 [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) 的 **74** 份品牌设计系统。每份是 Google Stitch 风格的 `DESIGN.md`：气质、色板、字体层级、组件、间距、阴影、Do/Don't、响应式、Agent Prompt。

**不要凭记忆「大概像某某品牌」**——先打开对应 `templates/<brand>.md`，再按其中 token 实现。

## 何时使用

- 「做成 Stripe / Linear / Starbucks / Nike 那种感觉」
- 「用某某品牌的 DESIGN.md 生成页面」
- 落地页、营销站、Dashboard、文档站需要可复现的视觉语言
- 用户丢来 awesome-design-md / getdesign.md 链接或品牌名

## 工作流（必须）

1. **选模板**：从下方目录匹配品牌；模糊时问用户 1 个澄清，或按场景推荐（见文末）。
2. **读全文**：`templates/<brand>.md`（整份；不要只扫标题）。
3. **实现**：把色板写成 CSS variables；字体按文内 stack（专有字体用文内 fallback / Google Fonts 替代）；组件状态（hover/focus/disabled）按 Section 4。
4. **约束**：遵守该模板的 Do's and Don'ts；不要混搭第二个品牌的主色/主字体。
5. **可选**：用户要求「写入项目」时，把该文件复制为项目根目录 `DESIGN.md`。

## 相关 skill

- `claude-design` / `impeccable` / `design-taste-frontend`：设计流程与品味；本 skill 提供**具体品牌词汇表**。
- 单风格抽象（`minimal`、`neon`…）：用户未点名品牌时可用；点名品牌时优先本库。

## HTML 落地提示

```html
:root {
  /* 从模板 Section 2 填入 */
  --color-bg: …;
  --color-text: …;
  --color-accent: …;
}
body {
  /* 从模板 Section 3 填入 font-family / size / weight / tracking */
}
```

专有字体不可用 CDN 时：用模板里的 fallback，或常见替代（Geist→Geist/Inter，sohne→Source Sans 3，Circular/Cereal→DM Sans）。**字重、字号、字距比字体名更重要。**

---

## 设计目录（74）

路径均为 `templates/<file>`。

### AI & LLM

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `claude.md` | Claude | 暖陶土强调色、干净编辑向 |
| `cohere.md` | Cohere | 鲜活渐变、数据仪表盘感 |
| `elevenlabs.md` | ElevenLabs | 暗色电影感、声波美学 |
| `minimax.md` | Minimax | 大胆暗色 + 霓虹 |
| `mistral.ai.md` | Mistral AI | 法式极简、紫调 |
| `ollama.md` | Ollama | 终端优先、单色 |
| `opencode.ai.md` | OpenCode | 开发者暗色主题 |
| `replicate.md` | Replicate | 白画布、代码向 |
| `runwayml.md` | Runway | 电影节编辑感、暗色英雄区 |
| `together.ai.md` | Together AI | 技术蓝图感 |
| `voltagent.md` | VoltAgent | 虚空黑 + 翠绿、终端风 |
| `x.ai.md` | xAI | 冷峻单色未来感 |

### Developer Tools & IDEs

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `cursor.md` | Cursor | 暗色界面、渐变点缀 |
| `expo.md` | Expo | 暗色、紧字距、代码中心 |
| `lovable.md` | Lovable | 活泼渐变、友好开发感 |
| `raycast.md` | Raycast | 暗色 chrome、鲜艳渐变 |
| `superhuman.md` | Superhuman | 高端暗色、键盘优先、紫光 |
| `vercel.md` | Vercel | 黑白精密、Geist |
| `warp.md` | Warp | 暗色 IDE、块状命令 UI |
| `slack.md` | Slack | 协作产品感（上游收录） |

### Backend / Data / DevOps

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `clickhouse.md` | ClickHouse | 黄强调、技术文档风 |
| `composio.md` | Composio | 现代暗色 + 彩色集成图标 |
| `hashicorp.md` | HashiCorp | 企业干净黑白 |
| `mongodb.md` | MongoDB | 绿叶品牌、文档向 |
| `posthog.md` | PostHog | 活泼刺猬、开发者暗色 |
| `sanity.md` | Sanity | 暗色编辑营销、珊瑚红 CTA |
| `sentry.md` | Sentry | 暗色仪表盘、粉紫强调 |
| `supabase.md` | Supabase | 暗翠绿、代码优先 |

### Productivity & SaaS

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `cal.md` | Cal.com | 干净中性、开发者简洁 |
| `intercom.md` | Intercom | 友好蓝、会话 UI |
| `linear.app.md` | Linear | 超极简、精密紫强调 |
| `mintlify.md` | Mintlify | 干净绿强调、阅读优化 |
| `notion.md` | Notion | 暖极简、衬线标题 |
| `resend.md` | Resend | 极简暗色、等宽点缀 |
| `zapier.md` | Zapier | 暖橙、插画友好 |

### Design & Creative

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `airtable.md` | Airtable | 彩色友好、结构化数据 |
| `clay.md` | Clay | 有机形、软渐变、艺术指导 |
| `figma.md` | Figma | 多色活泼且专业 |
| `framer.md` | Framer | 大胆黑蓝、动效优先 |
| `miro.md` | Miro | 明黄强调、无限画布 |
| `webflow.md` | Webflow | 蓝强调、打磨营销站 |

### Fintech & Crypto

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `binance.md` | Binance | Binance 黄 + 单色、交易台紧迫感 |
| `coinbase.md` | Coinbase | 干净蓝、信任机构感 |
| `kraken.md` | Kraken | 紫强调暗色、数据密 |
| `mastercard.md` | Mastercard | 暖奶油画布、轨道胶囊形 |
| `revolut.md` | Revolut | 暗色精致、渐变卡片 |
| `stripe.md` | Stripe | 紫渐变、字重 300 优雅 |
| `wise.md` | Wise | 亮绿强调、清晰友好 |

### E-commerce & Retail

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `airbnb.md` | Airbnb | 暖珊瑚、摄影驱动、圆角 |
| `meta.md` | Meta | 摄影优先、明暗二分、Meta Blue CTA |
| `nike.md` | Nike | 单色、巨大大写 Futura、全出血图 |
| `shopify.md` | Shopify | 暗色电影感、霓虹绿、超细 display |
| `starbucks.md` | Starbucks | 四阶绿、暖奶油画布、SoDoSans |

### Media & Consumer Tech

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `apple.md` | Apple | 大留白、SF Pro、电影感影像 |
| `hp.md` | HP | 纯白、Electric Blue CTA、几何字 |
| `ibm.md` | IBM | Carbon、结构化蓝 |
| `nvidia.md` | NVIDIA | 绿黑能量、技术力量感 |
| `pinterest.md` | Pinterest | 红强调、瀑布流、图像优先 |
| `playstation.md` | PlayStation | 三表面频道布局、青 hover 缩放 |
| `spacex.md` | SpaceX | 冷峻黑白、全出血、未来感 |
| `spotify.md` | Spotify | 暗底鲜绿、大胆字体、专辑艺术 |
| `theverge.md` | The Verge | 酸薄荷 + 紫外、Manuka display |
| `uber.md` | Uber | 大胆黑白、紧字距、都市能量 |
| `vodafone.md` | Vodafone | 纪念碑式大写、Vodafone Red 色带 |
| `wired.md` | WIRED | 纸白宽报密度、自定义衬线、墨蓝链接 |

### Automotive

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `bmw.md` | BMW | 暗色高端、德系精密 |
| `bmw-m.md` | BMW M | 赛车对比、M 色强调 |
| `bugatti.md` | Bugatti | 影院黑、单色禁欲、巨幅 display |
| `ferrari.md` | Ferrari | 黑白明暗编辑、Ferrari Red 极度克制 |
| `lamborghini.md` | Lamborghini | 真黑教堂、金强调、Neo-Grotesk |
| `renault.md` | Renault | 极光渐变、零圆角按钮 |
| `tesla.md` | Tesla | 极简减法、全视口摄影 |

### Retro Web（怀旧）

| 文件 | 品牌 | 风格一句话 |
|------|------|------------|
| `dell-1996.md` | Dell (1996) | 目录时代企业站、色块卡片、GIF 贴纸感 |
| `nintendo-2001.md` | Nintendo (2001) | Y2K 主机镀铬、半调导航、像素欢迎气泡 |

---

## 按场景快选

| 场景 | 优先模板 |
|------|----------|
| 开发者工具 / Dashboard | `linear.app` `vercel` `supabase` `raycast` `sentry` `cursor` |
| 文档 / 内容站 | `mintlify` `notion` `sanity` `mongodb` `wired` |
| 营销落地页 | `stripe` `framer` `apple` `spacex` `shopify` |
| 暗色产品 UI | `linear.app` `elevenlabs` `warp` `superhuman` `voltagent` |
| 浅色干净 | `vercel` `stripe` `notion` `cal` `replicate` |
| 活泼友好 | `posthog` `figma` `lovable` `zapier` `miro` |
| 高端奢侈 | `apple` `bmw` `bugatti` `ferrari` `lamborghini` `stripe` |
| 零售 / 消费品牌 | `starbucks` `nike` `airbnb` `meta` `mastercard` |
| 终端 / 等宽美学 | `ollama` `opencode.ai` `x.ai` `voltagent` |
| 怀旧 / 复古 Web | `dell-1996` `nintendo-2001` |

## 许可与归属

- 上游：[VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)（MIT）
- 模板为公开站点视觉的分析文档，**不主张拥有任何品牌视觉商标**；生成 UI 时勿冒充官方产品
- 同步信息见同目录 `SOURCE.txt`
