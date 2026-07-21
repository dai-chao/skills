---
name: parse-xlsx-stdlib
description: Parse .xlsx files and generate charts using only Python standard libraries (no pandas, openpyxl, or matplotlib). Useful when the sandbox lacks external dependencies and pip install is blocked.
trigger: Need to read Excel data or create charts, but pandas/openpyxl/matplotlib are unavailable and network install fails.
---

# Excel Parsing & Charting with Python Stdlib Only

## Trigger
- Sandbox environment lacks `pandas`, `openpyxl`, `xlrd`, `matplotlib`
- `pip install` fails due to proxy/firewall blocks
- Need to extract data from `.xlsx` and/or produce visualizations

## Core Insight
An `.xlsx` file is a ZIP archive containing XML files:
- `xl/sharedStrings.xml` — string lookup table
- `xl/worksheets/sheet1.xml` — cell data
- `xl/workbook.xml` — sheet definitions

## Step 1: Extract Data

```python
import zipfile
import xml.etree.ElementTree as ET

def get_text(cell, ns, shared_strings):
    """Extract text from a cell. Critical: check cell type."""
    cell_type = cell.get('t', '')  # 's' = shared string index

    # Inline text
    t = cell.find('ns:t', ns)
    if t is not None:
        return t.text or ''

    # Numeric or shared-string value
    v = cell.find('ns:v', ns)
    if v is not None:
        if cell_type == 's':
            idx = int(v.text)
            return shared_strings[idx] if idx < len(shared_strings) else ''
        return v.text or ''
    return ''

with zipfile.ZipFile('file.xlsx', 'r') as z:
    # --- Load shared strings ---
    shared_strings = []
    with z.open('xl/sharedStrings.xml') as f:
        root = ET.parse(f).getroot()
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for si in root.findall('ns:si', ns):
            texts = [t.text or '' for t in si.findall('.//ns:t', ns)]
            shared_strings.append(''.join(texts))

    # --- Load sheet ---
    with z.open('xl/worksheets/sheet1.xml') as f:
        root = ET.parse(f).getroot()
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for row in root.findall('ns:sheetData/ns:row', ns):
            row_num = int(row.get('r', 0))
            cells = {}
            for cell in row.findall('ns:c', ns):
                ref = cell.get('r', '')
                col = ''.join(c for c in ref if c.isalpha())
                cells[col] = get_text(cell, ns, shared_strings)
            print(row_num, cells)
```

### Pitfall: Shared String vs Raw Number
**Always** check `cell.get('t')`. If it equals `'s'`, the `<v>` node is an integer index into `sharedStrings.xml`. Otherwise `<v>` is the raw numeric or date value. Treating all `<v>` nodes as shared-string indices causes `ValueError` on numeric cells.

### Pitfall: Column Layouts Vary Between Exports
Do **not** hardcode column letters (e.g., assume column `B` is always "Amount"). The same vendor/system may shift columns when fields are added/removed. Always parse **Row 1** (the header) to build a map of `column_letter → column_name`, then look up data by name.

```python
# Build header map from row 1
header = {}
for cell in header_row.findall('ns:c', ns):
    ref = cell.get('r', '')
    col_letter = ''.join(c for c in ref if c.isalpha())
    header[col_letter] = get_text(cell, ns, shared_strings)

# Invert to name → letter
name_to_col = {v: k for k, v in header.items()}
amount_col = name_to_col.get('应付信息/应付金额（含税）')  # or whatever header text you need
```

### Tip: JSON Embedded in Cells
Some exports stuff JSON objects into shared strings (e.g., `{"Token类型":"output_token"}`). Since this is plain text in the XML, extract it with simple string operations:

```python
json_text = cell_value
val = ""
if '"Token类型":"' in json_text:
    start = json_text.find('"Token类型":"') + len('"Token类型":"')
    end = json_text.find('"', start)
    val = json_text[start:end]
```

## Step 2: Generate SVG Charts (No Matplotlib)

Use Python string formatting to emit raw SVG XML. Works for bar charts, pie charts, line charts.

```python
import math

def svg_bar_chart(categories, values, title, out_path):
    w, h = 700, 500
    margin = 60
    cw, ch = w - 2*margin, h - 2*margin
    max_v = max(values)
    n = len(categories)
    bar_w = cw / n * 0.5
    spacing = cw / n
    colors = ['#4A90D9', '#50C878', '#E94B3C', '#F5A623']

    svg = [f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">']
    svg.append('<rect width="100%" height="100%" fill="#fafafa"/>')
    svg.append(f'<text x="{w/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold">{title}</text>')

    # axes
    svg.append(f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{h-margin}" stroke="#333" stroke-width="2"/>')
    svg.append(f'<line x1="{margin}" y1="{h-margin}" x2="{w-margin}" y2="{h-margin}" stroke="#333" stroke-width="2"/>')

    for i, (cat, val) in enumerate(zip(categories, values)):
        x = margin + spacing*i + spacing*0.25
        bh = (val / max_v) * ch
        y = h - margin - bh
        svg.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bh}" fill="{colors[i%len(colors)]}" rx="4"/>')
        svg.append(f'<text x="{x+bar_w/2}" y="{y-8}" text-anchor="middle" font-size="13" font-weight="bold">{val}</text>')
        svg.append(f'<text x="{x+bar_w/2}" y="{h-margin+20}" text-anchor="middle" font-size="12">{cat}</text>')

    svg.append('</svg>')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
```

## Verification
- Confirm `zipfile.ZipFile('file.xlsx')` does not raise `BadZipFile` — ensures valid xlsx
- Print first 3 rows after parsing to sanity-check column alignment
- Check for empty strings in numeric columns: usually means the cell had a formula or was truly blank

## Limitations
- Does **not** evaluate formulas (reads cached values only)
- Does **not** parse dates automatically (Excel dates are serial numbers; convert if needed: `datetime(1899,12,30) + timedelta(days=serial)`)
- Multi-sheet workbooks require iterating `xl/worksheets/sheetN.xml`
