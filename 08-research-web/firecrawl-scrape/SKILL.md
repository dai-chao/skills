---
name: firecrawl-scrape
description: Web scraping & crawling for AI using Firecrawl
version: 1.0.0
tags: [web-scraping, ai, crawling, markdown]
---

# Firecrawl – AI Web Scraping

Firecrawl converts entire websites into clean, LLM-ready Markdown.
It handles JavaScript rendering, anti-bot measures, and sitemap discovery automatically.

- **GitHub**: github.com/mendableai/firecrawl (50 000+ ⭐)
- **License**: AGPL-3.0
- **Security**: SOC 2 Type 2 compliant cloud API; SSRF patches applied Dec 2024. No malware.

## Environment Variables

| Variable | Description |
|---|---|
| `{{FIRECRAWL_URL}}` | Base URL of the Firecrawl API |
| `{{FIRECRAWL_API_KEY}}` | API key for authentication |

## Usage Examples

### Scrape a single page to Markdown

```bash
curl -s -X POST "{{FIRECRAWL_URL}}/v1/scrape" \
  -H "Authorization: Bearer {{FIRECRAWL_API_KEY}}" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "formats": ["markdown"]}'
```

### Crawl an entire site

```bash
curl -s -X POST "{{FIRECRAWL_URL}}/v1/crawl" \
  -H "Authorization: Bearer {{FIRECRAWL_API_KEY}}" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.example.com", "limit": 50}'
```

### Map all URLs on a site

```bash
curl -s -X POST "{{FIRECRAWL_URL}}/v1/map" \
  -H "Authorization: Bearer {{FIRECRAWL_API_KEY}}" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## AI Agent Tips

- Use `scrape` for single-page content extraction, `crawl` for full-site indexing.
- Output is clean Markdown — ideal for feeding into RAG pipelines or LLM context.
- Respect `robots.txt`; Firecrawl honours it by default.
- Set `limit` on crawls to avoid excessive page counts.
