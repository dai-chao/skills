---
name: contract-risk-review
description: Review a contract from a specific party's perspective to identify unfavorable clauses, assess risk levels, and suggest modifications.
trigger: User uploads or references a contract and asks to review it for risks, unfavorable terms, or fairness from one party's viewpoint.
---

# Contract Risk Review Workflow

## 1. Extract Contract Text
- **DO NOT** use `read_file` on PDFs — it returns binary/garbled content.
- Use `execute_code` with Python and `PyPDF2` or `pdfplumber` to extract text.
- If extraction fails, try installing the package first (`pip install PyPDF2`).

## 2. Identify Parties and Roles
- Confirm which party the user represents (甲方, 乙方, etc.).
- Note the contract structure (sections, clauses, appendices).

## 3. Clause-by-Clause Analysis (from user's party perspective)
Focus on these red-flag categories:
- **Revenue / Payment**: unfavorable split, vague "net profit" definitions, unilateral deduction rights, delayed payment without penalty.
- **Scope of Work**: open-ended obligations ("unconditional", "permanent", "all related matters"), blurred boundaries between free and paid services.
- **Service Standards**: absolute terms ("no errors", "no downtime", "flawless"), unlimited rework obligations.
- **Working Hours / Availability**: excessive time windows, undefined response times, after-hours emergency duties without extra compensation.
- **Liability**: one-sided penalties, vague breach definitions ("negative attitude", "unsatisfactory"), unlimited indemnification.
- **Termination / Exit**: no fixed term, no termination for convenience, lock-in without exit mechanism.
- **Direct Obligations to Third Parties**: whether the user is made directly liable to end-customers bypassing the counterparty.

## 4. Risk Grading
Label each issue: **High** / **Medium** / **Low**.
Explain *why* it is unfair and what specific harm it could cause.

## 5. Provide Modification Suggestions
For each high/medium risk clause, offer concrete alternative wording:
- Replace subjective terms with measurable ones (e.g., "timely" → "within 2 hours").
- Cap unlimited obligations (e.g., "unlimited free rework" → "free rework up to X times").
- Define ambiguous financial terms (e.g., "net profit" → "gross revenue minus directly attributable material costs, verified by both parties").
- Add termination rights (e.g., "either party may terminate with 30 days' written notice").

## 6. Output Format
Present findings by risk category with:
- Clause reference (article/section number)
- Quoted problematic text (brief)
- Risk level
- Specific problem explanation
- Suggested modification

## Pitfalls
- "Net profit" splits without cost definitions are a common revenue trap.
- "Unconditional" service obligations effectively turn fixed fees into unlimited labor.
- Vague breach language ("消极服务", "未按标准") gives the counterparty unilateral punishment power.
- "Long-term / permanent" contracts without exit clauses lock the user in indefinitely.