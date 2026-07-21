# Session 2026-06-23: heartbeat.py URL 构造 bug 修复实录

## 背景

Cron 触发的 43Farm 心跳任务执行时，`heartbeat.py` 脚本在 Token 过期后的自动恢复链路中失败。错误信息：

```
ERROR: authorize-app 失败 (attempt 1, code=unknown): Route POST:/trpc/https://43chat.cn/open/agent/authorize-app not found
```

## 根因分析

`heartbeat.py` 中的 `http_request()` 函数统一使用 `f"{API_BASE}/{path}"` 构造 URL：

```python
API_BASE = "https://farm.43chat.cn/trpc"

def http_request(path, ...):
    url = f"{API_BASE}/{path}"  # 问题所在
```

当 `reactivate()` 调用 `authorize-app` 时传入了绝对 URL：

```python
http_request_safe(
    "https://43chat.cn/open/agent/authorize-app",
    method="POST",
    ...
)
```

这导致构造出的 URL 为：
```
https://farm.43chat.cn/trpc/https://43chat.cn/open/agent/authorize-app
```

后端返回 404 `NOT_FOUND`。

## 修复方案

在 `http_request()` 中增加绝对 URL 检测：

```python
def http_request(path, method="GET", data=None, headers=None, token=None):
    # 支持绝对 URL（如 43chat authorize-app 端点）和相对路径
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    else:
        url = f"{API_BASE}/{path}"
    ...
```

当 `path` 以 `http://` 或 `https://` 开头时，直接使用该 URL，不再拼接 `API_BASE`。

## 修复后的执行流程

1. `heartbeat.py` 被调用
2. 检测到 `lastMessageCheck` 已到期（53 分钟 > 30 分钟阈值）
3. `ensure_valid_token()` 发现 Farm Token 过期
4. `reactivate()` 尝试自动恢复：
   - `authorize-app` → 获取 App Token（修复后正常）
   - `farm.activate` → 获取新 Farm Token
5. 但 `load_chat43_key()` 发现 `api_key` 被服务器端掩码为 `***`
6. 脚本输出 `HEARTBEAT_BLOCKED` 并报告主人

## 状态文件策略

脚本在 `HEARTBEAT_BLOCKED` 场景下**不更新 `lastMessageCheck` 和 `lastVersionCheck`**，保留旧值以便下次 cron 重试。一旦主人修复 API Key，心跳立即恢复。

## 验证

修复后脚本可正确通过 `authorize-app` 获取 App Token（假设 API Key 有效）。本次执行因 API Key 被掩码而阻塞在更深层，但 URL 构造 bug 已消除。

## 关联文件

- `~/.hermes/skills/43farm/scripts/heartbeat.py` — 修复后的脚本
- `~/.config/43farm/state.json` — 状态文件（未被更新）
- `~/.config/43chat/credentials.json` — 包含 `claim_url` 供主人手动认领
