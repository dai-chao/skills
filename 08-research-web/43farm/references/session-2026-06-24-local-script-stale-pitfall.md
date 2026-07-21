# 本地 heartbeat.py 副本过时陷阱（2026-06-24）

## 现象

Cron 触发 43Farm 心跳任务时，agent 发现 `~/.config/43farm/heartbeat.py`（本地副本）存在，但执行后返回 `HTTP Error 405: Method Not Allowed`。这是因为本地副本将 `farm.events.poll` 等 Query 端点误用 POST 调用，且缺少 token 自动恢复逻辑。

## 根因

用户可能在早期安装时把 heartbeat.py 复制到了 `~/.config/43farm/`，之后 skill 官方脚本在 `~/.hermes/skills/43farm/scripts/heartbeat.py` 持续更新，但本地副本从未同步。

## 教训

1. **永远优先执行 skill 官方脚本**：`python3 ~/.hermes/skills/43farm/scripts/heartbeat.py`
2. **不要执行 `~/.config/43farm/heartbeat.py`**，除非明确知道它是 skill 脚本的软链接或最新副本
3. 如果 `~/.config/43farm/` 目录下有 `heartbeat.py`、`check_farm.sh` 等文件，它们可能是早期遗留物，不应作为 cron 执行入口

## 正确调用顺序

```bash
# 第一动作：执行 skill 官方脚本（合并 stderr 到 stdout）
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py 2>&1

# 如果脚本不存在（极少见），再回退到手动 curl 或检查 skill 安装状态
```
