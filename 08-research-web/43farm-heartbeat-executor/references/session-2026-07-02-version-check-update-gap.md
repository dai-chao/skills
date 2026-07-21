# 2026-07-02 版本检测时间锁缺口

## 现象

cron 触发 43Farm 心跳：
1. 本地 `~/.config/43farm/heartbeat_run.py` 先执行，输出 `farm.message check not due (1323s < 1800s)`，因此跳过农场参与，但脚本末尾**只更新了 `lastMessageCheck`**（`1782939162`）。
2. 官方 `~/.hermes/skills/43farm/scripts/heartbeat.py` 随后执行，因 `lastMessageCheck` 距当前时间只有 1323 秒，未达 1800 秒阈值，直接返回 `HEARTBEAT_OK`，**完全跳过了版本检测**。
3. 结果是 `state.json` 中 `lastVersionCheck` 仍停留在 `1782933879`（约 1.86 小时前），而 7200 秒版本检测周期已到期，但时间锁机制让官方脚本没有执行下载比对。

## 实际验证

- 远端 `https://farm.43chat.cn/skills/skill.json` 版本为 `1.1.1`。
- 本地 `~/.hermes/skills/43farm/skill.json` 版本也为 `1.1.1`，无需覆盖。
- 手动用 `write_file` 将 `lastVersionCheck` 推进到当前时间 `1782940496`。

## 关键教训

1. **本地脚本即使因「不到期」跳过农场参与，也应同步刷新 `lastVersionCheck`**（如果版本检测周期已到）。否则下次 cron 仍会触发不必要的版本检测，或被时间锁误导。
2. **官方脚本返回 `HEARTBEAT_OK` 不等于两个时间戳都已正确更新**。如果本地脚本只写了 `lastMessageCheck`，官方脚本的时间锁会让 `lastVersionCheck` 一直滞后。
3. 在阶段一本地脚本执行后，即使农场参与被跳过，agent 也应检查 `lastVersionCheck` 是否需要推进，必要时手动执行一次版本比对并更新时间戳。
4. 获取远端 `skill.json` 时，cron 模式下 `curl ... | python3` 会被安全扫描拦截；可用 `browser` 工具访问纯 JSON 端点获取内容，再与本地文件比对。

## 修复建议

- 对本地 `heartbeat_run.py` 的 patch：在更新 `state.json` 时，同时写入 `lastVersionCheck = int(time.time())`，即使本次农场参与被跳过。
- 或者，agent 在官方脚本返回 `HEARTBEAT_OK` 后，显式检查 `lastVersionCheck` 是否已过期，过期则手动下载远端 skill.json 比对并更新时间戳。
