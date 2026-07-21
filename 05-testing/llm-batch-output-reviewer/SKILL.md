---
name: llm-batch-output-reviewer
description: |
  Review batched LLM output from HTML test reports. Extract text replies, detect recurring
  linguistic issues, compare across iterations, and generate annotated HTML reports with
  specific fix suggestions. Designed for prompt-engineering QA workflows.
compatibility: Any environment with Python 3 and file access.
allowed-tools: file, terminal
metadata:
  version: "1.2.0"
---

# LLM Batch Output Reviewer

## Purpose

You have an HTML test report containing hundreds of LLM-generated text outputs (e.g. AI coach replies, chatbot responses). You want to:
1. Spot bad phrasing, jargon, or non-colloquial patterns at scale
2. Measure whether your prompt fixes actually reduced the issues
3. Generate an annotated report with specific rewrite suggestions

## Workflow

### Step 1: Parse the HTML report

The report typically has `<td class="reply">...</td>` cells. Extract all of them:

```python
import re
import html as html_module

with open("report.html", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r'<td class="reply">(.*?)</td>'
matches = re.findall(pattern, content, re.DOTALL)
```

**Pitfall**: replies may contain nested HTML tags or newlines. Use `re.DOTALL` and strip tags:
```python
text = re.sub(r'<[^>]+>', '', raw)
text = html_module.unescape(text).strip()
```

### Step 2: Define issue detectors

Create a dictionary of target phrases and their preferred replacements. Example patterns for Chinese conversational AI:

| Bad Pattern | Problem | Preferred |
|-------------|---------|-----------|
| `收到` + pace | Walkie-talkie jargon for slowing down | `降到/压到/控制在` |
| `呼吸拉长` | Ambiguous (deepen? slow down?) | `呼吸放慢一点` / `加深呼吸` |
| `LSD` / `VO2max` / `乳酸阈值` / `有氧基础` | Domain jargon users don't know | `长距离慢跑` / `最大摄氧量` / `身体转点` / `耐力底子` |
| `跑下来` (any variant) | Says "finished" mid-workout or at end | `跑完` / `坚持完` |
| `走下来` (any variant) | Says "finished walking" mid-workout or at end | `走完` |
| `满X公里了` | Unnatural colloquialism | `跑到X公里了` |
| `心率偏高先把` | Missing punctuation, keyword stack | `心率偏高，先把…` |
| `开外` for pace ranges | Misused word | `之间` |
| `收到` + instruction | Walkie-talkie jargon | `知道了` → `OK` / `行` |
| `收到` + pace/number | Misused as "drop to" (e.g. `配速可以收到5分30`) | `压到` / `降到` |
| `在线` for capability | Internet slang | `不错` / `够用` |
| `bpm` / `BPM` | Abbreviation users don't say aloud | remove, just state the number |
| `了了` / repeated `了` | Typo / token echo | single `了` |
| `这场` | Written-style classifier | `这次` |

Also detect **cross-script contamination** (simplified/traditional Chinese mix). LLMs occasionally emit traditional characters (`頂` for `顶`, `沒` for `没`, `點` for `点`). Use a small deny-list or Unicode range check:
```python
fan = ['頂','沒','點','說','話','進','過','開','長','體']
```
This is especially common when the model was trained on mixed corpora or the inference backend defaults to a Taiwan/HK locale.

**Pitfall — traditional-character evasion after prompt fix:** After banning a specific traditional character in the prompt (e.g. "不要用繁体字'說'"), the model may switch to a different traditional variant (`説` instead of `說`). Maintain a comprehensive mapping and check for all variants of high-frequency characters, not just the one that first appeared.

Also detect **prompt template leakage**: leftover markdown artifacts from the system prompt, e.g. `# 回复\n\n`, `### Response`, or `生成内容：`. These appear verbatim at the start of the reply and must be stripped entirely.

Also detect **context hallucination**: the AI claims knowledge of a previous session that the current context does not contain (e.g. `"上次你也是5公里跑进45分钟"` when no prior run data was supplied). Cross-check for temporal references (`上次`, `之前`, `上次跑`) against available metrics.

Also detect structural issues:
**Pitfall — exact-match evasion**: LLMs often swap exact phrases for morphological variants after a prompt edit. E.g. after banning `"能跑下来很稳"`, the model may say `"第一公里跑下来了"` or `"能坚持跑下来"`. Detect the **root substring** (`跑下来`) rather than the full phrase, or you will under-report.

Also detect structural issues:
- **Comma splice stacking**: ≥5 short clauses (4–14 chars) joined by commas reads like a robot checklist.
- **Overuse of `了`**: ≥4 occurrences in <120 chars creates dragging rhythm.
- **High heart-rate silence on milestones**: When `triggerType` is `km_milestone` or `phase_transition` and `heartRate` ≥175, the reply must mention the elevated heart rate, not just celebrate the distance.
- **Hydration reminder ignoring heart rate**: When `triggerType` is `hydration_reminder` and `heartRate` ≥175, the reminder should pair hydration with a heart-rate warning.
- **Safety concern dismissal**: When the user reports pain (`膝盖疼`), breathing difficulty (`喘不上气`), or near-injury (`差点绊倒`), replies that only say `"正常"` or `"慢走试试"` without clear stop recommendations are insufficient.

### Step 3: Count and compare

Run the detectors across the batch. If you have a previous baseline, print a before/after table so the user can see whether their prompt edits worked.

### Step 4: Generate annotated HTML

Insert a new column after the `reply` column in the original HTML:

1. Add `<th>修改建议</th>` to the header.
2. Add CSS for `.suggestion` (green tint, small font) and `.tag-issue` (red labels).
3. For each row, run `analyze_reply()`:
   - If no issues → `<span style="color:#888">语句通顺</span>`
   - If issues found → list red tags + **concrete rewritten text**

Use `re.sub` with a replacer function to inject the new `<td>` after each `reply` cell.

**Pitfall — replacement string escapes**: When building the replacement string inside `re.sub`, remember that `\u` in replacement templates is not a valid regex escape. Either:
- Use normal (non-raw) strings for replacements, or
- Use a lambda `lambda m: f"...{m.group(1)}..."` instead of a template string.

**Pitfall — fix ordering**: If you apply multiple text transformations (e.g. replace jargon, then merge short clauses), pass the **already-modified text** into the merger. Passing the original raw text will overwrite earlier fixes.

```python
# WRONG — overwrites the jargon fix
merged = merge_short_clauses(text)

# CORRECT — preserves prior fixes
merged = merge_short_clauses(modified)
```

**Pitfall — concrete rewrites required**: Do not return only issue tags. Users expect a **specific rewritten version** in the suggestion cell. Example:
```python
issue_tags = ' '.join(f'<span class="tag-issue">[{i}]</span>' for i in issues)
return f'{issue_tags}<br><br><b>建议版：</b>{modified}'
```

**Pitfall — tagged but not fixed in the suggested version**: It is common to flag `"LSD"` or `"跑下来"` in red tags while accidentally leaving the bad phrase inside `<b>建议版：</b>`. Always diff the original against the modified text before returning, or run a second pass that bans the target substring from the suggestion cell entirely.

**Pitfall — missing suggestion version entirely**: Sometimes the reviewer script outputs only red tags (e.g. `<span class="tag-issue">[连续短句堆叠]</span>`) and forgets the rewrite. Scan the batch for cells that contain `tag-issue` but not `建议版`, and auto-fill a corrected rewrite.

**Pitfall — patch-tool encoding corruption with CJK**: When injecting suggestion cells into large HTML files via the `patch` tool (find-and-replace mode), multi-byte CJK characters in replacement strings can be silently corrupted (e.g. `分` → `刅`). This happens because some patch backends mangle Unicode in replacement templates. **Workaround**: use `execute_code` with Python `str.replace()` or regex `re.sub()` instead, writing the full result back to disk. Never apply `patch` across lines that contain Chinese text inside the replacement string.

**Pitfall — `patch` tool silently corrupts CJK characters**: Even when using `patch` action='replace' with exact `old_string`/`new_string`, CJK characters in `new_string` may be corrupted (e.g. `分` → `刅`, `建议` → `刅议`). This has been observed on macOS with Python 3.14. Always verify CJK output after `patch` by reading back the file. If corruption is detected, use `execute_code` with Python `str.replace()` or `re.sub()` as the reliable alternative.

```python
# CORRECT — use execute_code for CJK text manipulation
import re

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ... make modifications ...

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
```

**Pitfall — HTML parser unavailable**: `BeautifulSoup` may not be installed in the execution environment. Fallback to regex (`re.DOTALL` + row-by-row `re.sub`) for injecting suggestion cells into large HTML reports.

**Pitfall — regex row extraction from compact HTML**: When HTML is minified or compact (no newlines between tags), simple `re.findall(r'<tr>(.*?)</tr>')` may fail because `.*?` with `re.DOTALL` can be too greedy across multiple rows. Use a two-step approach: first split by `</tr>`, then process each segment:
```python
# CORRECT — split by closing tag, then rebuild
segments = html_content.split('</tr>')
new_segments = []
for seg in segments:
    if '<td class="reply"' in seg:
        # Extract reply text, analyze, append suggestion
        reply_match = re.search(r'<td class="reply">(.*?)</td>', seg, re.DOTALL)
        if reply_match:
            reply = reply_match.group(1)
            suggestion = analyze_reply(reply)
            seg += f'<td class="suggestion">{suggestion}</td>'
    new_segments.append(seg)
new_html = '</tr>'.join(new_segments)
```

**Pitfall — row-rebuild vs in-place replacement**: For large HTML reports with 500+ rows, rebuilding the entire `<tbody>` from parsed rows is more reliable than trying to match and replace each row in-place with `str.replace()`. Parse all rows first, generate suggestion cells, then assemble a new tbody string and splice it back into the original HTML. This avoids partial-match failures when row content contains similar substrings.

**Pitfall — regex capture of row content**: When using regex to extract rows, the pattern must capture the FULL row including all nested tags. A common mistake is a greedy `.*` that swallows multiple rows. Use non-greedy `.*?` with `re.DOTALL`, or better, match from `<tr>` to `</tr>` and process the inner content separately:
```python
# CORRECT — match each <tr>...</tr> block individually
row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
rows = row_pattern.findall(html_content)

def rebuild_row(body, suggestion_html):
    return f'<tr>\n{body}\n{suggestion_html}\n</tr>'

new_tbody = '\n'.join(rebuild_row(body, sugg) for body in rows)
```

**Pitfall — HTML structure change when adding suggestion column**: When adding a new `<th>` to the header, also add a matching `<td>` to every row. If the header gains a column but some rows don't, the table layout breaks. Use a regex replacer that processes every `<tr>...</tr>` in the tbody uniformly.

```python
# Example: add suggestion column to every row
row_pattern = re.compile(r'<tr[^\u003e]*\u003e(.*?)\u003c/tr\u003e', re.DOTALL)

def process_row(m):
    body = m.group(1)
    # ... extract reply, run analyze_reply() ...
    suggestion = analyze_reply(reply_text, trigger_type, metrics)
    return f'<tr\u003e\n{body}\n<td class="suggestion">{suggestion}</td>\n</tr\u003e'

new_html = row_pattern.sub(process_row, html_content)
```

**Pitfall — table header not updated**: When adding a new column to the data rows, the `<thead>` must also gain a matching `<th>`. The safest approach is to replace the closing `</tr>` of the header row:
```python
# Add "修改建议" column to header
content = content.replace(
    '<th>输出</th>\n</tr>\n</thead>',
    '<th>输出</th><th style="min-width:300px">修改建议</th>\n</tr>\n</thead>'
)
```

**Pitfall — CJK text in suggestion cells**: When suggestion text contains Chinese characters, ensure the output file is written with `encoding="utf-8"`. Also, if using `execute_code` to write the file, the Python script itself must be UTF-8 encoded (default in Python 3, but verify when reading/writing).

```python
with open(output_path, "w", encoding="utf-8") as f:
    f.write(new_html)
```

**Pitfall — f-string CJK SyntaxError in execute_code**: When constructing CJK strings inside f-strings in `execute_code` scripts, nested quotes around Chinese text can trigger `SyntaxError`. Workaround: use `str.join()` to build headers or authorization strings instead of nested f-string quotes. Example:
```python
# WRONG — may trigger SyntaxError with CJK inside nested quotes
# auth_header = f"Authorization: Bearer {api_key}"
# CORRECT — use str.join()
auth_parts = ['Authorization:', 'Bearer', api_key]
auth_header = ' '.join(auth_parts)
```

**Pitfall — row content extraction with nested tags**: HTML rows often contain deeply nested tags (`<details>`, `<div class="mono">`, `<span>`). When extracting row content for analysis, the regex must handle arbitrary nesting depth. Use `re.DOTALL` and capture everything between the outer `<td>...</td>` boundaries, then parse inner cells separately:
```python
# Extract all complete rows first
row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
rows = row_pattern.findall(html_content)

# For each row, extract individual cells
cell_pattern = re.compile(r'<td[^\u003e]*>(.*?)</td>', re.DOTALL)
for row_body in rows:
    cells = cell_pattern.findall(row_body)
    # cells[0] = ID, cells[1] = name, cells[2] = tag, cells[3] = status, 
    # cells[4] = duration, cells[5] = input, cells[6] = reply
    reply_text = cells[6] if len(cells) > 6 else ""
```
```python
row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
rows = row_pattern.findall(html_content)

def rebuild_row(body, suggestion_html):
    # body is the content between <tr> and </tr>
    # Append suggestion_html before the closing </tr>
    return f'<tr>\n{body}\n{suggestion_html}\n</tr>'

new_tbody = '\n'.join(rebuild_row(body, sugg) for body in rows)
```

**Pitfall — context/time confusion in session boundaries**: End-of-session (`session_end`) triggers must use retrospective phrasing (`ran`, `finished`, `kept steady`). If the reply says `"先小幅降速"` or `"第一公里跑下来了"` while `durationS` is 3600s and `distanceM` is 8500, the model has lost track of elapsed time/distance. Cross-check metrics against milestone phrasing. Also extract `triggerType` from the input JSON within each HTML row (`workout_started`, `periodic_update`, `session_end`, `user_input`) to verify the coach's tone matches the event type.

**Pitfall — emotional-value override**: When the user sends an explicit emotional request (e.g. `"给我加加油"`, `"好累啊"`), a data-first reply (`"心率172偏高"`) feels robotic. The suggestion should lead with encouragement, then append data as context: `"满30分钟了，能坚持到现在已经很棒了！不过心率172有点偏高，咱们把配速降一点…"`

**Pitfall — comma/顿号 abuse when merging**: When automatically collapsing short clauses, do not blindly replace commas with顿号. Use顿号 only for true parallel items (actions or nouns). If the two sides are not parallel (e.g. `以下、前半程`, `秒每公里、是自然调整`), keep the comma or restructure the sentence.

**Pitfall — safety-priority override**: When the user reports a safety concern (e.g. `"膝盖疼"`, `"喘不上气"`, `"差点绊倒"`, `"低血糖"`), the coach must prioritize safety over encouragement or data analysis. Replies like `"慢走一刻钟试试"` for knee pain, or `"心率还行"` when the user can't breathe, are insufficient. The suggestion should explicitly recommend stopping or seeking help: `"膝盖疼先别跑了，停下来走走看，如果还疼建议去医院检查"`. Flag any reply that does not clearly address the safety risk.

**Pitfall — metric-context mismatch on milestones**: When `triggerType` is `km_milestone` or `phase_transition` and `heartRate` is ≥175, the coach should mention the elevated heart rate in the reply, not just celebrate the distance. Similarly, when `hydration_reminder` fires while `heartRate` ≥175, the reminder should pair hydration with a heart-rate warning. Cross-check trigger type against metrics before approving a reply.

### Step 5: Deliver summary to user

Present:
- Total cases processed
- Issue counts (tabular before/after if available)
- Top remaining problem categories
- Path to the generated annotated HTML file

## Example `analyze_reply` skeleton

```python
def analyze_reply(text, trigger_type="", metrics=None):
    issues = []
    modified = text
    metrics = metrics or {}

    # Template leakage
    if modified.startswith("# 回复") or modified.startswith("###"):
        modified = re.sub(r'^#\s+回复\s*\n+', '', modified)
        issues.append('严重模板泄露：# 回复')

    # Traditional Chinese characters
    fan_map = {'頂': '顶', '沒': '没', '點': '点', '說': '说', '話': '话', '進': '进', '過': '过', '開': '开', '長': '长', '體': '体', '説': '说'}
    for bad, good in fan_map.items():
        if bad in modified:
            modified = modified.replace(bad, good)
            issues.append(f'"{bad}"是繁体字，改为"{good}"')

    if "收到" in modified and ("分" in modified or "配速" in modified):
        modified = modified.replace("收到", "压到")
        issues.append('"收到"改为"压到"')

    if "呼吸拉长" in modified:
        modified = modified.replace("呼吸拉长", "呼吸放慢一点")
        issues.append('"呼吸拉长"改为"呼吸放慢一点"')

    # Context hallucination — temporal references without prior data
    if re.search(r'上次你也是|之前你跑过', modified):
        issues.append('上下文幻觉：教练不应知道上次数据')

    # Session-end tense check
    if trigger_type == "session_end" and re.search(r'先小幅降速|第一公里跑下来了', modified):
        issues.append('session_end 时态错误：不应使用未完成式指令')

    # ... more rules

    if not issues:
        return '<span style="color:#888">语句通顺，无明显问题</span>'

    tags = ' '.join(f'<span class="tag-issue">[{i}]</span>' for i in issues)
    return f'{tags}<br><br><b>建议版：</b>{modified}'
```

## Output file naming convention

Save reviewed reports alongside the originals or on the Desktop:
```
coach_chat_report_reviewed.html
coach_chat_report_reviewed_v2.html
...
```

## Generating Audit Reports (Right-Column Suggestions)

When the user asks for an audit file with suggestions in a new right-hand column (e.g. "在输出的右边加一列建议"):

1. **Parse the original HTML** row by row using regex with `re.DOTALL`:
```python
row_pattern = re.compile(r'<tr[^\u003e]*\u003e(.*?)\u003c/tr\u003e', re.DOTALL)
rows = row_pattern.findall(html_content)
```

2. **Extract per-row data**:
   - Case ID, name, tag, status, duration
   - Input JSON (from `<details>` block)
   - Reply text (from `<td class="reply">`)

3. **Run `analyze_reply()`** on each reply, passing both the reply text and the input JSON (to check triggerType, metrics, userMessage).

4. **Build a new HTML table** with an extra `<th>审核建议 💡</th>` column.

5. **Style suggestions by severity**:
   - 🟡 Minor / style: yellow left-border (`#ffc107`)
   - 🔴 Critical / data error: red left-border (`#dc3545`)
   - 🔵 Pattern / structural: blue left-border (`#17a2b8`)

6. **Include summary statistics at the top**:
   - Total cases, cases with issues, pass rate
   - Top 10 issue types with counts
   - Comparison table if baseline available

7. **Write to a new file** with `_AUDIT.html` suffix in the same directory.

**Pitfall — BeautifulSoup unavailable**: The execution environment may not have BeautifulSoup installed. Always fallback to regex-based parsing for HTML report generation.

**Pitfall — CJK in replacement strings**: When injecting suggestion cells via `patch` tool, multi-byte CJK characters can be silently corrupted. Use `execute_code` with Python `str.replace()` or `re.sub()` instead, writing the full result back to disk.

**Pitfall — suggestion column width**: Keep suggestion text concise (≤120 chars per item) so the table remains readable. Use `<div class="suggestion-item">` with `max-width` CSS rather than plain text.

**Pitfall — manual annotation vs auto-detection**: For persona-specific audits (e.g. "江湖师傅"人设检查), combine manual expert review with auto-detection:
   - **Manual**: Read representative samples from each scenario type, identify pattern-level issues (称呼不一致、语气现代化、中英文混杂)
   - **Auto**: Run regex detectors on all 500 rows for known bad patterns (英文单词、"徒弟"、过短回复)
   - **Merge**: Manual findings get detailed rewrite suggestions; auto findings get category tags
   - **Coverage**: Manual covers ~20 high-impact cases; auto covers the remaining ~480 for completeness

For a concrete implementation of this pattern, see `references/html_report_annotation_pattern.md`.

For a full jianghu_master persona audit (500 cases, 2026-07-16) with the complete list of anachronisms, gender-mismatch patterns, and repeated病句 templates discovered, see `references/jianghu_master_audit_20260716.md`.

**Pitfall — office_drama persona audit specifics**: When auditing the "办公室戏精同事" (office_drama) persona:
   - **Metaphor saturation**: Count occurrences of `deadline`, `KPI`, `连环call`, `述职PPT`, `周报`, `OKR`, `加班`, `工位`, `钉钉`, `群里@` per reply. Flag if ≥3 unique metaphors or ≥2 repetitions of the same metaphor.
   - **Nickname overuse**: Count `宝子` per reply and per batch. Flag if used in >80% of replies.
   - **Hydration monotony**: Check that `hydration_reminder` triggers do not all use the same `别等身体在群里@你` template. Expect ≥3 distinct variants in a 500-case batch.
   - **Weak-data hallucination**: When `metrics` lacks `heartRate`, `pace`, or `distanceM`, verify the reply does not invent specific numbers (e.g. `跑了15分钟了` when only `durationS=300` is present).
   - **User-preference violation**: When `userMessage` contains `别报心率`, `心率静音`, `不要一直说话`, or `安静`, verify the reply fully complies. Partial compliance (e.g. saying "后面只说配速" but then mentioning HR in the same reply) is a **critical** issue.
   - **Safety-tone calibration**: For `heartRate_high` with HR≥190, the reply must use urgent language (`立刻停下来`, `马上慢走`, `别硬撑`). Phrases like `偏高` or `收一收` are insufficient.
   - **Session-end risk acknowledgment**: For `session_end` with HR≥175, the summary must acknowledge the elevated heart rate as a risk, not praise the performance unconditionally.
   - **Contradiction check**: For safety events (`差点绊倒`, `膝盖疼`, `喘不上气`), verify the reply does not mix "stop" advice with "continue running" advice in the same response.

## When to update detectors

As the user iterates on prompts, previously fixed issues should drop to ~0. If an issue count rises instead, the prompt change likely introduced a new preference—flag it immediately.

## Session Example: Strictening Coach Chat Audit Rules

When a user says "我感觉你检测的太松了" after a first-pass audit, tighten the detectors and rerun the full batch. See `references/session-2026-07-11-coach-chat-strict-audit.md` for the strict rule set applied to a 500-case running coach HTML report (`pro_female` persona), including:

- Lowered thresholds for long-sentence and fragmentation detection
- Stricter safety thresholds (HR ≥ 170 / 175 / 180 / 190)
- User-preference enforcement (no pace / HR reporting after explicit request)
- Detection of fabricated session-end historical data
- Time-unit and logical-contradiction checks
- The annotated output file pattern with a right-hand "结果和建议" column

## Cross-Iteration Comparison

When the user runs a new test report after prompt edits, compare it against the previous report to measure whether fixes landed:

1. **Parse both reports** using the same extraction logic.
2. **Run the same detectors** on both batches.
3. **Produce a delta table** showing issue counts before/after:

| Issue Category | Before | After | Δ | Verdict |
|---|---|---|---|---|
| 套路化表达 | 83 | 12 | −71 | ✅ Fixed |
| 缺乏具体性 | 52 | 48 | −4 | ⚠️ Partial |
| 数据不匹配 | 4 | 0 | −4 | ✅ Fixed |

4. **Flag regressions**: If a category went up, the prompt change likely introduced a new pattern—surface it immediately.

**Pitfall — comparing different report sizes**: If the new report has 500 cases but the old one had 400, normalize counts to **per-100-cases** before comparing, or the numbers will mislead.

### Cycling-Specific Detectors

When reviewing cycling coach output (workoutType: cycling), add these cycling-specific patterns:

| Bad Pattern | Problem | Preferred |
|---|---|---|
| `骑下来` | Says "finished" mid-workout or at end | `骑完` |
| `齿比` + no direction | Mentions gear but not adjust up/down | `齿比往轻调一档` / `齿比加重一点` |
| `顺着骑` / `顺着踩` / `顺着这个节奏` | Overused generic filler, no data grounding | `保持22均速` / `心率150这个节奏很好` |
| `不知不觉` | Robotic time-passage marker | `就这么` / `已经` / `都` |
| `把烦恼都甩在身后` / `最好的奖赏` / `犒劳` | Overly literary, not coach-like | Delete or replace with concrete observation |
| `真的太棒了` / `真的很棒` / `特别棒` / `超级棒` | Praise inflation, feels insincere | Replace with specific affirmation (`心率控得很稳`) |
| `就行。` / `就好。` (weak ending) | Ends abruptly without next step | Add concrete guidance (`前面路口注意一下`) |
| `稍微` ×3+ in one reply | Word overuse, monotonous | Alternate with `略微` / `适当` / `稍微` |
| `别硬顶` ×2+ | Repetitive warning | `别勉强` / `放松点` / `不用死撑` |
| `收到` | Walkie-talkie jargon | `好的` / `明白` / `OK` |
| Heart rate high but no gear advice | Missing actionable guidance | Always pair heart-rate warning with `齿比调轻` or `减速` |
| `workout_started` but mentions elapsed time/distance | Context mismatch | Should say "刚开始" / "先热身" |
| `session_end` missing data summary | Incomplete wrap-up | Must include distance, duration, avg speed |
| `session_end` missing next-session advice | No forward guidance | Add `下次可以尝试…` / `建议…` |
| `hydration_reminder` too brief | Just "drink water" with no context | Pair with current state (`骑了X公里了，顺手补口水`) |
| User says pain (`疼`/`痛`/`酸`) + reply says `正常` only | Dismissive without explanation | Explain cause + give relief method |
| Speed mention mismatches pace data | Math error in conversion | Cross-check: pace "3:14" ≈ 18.5 km/h |
| User says `别报心率` / `心率静音` but reply still mentions HR | Disregards explicit user preference | Remove all HR references from that reply |
| User says `不要一直说话` / `安静` but reply is long | Ignores user's brevity request | Keep response under 20 chars |
| High HR (≥180) at `workout_started` / early phase | Starting too hard | Strong warning: `先慢走热身，别急着跑` |
| `session_end` with HR ≥180 but summary praises performance | Encourages dangerous behavior | Flag HR risk: `心率偏高，下次注意控制` |
| Near-injury (`差点绊倒`) + reply mixes "stop" with "keep running" | Contradictory safety advice | Insist on full stop + check before continuing |
| Weak data (no HR/pace/dist) + reply invents specific numbers | Hallucination | Replace with vague phrasing (`跑了一会儿`) |
| `hydration_reminder` repeated verbatim across 5+ cases | Monotonous, no variation | Rotate 3+ variants, sometimes pair with HR state |
| `session_end` with HR ≥175 but no risk mention | Missed safety flag | Always mention elevated HR in end summary |
| `km_milestone` + HR ≥175 but only celebrates distance | Ignores cardiovascular risk | Combine milestone + HR guidance |
| `heartRate_high` trigger but reply says `偏高` for HR≥190 | Understates severity | Use `立刻停下来` / `马上慢走` for HR≥190 |
| `pace_fast_sustained` + HR≥175 but reply is casual | Dangerous combo downplayed | Strong stop + recovery protocol |
| Reply uses traditional Chinese characters (`謝謝`→`謝謝`) | Simplified/traditional mix | Normalize to simplified |
| Same metaphor (`deadline`/`KPI`/`连环call`) used 3+ times in one reply | Repetitive, monotonous | Cap at 1-2 per reply, rotate metaphors |
| `宝子` used in every single reply | Overused称呼 | Vary with `你` / `咱` / 直接省略 |

### Persona-Specific Detectors

When reviewing output for a specific coach persona (e.g. `jianghu_master`), add persona-specific tone checks:

| Persona | Bad Pattern | Problem | Preferred |
|---|---|---|---|
| 江湖师傅 (jianghu_master) | 女教练场景用 `撑住`/`硬闯`/`扛住`/`熬过来` | 语气偏硬，与柔和女教练人设冲突 | `顺一顺`/`慢慢来`/`不着急` |
| 江湖师傅 (jianghu_master) | 弱数据场景说 `跑了有一会儿了` | 距离/时间极短时不合常理 | `刚开始，别急` |
| 江湖师傅 (jianghu_master) | 心率≥180 只说 `偏高`/`慢下来` | 安全指令不够明确 | `先停跑改慢走`/`别跑了` |
| 江湖师傅 (jianghu_master) | `km_milestone` + HR>165 只报距离 | 忽略心率风险 | 结合距离+心率双重指导 |
| 江湖师傅 (jianghu_master) | 补水提醒 `<8` 字 | 过短生硬，缺乏关心 | `润润喉，别等渴了才喝` |
| 江湖师傅 (jianghu_master) | 同一回复重复 `两步一吸两步一呼` | 啰嗦重复 | 只说一次 |
| 江湖师傅 (jianghu_master) | 同一回复重复 `按这个节奏继续跑` | 啰嗦重复 | 只说一次 |
| 江湖师傅 (jianghu_master) | `session_end` 总结数据错误 | 距离/时间/速度计算错误 | 核对输入metrics，确保总结数据准确 |
| 江湖师傅 (jianghu_master) | `hydration_reminder` 只说"润喉" | 过短，缺乏场景感 | `骑了X公里了，润喉一口，齿比别变` |
| 江湖师傅 (jianghu_master) | 摔车/疼痛场景回复像AI模板 | 开头"先停止运动，转移到安全位置"像机器人 | 用人设口吻：`徒儿！人没事吧？先靠边...` |
| 江湖师傅 (jianghu_master) | 回复含英文残词/单词 | `atest`、`humour`等 | 删除英文，补全中文表达 |
| 江湖师傅 (jianghu_master) | 用词错误 | `幌一眼`→`晃一眼`、`跑出去`→`骑出去` | 根据场景使用正确动词 |
| 江湖师傅 (jianghu_master) | 术语表述混乱 | `把链条挂到大盘上` | 用用户易懂的说法：`齿比调轻一档` |
| 江湖师傅 (jianghu_master) | 女教练场景使用 `为师` 自称 | 性别称谓冲突（为师偏男性化） | 改用 `师父` / `我` / `本座`，或接受为风格化设定但需统一 |
| 江湖师傅 (jianghu_master) | `算盘珠子` 自嘲梗 | 现代意象与江湖师父古典气质冲突，且易套路化（一批次可出现10+次） | `心里翻江倒海` / `七上八下` / `捏了把汗` |
| 江湖师傅 (jianghu_master) | `这口气还不必定性高低` | 病句模板，`定性高低`完全不通，常整批重复出现 | `这口气还说不准是高是低` / `先别急着下定论` |
| 江湖师傅 (jianghu_master) | `气沉在脚下` | 搭配不当 | `气沉丹田` / `劲沉脚下` |
| 江湖师傅 (jianghu_master) | `踩水上落叶` | 意象矛盾（水上落叶无法承载脚步） | `踩落叶` / `踏薄冰` / `点水而过` |
| 江湖师傅 (jianghu_master) | `既毕`（如`热身既毕`） | 过于文言，与整体半文半白语体不协调 | `热身已毕` / `热完身了` |
| 江湖师傅 (jianghu_master) | `破纪录` / `配重` / `进入中段` | 现代术语，破坏江湖沉浸感 | `破了自己的功课` / `身法的秤砣` / `行到中段` |
| 江湖师傅 (jianghu_master) | `瞎倒腾` / `自个` | 过于口语化，与师父身份不符 | `瞎折腾` / `自己` |
| 江湖师傅 (jianghu_master) | `架式` | 错别字 | `架势` |
| 江湖师傅 (jianghu_master) | `打尖`（如`像过村打尖似的`） | 过于生僻，多数用户不懂 | `打尖`→`歇脚补水` / `路过茶棚` |
| 江湖师傅 (jianghu_master) | `蹲坑时间长了站起来也未必稳当` | 粗俗表达，对用户不尊重 | 删除或改为`久坐起身也难免发飘` |
| 江湖师傅 (jianghu_master) | `早市大妈说跑得急` | 风格突兀，与江湖人设不一致 | 删除或改为江湖场景自嘲 |
| 江湖师傅 (jianghu_master) | `低头看一眼鞋带`（跑步中） | 安全隐患建议 | `先靠边停下，检查鞋带` |
| 江湖师傅 (jianghu_master) | `收功后吃点什么`（热身刚结束场景） | 跑题，与当前场景不符 | 聚焦当前阶段指导 |
| 江湖师傅 (jianghu_master) | `不必。`（独立成句） | 语义不完整，病句 | `不必硬撑。` / 删除 |
| 江湖师傅 (jianghu_master) | 心率≥175 仅说 `先喘口气再说` | 无实质安全建议 | 明确 `改慢走` / `停下来` + 补水 |
| 江湖师傅 (jianghu_master) | 同一意象（如`踩落叶`）整批出现10+次 | 意象单一，审美疲劳 | 轮换：落叶/薄冰/点水/梅花桩/薄雪/青草 |
| 江湖师傅 (jianghu_master) | 完全无 `徒儿`/`为师`/`功夫` 等人格标记词 | 退化为普通健身教练口吻（一批次可占20%） | 至少保留一处人设标记 |
| 办公室戏精 (office_drama) | `宝子` 每句必用 | 称呼过度饱和 | 交替使用 `你` / 直接省略 / 偶尔 `宝子` |
| 办公室戏精 (office_drama) | 同一回复中 `deadline`/`KPI`/`连环call`/`述职PPT`/`周报` 出现3+次 | 隐喻重复，审美疲劳 | 每回复最多2个职场隐喻，轮换使用 |
| 办公室戏精 (office_drama) | `不用写复盘` 在慢配速场景反复出现 | 表达单一 | 轮换：`不用赶`/`慢慢磨`/`不催你`/`OKR没催` |
| 办公室戏精 (office_drama) | 补水提醒全是 `别等身体在群里@你` | 零变化 | 结合心率状态换说法：`润一口，别让嗓子开静音会议` |
| 办公室戏精 (office_drama) | 开场/结束语固定模板 `来了来了，下班副本开启` | 套路化 | 准备3-4个开场变体 |
| 办公室戏精 (office_drama) | 高心率结束总结仍说 `这KPI完成得漂亮` | 鼓励危险行为 | HR≥175时必须指出 `心率偏高，下次注意控制` |
| 办公室戏精 (office_drama) | 用户说 `别报心率` 后仍提数字 | 不遵守用户指令 | 完全移除该回复中的所有HR数字 |
| 办公室戏精 (office_drama) | 用户说 `心率播报静音` 后回复仍很长 | 未响应静音请求 | 缩短至 ≤15字确认 |
| 办公室戏精 (office_drama) | 弱数据场景编造具体时长/距离 | 幻觉 | 用模糊表达：`跑了一会儿`/`刚开始` |
| 办公室戏精 (office_drama) | 用户说 `不要一直说话` 后回复仍长 | 未响应安静请求 | 缩短至 ≤20字 |
| 办公室戏精 (office_drama) | 繁体字混入 (`謝謝我聽見了`) | 人设不一致 | 统一简体 |
| 办公室戏精 (office_drama) | `差点绊倒` 先说停又说继续跑 | 安全建议前后矛盾 | 坚持要求完全停下检查 |
| 办公室戏精 (office_drama) | `heartRate_high` + HR≥190 只说 `偏高` | 轻描淡写极端风险 | 使用 `立刻停下来` / `马上慢走` |
| 办公室戏精 (office_drama) | `workout_started` + HR≥170 只说 `收一收` | 起步过剧未充分警告 | 强烈建议先慢走热身 |
| 办公室戏精 (office_drama) | `km_milestone` + HR≥175 只庆祝距离 | 忽略心率风险 | 结合距离+心率双重指导 |
| 办公室戏精 (office_drama) | `hydration_reminder` + HR≥175 只说喝水 | 错过双警告机会 | 配对：`润一口，心率也偏高，注意` |

### Cycling data cross-check

When reviewing running coach output (workoutType: running), add these running-specific patterns:

| Bad Pattern | Problem | Preferred |
|---|---|---|
| `跑下来` | Says "finished" mid-workout or at end | `跑完` |
| `走下来` | Says "finished walking" mid-workout or at end | `走完` |
| `呼吸拉长` | Ambiguous (deepen? slow down?) | `呼吸放慢一点` / `加深呼吸` |
| `收到` + pace/number | Walkie-talkie jargon for "drop to" | `压到` / `降到` / `控制在` |
| `收到` + instruction | Walkie-talkie jargon | `知道了` / `OK` / `行` |
| `LSD` / `VO2max` / `乳酸阈值` / `有氧基础` | Domain jargon users don't know | `长距离慢跑` / `最大摄氧量` / `身体转点` / `耐力底子` |
| `开外` for pace ranges | Misused word | `之间` |
| `bpm` / `BPM` | Abbreviation users don't say aloud | remove, just state the number |
| `满X公里了` | Unnatural colloquialism | `跑到X公里了` |
| `心率偏高先把` | Missing punctuation, keyword stack | `心率偏高，先把…` |
| `在线` for capability | Internet slang | `不错` / `够用` |
| `了了` / repeated `了` | Typo / token echo | single `了` |
| `这场` | Written-style classifier | `这次` |
| Heart rate ≥190 but reply says "收一档" | Insufficient urgency for extreme HR | `立刻停下来` / `马上慢走` |
| Heart rate ≥185 + pace < 5:00 | Dangerous combination | Strong stop recommendation |
| Knee pain (`膝盖疼`) + reply says "慢走试试" | Insufficient safety response | `先别跑了，停下来观察` |
| User can't breathe (`喘不上气`) + HR ≥175 + no stop | Safety risk | `立刻停下来，改成慢走` |
| `session_end` < 60 chars | Too brief for a wrap-up | Include data summary + next advice |
| `session_end` missing `下次` / `建议` | No forward guidance | Add `下次可以…` / `建议…` |
| `periodic_update` at 90min+ with no hydration mention | Long run needs fuel reminder | `记得补水` / `喝点水` |
| Weak data (no HR/pace) + no body-awareness guidance | Lost without metrics | `按体感跑` / `感受呼吸和落脚` |
| `user_input` empty message + no encouragement | Missed engagement opportunity | `跑得不错，继续保持` |
| `invalid_trigger` but persona maintained | Good — no issue | — |
| `workout_started` with HR ≥170 + no slow-start warning | Overexertion risk | `起步心率有点高，先放慢` |
| `hydration_reminder` with HR ≥175 + no HR mention | Missed dual warning | `润一口，心率也偏高，注意` |
| `pace_slow_sustained` at 10:00+ but told to "提步频" | May be unrealistic for beginner | `先稳住节奏，慢慢找感觉` |
| `pace_improving_sustained` at 11:00+ but told "提起来了" | Overstating minor improvement | `比刚才顺一点了，保持住` |
| `online_presence` at 5m/20min with no body check | Weak data check-in | `呼吸还顺吗？脚下感觉怎么样？` |
| `km_milestone` + HR > 165 but no HR mention | Ignores elevated heart rate at milestone | 结合距离+心率双重指导 |
| `hydration_reminder` < 8 chars | Too brief, lacks warmth | `润润喉，别等渴了才喝` |
| Weak data (dist < 500m or dur < 300s) + `跑了有一会儿了` | Contextually absurd | `刚开始，别急` |

### Cycling data cross-check

```python
def pace_to_speed(pace_str):
    """Convert pace 'M:SS' to km/h."""
    m, s = map(int, pace_str.split(':'))
    min_per_km = m + s / 60
    return round(60 / min_per_km, 1) if min_per_km > 0 else 0

# Example: pace "3:14" → 18.5 km/h
# If reply says "均速25" but pace is "3:14", flag mismatch
```
