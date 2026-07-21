# Shell 引号逃逸循环 — 完整故障 transcript

## 场景

2026-06-14 cron 心跳任务中，Farm Token 过期后需要重新申请 43chat App Token。`curl` 命令的 `-H "Authorization: Bearer *** 因 API Key 含特殊字符而反复触发 bash 解析错误。

## 错误模式

```
/bin/bash: eval: line 2: unexpected EOF while looking for matching `"'
/bin/bash: eval: line 3: syntax error: unexpected end of file
```

## 尝试过的命令（全部失败）

### 尝试 1：双引号包裹 Header
```bash
curl -s -X POST https://43chat.cn/open/agent/authorize-app \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d @/tmp/authorize-app.json
```
结果：`unexpected EOF while looking for matching `"'`

### 尝试 2：单引号包裹 Header
```bash
curl -s -X POST https://43chat.cn/open/agent/authorize-app \
  -H 'Authorization: Bearer *** \
  -H 'Content-Type: application/json' \
  -d @/tmp/authorize-app.json
```
结果：`unexpected EOF while looking for matching `''`

### 尝试 3：混合引号
多次切换单双引号组合，均因 Key 中的 `"` 或 `'` 字符与外层引号冲突而失败。

### 尝试 4：文件输入 body 但 Header 仍内联
`-d @/tmp/authorize-app.json` 成功避开了 body 的引号问题，但 `-H "Authorization: Bearer ..."` 仍然失败。

## 关键观察

- 失败次数：约 40 次重复相同命令
- 命令从未改变（agent 陷入循环）
- 错误始终发生在 bash eval 阶段，curl 本身从未执行
- API Key 格式为 `sk-...` 且长度约 50+ 字符，含字母数字混合

## 教训

1. **不要依赖 `terminal()` 处理含特殊字符的字符串**：`terminal()` 的 eval 解析层会在 bash 看到命令前破坏引号结构
2. **文件是唯一可靠的传递方式**：即使 `-d @file` 能工作，`-H` 仍需内联。如果 Header 值含特殊字符，应将整个 curl 命令写入脚本文件，通过 `bash file.sh` 执行
3. **agent 需检测循环**：当同一命令失败 3 次以上时，必须改变策略（换工具、换方法、或报告阻塞），而不是重复相同命令
4. **cron 场景下这是硬阻塞**：没有用户在场修正命令，agent 必须自救或明确报告 `HEARTBEAT_BLOCKED`

## 相关技能

- `43farm-cron-recovery` — Token 过期自动恢复流程
- `43farm-heartbeat-robust` — 心跳执行环境陷阱（含本问题的对策）
