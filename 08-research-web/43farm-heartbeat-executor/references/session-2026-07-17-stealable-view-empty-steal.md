# 2026-07-17 43Farm 心跳会话 — `farm.view` 显示可偷但 `farm.steal` 返回空

## 会话概要

- 触发方式：cron 心跳任务
- 执行脚本：`~/.config/43farm/heartbeat_run.py`
- 结果：脚本成功完成全部流程，农场状态正常，最终输出 `State updated (...)`（无 `HEARTBEAT_OK` 字符串，但业务正常）

## 观察到的正常现象

好友农场巡查中，脚本对好友 `12366677` 的 `farm.view` 显示 `Found 18 stealable plots!`，但随后调用 `farm.steal` 返回：

```json
{
  "result": {
    "data": {
      "stolen": []
    }
  }
}
```

**原因**：`farm.view` 的 `mature` 状态只表示地块已成熟，但 `farm.steal` 会再次检查可偷条件（如该地块已被其他好友偷完、或 `stealCount` 已达上限）。返回空数组是正常行为，不是错误，也不需要重试。

## 处置结论

- 不要因此对同一好友重复调用 `farm.steal`
- 脚本已自动继续检查下一位好友
- 最终报告时无需将“可偷但为空”列为异常事件
