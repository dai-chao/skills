# XSS Payload Bank and React Guidance

Use these payloads wherever user input is displayed, reflected, or rendered as HTML/URL.

## Basic payloads

```html
<script>alert('xss')</script>
<script>alert(document.cookie)</script>
<img src=x onerror=alert('xss')>
<img src=x onerror=alert(document.cookie)>
<svg onload=alert('xss')>
<body onload=alert('xss')>
<input onfocus=alert('xss') autofocus>
<iframe src="javascript:alert('xss')"></iframe>
"onclick="alert('xss')
'onclick='alert("xss")
"><script>alert(1)</script>
'><script>alert(1)</script>
```

## Encoded / evasion payloads

```html
&lt;script&gt;alert('xss')&lt;/script&gt;
<scr%69pt>alert('xss')</scr%69pt>
&#60;&#115;&#99;&#114;&#105;&#112;&#116;&#62;alert('xss')&#60;/&#115;&#99;&#114;&#105;&#112;&#116;&#62;
\u003cscript\u003ealert('xss')\u003c/script\u003e
<svg/onload=alert('xss')>
<img src="x" onerror="alert('xss')">
<a href="javascript:alert('xss')">click</a>
<a href="&#106;&#97;&#118;&#97;&#115;&#99;&#114;&#105;&#112;&#116;:alert('xss')">click</a>
```

## Common injection contexts

| Context | Payload | Notes |
|---------|---------|-------|
| HTML element content | `<script>alert(1)</script>` | Escaped by React JSX |
| HTML attribute | `"onclick="alert(1)` | Quote attribute values and escape |
| URL / href | `javascript:alert(1)` | Validate URL scheme |
| JavaScript string | `';alert(1);//` | Escape for JS context |
| CSS style | `</style><script>alert(1)</script>` | Avoid user data in style |

## React-specific rules

### Safe by default

```jsx
// Safe: React escapes the value
<p>{userInput}</p>
```

### Dangerous if not sanitized

```jsx
// NEVER do this with raw user input
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

Use DOMPurify:

```bash
npm install dompurify
```

```jsx
import DOMPurify from 'dompurify';

function RichText({ html }) {
    const safe = DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'a'],
        ALLOWED_ATTR: ['href'],
    });
    return <div dangerouslySetInnerHTML={{ __html: safe }} />;
}
```

### URL validation

```jsx
function SafeLink({ href, children }) {
    try {
        const url = new URL(href, window.location.origin);
        if (url.protocol !== 'http:' && url.protocol !== 'https:') {
            return <span>{children}</span>;
        }
        return <a href={href}>{children}</a>;
    } catch {
        return <span>{children}</span>;
    }
}
```

### Forbidden patterns

```javascript
// Never use these with user input
eval(userInput);
new Function(userInput);
setTimeout(userInput, 1000);
setInterval(userInput, 1000);
element.innerHTML = userInput;
```

## Go backend sanitization (optional)

If you must store rich text on the server, sanitize before storing or returning:

```go
import "github.com/microcosm-cc/bluemonday"

p := bluemonday.UGCPolicy()
safeHTML := p.Sanitize(userInput)
```

## Testing checklist

- [ ] Username displayed in a list/card
- [ ] Search keyword echoed on results page
- [ ] Error message includes user input
- [ ] Profile page shows nickname/bio
- [ ] URL parameters reflected in the page
- [ ] File names and metadata displayed
- [ ] Admin audit logs rendered in UI
- [ ] Email/notification templates with user content
