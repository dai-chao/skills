---
name: chinese-university-research
title: Chinese University & Major Research
description: Research Chinese university rankings, major evaluations, and academic reputation. Covers domestic (软科, 校友会, 学科评估) and international rankings (QS, THE, US News).
trigger: user asks about Chinese university rankings, major quality, 学科评估, or specific university reputation like 哈工大, 清华, 北大, etc.
---

# Chinese University & Major Research

## Workflow
1. **Identify the university/major** from the user's query.
2. **Search for latest rankings** — prioritize authoritative sources:
   - Domestic: 教育部学科评估 (A+, A, A-), 软科 (ARWU/BCUR), 校友会 (CUAA), 武书连
   - International: QS World, QS Asia, THE World, US News World, ARWU World
3. **Use browser to navigate** to Wikipedia or official ranking sites if web_search fails.
4. **Extract structured data** — use browser_console to query tables on Wikipedia pages.
5. **Summarize concisely** — user prefers bullet points, no long preambles.

## Key Data Points to Collect
- World rankings: QS, THE, US News, ARWU
- Domestic rankings: 软科, 校友会, 武书连, QS China, THE China
- Subject/major rankings: 学科评估 grade (A+, A, B+), QS subject, THE subject
- Notable affiliations: C9 League, 985/211, 双一流
- Employment reputation for specific majors

## Wikipedia Extraction Pattern
For university pages on en.wikipedia.org:
- Look for tables containing "University rankings"
- Use browser_console with: `document.querySelectorAll('table')` and filter by innerText containing ranking keywords
- General rankings table usually has: BCUR, QS, THE, USNWR, ARWU
- Subject rankings may be in a separate table further down the page

## Output Format
- Use structured lists with clear headers
- Include both world and domestic rankings when available
- For major evaluations, mention 学科评估 grade and employment prospects
- Keep it factual and concise — user dislikes verbosity

## Pitfalls
- web_search may return 403 errors — fall back to browser navigation
- Wikipedia pages may have collapsed sections — click to expand before extracting
- Chinese sites (百度百科, 知乎) often block automated access — prefer English Wikipedia for ranking data
- Some ranking tables load dynamically — may need to scroll before extraction
