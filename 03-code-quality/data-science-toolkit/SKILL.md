---
name: data-science-toolkit
description: "Data science workflows: Jupyter live kernel, Excel parsing, AI service cost comparison, and contract risk review."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Data Science, Jupyter, Excel, Cost Comparison, Contract Review]
    related_skills: [research-knowledge-tools]
---

# Data Science Toolkit

## When to Use This Skill

Trigger when the user wants to:
- Use Jupyter notebooks with live kernel
- Parse Excel files with standard library only
- Compare AI service costs across providers
- Review contracts for risk from a specific party's perspective

## Section 1: Jupyter Live Kernel

Iterative Python via live Jupyter kernel.
```bash
pip install jupyter
jupyter notebook
```

See [references/jupyter-live-kernel.md](references/jupyter-live-kernel.md) for full details.

## Section 2: Excel Parsing

Parse .xlsx files and generate charts using only Python standard library.
```python
import zipfile
import xml.etree.ElementTree as ET

# Extract shared strings and sheet data from xlsx
with zipfile.ZipFile('file.xlsx') as z:
    xml = z.read('xl/sharedStrings.xml')
```

See [references/parse-xlsx-stdlib.md](references/parse-xlsx-stdlib.md) for full details.

## Section 3: AI Service Cost Comparison

Build multi-currency price comparison tables for AI models.

See [references/ai-service-cost-comparison.md](references/ai-service-cost-comparison.md) for full details.

## Section 4: Contract Risk Review

Review contracts from a specific party's perspective.

See [references/contract-risk-review.md](references/contract-risk-review.md) for full details.

## Common Pitfalls

1. **Jupyter kernel disconnect**: Check kernel status before long operations
2. **Excel parsing**: Standard library approach is slow for large files; use pandas for >10k rows
3. **Cost comparison**: Prices change frequently; verify with provider APIs
4. **Contract review**: Not legal advice; always consult a lawyer for binding decisions
