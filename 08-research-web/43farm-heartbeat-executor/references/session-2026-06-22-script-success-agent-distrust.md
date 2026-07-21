# Session 2026-06-22: Script Succeeded but Agent Did Manual Follow-up

## Context
Cron-triggered 43Farm heartbeat. Agent had `43farm-heartbeat-executor` skill loaded but still performed manual checks before and after calling the script.

## Sequence of Events

### Phase 1: Agent Did Manual Checks Before Script (Wrong)
1. Created todo list
2. `read_file` ~/.config/43farm/credentials.json
3. `read_file` ~/.config/43farm/state.json
4. `terminal` `date +%s` + `echo` calculations to check time diffs
   - Message diff: 1996s (> 1800, due)
   - Version diff: 3323s (< 7200, NOT due)

**This is the exact anti-pattern the skill warns against.** The skill explicitly says:
> "在读取任何文件、计算任何时间差、调用任何 API 之前，先检查并执行脚本"
> "不要先读取 credentials.json 检查 token 是否过期"

### Phase 2: Script Called and Auto-recovered Token (Correct)
```bash
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py
```

Output (first run, exit code 1):
```
DEBUG: 空闲地块数 9, 金币 1721, 等级 27
DEBUG: 最优作物 pomegranate 价格 2425
被偷菜：XX 偷走了地块 8 的 corn x2
作物成熟：地块 8 的 corn
收获 1 块地：18 corn，+80 XP
卖出仓库作物，获得 504 金币
金币不足，无法种植 pomegranate（需要 2425，只有 1721）
从 一鱼 偷了：orange x3, orange x3, orange x3
从 加勒比德柱 偷了：orange x3, orange x3, orange x3, orange x3, orange x3, orange x3, orange x3, orange x3, orange x3, orange x3, orange x3, orange x3
```

Key observations:
- Farm Token was expired (earlier `farm.status` call returned 401)
- Script auto-recovered the token internally (via `auth.refreshToken` → `farm.activate`)
- Script completed all farm participation: harvest, sell, steal, events
- Script updated `lastMessageCheck` in state.json
- Exit code 1 indicates "有报告内容需要主人关注"

Second run with `2>&1`:
```
HEARTBEAT_OK
```

### Phase 3: Agent Manually Did Version Detection (Wrong)
After script succeeded, agent:
1. Read state.json again to verify `lastVersionCheck` was still old
2. Calculated version diff again: 3323s (< 7200)
3. **Incorrectly decided to manually run version detection anyway**
4. Downloaded remote skill.json, compared with local (both 1.1.0)
5. Manually updated `lastVersionCheck` in state.json

**Why this was wrong:**
- Version diff was 3323s, which is LESS than 7200 threshold
- Script correctly determined version check was NOT due and skipped it
- Agent's manual update unnecessarily advanced `lastVersionCheck`
- This wastes iteration and may interfere with normal check intervals

## Root Causes of Agent Misbehavior

1. **Inertia trap**: Agent's default behavior is to "read state first, then diagnose, then act"
   - The skill's "call script first" instruction was not strong enough to override this instinct
   - Agent created todo list and started reading files before remembering the script

2. **Distrust of script**: After script ran successfully, agent didn't trust it had handled everything
   - Agent re-read state.json to "verify" the script's work
   - Agent manually ran version detection even though script had correctly skipped it

3. **Misreading of time diff**: Agent saw `lastVersionCheck` was old and assumed it needed updating
   - Did not correctly compare 3323s against 7200s threshold
   - Was influenced by the fact that `lastMessageCheck` WAS updated (making it seem like "something should happen")

## Correct Behavior

```bash
# Step 1: Call script immediately (no file reads, no calculations)
python3 ~/.hermes/skills/43farm/scripts/heartbeat.py 2>&1

# Step 2: Interpret output
# - If HEARTBEAT_OK → done
# - If report content → report to owner, done
# - If HEARTBEAT_BLOCKED or SCRIPT_NOT_FOUND → load 43farm-cron-recovery

# Step 3: Nothing else. Do not verify, do not re-check, do not manually update state.
```

## Key Takeaway

**When the script exists and runs, it is the single source of truth.**

- The script handles: token validation, auto-recovery, time diff calculation, farm participation, version detection, state updates
- The agent's role is: call the script, interpret its output, report to owner
- The agent should NOT: read files first, calculate time diffs manually, verify script's work, do manual follow-up

**Trust the script. If it returns `HEARTBEAT_OK` or a report, the job is done.**
