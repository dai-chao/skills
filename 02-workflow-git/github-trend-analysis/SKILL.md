---
name: github-trend-analysis
title: GitHub Trending & Interesting Project Analysis
version: 1.0
description: |
  Analyze GitHub trending repositories and fast-growing/interesting open-source projects.
  Extract structured data from GitHub's dynamic trending pages, categorize by technology
  trends, and deliver actionable insights. Handles bot-detection by using direct navigation
  and JavaScript extraction rather than search engines.
triggers:
  - User asks about GitHub trending, fastest growing repos, interesting projects
  - User wants analysis of open-source project trends
  - User asks "最近有什么有意思的项目" or similar
---

# GitHub Trending & Interesting Project Analysis

## Problem
- GitHub Trending page is dynamic and requires browser interaction
- Search engines often fail (CAPTCHA/bot detection) for real-time trending data
- Raw project lists are not useful — need categorization and trend insight

## Primary Data Source

### GitHub Trending
- URL: https://github.com/trending
- Supports filters: Language, Date range (Today / This week / This month)
- Default shows ~25 repositories per page

**Navigation path:**
1. `browser_navigate` to https://github.com/trending
2. Click date range filter to select "This month" for meaningful growth data
3. Scroll to ensure all items are loaded (GitHub uses client-side rendering)
4. Use `browser_console` JavaScript extraction to get structured data

## Extraction Script

```javascript
// Extract all trending repositories from the page
// NOTE: GitHub's trending page uses <article> inside <main>, NOT generic article tags.
// The selector must target 'main article' to avoid picking up README markdown content.
Array.from(document.querySelectorAll('main article')).map(a => {
  const h2 = a.querySelector('h2 a');
  const desc = a.querySelector('p');
  const stars = a.querySelector('a[href*="stargazers"]');
  const lang = a.querySelector('[itemprop="programmingLanguage"]');
  return {
    name: h2?.textContent?.trim().replace(/\s+/g, ' '),
    desc: desc?.textContent?.trim(),
    stars: stars?.textContent?.trim(),
    lang: lang?.textContent?.trim()
  };
}).map(x => JSON.stringify(x)).join('\n')
```

## Analysis Framework

Once data is extracted (typically 20-25 projects), categorize by:

### 1. Growth Velocity (stars gained this period)
- **Explosive** (>20k stars/month): Breakout projects, usually AI-related
- **Fast** (10k-20k): Strong momentum, worth watching
- **Steady** (<10k): Established projects with consistent interest

### 2. Technology Trends (map projects to themes)
Common trend buckets (updated 2026-06):
Common trend buckets (updated 2026-06):
- **AI Agent Infrastructure**: token compression, skill security scanners, agent memory, knowledge graphs, skill marketplaces, agent internet access
- **AI Coding Tools**: knowledge graphs, memory, skills, agent frameworks
- **Video/Content Generation**: AI video, short-form content tools
- **Privacy/Local-First**: on-device, zero external API, local LLM
- **Anti-Detection**: stealth browsers, de-AI-writing tools
- **Infrastructure**: containers, testing, build tools
- **Novel Hardware/Signal**: WiFi sensing, spatial intelligence

### 3. Language Ecosystem
- Note primary languages (Rust, Python, TypeScript, Swift, Go)
- Identify language-specific trends (e.g., Rust for performance tools)

### 4. Developer/Organization Type
- Individual creators vs. corporate (Apple, Microsoft, Tencent, NVIDIA)
- Corporate projects often indicate strategic direction

## Output Format

Present results in three tiers:
1. **Top Growth** — fastest rising, with star counts and growth numbers
2. **High-Star Established** — already popular, still trending
3. **Interesting Emerging** — smaller but notable for innovation

Close with **Trend Summary** — 3-5 bullet points on what the data reveals about the current developer landscape.

## Pitfalls
- GitHub trending shows different data for logged-in vs. anonymous users — anonymous is fine for general analysis
- The "Today" filter is too noisy (single-day spikes); prefer "This week" or "This month"
- Some projects may have inflated stars from marketing campaigns — cross-check fork ratios and description quality
- Do NOT rely on web_search for this — GitHub trending data is real-time and search engines lag behind or get blocked
- If GitHub returns a rate limit or bot check, wait and retry with `browser_navigate`
- **Terminal curl to GitHub API is often blocked by user consent policy** — do NOT attempt `curl` to GitHub API as a fallback. Always use browser navigation and JavaScript extraction instead.
- **ProductHunt and similar sites are heavily CAPTCHA-protected** — do not waste time on them. Stick to GitHub trending + HN Show as primary sources.
- **JavaScript extraction must use `main article` selector** — generic `document.querySelectorAll('article')` will pick up README markdown content instead of trending repo cards, producing garbage output. Always scope to `main article`.
- **HN Show (https://news.ycombinator.com/show) is a reliable secondary source** — when GitHub trending is insufficient, HN Show provides recent project launches with community validation (points + comments). No CAPTCHA issues.
- **GitHub API via curl is blocked by user consent** — if encountered, immediately fall back to browser tools. Do not retry curl with different arguments.

## Verification
- Cross-check star counts against project pages if numbers seem suspicious
- Verify that top projects have meaningful descriptions (not just placeholder text)
- Ensure language tags are present — missing tags may indicate very new projects

## Related Skills
- `web-news-direct-access` — when search engines fail for related tech news
- `chinese-app-miniprogram-rankings` — similar pattern for Chinese ecosystem analysis

## References
- `references/2026-06-agent-infrastructure-trend-snapshot.md` — concrete project data from June 2026 session, with star counts and trend categorization