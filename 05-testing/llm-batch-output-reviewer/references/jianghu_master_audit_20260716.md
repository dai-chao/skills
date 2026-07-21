# jianghu_master Persona Audit — 2026-07-16

Source: `/Users/chao/Downloads/jianghu_master_20260716_181410_labeled.html`
Batch: 500 cases, running coach, persona=`jianghu_master`, mixed 男/女教练 scenarios.
Result: 439 pass (87.8%), 61 fail (12.2%).

## Methodology that worked

1. Extract replies via `re.findall(r'<td class="reply">(.*?)</td>', content, re.DOTALL)` then strip tags + `html.unescape`.
2. Extract case names via `<td>(S\d+[^<]+)</td>\s*<td><span class="tag">` pattern.
3. Extract fail annotations via rows containing `result-bad` — the report already had a "结果与建议" column with reviewer labels; parse those first before re-deriving issues.
4. Persona-marker coverage check: count `徒儿/为师/江湖/功夫/内功/丹田/吐纳/招式/火候/收功/轻功/马步/内息/气沉/心法/口诀/本门/武林` per reply. Replies with zero markers AND length > 30 chars = "persona naked" cases.
5. Frequency count of suspect phrases across the whole batch — the same LLM bug often repeats verbatim (e.g. `还不必定性高低` ×5, `算盘珠子` ×11).

## Headline findings (these generalize)

### 1. Gendered self-address mismatch (45 cases)
Female-coach scenarios (`S01/S03/S05/S07/S09/S11/S13/S15-...-女教练`) used `为师` — male-coded. Either:
- Change persona prompt to use gender-neutral `师父` / `我`, OR
- Accept `为师` as a stylistic choice but apply it uniformly (currently inconsistent).

### 2. Verbatim repeated病句 template (5 cases)
`心率XXX，这口气还不必定性高低，先按能完整说话的强度走，留意身体变化。`
— `定性高低` is not a valid Chinese phrase. The whole sentence is a template the model memorized. Ban the substring `定性高低` in the prompt, or add it to the detector list.

### 3. Anachronistic metaphor saturation (11 cases)
`为师嘴上...心里算盘珠子...` — abacus imagery clashes with the wandering-master aesthetic and is being used as a crutch self-deprecation gag. Suggest replacements: `心里翻江倒海` / `七上八下` / `捏了把汗` / `提着一口气`.

### 4. Persona-naked replies (101 cases, 20.2%)
Replies with zero jianghu markers — reads as a generic fitness coach. Most common in `periodic_update` and `online_presence` triggers where the model has little to say. Fix: prompt should require at least one persona marker per reply, even a single `徒儿`.

### 5. Safety silence at high HR (8 fail cases)
HR 175–184 with replies like `先喘口气再说` / `润喉一口` — no explicit slow-down/stop instruction. This is the single largest fail category. Detector rule: HR≥175 requires `慢走` or `停下` + hydration; HR≥185 requires `立刻` / `马上`.

### 6. session_end omissions (4 fail cases)
Missing: data summary, hydration reminder, or next-session advice. Detector: `triggerType=session_end` must contain distance + duration + at least one of {`补水`, `下次`, `建议`}.

### 7. Fabricated data at session_end (1 case)
Input had `distanceM=114` but reply said `0.11公里` — reviewer flagged as 编造数据 (technically correct conversion but presented as if it were a real accomplishment). Detector: cross-check every number in a session_end reply against the metrics JSON.

### 8. Crude/vulgar imagery (1 case)
`蹲坑时间长了站起来也未必稳当` — toilet humor breaks the master persona. Add `蹲坑` / `拉屎` / `尿` to a crude-word denylist for this persona.

### 9. Non-sequitur style drift (2 cases)
- `还常被早市大妈说跑得急` — modern street scene, not jianghu.
- `心里盘算收功后吃点什么` during a warmup_done trigger — off-topic for the current phase.

### 10. Unsafe advice (1 case)
`低头看一眼鞋带` mid-run — looking down while running is a trip hazard. Should be `先靠边停下，检查鞋带`.

## Detector additions made to SKILL.md

All patterns above were merged into the `jianghu_master` row of the persona-specific detector table in `../SKILL.md`. Key substrings to grep for:

```
为师          (when case name contains 女教练 — flag for review, not auto-fail)
算盘珠子
还不必定性
定性高低
气沉在脚下
踩水上落叶
既毕
破纪录
瞎倒腾
自个
架式
打尖
蹲坑
早市大妈
低头看一眼鞋带
收功后吃点什么
配重
进入中段
```

## Suggested prompt-side fixes (for the coach-prompt author, not the auditor)

1. Add to system prompt: `禁止使用"算盘珠子"、"还不必定性"、"定性高低"、"破纪录"等现代或不通的表达`.
2. Add: `女性教练场景下自称用"师父"或"我"，避免"为师"`.
3. Add: `每条回复至少包含一处江湖人设标记（徒儿/为师/师父/功夫/内息/心法等）`.
4. Add safety rule: `心率≥175 必须明确说"改慢走"或"停下"；≥185 必须说"立刻"`.
5. Add session_end rule: `结束语必须包含：距离+时长+补水提醒+下次建议`.
