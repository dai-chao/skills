# 脚本输出重定向 — cron 场景下捕获完整报告

## 现象

2026-06-23 心跳执行期间观察到：

1. `heartbeat.py` 将 DEBUG 信息（如 `DEBUG: 空闲地块数 0, 金币 29, 等级 27`）写入 **stderr**
2. 将报告内容（如 `收获 21 banana，+170 XP`、`从 X 偷了 pomegranate`）写入 **stdout**
3. 在 cron 无人值守场景下，agent 若只捕获 stdout，会丢失 DEBUG 上下文和完整事件列表

## 根因

脚本使用 `print(..., file=sys.stderr)` 输出 DEBUG，`print(...)` 输出报告。这是正常设计，但 cron 调用方需要合并两个流。

## 推荐调用方式

```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py 2>&1
```

或使用 `subprocess.run(..., capture_output=True)` 后合并 `stdout` 和 `stderr`。

## 反模式

```bash
# 错误：只捕获 stdout，丢失 DEBUG 和事件详情
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py > /tmp/hb.out

# 错误：分开捕获后只读取 stdout
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py > /tmp/hb.out 2> /tmp/hb.err
```

## 影响

- 合并输出后，agent 可以看到完整的事件列表（被偷、成熟、收获、偷菜）
- 合并输出后，agent 可以看到 DEBUG 信息（金币、等级、空闲地块数）
- 合并输出是生成完整报告给主人的前提
