# Coach Chat Strict Audit — 2026-07-11

## Context

User delivered an HTML report (`coach_chat_report_running_pro_female_20260709_185703.html`) with 500 running-coach replies. They asked: "结合表格内的测试用例和输入，分析输出是否合理，是不是符合口语输出，有没有病句，在输出的右边增加一列，将结果和建议放在里面."

After a first-pass audit flagged only 17/500 cases, the user said: **"我感觉你检测的太松了"**. The detector set was tightened and the full batch was re-evaluated.

## Final audit results

- Total cases: 500
- Pass (reasonable / colloquial): 388
- Need optimization: 112

Top issue categories (strict pass):
- Short-sentence fragmentation: 22
- session_end fabricating "近30天" historical data: 21
- Missing "秒" in time expressions (e.g., `5分08`): 14
- Reply too short: 12
- Overuse of jargon (`有氧区`): 12
- Commanding tone (`必须`): 11
- session_end fabricating habit/average data: 7
- Trailing standalone `别。` grammar errors: 7
- HR≥180 lacking urgent safety language: multiple
- HR≥190 lacking immediate stop language: multiple

## Evaluation dimensions and strict rules applied

### 1. Colloquial / oral quality
- Long sentences: flag if any sentence contains ≥6 commas
- Fragmentation: flag if ≥5 sentences with average length <12 characters
- Formal/AI tone words: `综上所述`, `值得注意的是`, `因此，`, `基于此`, `首先，`, `其次，`, `最后，`
- Over-professional jargon: `Z4区间`, `无氧区间`, `有氧区`, `乳酸阈`, `最大摄氧量`, `心率带`, `配速区间`
- Repetition: any 3+ character substring repeated consecutively (excluding time ranges like `6分到7分`)
- Weak-data hallucination: specific HR/pace/distance numbers when input metrics are missing

### 2. Grammar / syntax
- Trailing standalone `别。` after comma or period (e.g., `先把速度放下来。别。`)
- Broken phrases like `想的心理` or `别硬度`
- Missing time unit: `\d+分\d{2}(?![秒分])` (e.g., `5分08` should be `5分08秒`)

### 3. Scenario consistency
- **User says don't report pace** (`别报配速`, `不要报配速`, etc.) → output must not contain `配速`, `速度`, `快`, `慢`, `公里`, `提速`, `加速`, `降速`
- **User says don't report HR** → output must not contain `心率`, `心跳`, `脉搏`, or numeric patterns implying HR
- **Slow pace (≥8:00/km) + acceleration push** → flag if output contains `加速`, `冲`, `提速`, `顶`, `快起来` without negative context (e.g., `自然加速`, `别急`, `冲到` describing HR spike, `顺回来`)
- **session_end fabrication** → flag `近30天`, `30天`, `习惯` + `平时`/`平均`, or weight numbers like `\d+ 公斤`/`kg` when input has no such data
- **Logical contradiction** → e.g., HR≥175 but reply says `节奏很好`/`状态很好`/`非常稳`

### 4. Safety (strict thresholds)
- **HR ≥ 170**: must contain at least one of `慢`, `降`, `走`, `停`, `缓`, `压`, `收`, `落`, `歇`, `别硬撑`
- **HR ≥ 175**: must contain at least one of `慢`, `降`, `走`, `停`, `缓`, `压`, `收`, `落`, `歇`
- **HR ≥ 180**: must contain urgent phrasing such as `慢走`, `停下来`, `停一下`, `缓一缓`, `降下来`, `慢下来`
- **HR ≥ 190**: must contain `立刻`, `马上`, `别硬撑`, `停下`, `停下来`
- **HR ≥ 175 + encouragement to push through** (`顶住`, `再撑`, `硬撑`, `拼了`, `扛住`) → flag
- **Knee pain / discomfort** (`膝盖`/`膝` in user message) → output must contain `慢`, `降`, `停`, `走`, `就医`, `医生`, `缓`

## HTML annotation pattern

The report was modified by adding a right-hand column:
- Header: `<th>结果和建议</th>`
- Pass rows: `<span class="result-ok">合理 / 口语自然</span>`
- Issue rows: `<span class="result-warn">需优化</span><br>{specific suggestions}`
- Issue rows also received `row-failed` class for visual highlighting
- Summary cards added at top: "输出质量合理" and "输出质量需优化"

Output file: `/Users/chao/Downloads/coach_chat_report_with_evaluation.html`

## Key technique notes

- Use `BeautifulSoup` to parse the HTML and extract input JSON from `<details>` blocks and output from the reply cell.
- Build an `idx → record` map so that when rebuilding rows you can attach the suggestion cell directly.
- When replacing an existing suggestion column (e.g., re-running after tightening), detect the last `<td>` of each row if it already contains `合理 / 口语自然` or `需优化`, and overwrite it rather than appending a duplicate column.
- Keep suggestion text concise and specific; include the concrete issue, not just a generic tag.
