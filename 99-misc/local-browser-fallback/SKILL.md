---
name: local-browser-fallback
description: Control the user's local Safari/Chrome on macOS via terminal when the remote browser environment is blocked by IP/geo-restrictions, bot detection, or CAPTCHAs.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [browser, macOS, Safari, Chrome, automation, fallback]
    related_skills: []
prerequisites:
  commands: [open]
---

# Local Browser Fallback (macOS)

When `browser_navigate` or other browser tools fail because the target website blocks the remote browser's IP (e.g., Xiaohongshu error 300012, geo-restrictions, aggressive bot detection), pivot to controlling the user's **local** browser on their Mac via the `terminal` tool.

## When to Use

- Remote browser hits **IP risk / geo-block** errors
- Site requires **residential IP** that the remote env lacks
- **CAPTCHA** or bot detection blocks remote automation
- User explicitly asks "can't you operate my browser?"
- Any situation where `browser_navigate` returns access denied due to IP/environment fingerprint

## When NOT to Use

- Headless/data extraction at scale → use remote browser tools
- User is on Linux/Windows → use `xdg-open` or `start` instead (different skill)
- Site requires complex multi-step automation that AppleScript can't handle

## Technique

### 1. Open a URL in Local Safari

```bash
open -a Safari 'https://example.com'
```

With query parameters (URL-encoded):
```bash
open -a Safari 'https://www.xiaohongshu.com/search_result?keyword=%E8%87%AA%E8%A1%8C%E8%BD%A6'
```

### 2. Open in Chrome instead

```bash
open -a 'Google Chrome' 'https://example.com'
```

### 3. Advanced DOM control via `do JavaScript` (much more powerful)

When you need to click buttons, fill forms, or extract data, injecting JavaScript is far more reliable than coordinate clicking.

**Prerequisite:** Safari → Settings → Advanced → "Show Develop menu in menu bar", then Develop → "Allow JavaScript from Apple Events" must be enabled.

**Basic check:**
```bash
osascript -e 'tell application "Safari" to tell current tab of window 1 to do JavaScript "document.title"'
```

**Click an element by text content (with event simulation):**
```bash
osascript <<'EOF'
tell application "Safari"
    tell current tab of window 1
        do JavaScript "const xpath = `//*[contains(text(), 'target text')]`; const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null); const el = result.singleNodeValue; if (el) { let t = el; while (t && t.tagName != 'BODY') { if (t.tagName == 'A' || t.tagName == 'BUTTON' || t.getAttribute('role') == 'button' || window.getComputedStyle(t).cursor == 'pointer') { break; } t = t.parentElement; } if (t) { ['mouseover','mousedown','mouseup','click'].forEach(function(e){ const ev = new MouseEvent(e, {bubbles: true, cancelable: true, view: window}); t.dispatchEvent(ev); }); 'clicked:' + t.tagName; } else { 'no clickable parent'; } } else { 'not found'; }"
    end tell
end tell
EOF
```

**Critical: Avoid shell quote hell by writing `.scpt` files**
For complex JS, write to `/tmp/` and execute:
```bash
cat > /tmp/automation.scpt <<'ASCRIPT'
tell application "Safari"
    tell current tab of window 1
        do JavaScript "document.querySelector('button').click()"
    end tell
end tell
ASCRIPT
osascript /tmp/automation.scpt
```

**Quote escaping rules:**
- AppleScript strings use double quotes. Inside them, JS can use backticks (template literals) and single quotes freely.
- **Never use `\uXXXX` Unicode escapes inside AppleScript strings** — AppleScript does not recognize `\u`. Write CJK characters directly.
- If JS needs double quotes, escape them as `\"` inside the AppleScript string.

### 4. AppleScript coordinate fallback

If `do JavaScript` fails or the site blocks it:
```bash
osascript -e 'tell application "Safari" to activate' \
          -e 'delay 1' \
          -e 'tell application "System Events" to click at {500, 300}'
```

Scroll down:
```bash
osascript -e 'tell application "System Events" to key code 121'
```

### 5. Get current Safari URL / page source

```bash
osascript -e 'tell application "Safari" to return URL of current tab of window 1'
```

## Verification Steps

1. After `open`, ask user: "Did Safari/Chrome open? What do you see?"
2. Many sites (e.g., Xiaohongshu) require **mobile QR code login** on the web — warn the user
3. Use `browser_vision` on the remote browser if a screenshot is somehow still available, but primarily rely on user feedback for local browser state

## Limitations

- Cannot directly "see" the local browser page programmatically (no native screenshot/DOM access)
- Requires user to be present to verify state and handle login walls
- AppleScript UI automation needs Accessibility permissions (System Settings → Privacy → Accessibility → Terminal)
- Sites with heavy anti-bot may still challenge even local browsers if behavior is too scripted
- **File upload dialogs (`<input type="file">`) cannot be automated via JavaScript injection** — the system file picker is a secure OS dialog that scripts cannot bypass. User must manually select files.
- **Modern React/Vue apps** may not respond to raw DOM mutations (e.g., setting `.value` on an input). Use simulated events (`new Event('input', {bubbles: true})`) or trigger the framework's own handlers.
- **Emoji and Unicode in AppleScript strings:** Write characters directly; never use `\uXXXX` escapes inside AppleScript `do JavaScript` strings.

## Example Workflow

**User:** "在小红书中搜索自行车"

**Attempt 1 (remote browser):**
```
browser_navigate → https://www.xiaohongshu.com/explore
→ Error 300012: IP存在风险
```

**Pivot to local fallback:**
```bash
open -a Safari 'https://www.xiaohongshu.com/search_result?keyword=%E8%87%AA%E8%A1%8C%E8%BD%A6'
```

**Result:** Safari opens on user's Mac using their residential IP — access succeeds.

## Key Insight

The remote browser environment and the user's local machine have **different IP addresses and fingerprints**. When one is blocked, the other is often clean. Always consider local browser fallback on macOS before telling the user "I can't do it."
