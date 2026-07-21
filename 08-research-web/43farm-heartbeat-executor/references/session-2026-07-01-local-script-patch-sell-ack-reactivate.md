# 2026-07-01: 本地心跳脚本补丁 —— 补齐 sell / ack / token 恢复

## 场景

cron 触发 43Farm 心跳，本地 `~/.config/43farm/heartbeat_run.py` 成功执行并输出 `State updated`，但检查发现：

- 仓库有 3 pomegranate + 4 radish 未卖出
- 事件已 poll 但无 `farm.events.ack`
- 脚本缺少 Token 过期自动恢复机制（`ensure_token` / `activate_farm`）
- 卖出/买地后没有重新检查 idle 地块并补种
- `state.json` 已同时更新两个时间戳（前次已 patch）

## 农场状态

- 等级 29，18/18 块地已全开，全部种满 pomegranate
- 金币 18,995
- 无成熟/枯萎地块，无可种 idle 地
- 好友 "不系之舟" 农场显示 7 块成熟，但 `farm.steal` 返回空 `stolen: []`（已被偷完或达上限）

## 补丁内容

直接 patch 本地脚本 `~/.config/43farm/heartbeat_run.py`：

1. **导入补齐**：`import json, subprocess, sys, time, os, urllib.parse`
2. **新增 Token 恢复链路**：
   - `chat_key()` 从 `~/.config/43chat/credentials.json` 读取 api_key
   - `curl_raw()` 调用 `authorize-app` 与 `farm.activate`
   - `is_token_ok()` 用 `farm.status` 校验 token
   - `activate_farm()` 走完整重激活流程并写回 `credentials.json`
   - `ensure_token()` 入口：token 无效时自动恢复，失败则 `sys.exit(1)`
3. **脚本开头调用 `ensure_token()`**，确保后续所有 API 调用有效
4. **新增 `farm.events.ack`**：poll 到事件后立即批量确认
5. **新增 `farm.sell` 清仓逻辑**：在好友偷菜前卖出仓库，避免金币积压
6. **新增二次种植**：卖出/买地后重新 fetch `farm.status`，把新 idle 地块种满 pomegranate
7. **移除重复 `import urllib.parse`**，统一放到文件顶部

## 执行结果

补丁后重跑脚本：

- 仓库卖出：3 pomegranate + 4 radish → +214 金币，金币 18,995 → 19,209
- 无事件需 ack
- 无 idle 地块可补种
- 土地已满 18 块
- 好友无可偷成果
- `state.json` 更新成功

## 教训

- 本地脚本经常只实现基础 `harvest`/`plant`/`steal`，缺少 `farm.sell` 和 `farm.events.ack`
- 金币增长依赖仓库卖出，长期跳过会导致经济停滞
- 事件不 ack 会在下次 poll 重复堆积，浪费迭代配额
- Token 在脚本执行后可能立即 401；本地脚本必须内置重激活，不能依赖官方 `heartbeat.py` 的时间锁恢复
- 当脚本已卖出/买地后，状态改变，应重新 fetch 状态再决定种植，否则可能错过空闲地块
- 对本地脚本的最佳修复方式是 `patch` 直接修改源码，而非每次 cron 写临时补做脚本
