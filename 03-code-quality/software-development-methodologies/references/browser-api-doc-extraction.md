# Browser API Documentation Extraction

## Problem
`web_extract` often fails on modern documentation sites (SPAs, auth-gated, or private-network flagged) because the content is rendered client-side or blocked by bot detection. The browser stack can load the page and extract the full rendered text, but doing it element-by-element is brittle.

## Technique
Use `browser_console` with a single JavaScript expression to dump the entire main content area as plain text, then parse it manually into structured API documentation.

### Steps
1. `browser_navigate` to the docs URL.
2. If the page has a navigation tree, `browser_click` the specific endpoint link.
3. Run `browser_console` with:
   ```javascript
   document.querySelector('main')?.innerText || document.body.innerText
   ```
4. The result is a large plain-text string containing all headings, parameter tables, code blocks, and descriptions in reading order.
5. Parse the text into structured fields (endpoint, method, headers, request body params, response fields) and present it to the user in a clean format.

## Why This Works
- `innerText` respects CSS visibility and returns human-readable text, not raw HTML.
- It captures content inside React/Vue/Angular-rendered components that `web_extract` misses.
- It avoids fragile ref-based element traversal (which breaks when the site re-renders or changes layout).

## Worked Example: MiniMax Voice Clone API
**URL:** `https://platform.minimax.io/docs/api-reference/voice-cloning-clone`

`web_extract` returned empty (blocked). Browser navigation succeeded. One `browser_console` call with `document.querySelector('main')?.innerText || document.body.innerText` returned the full API spec including:
- Endpoint: `POST https://api.minimax.io/v1/voice_clone`
- All headers, body parameters with types/defaults/descriptions
- Response schema and example JSON
- Interjection tags supported by the model
- Pricing and retention notes (7-day auto-deletion)

The extracted text was then formatted into a structured table + JSON block for the user.

## Pitfalls
- Some docs sites lazy-load content below the fold. If `innerText` is truncated, `browser_scroll` down first, then re-run the console expression.
- `innerText` loses code formatting (indentation is preserved but not syntax highlighting). For code blocks, the text is usually still readable.
- If the site uses shadow DOM, `document.querySelector('main')` may miss content. Fallback to `document.body.innerText` covers most cases.
