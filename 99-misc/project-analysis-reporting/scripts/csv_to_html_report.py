#!/usr/bin/env python3
"""CSV-to-HTML Report Generator — Leadership-ready self-contained HTML

Usage:
    python3 csv_to_html_report.py /path/to/data.csv /path/to/output.html "Report Title"

Groups data by date → user → model. Produces summary cards, Chart.js charts,
collapsible detail tables, and data insights. Output is a single self-contained
HTML file with no external dependencies (Chart.js loaded from CDN).

Template: project-analysis-reporting/templates/html-report-template.html
"""
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime


def parse_csv(csv_path):
    """Parse CSV and return list of dicts with normalized fields."""
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        # Auto-detect common column names
        col_map = {}
        for i, h in enumerate(header):
            h_lower = h.lower().strip()
            if h_lower in ('user_id', 'userid', 'uid', 'user id', 'user_id'):
                col_map['user_id'] = i
            elif h_lower in ('model', 'model_name', '使用的模型'):
                col_map['model'] = i
            elif h_lower in ('created_at', 'createdat', 'create_time', '时间'):
                col_map['created_at'] = i
            elif h_lower in ('duration_ms', 'duration', '耗时', '运行时长'):
                col_map['duration_ms'] = i

        # Fallback: use first matching column by partial name
        if 'user_id' not in col_map:
            for i, h in enumerate(header):
                if 'user' in h.lower():
                    col_map['user_id'] = i
                    break
        if 'model' not in col_map:
            for i, h in enumerate(header):
                if 'model' in h.lower() or '模型' in h:
                    col_map['model'] = i
                    break
        if 'created_at' not in col_map:
            for i, h in enumerate(header):
                if 'time' in h.lower() or 'date' in h.lower() or '时间' in h:
                    col_map['created_at'] = i
                    break
        if 'duration_ms' not in col_map:
            for i, h in enumerate(header):
                if 'duration' in h.lower() or '耗时' in h or '时长' in h:
                    col_map['duration_ms'] = i
                    break

        for row in reader:
            if not row:
                continue
            try:
                created = row[col_map.get('created_at', 0)]
                # Try common formats
                dt = None
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M',
                            '%Y/%m/%d %H:%M', '%Y-%m-%d'):
                    try:
                        dt = datetime.strptime(created.strip(), fmt)
                        break
                    except ValueError:
                        continue
                if dt is None:
                    continue

                duration = 0
                if 'duration_ms' in col_map:
                    try:
                        duration = int(row[col_map['duration_ms']])
                    except (ValueError, IndexError):
                        pass

                data.append({
                    'user_id': row[col_map.get('user_id', 0)],
                    'model': row[col_map.get('model', 0)],
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M:%S'),
                    'duration_ms': duration,
                })
            except Exception:
                continue
    return data


def aggregate(data):
    """Group by date → user → stats."""
    date_user_stats = defaultdict(lambda: defaultdict(lambda: {
        'total_duration_ms': 0,
        'model_counts': defaultdict(int),
        'records': []
    }))
    model_counts = defaultdict(int)
    user_counts = defaultdict(int)
    daily_counts = defaultdict(int)
    hourly_counts = defaultdict(int)

    for d in data:
        date_user_stats[d['date']][d['user_id']]['total_duration_ms'] += d['duration_ms']
        date_user_stats[d['date']][d['user_id']]['model_counts'][d['model']] += 1
        date_user_stats[d['date']][d['user_id']]['records'].append(d)
        model_counts[d['model']] += 1
        user_counts[d['user_id']] += 1
        daily_counts[d['date']] += 1
        hourly_counts[int(d['time'][:2])] += 1

    return date_user_stats, model_counts, user_counts, daily_counts, hourly_counts


def build_html(data, title="数据报告"):
    date_user_stats, model_counts, user_counts, daily_counts, hourly_counts = aggregate(data)
    total_calls = len(data)
    unique_users = len(user_counts)
    total_duration_min = sum(d['duration_ms'] for d in data) / 60000
    top_model = max(model_counts, key=model_counts.get) if model_counts else 'N/A'
    peak_date = max(daily_counts, key=daily_counts.get) if daily_counts else 'N/A'
    avg_duration = total_duration_min / total_calls if total_calls else 0

    dates = sorted(date_user_stats.keys())
    daily_labels = json.dumps(dates)
    daily_values = json.dumps([daily_counts[d] for d in dates])

    user_labels = json.dumps(list(user_counts.keys())[:10])
    user_values = json.dumps(list(user_counts.values())[:10])

    model_items = sorted(model_counts.items(), key=lambda x: -x[1])[:8]
    model_labels = json.dumps([m[0] for m in model_items])
    model_values = json.dumps([m[1] for m in model_items])
    model_colors = json.dumps([
        '#ff6b35', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7',
        '#dfe6e9', '#fd79a8', '#a29bfe'
    ][:len(model_items)])

    hours = list(range(24))
    hourly_values = json.dumps([hourly_counts.get(h, 0) for h in hours])
    hourly_labels = json.dumps([f"{h:02d}:00" for h in hours])

    # Build detail sections
    detail_sections = []
    for date in dates:
        users = date_user_stats[date]
        user_sections = []
        for user_id in sorted(users.keys()):
            stats = users[user_id]
            total_min = stats['total_duration_ms'] / 60000
            model_breakdown = ', '.join(
                f"{m}: {c}次" for m, c in sorted(stats['model_counts'].items(), key=lambda x: -x[1])
            )
            records_html = ''.join(
                f"<tr><td>{r['time']}</td><td><span class='model-badge'>{r['model']}</span></td><td>{r['user_id']}</td></tr>"
                for r in stats['records']
            )
            user_sections.append(f'''
                <div class="user-section">
                    <div class="user-header" onclick="toggleUser(event, this)">
                        <div class="user-avatar">{user_id[:2].upper()}</div>
                        <div class="user-info">
                            <div class="user-id">用户: {user_id}</div>
                            <div class="user-stats">
                                <span>⏱️ 总耗时: {total_min:.1f} 分钟</span>
                                <span>📊 调用次数: {len(stats['records'])} 次</span>
                                <span class="highlight">🤖 {model_breakdown}</span>
                            </div>
                        </div>
                        <span class="user-toggle">▼</span>
                    </div>
                    <div class="user-content collapsed">
                        <table>
                            <thead><tr><th>时间</th><th>模型名称</th><th>用户ID</th></tr></thead>
                            <tbody>{records_html}</tbody>
                        </table>
                    </div>
                </div>
            ''')

        detail_sections.append(f'''
            <div class="date-section">
                <div class="date-header collapsed" onclick="toggleDate(this)">
                    <div class="left"><span>📅</span><span>{date}</span></div>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="date-content collapsed">
                    {''.join(user_sections)}
                </div>
            </div>
        ''')

    # Insights
    avg_daily = total_calls / len(dates) if dates else 0
    top_user = max(user_counts, key=user_counts.get) if user_counts else 'N/A'
    peak_hour = max(hourly_counts, key=hourly_counts.get) if hourly_counts else 0

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: #fff;
            border-radius: 20px;
            border: 1px solid #e5e5ea;
        }}
        .header h1 {{ font-size: 2.5em; font-weight: 700; color: #1d1d1f; margin-bottom: 10px; }}
        .header .subtitle {{ color: #999; font-size: 1.1em; }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .summary-card {{
            background: #fff;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #e5e5ea;
            text-align: center;
            transition: transform 0.2s;
        }}
        .summary-card:hover {{ transform: translateY(-4px); }}
        .summary-card .icon {{ font-size: 2em; margin-bottom: 10px; }}
        .summary-card h3 {{
            font-size: 0.85em;
            color: #999;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .value {{ font-size: 2.2em; font-weight: 700; color: #1d1d1f; }}
        .summary-card .sub {{ font-size: 0.8em; color: #999; margin-top: 5px; }}
        .card-accent {{ border-top: 3px solid #ff6b35; }}

        .charts-section {{ margin-bottom: 40px; }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
        }}
        .chart-card {{
            background: #fff;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #e5e5ea;
        }}
        .chart-card h3 {{ font-size: 1em; color: #ff6b35; margin-bottom: 16px; }}
        .chart-container {{ position: relative; height: 280px; }}
        .chart-full {{ grid-column: 1 / -1; }}
        .chart-full .chart-container {{ height: 320px; }}

        .analysis-section {{
            background: #fff;
            border-radius: 16px;
            padding: 30px;
            border: 1px solid #e5e5ea;
            margin-bottom: 40px;
        }}
        .analysis-section h2 {{ font-size: 1.3em; color: #ff6b35; margin-bottom: 20px; }}
        .analysis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .analysis-item {{
            background: #fafafa;
            border-radius: 12px;
            padding: 20px;
            border-left: 3px solid #ff6b35;
        }}
        .analysis-item h4 {{ font-size: 0.9em; color: #999; margin-bottom: 8px; }}
        .analysis-item p {{ font-size: 1.1em; color: #1d1d1f; line-height: 1.5; }}
        .analysis-item .highlight {{ color: #ff6b35; font-weight: 600; }}

        .date-section {{
            margin-bottom: 30px;
            background: #fff;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid #e5e5ea;
        }}
        .date-header {{
            background: linear-gradient(90deg, #ff6b35, #e85d04);
            padding: 16px 24px;
            font-size: 1.2em;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
            color: #fff;
        }}
        .date-header .left {{ display: flex; align-items: center; gap: 10px; }}
        .date-header .toggle-icon {{ transition: transform 0.3s; font-size: 0.8em; }}
        .date-header.collapsed .toggle-icon {{ transform: rotate(-90deg); }}
        .date-content {{
            max-height: 20000px;
            overflow: hidden;
            transition: max-height 0.4s ease;
        }}
        .date-content.collapsed {{ max-height: 0; }}

        .user-section {{
            padding: 20px 24px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .user-section:last-child {{ border-bottom: none; }}
        .user-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            user-select: none;
        }}
        .user-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.8em;
            color: #fff;
        }}
        .user-info {{ flex: 1; }}
        .user-id {{ font-size: 1em; font-weight: 600; color: #1d1d1f; }}
        .user-stats {{
            font-size: 0.8em;
            color: #999;
            margin-top: 3px;
        }}
        .user-stats span {{ margin-right: 16px; }}
        .user-stats .highlight {{ color: #ff6b35; font-weight: 600; }}
        .user-toggle {{ font-size: 0.8em; transition: transform 0.3s; }}
        .user-header.collapsed .user-toggle {{ transform: rotate(-90deg); }}
        .user-content {{
            max-height: 20000px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        .user-content.collapsed {{ max-height: 0; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }}
        th {{
            background: #fafafa;
            color: #ff6b35;
            font-weight: 600;
            text-align: left;
            padding: 10px 14px;
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 10px 14px;
            border-bottom: 1px solid #f0f0f0;
            color: #1d1d1f;
        }}
        tr:hover td {{ background: #f5f5f7; }}
        .model-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 16px;
            font-size: 0.8em;
            font-weight: 500;
            background: #eef2ff;
            color: #667eea;
            border: 1px solid #dbe4ff;
        }}

        .footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #999;
            font-size: 0.85em;
        }}

        @media print {{
            body {{ background: #fff; color: #333; }}
            .date-section, .chart-card, .analysis-section, .summary-card {{ background: #fff; border: 1px solid #ddd; }}
            .header {{ background: #fff; }}
            th {{ background: #e9ecef; color: #333; }}
            td {{ color: #333; border-bottom: 1px solid #eee; }}
            .user-id {{ color: #333; }}
            .model-badge {{ border: 1px solid #ccc; }}
            .date-content, .user-content {{ max-height: none !important; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">数据周期: {dates[0] if dates else 'N/A'} 至 {dates[-1] if dates else 'N/A'} | 共 {total_calls} 条记录 | {unique_users} 位用户</div>
        </div>

        <div class="summary-grid">
            <div class="summary-card card-accent">
                <div class="icon">📊</div>
                <h3>总调用次数</h3>
                <div class="value">{total_calls}</div>
                <div class="sub">全部记录</div>
            </div>
            <div class="summary-card card-accent">
                <div class="icon">👥</div>
                <h3>活跃用户数</h3>
                <div class="value">{unique_users}</div>
                <div class="sub">独立用户</div>
            </div>
            <div class="summary-card card-accent">
                <div class="icon">⏱️</div>
                <h3>总运行时长</h3>
                <div class="value">{total_duration_min:.1f}</div>
                <div class="sub">分钟</div>
            </div>
            <div class="summary-card card-accent">
                <div class="icon">🤖</div>
                <h3>最常用模型</h3>
                <div class="value">{top_model}</div>
                <div class="sub">调用最多</div>
            </div>
            <div class="summary-card card-accent">
                <div class="icon">📈</div>
                <h3>峰值日期</h3>
                <div class="value">{peak_date}</div>
                <div class="sub">{daily_counts.get(peak_date, 0)} 次调用</div>
            </div>
            <div class="summary-card card-accent">
                <div class="icon">⏳</div>
                <h3>平均单次耗时</h3>
                <div class="value">{avg_duration:.2f}</div>
                <div class="sub">分钟</div>
            </div>
        </div>

        <div class="charts-section">
            <div class="charts-grid">
                <div class="chart-card chart-full">
                    <h3>📈 每日调用趋势</h3>
                    <div class="chart-container"><canvas id="dailyChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>👤 用户调用分布</h3>
                    <div class="chart-container"><canvas id="userChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>🤖 模型使用占比</h3>
                    <div class="chart-container"><canvas id="modelChart"></canvas></div>
                </div>
                <div class="chart-card chart-full">
                    <h3>⏰ 24小时调用热力分布</h3>
                    <div class="chart-container"><canvas id="hourlyChart"></canvas></div>
                </div>
            </div>
        </div>

        <div class="analysis-section">
            <h2>📋 数据洞察</h2>
            <div class="analysis-grid">
                <div class="analysis-item">
                    <h4>使用活跃度</h4>
                    <p>平均每天 <span class="highlight">{avg_daily:.0f}</span> 次调用，峰值日期 <span class="highlight">{peak_date}</span> 达到 <span class="highlight">{daily_counts.get(peak_date, 0)}</span> 次。整体使用呈{"上升" if daily_counts.get(dates[-1], 0) > daily_counts.get(dates[0], 0) else "波动"}趋势。</p>
                </div>
                <div class="analysis-item">
                    <h4>模型偏好</h4>
                    <p><span class="highlight">{top_model}</span> 是绝对主力，占比 <span class="highlight">{model_counts[top_model]/total_calls*100:.1f}%</span>。共使用 <span class="highlight">{len(model_counts)}</span> 种不同模型，模型选择{"相对集中" if max(model_counts.values())/total_calls > 0.5 else "较为分散"}。</p>
                </div>
                <div class="analysis-item">
                    <h4>时段特征</h4>
                    <p>使用高峰集中在 <span class="highlight">{peak_hour}:00</span> 左右，{"夜间" if peak_hour < 6 or peak_hour > 22 else "白天"}使用{"较少" if peak_hour < 6 or peak_hour > 22 else "活跃"}。平均单次耗时 <span class="highlight">{avg_duration:.2f}</span> 分钟。</p>
                </div>
                <div class="analysis-item">
                    <h4>用户粘性</h4>
                    <p>头部用户 <span class="highlight">{top_user}</span> 调用 <span class="highlight">{user_counts[top_user]}</span> 次，占总量的 <span class="highlight">{user_counts[top_user]/total_calls*100:.1f}%</span>。{"用户分布较为均衡" if user_counts[top_user]/total_calls < 0.3 else "存在明显的头部用户效应"}。</p>
                </div>
            </div>
        </div>

        {''.join(detail_sections)}

        <div class="footer"><p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div>
    </div>

    <script>
        Chart.defaults.color = '#666';
        Chart.defaults.borderColor = '#e5e5ea';

        new Chart(document.getElementById('dailyChart'), {{
            type: 'line',
            data: {{
                labels: {daily_labels},
                datasets: [{{
                    label: '调用次数',
                    data: {daily_values},
                    borderColor: '#ff6b35',
                    backgroundColor: 'rgba(255,107,53,0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }} }}, x: {{ grid: {{ display: false }} }} }}
            }}
        }});

        new Chart(document.getElementById('userChart'), {{
            type: 'doughnut',
            data: {{
                labels: {user_labels},
                datasets: [{{
                    data: {user_values},
                    backgroundColor: ['#ff6b35','#4ecdc4','#45b7d1','#96ceb4','#ffeaa7','#fd79a8','#a29bfe','#dfe6e9'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'right', labels: {{ boxWidth: 12 }} }} }}
            }}
        }});

        new Chart(document.getElementById('modelChart'), {{
            type: 'pie',
            data: {{
                labels: {model_labels},
                datasets: [{{
                    data: {model_values},
                    backgroundColor: {model_colors},
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'right', labels: {{ boxWidth: 12 }} }} }}
            }}
        }});

        new Chart(document.getElementById('hourlyChart'), {{
            type: 'bar',
            data: {{
                labels: {hourly_labels},
                datasets: [{{
                    label: '调用次数',
                    data: {hourly_values},
                    backgroundColor: '#ff6b35',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }} }}, x: {{ grid: {{ display: false }} }} }}
            }}
        }});

        function toggleDate(el) {{
            el.classList.toggle('collapsed');
            el.nextElementSibling.classList.toggle('collapsed');
        }}
        function toggleUser(e, el) {{
            e.stopPropagation();
            el.classList.toggle('collapsed');
            el.nextElementSibling.classList.toggle('collapsed');
        }}
    </script>
</body>
</html>'''


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.csv> <output.html> [title]")
        sys.exit(1)

    csv_path = sys.argv[1]
    output_path = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else "数据报告"

    data = parse_csv(csv_path)
    if not data:
        print("No data parsed from CSV")
        sys.exit(1)

    html = build_html(data, title)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report generated: {output_path}")
    print(f"Records: {len(data)}")


if __name__ == '__main__':
    main()
