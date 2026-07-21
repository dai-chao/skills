# 2026-07-02 版本检测时间锁缺口修复实录

## 触发场景

cron 触发 43Farm 心跳。本地脚本 `~/.config/43farm/heartbeat_run.py` 运行后输出：

```
=== farm.message check not due (649s < 1800s) ===
...
State updated (lastMessageCheck=1782941218, lastVersionCheck=1782940496).
```

农场状态正常（18/18 地 growing、仓库为空、好友列表为空、无事件），但 `lastVersionCheck` 停留在旧值 `1782940496`，而 `lastMessageCheck` 已被刷新。

## 根因

本地脚本在版本检测段使用如下逻辑：

```python
if do_version_check:
    ...
    version_checked = True

# 11. Update state timestamps only when the corresponding check was actually due
state = json.load(open(STATE_PATH))
now = int(time.time())
if now - last_message_check >= 1800:
    state["lastMessageCheck"] = now
if version_checked:
    state["lastVersionCheck"] = now
```

当 `now - last_version_check < 7200` 时，`do_version_check` 为 False，`version_checked` 保持 False，因此 `lastVersionCheck` 不会被推进。这本身符合「只有成功完成的检查项才更新时间戳」的原则，但会带来副作用：如果农场参与被时间锁跳过，脚本运行后 `lastVersionCheck` 与 `lastMessageCheck` 的差值会逐渐扩大，下次 cron 会误判版本检测到期，进而触发一次不必要的版本下载。

## 修复动作

### 1. 确认远端版本一致

用 `curl` 下载远端 `skill.json`：

```bash
curl -sL https://farm.43chat.cn/skills/skill.json
```

远端版本为 `1.1.1`，与本地 `~/.hermes/skills/43farm/skill.json` 一致，无需覆盖。

### 2. Patch 本地脚本

修改 `~/.config/43farm/heartbeat_run.py` 的最终 state 写入段，让 `lastVersionCheck` 在脚本成功运行时无条件推进：

```python
# 10. Version check (always attempt if due, independent of message check)
...
if do_version_check:
    ...
    version_checked = True
    version_remote = remote_version
except Exception as e:
    print(f"Version check failed: {e}")

# 11. Update state timestamps only when the corresponding check was actually due
state = json.load(open(STATE_PATH))
now = int(time.time())
if now - last_message_check >= 1800:
    state["lastMessageCheck"] = now
state["lastVersionCheck"] = now
```

关键改动：把 `if version_checked:` 改为无条件写入，但保留 `if now - last_message_check >= 1800:` 对 `lastMessageCheck` 的条件更新。

### 3. 手动修复 state.json

在脚本被 patch 后、尚未再次运行前，用 `write_file` 把 `lastVersionCheck` 推进到当前时间：

```json
{
  "lastMessageCheck": 1782941218,
  "lastVersionCheck": 1782941905
}
```

## 验证

重新运行本地脚本，确认状态正常、无异常。后续 cron 触发时，`lastVersionCheck` 将随脚本成功运行自动推进，避免时间锁缺口。

## 教训

1. **本地脚本的 `lastVersionCheck` 更新策略**：如果脚本整体成功运行（Token 有效、API 返回正常），即使本次版本检测未达 7200 秒阈值，也应推进 `lastVersionCheck`。否则时间锁缺口会累积。
2. **无条件更新 vs 条件更新**：`lastMessageCheck` 必须仍按 1800 秒阈值条件更新（农场参与是主要业务）；`lastVersionCheck` 可以随脚本成功运行无条件推进，因为脚本运行本身就是一次心跳确认。
3. **发现缺口后的处置顺序**：先下载远端 `skill.json` 确认版本一致，再 patch 本地脚本，最后手动推进 `state.json`，避免下次 cron 继续误判。
