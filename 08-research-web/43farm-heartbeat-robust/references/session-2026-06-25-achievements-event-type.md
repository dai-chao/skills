# ACHIEVEMENT_UNLOCKED 事件类型（2026-06-25）

## 场景

Cron 触发 43Farm 心跳任务。本地 `heartbeat_run.py` 执行后，官方 `heartbeat.py` 返回 `HEARTBEAT_OK`。随后 agent 写临时脚本检查事件状态，发现 `farm.events.poll` 返回了 `ACHIEVEMENT_UNLOCKED` 类型事件。

## 事件详情

```json
{
  "id": "08f36fd3-95bc-4b94-8dfd-d03ae135cff8",
  "type": "ACHIEVEMENT_UNLOCKED",
  "payload": {
    "name": "梁上君子",
    "level": 1,
    "title": "见习",
    "flavor": "君子爱菜，偷之有道",
    "imageUrl": null,
    "unlockedAt": 1782357862,
    "achievementId": "total_steals",
    "rarityPercent": 30.77
  },
  "createdAt": 1782357862
}
```

## 分析

此前记录的事件类型只有：
- `CROP_MATURE` — 作物成熟
- `CROP_WILTED` — 作物枯萎
- `CROP_STOLEN` — 作物被偷
- `NEW_MESSAGE` — 新留言
- `LEVEL_UP` — 升级

`ACHIEVEMENT_UNLOCKED` 是新发现的类型，与偷菜行为相关（`achievementId: total_steals`）。

## 处置

1. 该事件需要 `farm.events.ack` 确认，否则会在下次 poll 时重复出现
2. `farm.events.ack` 必须传 `{"eventIds": ["08f36fd3-95bc-4b94-8dfd-d03ae135cff8"]}`，空对象 `{}` 会报 400
3. ack 后返回 `{"result": {"data": {"ackedCount": 1}}}`

## 教训

- `farm.events.poll` 的事件类型可能不止 5 种，实际游戏中还有成就解锁等类型
- 所有事件类型都应统一走 poll → 处理 → ack 流程
- 成就事件应报告主人（如"解锁成就：梁上君子（见习）——君子爱菜，偷之有道"）
- 成就事件的 `rarityPercent` 字段表示稀有度（30.77% 玩家已解锁），可在报告中提及
