# CSV-to-HTML Report — Reproduction Recipe

## Session Context
- Source: `/Users/chao/Desktop/csv/query_result.csv` (72MB, 4035 records, 19 columns)
- Output: `/Users/chao/Desktop/csv/ai_usage_report.html` (1111 KB)
- User request: group by date → user → model, show uid/time/model, summarize daily duration and model call counts, leadership-ready design

## Key Fields Extracted
- `user_id` — grouping dimension 2
- `model` — grouping dimension 3 + badge color
- `created_at` → parsed to `date` (YYYY-MM-DD) and `time` (HH:MM:SS)
- `duration_ms` — aggregated per user per day

## Aggregation Logic
```python
from collections import defaultdict

date_user_stats = defaultdict(lambda: defaultdict(lambda: {
    'total_duration_ms': 0,
    'model_counts': defaultdict(int),
    'records': []
}))

for d in data:
    date_user_stats[d['date']][d['user_id']]['total_duration_ms'] += d['duration_ms']
    date_user_stats[d['date']][d['user_id']]['model_counts'][d['model']] += 1
    date_user_stats[d['date']][d['user_id']]['records'].append(d)
```

## Design Decisions
- Dark theme with orange (#ff6b35) accent — matches user's existing project branding
- Model badges color-coded: TTS = green, MiniMax = yellow
- User avatar = first 2 chars of UID uppercase
- Summary cards at bottom: total calls, active users, total duration, top model
- CSS bar chart for model distribution — no external JS
- `@media print` flips to white background for clean printing

## Stats from This Run
- Records: 4,035
- Unique users: 11
- Date range: 2026-06-15 to 2026-06-21
- Total duration: 448.5 minutes
- Top model: MiniMax-M2.5
