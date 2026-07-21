# Hacker News Show HN as a Trending Project Source

## Why it matters
HN Show posts are a goldmine for "interesting projects with users but no revenue yet". The community is technical, critical, and quick to spot genuinely useful tools. High engagement (points + comments) correlates with real user interest, not just marketing.

## URL
- https://news.ycombinator.com/show

## What to look for
- **Points > 100** = strong interest
- **Comments > 50** = active discussion, often reveals real use cases and pain points
- **"Show HN" prefix** = the creator posted it themselves, usually early stage

## Categories commonly seen
- Developer tools (CLI utilities, local-first apps)
- Privacy/security tools (offline, zero-cloud)
- AI infrastructure (agent skills, compression, local servers)
- Content/curiosity tools (maps, Wikipedia, education)
- Productivity (lightweight alternatives to Jira, Notion, etc.)

## Extraction approach
Use `browser_navigate` to https://news.ycombinator.com/show, then scroll. The page is static HTML — no JavaScript needed for basic extraction. For structured data, use `browser_console` with:

```javascript
Array.from(document.querySelectorAll('.athing')).map(row => {
  const title = row.querySelector('.titleline > a')?.textContent;
  const url = row.querySelector('.titleline > a')?.href;
  const sub = row.nextElementSibling;
  const score = sub?.querySelector('.score')?.textContent;
  const comments = sub?.querySelector('a[href*="item?id="]:last-of-type')?.textContent;
  return {title, url, score, comments};
})
```

## When to use alongside GitHub trending
- GitHub trending = what developers are starring (passive interest)
- HN Show = what developers are actively discussing and trying (active engagement)
- Combine both for a fuller picture of "what's actually getting used"

## Pitfalls
- HN front page rotates fast — posts older than 48h may be buried
- Some Show HN posts are stealth marketing — check comment sentiment
- Low points does NOT mean bad idea — niche tools often have small but passionate audiences