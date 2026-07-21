---
name: web-news-direct-access
title: 当搜索引擎被拦截时直接访问新闻源
version: 1.0
description: |
  在 headless browser 中，Google/Baidu/Bing/DuckDuckGo 等搜索引擎很容易触发 CAPTCHA 或验证。
  本 skill 记录了一套可复用的回退策略：直接访问可信新闻网站，
  并通过 JavaScript 提取特定版块内容。
trigger: 
  - 用户询问时事/新闻
  - 搜索引擎返回 CAPTCHA 、验证码或空白页面
  - 需要快速获取新闻稿件内容
---

# 当搜索引擎被拦截时直接访问新闻源

## 常见失败模式

在远程浏览器中试图搜索时导向验证：
- Google: “Our systems have detected unusual traffic”
- Baidu: 百度安全验证（滑块）
- Bing: 超时或空白结果
- DuckDuckGo: “Select all squares containing a duck” 或无结果

## 回退步骤

1. **放弃通用搜索引擎**。不要在验证页上浪费时间。
2. **根据语言/地区选择新闻源**：
   - 中文时事: BBC 中文 (bbc.com/zhongwen/simp)、Reuters 中文、华尔街日报中文、联合早报
   - 英文时事: Reuters、BBC、NYT、AP News、Politico
   - 财经: CNBC/Financial Times；科技: The Verge/TechCrunch
3. **直接访问首页或专题页**。新闻网站通常比搜索引擎对 bot 更宽容。
4. **用站内搜索或专题标签**找稿件。
5. **提取内容**：
   - 简单文章用 `browser_snapshot(full=true)` 足够。
   - 长文章/专题页用 `browser_console` 执行 JavaScript 精确提取。

## 常用提取脚本

```javascript
// 获取所有带 id 的标题
Array.from(document.querySelectorAll('h1,h2,h3,h4'))
  .map(h => ({ tag: h.tagName, id: h.id, text: h.textContent.trim() }));

// 提取两个 heading 之间的内容
const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4'));
const startIdx = headings.findIndex(h => h.id === 'target-section-id');
const endIdx = headings.findIndex((h, i) => i > startIdx && h.tagName === 'H1');
const section = headings.slice(startIdx, endIdx).map(h => h.innerText).join('\n');
section;

// 搜索关键词并返回所在段落
const paras = Array.from(document.querySelectorAll('p'));
paras.filter(p => p.innerText.includes('关键词')).map(p => p.innerText);
```

## 注意事项

- 不要在验证页上浪费时间，当断则断。
- 时事类问题要注意文章日期与事件时间匹配。
- 新闻网站站内搜索也可能有 bot 限制，优先试首页/专题页。
- 如果所有新闻源都无法访问，告知用户无法获取实时信息。