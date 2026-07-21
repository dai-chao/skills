---
name: ai-service-cost-comparison
title: AI Service Cost Comparison Analysis
description: |
  Build multi-currency price comparison tables for AI model APIs (LLM, TTS, etc.)
  from JSON usage logs. Outputs a styled Excel workbook with automatic cost
  calculations, exchange-rate conversion, and side-by-side provider comparison.
triggers:
  - user asks to compare AI model pricing across providers
  - user provides API usage logs and wants cost analysis
  - need to calculate LLM / TTS / image generation costs from logs
  - multi-currency price comparison for cloud AI services
requires:
  - python3 with openpyxl (use /usr/bin/python3 on macOS, not venv)
  - json usage logs from the AI platform
  - unit pricing for each provider/model
---

# AI Service Cost Comparison Analysis

## 1. Design the Excel Framework

Create a workbook with these sheets:

| Sheet | Purpose |
|-------|---------|
| `汇率配置` | Exchange-rate placeholders (USD→CNY, platform-token→CNY, etc.) |
| `{Service}价格对比` | One sheet per service type (TTS, LLM, image, etc.) |
| `综合成本汇总` | Auto-pull subtotals and compute share % |

**Key columns per comparison sheet:**
- 服务商 / 模型 / 计费项
- 原始单价 + 币种
- 统一CNY单价 (formula-driven from exchange-rate sheet)
- 预估调用量 (yellow highlight — user fills or script injects)
- 预估总成本 (CNY)
- vs 基准差额 (CNY + %)

**Styling conventions:**
- Green rows = Provider A (e.g., 云雾)
- Orange rows = Provider B (e.g., 阿里云)
- Yellow cells = editable call-volume placeholders
- Blue header + grey subtotal rows

## 2. Parse JSON Usage Logs

Save the JSON to disk first (logs can be large), then parse with Python:

```python
import json
with open('/path/to/logs.json') as f:
    data = json.load(f)
items = data['data']['items']
```

**Common log fields to aggregate:**
| Service | Field | Unit |
|---------|-------|------|
| LLM | `prompt_tokens` | tokens |
| LLM | `completion_tokens` | tokens |
| LLM | `other['cache_tokens']` | tokens (cache hit) |
| TTS | `other['char_units']` | 万字符 |
| TTS | `other['actual_chars']` | characters |

**Aggregate loop pattern:**
```python
total_prompt = sum(i['prompt_tokens'] for i in items)
total_completion = sum(i['completion_tokens'] for i in items)
total_cache = sum(json.loads(i['other']).get('cache_tokens',0) for i in items)
```

## 3. Cost Calculation Formulas

**LLM example (cloud A vs cloud B):**
```
Cloud A cost = (prompt/1e6 * input_price) + (completion/1e6 * output_price)
Cloud B cost = ((prompt-cache)/1e6 * input_price)
             + (cache/1e6 * cache_hit_price)
             + (completion/1e6 * output_price)
```

**TTS example:**
```
Cloud A cost = char_units * price_per_10k_chars
Cloud B cost = char_units * price_per_10k_chars
```

**Currency normalization:**
- Always convert to a single base currency (recommend CNY) for side-by-side comparison.
- Leave exchange rates as editable cells so the user can update them.

## 4. Inject Data Back into Excel

Use `openpyxl` to load the template and overwrite the yellow placeholder cells:

```python
from openpyxl import load_workbook
wb = load_workbook('comparison.xlsx')
ws = wb['文本输出价格对比']
ws['G2'] = round(total_prompt / 1e6, 4)   # input volume
ws['G3'] = round(total_completion / 1e6, 4) # output volume
wb.save('comparison.xlsx')
```

## 5. Environment Pitfall

- The sandbox venv often lacks `pandas` / `openpyxl`.
- **Always use `/usr/bin/python3` on macOS** (it ships with openpyxl).

## 6. Verification Checklist

- [ ] Exchange-rate sheet has editable placeholders
- [ ] All provider rows use distinct colors
- [ ] Volume cells are highlighted yellow before injection
- [ ] Formulas use absolute references (`$H$4`) where needed
- [ ] Subtotal rows sum correctly
- [ ] Summary sheet pulls from all service sheets
