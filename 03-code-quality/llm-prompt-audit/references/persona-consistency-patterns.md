# Persona Consistency & Theatricality Audit Patterns

Cross-output patterns for auditing whether an AI persona maintains character consistency, emotional range, and lexical variety across a batch of generated responses.

## When to Use

- After running batch tests (100+ rows) against a persona prompt
- When user says "check if responses match the persona" or "review character consistency"
- When persona feels "flat" or "repetitive" despite individual responses looking OK

## 1. Cross-Output Repetitive Phrase Detection

### Technique

Count phrase occurrences across ALL outputs in the batch. Flag phrases that appear too frequently.

```python
def count_phrases_across_outputs(outputs, threshold_ratio=0.05):
    """
    outputs: list of all generated reply strings
    threshold_ratio: flag if phrase appears in more than N% of outputs
    """
    from collections import Counter
    import re
    
    # Extract candidate phrases (2-6 word sequences)
    all_phrases = Counter()
    for output in outputs:
        words = re.findall(r'[\u4e00-\u9fff]+', output)  # Chinese words
        for n in range(2, 7):
            for i in range(len(words) - n + 1):
                phrase = ''.join(words[i:i+n])
                all_phrases[phrase] += 1
    
    threshold = len(outputs) * threshold_ratio
    flagged = {phrase: count for phrase, count in all_phrases.items() 
               if count > threshold and len(phrase) >= 4}
    return flagged
```

### Thresholds

| Batch Size | Flag Ratio | Example |
|------------|-----------|---------|
| 100 | >10% (10+ times) | Phrase appears in 10+ outputs |
| 500 | >5% (25+ times) | Phrase appears in 25+ outputs |
| 1000 | >3% (30+ times) | Phrase appears in 30+ outputs |

### Common Culprits by Persona Type

| Persona | Overused Phrases Found | Suggested Variants |
|---------|----------------------|-------------------|
| office_drama | 赶会模式 (131x/500), 周报 (71x), 步幅收小一点 (66x) | 汇报模式/加班模式/被老板@模式/deadline模式; 复盘/OKR/排期/会议纪要; 步子压一压/别迈那么大 |
| wuxia_master | 徒儿 (N x), 真气/内力 | Vary address: 小子/姑娘/你; Vary energy terms |
| friendly_coach | 很棒/不错/加油 (N x) | 具体 praise: "这段稳"/"节奏对了"/"呼吸顺了" |

## 2. Theatricality / Emotional Range Assessment

### Technique

Score each output on emotional markers. A "戏精" persona should have HIGH scores; a calm mentor should have LOW scores (consistency is key).

```python
def assess_theatricality(reply, expected_persona_type='dramatic'):
    """
    expected_persona_type: 'dramatic' | 'calm' | 'professional'
    Returns dict of scores and flags
    """
    scores = {
        'exclamation_marks': reply.count('！') + reply.count('!'),
        'question_marks': reply.count('？') + reply.count('?'),
        'internet_slang': sum(1 for w in ['宝子', '家人们', '绝了', '救命', 'yyds', '栓Q'] if w in reply),
        'exaggeration_words': sum(1 for w in ['太', '超级', '巨', '爆', '炸', '疯', '死'] if w in reply),
        'emoticons': len(re.findall(r'[\ud83c-\udbff\udc00-\udfff]', reply)),  # Unicode emoji
    }
    
    if expected_persona_type == 'dramatic':
        # Dramatic persona SHOULD have these
        if scores['exclamation_marks'] == 0 and scores['question_marks'] == 0:
            return "FLAT: 缺少情绪起伏（无感叹号/反问句）"
        if scores['internet_slang'] == 0 and scores['exaggeration_words'] == 0:
            return "FLAT: 缺少网络热梗或夸张表达"
    
    elif expected_persona_type == 'calm':
        # Calm persona should NOT have too many
        if scores['exclamation_marks'] > 2:
            return "TOO_DRAMATIC: 平静人设不应有多重感叹"
    
    return "OK"
```

### Batch-Level Emotional Range

```python
def assess_batch_emotional_range(outputs, persona_type='dramatic'):
    """Check if the persona shows consistent emotional range across batch."""
    total = len(outputs)
    with_exclamation = sum(1 for o in outputs if '！' in o or '!' in o)
    with_question = sum(1 for o in outputs if '？' in o or '?' in o)
    with_slang = sum(1 for o in outputs if any(w in o for w in ['宝子', '家人们', '绝了']))
    
    if persona_type == 'dramatic':
        if with_exclamation / total < 0.05:
            return f"情绪范围不足: 仅{with_exclamation}/{total}条有感叹号，戏精人设需要更多情绪起伏"
        if with_question / total < 0.02:
            return f"互动感不足: 仅{with_question}/{total}条有反问句"
    
    return "情绪范围OK"
```

## 3. Robotic Response Detection

### Patterns to Flag

| Pattern | Why It's Bad | Better Alternative |
|---------|-------------|-------------------|
| `^收到` | Walkie-talkie, no persona | `好嘞` / `明白` / `收到over` / `OKK` / `遵命` |
| `^好的，` | Generic acknowledgment | Persona-specific: `得嘞` / `成` / `没问题` |
| `先把...，然后...，最后...` | Overly structured, no warmth | Break structure, add asides or personality |
| `亮点是...可改...` (session_end) | Template report | Persona-wrapped summary: "这班演得..." / "给你颁个奖..." |

### Detection Regex

```python
ROBOTIC_PATTERNS = [
    (r'^收到[,，]', "机械回应: '收到'像对讲机"),
    (r'^好的[,，]', "机械回应: '好的'过于 generic"),
    (r'亮点是.*可改', "模板化总结: session_end像标准报告"),
    (r'先停止运动，转移到安全位置', "安全模板: 完全脱离人设的标准手册语言"),
]

def detect_robotic_patterns(reply):
    flags = []
    for pattern, reason in ROBOTIC_PATTERNS:
        if re.search(pattern, reply):
            flags.append(reason)
    return flags
```

## 4. Safety Response Persona-Break Detection

### The Problem

When user reports injury/danger, the model often switches to **template safety language** that completely breaks character.

### Example (office_drama persona)

**Bad:**
```
先停止运动，转移到安全位置。先检查是否有明显出血、肿胀或无法承重，
10到15分钟内冷敷患处并避免继续发力。若疼痛持续、肿胀加重或出现头晕胸闷，尽快就医。
```

**Good (same persona):**
```
先停！别演了！检查一下有没有事，疼得厉害就收工，身体比KPI重要！
```

### Detection

```python
SAFETY_TEMPLATE_MARKERS = [
    '先停止运动，转移到安全位置',
    '检查是否有明显出血',
    '冷敷患处',
    '避免继续发力',
    '尽快就医',
    '若疼痛持续',
]

def detect_safety_persona_break(reply, trigger_type, user_msg):
    if user_msg and any(w in user_msg for w in ['摔', '绊', '疼', '伤', '晕']):
        for marker in SAFETY_TEMPLATE_MARKERS:
            if marker in reply:
                return f"安全提示人设割裂: 出现标准手册语言'{marker[:15]}...'"
    return None
```

## 5. Response Length & Engagement Patterns

### Too Short = Missing Persona Voice

| Context | Min Length | Flag If Shorter |
|---------|-----------|----------------|
| `hydration_reminder` | 15 chars | "补水提醒过短，缺少人设絮叨感" |
| `session_end` | 40 chars | "结束语过短，应总结+鼓励" |
| `user_input` (complex) | 30 chars | "用户问题较复杂，回复过短" |
| `km_milestone` | 20 chars | "里程碑应给予成就感" |

### Too Long = Rambling

| Context | Max Length | Flag If Longer |
|---------|-----------|----------------|
| User says "少说点" | 15 chars | "用户要求极简，回复过长" |
| `periodic_update` (normal) | 80 chars | "定期播报过长" |

## 6. Complete Audit Function

```python
def full_persona_audit(reply, trigger_type, hr=None, pace=None, 
                       distance=None, duration=None, user_msg=None,
                       persona_type='dramatic', all_outputs=None):
    """
    Full persona consistency audit combining safety, scene, respect, 
    terminology, AND theatricality/persona-consistency checks.
    """
    issues = []
    
    # === Existing checks (safety, scene, respect, terminology) ===
    # ... (see audit_running_coach_outputs.py)
    
    # === NEW: Robotic pattern detection ===
    robotic = detect_robotic_patterns(reply)
    issues.extend(robotic)
    
    # === NEW: Safety persona break ===
    safety_break = detect_safety_persona_break(reply, trigger_type, user_msg)
    if safety_break:
        issues.append(safety_break)
    
    # === NEW: Theatricality (for dramatic personas) ===
    if persona_type == 'dramatic':
        theatrical = assess_theatricality(reply, persona_type)
        if theatrical != "OK":
            issues.append(theatrical)
    
    # === NEW: Length checks ===
    if trigger_type == 'hydration_reminder' and len(reply) < 15:
        issues.append("补水提醒过短，缺少人设絮叨感")
    if trigger_type == 'session_end' and len(reply) < 40:
        issues.append("结束语过短，应总结+鼓励")
    
    return "；".join(issues) if issues else "✅ 无明显问题"
```

## 7. Report Generation

### HTML Column Addition

```python
def add_suggestion_column(original_html, suggestion_map):
    """Add CSS, header, and suggestion cells to HTML report."""
    # Add CSS
    css_addition = '''
  .suggestion { max-width: 320px; line-height: 1.5; color: #92400e; 
                background: #fef3c7; padding: 8px 10px; border-radius: 6px; 
                font-size: 12.5px; white-space: pre-wrap; }
  .suggestion-ok { color: #166534; background: #dcfce7; }
  .suggestion-issue { color: #991b1b; background: #fee2e2; }
'''
    modified = original_html.replace("</style>", css_addition + "\n</style>")
    
    # Add header
    modified = modified.replace(
        "  <th>输出</th>\n</tr>\n</thead>",
        "  <th>输出</th>\n  <th style=\"min-width:320px\">修改建议</th>\n</tr>\n</thead>",
    )
    
    # Add cells per row
    for idx, suggestion in suggestion_map.items():
        row_start = modified.find(f"<td>{idx}</td>")
        if row_start == -1:
            continue
        tr_end = modified.find("</tr>", row_start)
        if tr_end == -1:
            continue
        
        css_class = "suggestion-ok" if suggestion == "✅ 无明显问题" else "suggestion"
        cell = f'<td class="{css_class}">{suggestion}</td>\n'
        modified = modified[:tr_end] + cell + modified[tr_end:]
    
    return modified
```

### Summary Dashboard

Add a summary block at the top of the HTML report:

```html
<div style="background:#fef3c7; border:2px solid #f59e0b; border-radius:12px; padding:24px; margin:20px;">
  <h2>Persona Audit Summary</h2>
  <ul>
    <li>Total rows: {total}</li>
    <li>Critical issues: {critical} ({critical/total*100:.1f}%)</li>
    <li>Repetitive phrases: {len(repetitive_phrases)}</li>
    <li>Flat tone: {flat_count} ({flat_count/total*100:.1f}%)</li>
  </ul>
</div>
```

## Pitfalls

- **Don't flag every repetition** — some repetition is natural (e.g., "呼吸" will appear often in a coach). Only flag phrases that are clearly overused relative to batch size.
- **Persona type matters** — a "calm mentor" SHOULD be flat; only flag theatricality issues when persona claims to be dramatic/expressive.
- **Context matters for length** — `user_input` with "嗯" can be short; `session_end` should never be.
- **Safety overrides theatricality** — if HR is dangerous, clear safety language is more important than staying in character. But safety CAN be wrapped in persona voice.
- **Cross-output analysis requires full batch** — single-row analysis cannot detect repetition. Must read entire report first.
