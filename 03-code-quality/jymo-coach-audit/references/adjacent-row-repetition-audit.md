# Adjacent-Row Repetition Audit

## Context

When reviewing bulk coach chat test reports (500+ rows), phrase repetition can be measured globally ("this phrase appears in X% of all responses") or locally ("this phrase appears in 3 consecutive rows of the same session"). The latter is more important for user experience — users hear replies in real-time within a single session, not across all sessions.

## Rule

Within a single session (identified by `case_name` prefix, e.g., "C01-通勤折叠车-女教练"), if two consecutive rows (e.g., #11 and #12) contain the same phrase, flag it as adjacent-row repetition even if the phrase's global frequency is moderate.

## Phrases to Monitor

| Phrase | Global Freq (this report) | Threshold | Suggested Variants |
|--------|---------------------------|-----------|-------------------|
| 齿比放轻 | ~17% | adjacent | 踩轻点, 阻力小一点, 踏频稳一点 |
| 档位放轻 | ~8% | adjacent | 齿比轻一档, 阻力调小 |
| 这单 | ~26% | adjacent | 这段, 这程, 这活儿 |
| 交差 | ~15% | adjacent | 完成, 搞定, 拿下 |
| 顺着踩 | ~6% | adjacent | 保持节奏, 稳住, 就这样顺下去 |
| 手腕松一松 | ~8% | adjacent | 手腕放松, 握把松一点, 手指松一松 |
| 心率/心跳落下来 | ~10% | adjacent | 心跳回落, 心率降回正常, 心跳稳下来 |
| 靠边停下来 | ~7% | adjacent | 先停路边, 靠边歇一下, 停路边缓一缓 |
| 停5-10分钟 | ~5% | adjacent + HR-aware | HR 190+ → 10-15分钟 |
| 别硬撑 | ~6% | adjacent | 别硬扛, 别顶着, 别逼自己 |
| deadline | ~5% | adjacent | 排期, 截止日, 老板催 |
| 周报字数 | ~3% | adjacent | 日报字数, 汇报材料 |

## Implementation

In the auto-annotator script, pass `prev_reply` and `next_reply` to the suggestion generator. For each row, check if the same phrase exists in the previous or next row's reply text. If so, flag it once per row (break after first match to avoid spam).

```python
def generate_suggestion(metrics, reply_text, case_name, prev_reply, next_reply):
    suggestions = []
    # ... other rules ...
    adj_phrases = [
        ("齿比放轻", "齿比放轻", "建议轮换用'踩轻点'/'阻力小一点'"),
        ("这单", "这单", "建议轮换用'这段'/'这程'"),
        # ... etc
    ]
    for phrase, check_phrase, advice in adj_phrases:
        if check_phrase in reply_text:
            prev_has = prev_reply and check_phrase in prev_reply
            next_has = next_reply and check_phrase in next_reply
            if prev_has or next_has:
                suggestions.append(f"【表达】相邻回复重复出现'{phrase}'，{advice}")
                break  # Only flag one per row
    return suggestions
```

## Why This Matters

In the 2026-06-17 office_drama report, "齿比放轻" appeared in 83 rows (16.6% globally) — not enough to trigger a global >30% flag. But within the C01 session, it appeared in 4 consecutive rows (#16-#19), making it highly noticeable to a real user. Adjacent-row detection catches this.
