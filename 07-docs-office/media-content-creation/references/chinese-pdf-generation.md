---
name: chinese-pdf-generation
title: Chinese PDF Generation on macOS
description: Generate professional PDF documents with Chinese text on macOS using fpdf2, including environment workarounds and layout fixes.
trigger: When asked to create a PDF containing Chinese text, tables, or structured reports on macOS.
---

# Chinese PDF Generation on macOS

## Environment Setup
- The active venv often lacks `pip`. Use **system Python** instead:
  - Python: `/usr/bin/python3`
  - Pip: `/usr/bin/python3 -m pip`
- Install fpdf2: `/usr/bin/python3 -m pip install fpdf2 -q`
- Chinese font (pre-installed on macOS):
  - `/System/Library/Fonts/Supplemental/Arial Unicode.ttf`

## Minimal Working Example
```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_font('ArialUnicode', '', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf', uni=True)
pdf.add_font('ArialUnicode', 'B', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf', uni=True)
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font('ArialUnicode', 'B', 14)
pdf.cell(0, 10, '中文标题', new_x="LMARGIN", new_y="NEXT")
pdf.output('/path/to/output.pdf')
```

## Critical Layout Fixes
- **Never use** `pdf.multi_cell(0, ...)` after `pdf.cell()` on the same line. The remaining width may be miscalculated.
- **Correct pattern** for side-by-side time + description:
  ```python
  pdf.cell(34, 6, '09:00', new_x="RIGHT", new_y="TOP")
  pdf.multi_cell(156, 6, '活动描述...', new_x="LMARGIN", new_y="NEXT")
  ```
- Always specify explicit widths for `multi_cell` when not starting at left margin.

## Workflow
1. Write script to `/tmp/script.py` (avoids venv issues).
2. Execute with `/usr/bin/python3 /tmp/script.py`.
3. Save output to `/Users/<user>/Desktop/` for easy access.

## Pitfalls
- `DeprecationWarning` about `uni` parameter is harmless; fpdf2 auto-detects Unicode now.
- Missing glyph warnings for emoji (e.g., ⚠) are harmless but emoji won't render; use text replacements like `!!` instead.
- If `add_font` fails, verify the TTF path exists; some macOS versions place Arial Unicode under `/Library/Fonts/`.
