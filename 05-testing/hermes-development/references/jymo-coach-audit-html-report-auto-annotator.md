# Auto-Annotating Coach Chat HTML Reports

## Purpose
When a `coach_chat_report_*.html` file is too large to read line-by-line (10k+ lines), use this automated approach to add a "修改建议" column with rule-based analysis.

## Python Script Pattern

```python
import re

with open('coach_chat_report_*.html', 'r', encoding='utf-8') as f:
    content = f.read()

def analyze_reply(reply_text):
    suggestions = []
    
    # Metaphor fatigue check
    metaphor_count = reply_text.count("像")
    if metaphor_count >= 1:
        suggestions.append(f"比喻句过多(含'像'×{metaphor_count})，建议每3-5条回复用1次")
    
    # Repetitive phrase checks (customize per persona)
    if reply_text.count("齿比") >= 1:
        suggestions.append("'齿比调/松一调'重复，建议轮换：'档位轻一档'、'踏频稳一点'")
    
    if "往前推" in reply_text or "继续往前" in reply_text:
        suggestions.append("'往前推/继续往前'重复，建议轮换：'保持这个节奏'、'就这样顺下去'")
    
    if "KPI" in reply_text or "项目" in reply_text or "交付" in reply_text:
        suggestions.append("办公室梗(KPI/项目/交付)使用合理，但不要每条都带，建议间隔使用")
    
    if not suggestions:
        return "表达自然，无明显问题"
    
    return "；".join(suggestions[:2])

# Add header column
content = content.replace(
    '<th>输出</th>\n</tr>',
    '<th>输出</th>\n  <th>修改建议</th>\n</tr>'
)

# Add CSS for new column
content = content.replace(
    '.reply { max-width: 480px; line-height: 1.5; }',
    '.reply { max-width: 480px; line-height: 1.5; }\n  .suggestion { max-width: 400px; line-height: 1.5; color: #c2410c; font-size: 12px; background: #fff7ed; }'
)

# Find all reply cells and append suggestion
pattern = r'<td class="reply">([^<]+)</td>\s*</tr>'

def replacer(match):
    reply_text = match.group(1)
    suggestion = analyze_reply(reply_text)
    return f'<td class="reply">{reply_text}</td>\n<td class="reply suggestion">{suggestion}</td>\n</tr>'

new_content = re.sub(pattern, replacer, content)

with open('*_reviewed.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
```

## Key Notes
- The regex `([^<]+)` assumes reply text contains no HTML tags. If replies contain `<br>` or other tags, adjust the regex.
- CSS class `suggestion` uses orange (`#c2410c`) on light orange background (`#fff7ed`) for visibility without being as alarming as red.
- Limit suggestions to 2 per row to keep table width manageable.
- The analysis function should be customized per persona — different personas have different repetitive phrase clusters.

## When to Use
- Bulk test reports with 500+ rows
- Initial persona quality assessment
- Before/after prompt A/B comparison
