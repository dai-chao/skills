# SearXNG 403 Diagnosis Notes

## Symptom

`web_search` returns:

```json
{
  "success": false,
  "error": "SearXNG returned HTTP 403"
}
```

## What 403 means here

- Outbound HTTPS from the environment is healthy (test with `curl -I https://www.google.com`).
- The SearXNG backend itself is rejecting the query. This can be:
  - backend IP/rate limited by a downstream engine,
  - query-specific blocking,
  - backend misconfiguration.

## Confirm scope

Test with a trivial query:

```python
web_search(query="hello world")
```

If it also 403, the whole backend is down/blocked. If only your query 403, the query is triggering the block.

## Alternatives tried

- DuckDuckGo Lite HTML: reachable but results are heavily obfuscated; reliable parsing requires ongoing maintenance.
- Google direct: `curl -I` returns 200 but HTML parsing is fragile and against ToS for automated scraping.
- Site-specific APIs (Open-Meteo, etc.) are the most reliable when they cover the topic.

## Preferred response

Do not declare "search is broken". Instead:

1. State that the configured SearXNG backend is returning 403 for this query.
2. Try a direct source/API if the query domain has one.
3. Offer to fetch a specific known URL with `curl` or the browser if the user points to it.
