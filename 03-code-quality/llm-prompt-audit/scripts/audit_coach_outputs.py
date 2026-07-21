#!/usr/bin/env python3
"""
Audit Jymo coach_chat_test HTML report outputs.
Adds a "修改建议" column with per-row suggestions.

Usage:
    python audit_coach_outputs.py input_report.html output_report.html
"""

import re
import html
import sys


def audit_output(output, trigger, hr=None, dist=None, dur=None, user_msg=None, status=""):
    """Audit a single coach output against tone/safety/accuracy rules."""
    issues = []

    if "错误" in status or "[错误]" in output:
        return "接口错误，非文案问题"

    # Tone: robotic short sentences
    segments = output.split("，")
    short_segments = [s for s in segments if len(s.strip()) <= 4 and s.strip()]
    if len(short_segments) >= 3:
        issues.append("机械短句堆砌，像对讲机")

    if output.count("，") >= 4 and len(output) < 40:
        issues.append("逗号过多，句子碎片化")

    # Safety: high heart rate
    if hr and hr >= 170:
        if not any(w in output for w in ["偏高", "高", "收"]):
            issues.append(f"心率{hr}已偏高，未明确提醒风险")
        if not any(w in output for w in ["齿比", "慢", "轻"]):
            issues.append("高心率场景未给出具体降档建议")

    if hr and hr >= 180:
        if not any(w in output for w in ["危险", "太高", "马上"]):
            issues.append(f"心率{hr}过高，语气应更紧迫")

    # Trigger matching
    if trigger == "workout_started":
        if "齿比" in output or "踏频" in output:
            issues.append("刚起步不宜提齿比/踏频，应先放松")

    if trigger == "warmup_done":
        if "热身" not in output and "活动开" not in output:
            issues.append("warmup_done未提及热身完成")

    if trigger == "km_milestone":
        if hr and hr >= 150:
            if "心率" not in output and "喘" not in output:
                issues.append("里程碑时心率已偏高，应结合心率提醒")

    if trigger == "heartRate_high":
        if "心率" not in output:
            issues.append("heartRate_high触发但未提及心率")
        if not any(w in output for w in ["齿比", "慢", "轻", "收"]):
            issues.append("高心率未给出具体降强度动作")

    if trigger == "hydration_reminder" and len(output) < 8:
        issues.append("补水提醒过于生硬简短")

    if trigger == "session_end" and len(output) < 10:
        issues.append("结束语过于简短，应总结或鼓励")

    if trigger == "user_input" and user_msg:
        if "徒儿" not in output and "你" not in output:
            issues.append("回答用户疑问时缺少直接称呼，像自言自语")

    # Persona: overuse of 徒儿
    if output.count("徒儿") >= 2:
        issues.append("'徒儿'称呼过于频繁，显得刻意")

    # Terminology
    if "踏频" in output:
        issues.append("'踏频'过于专业术语，应说'踩踏节奏'")
    if "VO2max" in output or "乳酸" in output or "阈值" in output:
        issues.append("出现跑步专业术语，不符合口语化")
    if "收到" in output:
        issues.append("'收到'像对讲机，应改为'好'/'行'")
    if "推进" in output:
        issues.append("'推进'过于书面化，应改为'往前骑'/'继续走'")
    if "均速" in output:
        issues.append("'均速'过于术语，应改为'速度'/'配速'")
    if "维持住" in output:
        issues.append("'维持住'生硬，应改为'保持住'/'就这么踩着'")

    # Redundancy / awkward phrasing
    if "节奏稳住很稳" in output or "稳住很稳" in output:
        issues.append("语义重复")
    if "顺着来就行吧？" in output:
        issues.append("'就行吧？'语气犹豫，师傅人设应更笃定")
    if "踩过了" in output:
        issues.append("'踩过了'表意不清，应改为'骑到了'/'完成了'")
    if "活活血" in output:
        issues.append("'活活血'略显随意，可改为'活动活动手指'")
    if "问题不大" in output and hr and hr >= 160:
        issues.append(f"心率{hr}时说'问题不大'过于轻描淡写")
    if "找找节奏" in output and trigger != "workout_started":
        issues.append("非起步阶段说'找节奏'不合理")

    # Data accuracy
    if dist:
        dist_km = dist / 1000
        for dp in re.findall(r"(\d+\.?\d*)\s*公里", output):
            mentioned = float(dp)
            if abs(mentioned - dist_km) > 0.5 and abs(mentioned - round(dist_km)) > 0.5:
                issues.append(f"提到{mentioned}公里，实际约{dist_km:.1f}公里，数据偏差大")
                break

    if dur:
        dur_min = dur / 60
        for dp in re.findall(r"(\d+)\s*分钟", output):
            mentioned = float(dp)
            if abs(mentioned - dur_min) > 2:
                issues.append(f"提到{int(mentioned)}分钟，实际约{dur_min:.0f}分钟，时间偏差大")
                break

    return "；".join(issues) if issues else "✅ 无明显问题"


def extract_rows(html_content):
    """Extract data rows from the HTML report."""
    row_pattern = re.compile(r"<tr[^>]*>(.*?)\s*</tr>", re.DOTALL)
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)

    rows = []
    for row in row_pattern.findall(html_content):
        cells = td_pattern.findall(row)
        if len(cells) < 7:
            continue

        idx = cells[0].strip()
        status = re.sub(r"<[^>]+>", "", cells[3]).strip()
        input_cell = cells[5]
        output_cell = cells[6]

        input_decoded = html.unescape(input_cell)

        trigger_match = re.search(r'"triggerType"\s*:\s*"([^"]+)"', input_decoded)
        trigger_type = trigger_match.group(1) if trigger_match else "unknown"

        hr_match = re.search(r'"heartRate"\s*:\s*(\d+)', input_decoded)
        heart_rate = int(hr_match.group(1)) if hr_match else None

        dist_match = re.search(r'"distanceM"\s*:\s*([\d.]+)', input_decoded)
        distance = float(dist_match.group(1)) if dist_match else None

        dur_match = re.search(r'"durationS"\s*:\s*([\d.]+)', input_decoded)
        duration_s = float(dur_match.group(1)) if dur_match else None

        user_msg_match = re.search(r'"userMessage"\s*:\s*"([^"]+)"', input_decoded)
        user_message = user_msg_match.group(1) if user_msg_match else None

        output = re.sub(r"<[^>]+>", "", output_cell).strip()

        rows.append({
            "idx": idx,
            "trigger_type": trigger_type,
            "heart_rate": heart_rate,
            "distance": distance,
            "duration_s": duration_s,
            "user_message": user_message,
            "output": output,
            "status": status,
        })
    return rows


def build_suggestion_map(rows):
    """Build a map of row index -> suggestion."""
    return {
        r["idx"]: audit_output(
            r["output"],
            r["trigger_type"],
            hr=r["heart_rate"],
            dist=r["distance"],
            dur=r["duration_s"],
            user_msg=r["user_message"],
            status=r["status"],
        )
        for r in rows
    }


def add_suggestions_to_html(original_html, suggestion_map):
    """Insert suggestion CSS, header, and cells into the HTML."""
    # CSS
    style_addition = """
  .suggestion { max-width: 320px; line-height: 1.5; color: #b45309; font-size: 12px; }
  .suggestion.ok { color: #16a34a; }
  th.suggestion-header { background: #7c2d12; }
"""
    modified = original_html.replace("</style>", style_addition + "\n</style>")

    # Header
    modified = modified.replace(
        "  <th>输出</th>\n</tr>\n</thead>",
        "  <th>输出</th>\n  <th class=\"suggestion-header\">修改建议</th>\n</tr>\n</thead>",
    )

    # Data rows: find each row by its index marker and insert before </tr>
    for idx, suggestion in suggestion_map.items():
        row_start = modified.find(f"<td>{idx}</td>")
        if row_start == -1:
            continue
        tr_end = modified.find("</tr>", row_start)
        if tr_end == -1:
            continue

        css_class = "suggestion ok" if suggestion == "✅ 无明显问题" else "suggestion"
        cell = f'<td class="{css_class}">{suggestion}</td>\n'
        modified = modified[:tr_end] + cell + modified[tr_end:]

    return modified


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input.html output.html")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r", encoding="utf-8") as f:
        original = f.read()

    rows = extract_rows(original)
    suggestion_map = build_suggestion_map(rows)

    modified = add_suggestions_to_html(original, suggestion_map)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(modified)

    ok = sum(1 for s in suggestion_map.values() if s == "✅ 无明显问题")
    issues = len(suggestion_map) - ok
    print(f"Processed {len(rows)} rows. ✅ {ok}  |  ⚠️ {issues}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
