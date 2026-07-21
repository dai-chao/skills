#!/usr/bin/env python3
"""
Auto-annotates Jymo coach chat HTML test reports with a "修改建议" column.

Usage:
    python3 auto_annotate_report.py <input.html> [output.html]

If output is omitted, writes to <input>_reviewed.html.
"""

import re
import html
import json
import sys
from pathlib import Path
import typing
from typing import Optional


def extract_metrics(input_json_str: str) -> dict:
    try:
        data = json.loads(input_json_str)
        metrics = data.get("metrics", {})
        return {
            "heartRate": metrics.get("heartRate"),
            "heartRateAvailable": metrics.get("heartRateAvailable", False),
            "pace": metrics.get("pace"),
            "distanceM": metrics.get("distanceM"),
            "durationS": metrics.get("durationS"),
            "triggerType": data.get("triggerType"),
            "userMessage": data.get("userMessage"),
            "workoutType": metrics.get("workoutType"),
        }
    except Exception:
        return {}


def parse_pace(pace_str: str) -> Optional[float]:
    if not pace_str:
        return None
    try:
        parts = pace_str.split(":")
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            total_seconds = minutes * 60 + seconds
            if total_seconds > 0:
                return 3600.0 / total_seconds
        return None
    except Exception:
        return None


def generate_suggestion(metrics: dict, reply_text: str, case_name: str) -> str:
    suggestions = []
    hr = metrics.get("heartRate")
    pace_str = metrics.get("pace")
    trigger = metrics.get("triggerType")
    user_msg = metrics.get("userMessage")
    speed_kmh = parse_pace(pace_str)

    # --- Safety ---
    if hr and hr >= 190:
        has_stop = "停下来" in reply_text or "靠边" in reply_text or "停" in reply_text
        has_urgency = "立刻" in reply_text or "别硬撑" in reply_text or "别骑了" in reply_text
        if not has_stop:
            suggestions.append(f"【安全-严重】HR{hr}≥190，必须建议'立刻停下来'，当前仅建议减速")
        elif not has_urgency:
            suggestions.append(f"【安全】HR{hr}≥190，建议语气更强硬，加入'立刻'或'别硬撑'")
    elif hr and hr >= 180:
        has_stop = "停下来" in reply_text or "靠边" in reply_text or "停" in reply_text
        if not has_stop:
            suggestions.append(f"【安全】HR{hr}≥180，应建议'停下来'而非仅减速")
    elif hr and hr >= 175:
        has_ack = "偏高" in reply_text or "太高" in reply_text or "超标" in reply_text
        has_action = "放轻" in reply_text or "降下来" in reply_text or "缓" in reply_text or "停" in reply_text
        if not has_ack and not has_action:
            suggestions.append(f"【安全】HR{hr}≥175，应明确提示心率偏高并给出降强度建议")
        elif not has_ack and has_action:
            suggestions.append(f"【安全】HR{hr}≥175，建议明确说出'偏高/太高'等形容词")

    # --- Persona ---
    wuxia_terms = ["运功", "内力", "招式", "真气", "丹田", "经脉"]
    for term in wuxia_terms:
        if term in reply_text:
            suggestions.append(f"【人设】出现武侠术语'{term}'，不符合办公室戏精人设")

    robot_phrases = ["收到", "很好，继续加油", "坚持就是胜利"]
    for phrase in robot_phrases:
        if phrase in reply_text:
            suggestions.append(f"【人设】出现机械用语'{phrase}'，建议换成职场梗")

    if "各位" in reply_text or "大家" in reply_text:
        suggestions.append("【人设】使用了'各位/大家'，这是1对1陪练不是群课")

    # --- Data Integrity ---
    if metrics.get("heartRateAvailable") is False or hr is None:
        if "心率" in reply_text or "HR" in reply_text.upper():
            suggestions.append("【数据】输入无有效心率，回复不应提及心率")

    if trigger == "pace_slow_sustained" and speed_kmh and speed_kmh > 20:
        suggestions.append(f"【数据】trigger=pace_slow但pace={pace_str}(≈{speed_kmh:.1f}km/h)，测试数据矛盾")

    if trigger == "pace_improving_sustained" and speed_kmh and speed_kmh < 10:
        suggestions.append(f"【数据】trigger=pace_improving但pace={pace_str}(≈{speed_kmh:.1f}km/h)，测试数据矛盾")

    # --- Scene ---
    if speed_kmh and speed_kmh < 8:
        if "加速" in reply_text or "冲" in reply_text:
            suggestions.append(f"【场景】pace≈{speed_kmh:.1f}km/h很慢，但回复建议'加速/冲'，矛盾")

    # --- User Input ---
    if user_msg and trigger == "user_input":
        if user_msg == "心率是不是高了" and "心率" not in reply_text:
            suggestions.append("【交互】用户问心率，回复未提及心率")
        if user_msg == "这个速度合适吗" and "速度" not in reply_text and "pace" not in reply_text.lower():
            suggestions.append("【交互】用户问速度，回复未回应速度问题")
        if user_msg == "腿有点酸了" and "酸" not in reply_text and "腿" not in reply_text:
            suggestions.append("【交互】用户说腿酸，回复未回应")
        if user_msg == "手掌有点发麻" and ("麻" not in reply_text and "手掌" not in reply_text):
            suggestions.append("【交互】用户说手掌发麻，回复未回应")

    # --- Session End ---
    if trigger == "session_end" and hr and hr >= 180:
        if "心率" not in reply_text:
            suggestions.append(f"【安全】session_end时HR={hr}≥180，总结中必须提及高心率问题")

    # --- Metaphor Fatigue ---
    metaphor_count = reply_text.count("像") + reply_text.count("就像") + reply_text.count("相当于")
    if metaphor_count >= 2:
        suggestions.append(f"【表达】单句含{metaphor_count}个比喻，过于密集，建议精简")

    return "<br>".join(suggestions) if suggestions else ""


def annotate_report(input_path: str, output_path: Optional[str] = None) -> str:
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_suffix("").with_name(
            input_path.stem + "_reviewed" + input_path.suffix
        )
    else:
        output_path = Path(output_path)

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # --- 1. Add CSS ---
    style_addition = """
  .suggestion { max-width: 380px; line-height: 1.5; font-size: 12px; }
  .suggestion .tag-sev { display: inline-block; background: #fecaca; color: #991b1b; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-right: 4px; }
  .suggestion .tag-warn { display: inline-block; background: #fed7aa; color: #9a3412; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-right: 4px; }
  .suggestion .tag-info { display: inline-block; background: #dbeafe; color: #1e40af; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-right: 4px; }
  .suggestion .tag-data { display: inline-block; background: #e9d5ff; color: #6b21a8; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-right: 4px; }
  tr.row-has-suggestion td { background: #fffbeb; }
  tr.row-sev td { background: #fef2f2; }
"""
    content = content.replace("</style>", style_addition + "\n</style>")

    # --- 2. Add header column ---
    header_old = '<th>#</th>\n  <th>用例</th>\n  <th>分类</th>\n  <th>状态</th>\n  <th>耗时</th>\n  <th>输入</th>\n  <th>输出</th>'
    header_new = '<th>#</th>\n  <th>用例</th>\n  <th>分类</th>\n  <th>状态</th>\n  <th>耗时</th>\n  <th>输入</th>\n  <th>输出</th>\n  <th>修改建议</th>'
    content = content.replace(header_old, header_new)

    # --- 3. Parse rows and build suggestion map ---
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", content, re.DOTALL)
    if not tbody_match:
        raise ValueError("No <tbody> found in HTML")
    tbody = tbody_match.group(1)

    def parse_row(row_html: str) -> Optional[dict]:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
        if len(tds) < 7:
            return None
        row_id = re.sub(r"<[^>]+>", "", tds[0]).strip()
        case_name = re.sub(r"<[^>]+>", "", tds[1]).strip()
        input_html = tds[5]
        json_match = re.search(r'<div class="mono">(.*?)</div>', input_html, re.DOTALL)
        input_json = html.unescape(json_match.group(1)) if json_match else ""
        reply_html = tds[6]
        reply_text = re.sub(r"<[^>]+>", "", reply_html).strip()
        return {
            "row_id": row_id,
            "case_name": case_name,
            "input_json": input_json,
            "reply_text": reply_text,
        }

    tbody_rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody, re.DOTALL)
    parsed_rows = [parse_row(r) for r in tbody_rows if parse_row(r)]

    suggestion_map: dict[str, str] = {}
    for row in parsed_rows:
        metrics = extract_metrics(row["input_json"])
        suggestion = generate_suggestion(metrics, row["reply_text"], row["case_name"])
        suggestion_map[row["row_id"]] = suggestion

    # --- 4. Add suggestion TD to each row ---
    def add_suggestion_to_row(match: re.Match) -> str:
        row_html = match.group(1)
        id_match = re.search(r"<td[^>]*>(\d+)</td>", row_html)
        if not id_match:
            return match.group(0)
        row_id = id_match.group(1)
        suggestion = suggestion_map.get(row_id, "")

        if suggestion:
            sev_class = "row-sev" if ("安全-严重" in suggestion or ("安全" in suggestion and ("≥190" in suggestion or "≥180" in suggestion))) else "row-has-suggestion"
            new_row = match.group(0)
            if 'class=""' in new_row:
                new_row = new_row.replace('class=""', f'class="{sev_class}"')
            elif 'class="' in new_row and sev_class not in new_row:
                new_row = new_row.replace('class="', f'class="{sev_class} ')

            formatted = suggestion
            formatted = formatted.replace("【安全-严重】", '<span class="tag-sev">安全-严重</span>')
            formatted = formatted.replace("【安全】", '<span class="tag-sev">安全</span>')
            formatted = formatted.replace("【人设】", '<span class="tag-warn">人设</span>')
            formatted = formatted.replace("【数据】", '<span class="tag-data">数据</span>')
            formatted = formatted.replace("【场景】", '<span class="tag-warn">场景</span>')
            formatted = formatted.replace("【交互】", '<span class="tag-info">交互</span>')
            formatted = formatted.replace("【表达】", '<span class="tag-info">表达</span>')

            new_td = f'<td class="suggestion">{formatted}</td>'
            new_row = new_row.replace("</tr>", f"{new_td}\n</tr>")
            return new_row
        else:
            new_td = '<td class="suggestion">-</td>'
            return match.group(0).replace("</tr>", f"{new_td}\n</tr>")

    tbody_new = re.sub(r"<tr[^>]*>(.*?)</tr>", add_suggestion_to_row, tbody, flags=re.DOTALL)
    content = content.replace(tbody, tbody_new)

    # --- 5. Update title ---
    content = content.replace(
        "<title>AI陪跑接口测试报告</title>",
        "<title>AI陪跑接口测试报告 - 已审核</title>",
    )
    content = content.replace(
        "<h1>AI陪跑接口测试报告</h1>",
        '<h1>AI陪跑接口测试报告 <span style="font-size:14px;color:#666;background:#e0e7ff;padding:2px 8px;border-radius:4px;">已审核</span></h1>',
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    issue_count = len([v for v in suggestion_map.values() if v])
    print(f"Annotated {len(parsed_rows)} rows, {issue_count} with issues.")
    print(f"Output: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 auto_annotate_report.py <input.html> [output.html]")
        sys.exit(1)
    annotate_report(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
