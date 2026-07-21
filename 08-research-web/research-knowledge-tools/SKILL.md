---
name: research-knowledge-tools
description: "Research and knowledge management: arXiv papers, prediction markets (Polymarket), maps/geocoding, Google Workspace, Airtable, Notion, Obsidian, news access, app rankings, travel planning, and LLM Wiki."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Research, Knowledge Management, arXiv, Polymarket, Maps, Google Workspace, Airtable, Notion, Obsidian, News, Travel, Wiki]
    related_skills: [media-content-creation, llm-evaluation]
---

# Research & Knowledge Tools

## When to Use This Skill

Trigger when the user wants to:
- Search academic papers on arXiv
- Query prediction markets (Polymarket)
- Get geocoding, POIs, or routes
- Use Google Workspace (Gmail, Calendar, Drive, Docs, Sheets)
- Manage data in Airtable or Notion
- Work with Obsidian markdown notes
- Access news directly via search engines
- Check Chinese app/mini-program rankings
- Plan experiential travel
- Build a compounding knowledge base (LLM Wiki)

## Section 1: Academic Research

### arXiv
Search papers by keyword, author, category, or ID.
```bash
# Search via arXiv API
curl "http://export.arxiv.org/api/query?search_query=all:llm&start=0&max_results=10"
```

See [references/arxiv.md](references/arxiv.md) for full details.

## Section 2: Prediction Markets

### Polymarket
Query markets, prices, orderbooks, history.
```bash
# Get market data
curl "https://clob.polymarket.com/markets"
```

See [references/polymarket.md](references/polymarket.md) for full details.

## Section 3: Maps & Geolocation

Geocode, find POIs, routes, timezones via OpenStreetMap/OSRM.
```bash
# Geocoding with Nominatim
curl "https://nominatim.openstreetmap.org/search?q=Paris&format=json"
```

See [references/maps.md](references/maps.md) for full details.

## Section 4: Productivity & Data Tools

### Google Workspace
Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python.
```bash
pip install gws
gws auth login
gws drive list
```

See [references/google-workspace.md](references/google-workspace.md) for full details.

### Airtable
REST API for records CRUD, filters, upserts.
```bash
curl "https://api.airtable.com/v0/$BASE_ID/$TABLE_NAME" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY"
```

See [references/airtable.md](references/airtable.md) for full details.

### Notion
Pages, databases, markdown, Workers.
```bash
pip install ntn
ntn page list
```

See [references/notion.md](references/notion.md) for full details.

### Obsidian
Read, search, create, edit notes in Obsidian vault.
```bash
# Obsidian vault is a local folder of markdown files
ls ~/Documents/Obsidian/Vault/
```

See [references/obsidian.md](references/obsidian.md) for full details.

## Section 5: News & Rankings

### Web News Direct Access
Access news via headless browser (Google/Baidu/Bing/DuckDuckGo).
```python
# Use browser tools to search news
# See browser_navigate and browser_snapshot
```

See [references/web-news-direct-access.md](references/web-news-direct-access.md) for full details.

### Chinese App & Mini-Program Rankings
Retrieve and analyze Chinese mobile app and WeChat mini-program rankings.

See [references/chinese-app-miniprogram-rankings.md](references/chinese-app-miniprogram-rankings.md) for full details.

## Section 6: Travel Planning

Plan experiential travel (fishing, farming, harvesting, etc.).

See [references/travel-experience-planning.md](references/travel-experience-planning.md) for full details.

## Section 7: LLM Wiki

Build and maintain a persistent, compounding knowledge base as interlinked markdown files.

### Three-Layer Architecture
1. **raw/** — Immutable source material
2. **wiki pages** — Agent-owned markdown in entities/, concepts/, comparisons/, queries/
3. **SCHEMA.md** — Domain conventions, tag taxonomy, page thresholds

### Critical Workflow
Always orient by reading SCHEMA.md → index.md → log.md at the start of every session.

See [references/llm-wiki.md](references/llm-wiki.md) for full details.

## Common Pitfalls

1. **arXiv rate limits**: Use export.arxiv.org, not arxiv.org directly
2. **Polymarket API**: CLOB API requires proper headers
3. **Nominatim rate limits**: Max 1 request/second; use OSRM for routing
4. **Google Workspace auth**: OAuth2 flow required; tokens expire
5. **Airtable pagination**: Use offset parameter for large tables
6. **Notion block limits**: 100 blocks per request; paginate
7. **Obsidian sync**: Use git or Obsidian Sync for multi-device
8. **News search**: Search engines block headless browsers; use proper User-Agent
9. **LLM Wiki contradictions**: Always flag contested information
10. **Client-side hydrated sites (Docusaurus, Next.js, etc.)**: `browser_snapshot` often returns empty because the accessibility tree is built after JavaScript hydration. If you get `(empty page)` with 0 elements on a known-good URL, the page likely hydrates client-side. **Fallback chain**: (a) wait a few seconds and retry `browser_snapshot`, (b) use `curl -s -L -A "Mozilla/5.0 ..." <url>` to fetch the server-rendered HTML directly, (c) use `browser_console` with `document.body.innerText` or `document.querySelector` to extract content post-hydration. Do NOT conclude the site is unreachable.
11. **Search engine backends can be flaky**: When `web_search` returns HTTP 403 or 429 repeatedly, do not keep retrying the same query. **Fallback chain**: (a) use Playwright/Bing `browser_navigate` with a direct search URL (e.g. `https://www.bing.com/search?q=<query>`) and parse the rendered results via `browser_snapshot`, (b) use `execute_code` with Python `urllib` to fetch from Brave/Google directly, (c) use targeted GitHub `browser_navigate` + `browser_snapshot` to find repositories, (d) read raw `https://raw.githubusercontent.com/<owner>/<repo>/main/README.md` directly to extract project details. Capture the competitor/research findings in a `references/<topic>.md` file under this skill.
12. **Playwright `browser_navigate` is the preferred browser search fallback**: When `web_search` fails, use Playwright (not legacy browser tools) to open a direct search engine URL, wait for the page, and extract results via `browser_snapshot`. This is more reliable than scraping JSON endpoints because the rendered HTML is visible to the browser. Do NOT fall back to `web_search` again after it has already failed.
