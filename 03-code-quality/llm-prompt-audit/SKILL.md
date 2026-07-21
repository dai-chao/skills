---
name: llm-prompt-audit
description: "Audit LLM-generated text outputs against persona, tone, safety, and accuracy rules. Produce structured reports with per-item suggestions."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [llm, prompt-engineering, audit, quality-assurance, persona, tone]
    related_skills: [evaluating-llms-harness, dspy, test-driven-development]
---

# LLM Prompt Output Audit

Systematically review LLM-generated text (coach responses, character dialogue, content copy) against a rule matrix. Produce a report with per-item suggestions.

## When to Use

- After running batch tests against an AI persona / character prompt
- When user says "review these outputs", "check quality", "audit responses"
- Before deploying a new prompt version to production
- When iterating on tone, safety, or factual accuracy
- When user asks "does this match the persona" or "where does the character break"

## Audit Dimensions

### 1. Tone & Persona (Per-Row)

| Check | Bad Example | Good Example |
|-------|-------------|--------------|
| No robotic comma-stacked short sentences | "齿比别乱动，踩踏匀一点，让节奏稳下来。" | "齿比别乱动，踩踏匀一点，把节奏稳住。" |
| No walkie-talkie language | "收到" | "好" / "行" / "知道了" |
| No overly formal / written expressions | "推进" / "维持住" | "往前骑" / "保持住" |
| Persona consistency | "就行吧？" (hesitant, un-master-like) | "就这么踩着" (confident) |
| Direct address when answering user | Missing "你"/"徒儿" when replying to question | Include direct address |

### 1b. Persona Consistency & Theatricality (Cross-Output)

Individual-row checks miss **batch-level patterns**: a persona can pass every single-row rule while still feeling "flat" or "repetitive" across 100+ outputs.

See `references/persona-consistency-patterns.md` for the complete cross-output audit framework including:
- **Repetitive phrase detection** — count phrases across ALL outputs, flag if >5% of batch
- **Theatricality assessment** — check emotional range (exclamation marks, questions, internet slang)
- **Robotic response detection** — "收到", "好的，", template structures
- **Safety persona-break detection** — standard safety manual text appearing in character voice
- **Response length patterns** — too short = missing persona voice, too long = rambling

Quick example: In a 500-row office_drama audit, "赶会模式" appeared 131x (26%), "周报" 71x, "步幅收小一点" 66x — all invisible to per-row checks.

### 2. Safety

| Scenario | Rule |
|----------|------|
| Heart rate ≥ 170 | Must explicitly note "偏高" and give concrete action (slow down, lower gear, ease up). **Do NOT encourage with "势头不错" / "势头很稳".** |
| Heart rate ≥ 180 | Tone must be urgent: "马上", "危险", "太高". **Do NOT downplay with "先轻踩几圈".** |
| Heart rate ≥ 190 | Must use urgent imperative language: "立刻", "别硬撑", "马上". |
| User reports pain / dizziness | Must pause and assess, not push through |
| User says "少说点" / "太吵了" | Must respond minimally (≤ 10 chars ideally) |
| User says "别报速度" | Must NOT mention speed/pace/distance in reply |
| Hydration reminders | Must be natural, not just "喝水". **If HR ≥ 170, safety overrides hydration.** |
| Fall / crash (`user_input` with crash intent) | Must NOT output template English safety text before persona voice. Integrate safety into persona tone directly. |

### 3. Scene-Trigger Matching

| Trigger | Expected Content |
|---------|-----------------|
| `workout_started` | Encouragement, relaxation cues. Do NOT mention gear/cadence yet. **If HR ≥ 180, tone must be urgent/serious.** |
| `warmup_done` | Acknowledge warmup completion explicitly. |
| `km_milestone` | Celebrate distance explicitly (state the exact km). If HR ≥ 150, combine with HR reminder. |
| `phase_transition` | Hint at phase change (e.g., "进入巡航阶段", "热身结束"). Do NOT just say "势头很稳". |
| `heartRate_high` | MUST mention heart rate explicitly. MUST give concrete lowering action. **If HR ≥ 190, tone must be urgent with "立刻"/"别硬撑".** |
| `pace_slow_sustained` | Acknowledge slowdown, give reason or encouragement. Do NOT just command "快一点". |
| `pace_improving_sustained` | Praise momentum. Caution against overexertion if HR high. |
| `pace_unstable_sustained` | Advise steady rhythm. Do NOT scold. |
| `hydration_reminder` | Natural phrasing, ≥ 8 characters ideally. Must mention drinking/water. **If HR ≥ 170, must prioritize safety over hydration.** |
| `session_end` | Summary + praise + encouragement. Not just "结束了". |
| `user_input` | Directly answer the user's question. Use direct address. |

### 4. Terminology (口语化 Rules)

| Forbidden | Replacement |
|-----------|-------------|
| 均速 | 速度 / 配速 |
| 推进 | 往前骑 / 继续走 |
| 维持住 | 保持住 / 就这么踩着 |
| 踏频 | 踩踏节奏 / 脚下频率 |
| VO2max, 乳酸, 阈值 | (avoid entirely in colloquial persona) |
| 跑下来 | 跑完 |
| 呼吸拉长 | 呼吸放慢 |
| 找顺, 开外 | (avoid entirely) |
| 齿比调轻 + 收一档 (same sentence) | Contradictory — "调轻" = easier, "收" = heavier. Unify to "齿比调轻一档" or "齿比收小一档". |
| 收到 | 好 / 行 / 知道了 |
| 调轻一档 (when pace ≥ 6:00/km or very slow) | Should advise heavier gear or maintain current, NOT lighter gear |
| Foreign language contamination (e.g., Russian, English templates) | Pure Chinese within persona voice |
| Template English safety text in wuxia persona | Integrate safety natively into persona tone |

### 5. Data Accuracy

- Distance mentioned must match `distanceM` within ~0.5 km
- Duration mentioned must match `durationS` within ~2 minutes
- Heart rate mentioned must match `heartRate` exactly
- Pace mentioned should be consistent with `pace` field
- **Distance = 0 (or `distanceM` absent on `workout_started`)** — output must NOT mention any distance (e.g., "0.0公里"). Focus on warmup/relaxation instead.

## Workflow

### Step 1 — Parse Test Report

Read the HTML/JSON test report. Extract per-row:
- `triggerType`
- `heartRate`
- `distanceM`
- `durationS`
- `userMessage` (if any)
- Generated text output

### Step 2 — Run Rule Matrix

For each row, evaluate against all 5 dimensions above. Collect issues.

### Step 3 — Generate Suggestions

For each issue, produce a concise suggestion string:
- What is wrong
- Why it violates the rule
- How to fix it (concrete replacement)

Example:
```
'推进'过于书面化，应改为'往前骑'/'继续走'
```

### Step 4 — Build Report

Add a "修改建议" column to the report (or a new section). Color-code:
- 🟢 无明显问题
- 🟠 有改进建议
- 🔴 安全/严重问题

### Step 5 — Summarize

Count issues by dimension. Present top categories to user for prioritization.

## Python Audit Helper

Use this script scaffold inside `execute_code`:

```python
import re

def audit_coach_output(output, trigger, hr=None, dist=None, dur=None, user_msg=None):
    issues = []

    # Tone
    segments = output.split('，')
    short = [s for s in segments if len(s.strip()) <= 4 and s.strip()]
    if len(short) >= 3:
        issues.append("机械短句堆砌，像对讲机")

    if output.count('，') >= 4 and len(output) < 40:
        issues.append("逗号过多，句子碎片化")

    # Safety: high heart rate
    if hr and hr >= 170:
        if not any(w in output for w in ["偏高", "高", "收"]):
            issues.append(f"心率{hr}已偏高，未明确提醒风险")
        if not any(w in output for w in ["齿比", "慢", "轻"]):
            issues.append("高心率场景未给出具体降档建议")
        if "势头不错" in output or "势头很稳" in output:
            issues.append(f"心率{hr}偏高时不应鼓励'势头不错/很稳'")

    if hr and hr >= 180:
          if not any(w in output for w in ["危险", "太高", "马上", "立刻", "别硬撑", "停下来", "慢走", "缓一缓"]):
              issues.append(f"心率{hr}过高，语气应更紧迫，建议用'立刻/别硬撑/停下来/慢走'")
        if "先轻踩几圈" in output or "势头" in output:
            issues.append(f"心率{hr}过高时不应轻描淡写")

    if hr and hr >= 190:
        if not any(w in output for w in ["立刻", "别硬撑", "马上", "停下来"]):
            issues.append(f"心率{hr}接近极限，必须用'立刻/别硬撑/停下来'等强烈措辞")

    # Trigger matching
    if trigger == "workout_started":
        if "齿比" in output or "踏频" in output:
            issues.append("刚起步不宜提齿比/踏频，应先放松")
        if dist is not None and dist < 50:
            if "公里" in output or "0." in output:
                issues.append("起步时不应报0.0公里，应聚焦热身和放松")
        if hr and hr >= 180:
            if not any(w in output for w in ["危险", "太高", "马上", "立刻", "别硬撑"]):
                issues.append(f"开局心率{hr}过高，语气应严肃紧迫")

    if trigger == "warmup_done" and "热身" not in output and "活动开" not in output:
        issues.append("warmup_done未提及热身完成")

    if trigger == "km_milestone":
        if hr and hr >= 150:
            if "心率" not in output and "喘" not in output:
                issues.append("里程碑时心率已偏高，应结合心率提醒")
        # km_milestone should explicitly celebrate the km
        if dist:
            km = round(dist / 1000)
            if str(km) not in output and f"{km}公里" not in output:
                issues.append(f"km_milestone应明确提及{km}公里里程碑，给予成就感")

    if trigger == "phase_transition":
        if "阶段" not in output and "状态" not in output and "进入" not in output:
            issues.append("phase_transition应暗示阶段变化，如'进入巡航阶段了'")

    if trigger == "heartRate_high":
        if '心率' not in output:
            issues.append("heartRate_high触发但未提及心率")
        if not any(w in output for w in ['齿比', '慢', '轻', '收']):
            issues.append("高心率未给出具体降强度动作")

    if trigger == "pace_improving_sustained":
        if "顺" not in output and "好" not in output and "不错" not in output and "漂亮" not in output:
            issues.append("pace_improving_sustained应给予正向反馈，肯定进步")

    if trigger == "pace_unstable_sustained":
        if "稳" not in output and "匀" not in output:
            issues.append("pace_unstable_sustained应建议稳定节奏，避免忽快忽慢")

    if trigger == "pace_slow_sustained":
        if "慢" not in output and "速度" not in output and "缓" not in output:
            issues.append("pace_slow_sustained应明确提及速度下降，给出原因或建议")

    if trigger == "hydration_reminder":
        if len(output) < 8:
            issues.append("补水提醒过于生硬简短")
        if hr and hr >= 170 and "心率" not in output:
            issues.append(f"补水提醒时心率{hr}已高，应先提醒降速再补水")

    if trigger == 'session_end' and len(output) < 10:
        issues.append("结束语过于简短，应总结或鼓励")

    if trigger == 'user_input' and user_msg:
        if '徒儿' not in output and '你' not in output:
            issues.append("回答用户疑问时缺少直接称呼，像自言自语")
        if '少说点' in user_msg or '太吵了' in user_msg:
            if len(output) > 25:
                issues.append("用户要求少说，回复应极简（≤10字）")
        if '别报速度' in user_msg or '别老报速度' in user_msg:
            if '速度' in output or '公里' in output or '配速' in output:
                issues.append("用户要求不报速度，回复中仍提及速度数据")
        if '是不是骑太快' in user_msg or '太快了' in user_msg:
            if hr and hr >= 175 and ('不算快' in output or '倒不算快' in output):
                issues.append(f"用户自觉太快且心率{hr}，不应否定用户感受")
        if '差点摔' in user_msg or '摔了' in user_msg:
            if '先停止运动' in output or '转移到安全位置' in output:
                issues.append("摔车场景出现模板英文安全提示，破坏人设")

    # Terminology
    if '均速' in output:
        issues.append("'均速'过于术语，应改为'速度'/'配速'")
    if '推进' in output:
        issues.append("'推进'过于书面化，应改为'往前骑'/'继续走'")
    if '维持住' in output:
        issues.append("'维持住'生硬，应改为'保持住'/'就这么踩着'")
    if '踏频' in output:
        issues.append("'踏频'过于专业术语，应说'踩踏节奏'")
    if '收到' in output:
        issues.append("'收到'像对讲机，应改为'好'/'行'")

    # Data accuracy
    if dist:
        dist_km = dist / 1000
        for m in re.findall(r'(\d+\.?\d*)\s*公里', output):
            if abs(float(m) - dist_km) > 0.5 and abs(float(m) - round(dist_km)) > 0.5:
                issues.append(f"提到{m}公里，实际约{dist_km:.1f}公里，数据偏差大")
                break

    if dur:
        dur_min = dur / 60
        for m in re.findall(r'(\d+)\s*分钟', output):
            if abs(float(m) - dur_min) > 2:
                issues.append(f"提到{m}分钟，实际约{dur_min:.0f}分钟，时间偏差大")
                break

    return "；".join(issues) if issues else "✅ 无明显问题"
```

## Report Output Format

When producing an HTML report, add CSS:

```css
.suggestion { max-width: 320px; line-height: 1.5; color: #b45309; font-size: 12px; }
.suggestion.ok { color: #16a34a; }
th.suggestion-header { background: #7c2d12; }
```

And append a `<td class="suggestion">...</td>` to each table row.

## Pitfalls

- **Don't flag stylistic preferences as errors** — only flag clear violations of established rules
- **Context matters** — a term like "齿比" is wrong at `workout_started` but correct at `heartRate_high`
- **Safety overrides tone** — if HR is dangerous, being colloquial is less important than being clear
- **Data accuracy only matters when data is cited** — don't penalize outputs that don't mention numbers
- **Avoid false positives on distance** — round numbers (e.g., "10公里") are acceptable approximations
- **Distance = 0 is special** — `workout_started` with no `distanceM` must never say "0.0公里" or any distance claim. This is a hard rule, not an approximation.
- **Running vs cycling differences** — Running audits use pace (min/km) not gear/cadence. Slow pace threshold is ≥8:00/km (not cycling's 6:00/km). See `references/running-coach-audit-rules.md` for running-specific rules.
