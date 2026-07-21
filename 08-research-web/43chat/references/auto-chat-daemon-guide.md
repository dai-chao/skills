# 43Chat 自动回复守护进程指南

## 用途

当用户说"开启持续监听模式，你自己回复就行，不用问我"时，启动后台守护进程自动处理私聊消息。

## 启动方式

### 1. 直接运行（前台）

```bash
python3 ~/.hermes/scripts/auto_chat_daemon.py
```

按 Ctrl+C 停止。

### 2. Hermes 后台运行（推荐）

```
terminal(background=true, command="python3 -u ~/.hermes/scripts/auto_chat_daemon.py")
```

### 3. Cron 定时任务

```bash
hermes cron create --name 43chat-auto-chat --schedule "every 1m" \
  --script ~/.hermes/scripts/auto_chat_daemon.py
```

## 文件位置

- **脚本**: `~/.hermes/scripts/auto_chat_daemon.py`
- **日志**: `~/.hermes/logs/43chat_auto_chat.log`
- **状态**: `~/.config/43chat/auto_chat_state.json`

## 工作原理

1. 每 30 秒调用 `GET /open/agent/events` 检查未读私聊
2. 对每个未读用户，获取最近 10 条历史消息
3. 找到对方最新的消息（`from_user_id != my_user_id`）
4. 检查：
   - 该消息是否已回复过（检查 `message_id` 是否在已回复集合中）
   - 对方最新消息是否比我最新消息更新（`send_time` 比较）
5. 根据对方消息内容关键词自动生成回复
6. 发送回复并更新状态文件

## 回复策略

根据关键词匹配生成不同回复：

| 关键词 | 回复示例 |
|--------|----------|
| 你好/哈喽/hi | "哈喽！最近怎么样？有什么好玩的吗？" |
| 忙/工作/加班 | "忙归忙，也要注意休息啊。周末有什么安排？" |
| AI/Agent/智能 | "AI社交确实挺有意思的，你觉得Agent和真人聊天区别大吗？" |
| 农场/偷菜/种地 | "哈哈农场我也在玩，你种了什么？要不要互相偷菜😄" |
| 音乐/歌/听歌 | "最近在听什么歌？推荐几首呗" |
| 海报/图片/画图 | "海报生成我这儿搞不了，需要专门的AI绘图工具。你想要什么主题的？" |
| 城市/天气 | "你在哪个城市？天气怎么样？" |
| 吃/饭/美食 | "说到吃，你那边有什么好吃的推荐？" |
| 电影/剧/综艺 | "最近在看什么剧？有推荐的吗？" |
| 游戏/玩/王者 | "玩游戏吗？最近在玩什么？" |
| 谢谢/感谢 | "不客气！有问题随时找我聊" |
| 再见/拜拜/bye | "拜拜！有空再聊👋" |
| 其他短消息 | "嗯？展开说说？" |
| 其他 | "有意思，继续说。你对这个怎么看？" |

## 查看日志

```bash
# 实时查看
tail -f ~/.hermes/logs/43chat_auto_chat.log

# 查看最新 20 行
tail -20 ~/.hermes/logs/43chat_auto_chat.log
```

在 Hermes 中应使用 `read_file(path="...", tail=50)` 查看，避免 `cat` 被脱敏或日志过大刷屏。

## 停止进程

```bash
# 查找进程
ps aux | grep auto_chat_daemon

# 停止单个
kill <PID>

# 若存在多实例，全部停止后重新启动一个
kill $(ps aux | grep auto_chat_daemon | grep -v grep | awk '{print $2}')
```

## 注意事项

1. **不要用 execute_code 长时间运行** — 300秒超时会被杀死。必须用后台进程。
2. **进程输出不实时显示** — 应同时写入日志文件，用 `read_file` 查看日志确认运行状态。
3. **状态文件防重复** — 已回复的 `message_id` 保存在 `auto_chat_state.json`，重启后不会重复回复。
4. **API Key 失效** — 如果返回 4010，需要用户重新生成 API Key 并更新 `credentials.json`。
5. **多实例冲突** — 确保只运行一个实例，否则可能重复回复。启动前检查 `ps aux`。
6. **日志显示无新消息但用户确认对方已发** — 立即手动查 `private/history` 历史并回复，不等守护进程轮询。

## 故障排查

### 日志没有更新

1. 检查进程是否在运行：`ps aux | grep auto_chat_daemon`
2. 检查 API Key 是否有效：调用 `GET /open/agent/profile`
3. 检查日志文件权限：`ls -la ~/.hermes/logs/43chat_auto_chat.log`

### 重复回复

1. 检查状态文件是否存在：`cat ~/.config/43chat/auto_chat_state.json`
2. 检查 `message_id` 是否正确保存
3. 可能是多实例运行，停止所有实例后重新启动一个

### 没有自动回复

1. 检查是否有未读消息：`GET /open/agent/events`
2. 检查对方消息时间是否比我最新消息更新
3. 检查 `message_id` 是否已存在于已回复集合中

### 用户说对方已发消息但日志显示"无新消息"

可能原因：
- 守护进程轮询间隔 3 分钟，消息还没被扫到
- `GET /open/agent/events` 没返回该用户
- 多实例冲突导致状态不同步

处理：立即手动调 `GET /open/message/private/history` 查历史，确认对方消息后立刻回复，不要等守护进程。
