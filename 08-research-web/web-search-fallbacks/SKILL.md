---
name: web-search-fallbacks
description: Reliable fallback paths when the primary web_search backend (SearXNG) is unavailable or blocked. Covers direct search APIs, weather APIs, and quick curl-based alternatives.
version: 1.0.0
category: research
---

# Web Search Fallbacks

## When to use

Use this skill when `web_search` returns errors like `SearXNG returned HTTP 403`, or `web_extract` is blocked for a target site. The goal is to get the answer another way, not to declare search unavailable.

## Quick diagnosis

1. Try a trivial query (`hello world`) to confirm the failure is backend-wide, not query-specific.
2. Try `curl -I https://www.google.com` to confirm outbound HTTPS is healthy.
3. If the failure is only `web_search` / SearXNG, proceed with fallbacks.
4. If general HTTPS is broken, fix the environment/network first; this skill cannot help.

## Fallbacks by need

### Weather (no search needed)

Use Open-Meteo free API directly. It needs no API key and supports Taiwan cities well.

See [`references/open-meteo-weather-api.md`](references/open-meteo-weather-api.md) for coordinates and weather-code mapping.

Example:

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=25.0330&longitude=121.5654&current=temperature_2m,relative_humidity_2m,weather_code&timezone=Asia/Taipei"
```

### General search

- **DuckDuckGo Lite** (HTML): often works when SearXNG is blocked, but results are embedded in obfuscated HTML and may need adaptive parsing.
- **Google direct via curl**: `curl -I https://www.google.com/search?q=...` usually returns 200, but parsing the HTML for results is fragile.
- **Site-specific APIs**: for Wikipedia, IMDb, GitHub, etc., prefer their documented APIs over scraping.
- **Targeted site navigation**: when a known authoritative page exists (e.g., docs at `pgyer.com/doc/view/<slug>`), skip search and use `browser_navigate` directly to load the page. If the URL slug is uncertain, check the page tree exposed in the Next.js `_next/static` JSON payload (e.g., `/doc/view/certified` for "实名认证") or navigate to the site's root and read the sidebar.

See [`references/searxng-403-diagnosis.md`](references/searxng-403-diagnosis.md) for the failure pattern and parser notes.

## Reusable script

[`scripts/fallback_search.py`](scripts/fallback_search.py) provides a tiny command-line wrapper:

```bash
fallback_search.py weather [city]      # Taiwan city weather via Open-Meteo
fallback_search.py search <query>        # DuckDuckGo Lite HTML scrape (best-effort)
```

Keep the script lightweight; if it breaks, fix the parser rather than building a whole scraping framework.

## Reference notes

- [`references/searxng-403-diagnosis.md`](references/searxng-403-diagnosis.md): SearXNG 403/429 failure pattern and parser notes.
- [`references/open-meteo-weather-api.md`](references/open-meteo-weather-api.md): Taiwan city coordinates and Open-Meteo weather codes.
- [`references/pgyer-docs-sitemap.md`](references/pgyer-docs-sitemap.md): 蒲公英（pgyer.com）文档中心已知 slug 映射与未知 slug 查找方法.

## What not to harden

- Do not write a rule that "web_search is broken". SearXNG may be restored at any time.
- Do not over-engineer a fallback search engine. The value is in getting the specific answer now, not in replacing the primary tool permanently.
