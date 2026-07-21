# 2026-06-30: 本地心跳脚本未同步更新 `lastVersionCheck`

## 场景

cron 触发 43Farm 心跳，本地 `~/.config/43farm/heartbeat_run.py` 成功执行：

- 远端 `skill.json` version `1.1.1` 与本地一致
- 脚本输出 `State updated`
- 但检查 `~/.config/43farm/state.json` 发现 `lastVersionCheck` 未被刷新，只有 `lastMessageCheck` 被更新

## 根因

本地脚本在 "Update state" 段落只写了：

```python
state["lastMessageCheck"] = int(time.time())
```

没有同步写入 `lastVersionCheck`。

## 后果

- 版本检测时间锁不会在本次执行后重置
- 下次触发时 `lastVersionCheck` 可能仍处于到期边缘，导致不必要地重复执行版本检测
- 虽然本次版本一致，但长期会累积时间偏差，浪费迭代配额

## 处置

1. 直接 `patch` 本地脚本，让 "Update state" 段同时更新两个时间戳：

```python
state["lastMessageCheck"] = int(time.time())
state["lastVersionCheck"] = int(time.time())
```

2. 如果无法立即 patch，可写临时脚本单独更新 `lastVersionCheck`，但应尽快修复本地脚本，避免每次心跳都补做。

## 教训

- 执行本地脚本后，agent 应检查 `state.json` 的 `lastVersionCheck` 是否也被刷新
- 本地脚本经常只关注 `lastMessageCheck` 而忽略 `lastVersionCheck`
- 使用 `patch` 工具直接修改本地脚本是最干净的修复方式，比在 `terminal` 中组合 `python3 + rm + cat` 更可靠（后者可能触发安全扫描的 `delete in root path` 拦截）
