---
title: Chinese App & Mini-Program Ranking Research
name: chinese-app-miniprogram-rankings
version: 1.0
description: >
  Retrieve and analyze Chinese mobile app and WeChat mini-program popularity
  rankings when search engines are unavailable (CAPTCHA-blocked in remote
  browser environments).
triggers:
  - User asks about 小程序排行榜, APP排行, 最火的应用, mini-program trends
  - User wants market data on Chinese mobile apps or WeChat ecosystem
  - Search engines fail due to CAPTCHA/bot detection
---

# Chinese App & Mini-Program Ranking Research

## Problem
Standard web search (Google, Baidu, Bing) often returns CAPTCHA or bot-detection pages in remote browser environments, making it impossible to retrieve current ranking data through search queries.

## Primary Data Source

### 易观千帆 (Analysys Qianfan)
- URL: https://qianfan.analysys.cn/
- Navigate to: 千帆榜单 → 小程序榜 (or APP榜)
- Direct path: `/megi/tuna/rankApp` with query param for mini-programs
- **Key advantage**: Top-level ranking tables are accessible without login.
- Provides: Monthly active users (MAU), month-over-month growth, category, developer

**How to extract data:**
1. Navigate to the ranking page
2. Confirm the tab is on 小程序月度TOP榜
3. The ranking table shows 10 items per page by default
4. Click the next-page button () to paginate through results
5. Extract rankings from the structured table cells (排名 + 小程序名称)

## Alternative Sources

| Platform | URL | Notes |
|---|---|---|
| 阿拉丁指数 | https://www.aldzs.com/toplist | May have connection issues; try if Qianfan fails |
| QuestMobile | index.questmobile.com.cn | Requires institutional access for deep data |
| 微信指数 | 微信搜一搜内置 | Not accessible via browser tools |

## Analysis Framework

Once rankings are extracted (typically top 30-50), categorize by:

1. **Developer ecosystem** (Tencent vs. independent) — identify platform bias
2. **Industry verticals**: 政务/生活, 物流/出行, 外卖/餐饮, 电商/购物, 办公/工具, 视频/内容, 游戏, 金融/支付, 医疗
3. **User behavior insights**:
   - 刚需高频 vs 低频实用
   - B端工具 vs C端消费
   - Super-app satellites (美团系, 拼多多系) vs standalone

## Pitfalls
- Do NOT rely on search engines as the first step for this task — they will likely be blocked
- Some entries show "--" instead of a name in the detail table; trust the ranked list table more
- Pagination requires clicking the forward arrow repeatedly; snapshot after each click
- MAU numbers may be hidden behind login walls — rank order is still valuable without absolute numbers

## Verification
- Cross-check top 10 names against known major players (美团, 拼多多, 腾讯系) to confirm data sanity
- If the page loads but tables are empty, the site may have updated its layout — try 阿拉丁 as fallback