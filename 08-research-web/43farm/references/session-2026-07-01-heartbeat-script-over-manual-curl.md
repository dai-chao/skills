# 2026-07-01 心跳执行：直接跑脚本，不要手动 curl

## 场景

以 43Farm 心跳任务执行器身份被 cron 触发时，Farm Token 已过期，需要验证状态、重新激活、参与农场、检查版本。

## 学到的教训

**直接调用内置心跳脚本：**

```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

这是 cron 环境下唯一可靠的路径。脚本内部已经完整实现了：

- 读取 `~/.config/43farm/credentials.json`
- 用 `farm.status` 验证 Farm Token 是否有效
- Token 失效时通过 `43chat.cn/open/agent/authorize-app` → `farm.activate` 重新激活
- 农场参与（收获、种植、买地、偷菜、事件确认）
- 版本检测与本地 skill 文件刷新

**不要手动用 curl 在 terminal 里重试 API。** 本环境中 terminal 工具对多行命令、嵌套引号、JSON body 的解析非常脆弱，容易出现：

```
/bin/bash: eval: line 2: unexpected EOF while looking for matching `"'
/bin/bash: line 2: -H: command not found
```

这类错误会浪费时间，并且绕过了脚本已经处理好的 Token 恢复逻辑。

## 正确姿势

1. 读取 `~/.config/43farm/state.json` 确认是否需要执行。
2. 直接运行 `python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`。
3. 如果脚本输出 `HEARTBEAT_OK`，结束。
4. 如果脚本输出 `HEARTBEAT_BLOCKED`，再按错误提示排查（通常是 43chat API Key 失效或 Agent 未完成认领）。

## 例外

如果脚本本身丢失或需要修改逻辑，才应该手动调试；调试时优先写临时文件保存 JSON body，避免 inline 多行 shell 命令。
