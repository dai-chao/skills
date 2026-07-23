#!/usr/bin/env python3
"""
build-report.py — Skill 学习导览构建器（v3 中文导览版）

AI 只需生成一个 skill-data.json（5-15KB），
本脚本自动：
  1. 读取固定骨架（template-head.html 的 CSS + template-scripts.html 的 JS）
  2. 按顺序拼装 5 个中文模块
  3. 注入数据 → 输出完整单页 HTML

6 个模块（固定顺序）：
  purpose         — 01 这个 Skill 是做什么的
  file_structure  — 02 文件结构怎么读
  execution_flow  — 03 Skill 是怎么运行的
  core_file       — 04 核心文件解读
  master_insights — 05 大师视角分析
  learning_path   — 06 学习路线与改造建议

用法：
  python3 scripts/build-report.py --data skill-data.json --output output.html
"""

import json, os, sys, html as html_lib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
REF_DIR = os.path.join(SKILL_DIR, "references")

# 6 个模块的固定顺序与默认导航标题
MODULE_ORDER = ["purpose", "file_structure", "execution_flow", "core_file", "master_insights", "learning_path"]
DEFAULT_NAV = {
    "purpose": "用途",
    "file_structure": "文件结构",
    "execution_flow": "运行流程",
    "core_file": "核心文件",
    "master_insights": "大师视角",
    "learning_path": "学习路线",
}
# 每个模块编号的强调色
DEFAULT_NUM_COLOR = {
    "purpose": "var(--color-role-entry)",
    "file_structure": "var(--color-role-reference)",
    "execution_flow": "var(--color-role-script)",
    "core_file": "var(--color-role-entry)",
    "master_insights": "var(--color-role-asset)",
    "learning_path": "var(--color-accent)",
}


def esc(s):
    return html_lib.escape(str(s)) if s else ""


def order_sections(all_sections):
    """
    按 MODULE_ORDER 的固定顺序排列 sections。
    - 有 type 的按类型排序；
    - 没有 type 的（向后兼容）按原顺序追加到末尾。
    """
    typed = {}
    untyped = []
    for s in all_sections:
        t = s.get("type", "")
        if t in MODULE_ORDER:
            typed[t] = s
        else:
            untyped.append(s)

    ordered = [typed[t] for t in MODULE_ORDER if t in typed]
    if not ordered:  # 完全没有 type 的旧数据，原样返回
        return all_sections
    ordered.extend(untyped)
    return ordered


def build_report(data, output_path):
    skill_name = data.get("name", "Skill")
    total_files = data.get("total_files", 0)
    total_lines = data.get("total_lines", 0)

    # 读取固定骨架
    head_path = os.path.join(REF_DIR, "template-head.html")
    scripts_path = os.path.join(REF_DIR, "template-scripts.html")
    with open(head_path, 'r', encoding='utf-8') as f:
        head_html = f.read()
    with open(scripts_path, 'r', encoding='utf-8') as f:
        scripts_html = f.read()

    # 替换 title
    head_html = head_html.replace(
        "<title>Skill Visualizer — 可视化分析</title>",
        f"<title>{esc(skill_name)} — Skill 学习导览</title>"
    )
    head_html = head_html.replace("Skill 可视化分析", f"{esc(skill_name)} — 学习导览")

    sections = order_sections(data.get("sections", []))
    print(f"[build] 模块数: {len(sections)}", file=sys.stderr)
    print(f"[build] 模块顺序: {[s.get('type','?') for s in sections]}", file=sys.stderr)

    # ===== 构建 HTML =====
    body = []
    body.append(head_html)
    body.append("</head>\n<body>\n")

    # NAV
    nav_dots = "\n".join([
        '      <button class="nav-dot{active}" data-target="section-{i}" title="{t}" aria-label="{t}"></button>'.format(
            active=" active" if i == 0 else "",
            i=i + 1,
            t=esc(s.get("nav_title") or DEFAULT_NAV.get(s.get("type", ""), "")),
        )
        for i, s in enumerate(sections)
    ])
    body.append(f'''<nav class="nav">
  <div class="progress-bar" id="progress-bar"></div>
  <div class="nav-inner">
    <span class="nav-title">{esc(skill_name)} — 学习导览</span>
    <div class="nav-dots">\n{nav_dots}\n    </div>
  </div>
</nav>\n''')

    # SECTIONS
    for i, section in enumerate(sections):
        bg = "var(--color-bg)" if i % 2 == 0 else "var(--color-bg-warm)"
        content_class = "section-content-wide" if section.get("wide") else "section-content"
        stype = section.get("type", "")
        num_color = section.get("num_color") or DEFAULT_NUM_COLOR.get(stype, "var(--color-accent)")

        body.append(f'<section class="section" id="section-{i+1}" style="background:{bg}">\n')
        body.append(f'  <div class="{content_class}">\n')
        body.append(f'''    <header class="section-header animate-in">
      <div class="section-num" style="color:{num_color}">{i+1:02d}</div>
      <h1 class="section-title">{esc(section.get("title",""))}</h1>
      <p class="section-subtitle">{esc(section.get("subtitle",""))}</p>
    </header>\n''')
        body.append(section.get("html", ""))
        body.append("\n  </div>\n</section>\n\n")

    # FOOTER
    body.append(f'''
<div style="text-align:center;padding:2.5rem;opacity:0.6">
  <p style="font-family:var(--font-display);font-size:1.125rem;color:var(--color-text-muted)">由 <strong>Skill 学习导览工具</strong> 生成</p>
  <p style="font-family:var(--font-mono);font-size:0.75rem;color:var(--color-text-muted);margin-top:0.5rem">分析对象：{esc(skill_name)} · {total_files} 文件 · {total_lines:,} 行 · {len(sections)} 个模块</p>
</div>\n''')

    # SCRIPTS — 注入数据到 JS（供文件说明、运行流程详情使用）
    file_data_js = json.dumps(data.get("file_data", {}), ensure_ascii=False)
    flow_steps_js = json.dumps(data.get("flow_steps", []), ensure_ascii=False)

    body.append("<script>\n")
    body.append(f"const fileData = {file_data_js};\n")
    body.append(f"const flowSteps = {flow_steps_js};\n")
    body.append(f"const totalSections = {len(sections)};\n\n")

    fixed_js = scripts_html
    if fixed_js.strip().startswith("<script>"):
        fixed_js = fixed_js.replace("<script>", "", 1)
    body.append(fixed_js)
    body.append("\n</body>\n</html>")

    # 写入
    full_html = "".join(body)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"[build] 生成完成: {output_path}", file=sys.stderr)
    print(f"[build] 文件大小: {len(full_html):,} bytes", file=sys.stderr)
    return len(full_html)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skill 学习导览构建器")
    parser.add_argument("--data", "-d", required=True, help="JSON 数据文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出 HTML 文件路径")
    args = parser.parse_args()

    with open(args.data, 'r', encoding='utf-8') as f:
        data = json.load(f)

    build_report(data, args.output)


if __name__ == "__main__":
    main()


# ========================================
# SCHEMA: skill-data.json
# ========================================
#
# {
#   "name": "Skill 名称",
#   "total_files": 4,
#   "total_lines": 1500,
#
#   "file_data": {                        # 文件说明（模块 02 / 04 可点击查看）
#     "SKILL.md": {
#       "role": "entry",                  # entry | reference | script | config | asset | hook
#       "lines": 200,
#       "color": "#D94F30",
#       "summary": "核心指令文件……",
#       "value": "key"                    # key（关键）| aux（辅助）| skip（可忽略）
#     }
#   },
#
#   "flow_steps": [                       # 模块 03 运行流程（也可直接写进 section html）
#     {
#       "title": "第 1 步：触发识别",
#       "read": "读取用户输入与触发词",
#       "judge": "判断是否命中触发关键词",
#       "output": "决定是否启动 Skill",
#       "files": [["#D94F30", "SKILL.md"]]
#     }
#   ],
#
#   "sections": [                         # 6 个模块（顺序可乱，构建脚本会按 type 重排）
#     {
#       "type": "purpose",                # purpose | file_structure | execution_flow
#                                         # core_file | master_insights | learning_path
#       "nav_title": "用途",              # 导航圆点标题（中文，留空则用默认）
#       "title": "这个 Skill 是做什么的",
#       "subtitle": "一句话看懂它的用途",
#       "num_color": "#D94F30",           # 可选，模块编号颜色
#       "wide": false,                    # 可选，是否用宽版容器
#       "html": "..."                     # 模块 HTML 内容（复用骨架 CSS 类名）
#     }
#   ]
# }
#
# ========================================
# 6 个模块（固定顺序）
# ========================================
#
# | type            | 中文标题              | 回答的小白问题            |
# |-----------------|----------------------|--------------------------|
# | purpose         | 这个 Skill 是做什么的 | 它是干什么的？            |
# | file_structure  | 文件结构怎么读        | 文件分别负责什么？        |
# | execution_flow  | Skill 是怎么运行的    | 按什么顺序工作？          |
# | core_file       | 核心文件解读          | 想学习先看哪里？          |
# | master_insights | 大师视角分析          | 它做得好不好？设计原理？  |
# | learning_path   | 学习路线与改造建议    | 想改造从哪下手？          |
#
# 已删除：file_constellation（星座图）、interaction_matrix（交互矩阵）、
#         extensions（延伸方向，已并入 learning_path）
