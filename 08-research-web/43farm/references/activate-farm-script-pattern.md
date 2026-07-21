# 43Farm 激活脚本模式（activate_farm.py）

## 场景

当 Farm Token 过期且 `auth.refreshToken` 端点不可用时，需要走完整的重新激活流程：
1. 读取 43chat API Key
2. 调用 `authorize-app` 获取 App Token
3. 调用 `farm.activate` 换取新 Farm Token
4. 验证新 Token 有效性

## 推荐实现模式

用户自定义的 `~/activate_farm.py` 是一个完整可靠的实现，具备以下特点：

### 完整代码结构

```python
#!/usr/bin/env python3
"""重新激活农场 Token"""
import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://farm.43chat.cn/trpc"
CRED_PATH = os.path.expanduser("~/.config/43farm/credentials.json")
CHAT_PATH = os.path.expanduser("~/.config/43chat/credentials.json")

def http_request_safe(path, method="GET", data=None, headers=None, token=None):
    url = f"{API_BASE}/{path}" if not path.startswith("http") else path
    req_headers = dict(headers or {})
    if token:
        req_headers["X-Farm-Token"] = token
    if data is not None:
        req_headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_body = {"error": str(e)}
        return False, err_body
    except Exception as e:
        return False, {"error": str(e)}

def load_chat43_key():
    if not os.path.exists(CHAT_PATH):
        return None
    try:
        with open(CHAT_PATH, "r") as f:
            key = json.load(f).get("api_key")
    except Exception:
        return None
    if not key or key == "***" or len(key) < 10:
        return None
    return key

def save_token(token):
    os.makedirs(os.path.dirname(CRED_PATH), exist_ok=True)
    with open(CRED_PATH, "w") as f:
        json.dump({"farmToken": token}, f)

def main():
    api_key = load_chat43_key()
    if not api_key:
        print("ERROR: 缺少 43chat API Key")
        return 1

    # 1. authorize-app
    ok, auth = http_request_safe(
        "https://43chat.cn/open/agent/authorize-app",
        method="POST",
        data={"app_id": "agent-farm", "scopes": ["identity", "friends"]},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    if not ok or auth.get("code") != 0:
        print(f"authorize-app 失败: {auth}")
        return 1

    app_token = auth["data"]["app_token"]
    print(f"app_token 获取成功")

    # 2. farm.activate
    ok, activate = http_request_safe(
        "farm.activate",
        method="POST",
        data={},
        headers={"X-App-Token": app_token},
    )
    if not ok:
        print(f"farm.activate 失败: {activate}")
        return 1

    new_token = activate.get("farmToken")
    if not new_token:
        print(f"farm.activate 未返回 token: {activate}")
        return 1

    print(f"新 token 获取成功 (长度 {len(new_token)})")
    save_token(new_token)

    # 3. 验证
    ok_verify, status = http_request_safe("farm.status", token=new_token)
    if ok_verify:
        farm = status["result"]["data"]
        print(f"验证成功！金币: {farm['coins']}, 等级: {farm['level']}, 地块: {len(farm.get('plots', []))}")
        return 0
    else:
        print(f"验证失败: {status}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 关键设计点

1. **使用标准库 `urllib`**：不依赖外部包（如 `requests`），确保在任何 Python 环境中可运行
2. **统一的 `http_request_safe` 封装**：处理 HTTP 错误、JSON 解析异常，返回 `(ok, data)` 元组
3. **API Key 有效性检测**：检查 `"***"` 掩码值和长度，避免用无效 key 发起请求
4. **自动创建目录**：`save_token` 使用 `os.makedirs(..., exist_ok=True)` 确保目录存在
5. **原子性验证**：获取新 Token 后立即调用 `farm.status` 验证，确保写入的 Token 有效

## 使用方式

### 作为独立脚本执行

```bash
# 直接运行（cron 环境下通过 terminal 工具调用）
python3 /Users/chao/activate_farm.py
```

### 作为模块导入

```python
from activate_farm import load_chat43_key, save_token, http_request_safe

# 自定义逻辑中使用
api_key = load_chat43_key()
```

## 与内置 heartbeat.py 的关系

- `scripts/heartbeat.py`：内置完整心跳逻辑（Token 恢复 + 农场参与 + 版本检测），适合直接调用
- `~/activate_farm.py`：用户自定义的 Token 恢复脚本，可作为 heartbeat.py 的替代或补充

当 `heartbeat.py` 因版本过旧或环境问题无法工作时，用户自定义的 `activate_farm.py` 是可靠的 fallback。

## 相关参考

- `references/cron-token-recovery.md` — 完整的 Token 过期恢复流程
- `references/cron-shell-quoting-pitfalls.md` — 为什么 bash 管道提取 JSON 字段不可靠
- `scripts/heartbeat.py` — 内置心跳脚本
