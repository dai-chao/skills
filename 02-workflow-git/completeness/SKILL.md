---
name: completeness
description: Post-implementation final validation — verify end-to-end traceability, constitution compliance, and requirement fulfillment across all artifacts and code changes.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

After ALL implementation batches are complete, perform a comprehensive final validation that the entire chain from requirements to implementation is complete and consistent. This is the **completeness** quality gate — the last gate before the feature is declared done.

## Operating Constraints

**READ-ONLY ANALYSIS**: Do **not** modify source code files. Only write to checkpoint/traceability artifacts. Output a structured migration report with actionable feedback.

**Constitution Authority**: The project constitution (`$APPMOD_DIR/constitution.md`) is **non-negotiable**. Constitution violations are automatically CRITICAL and require implementation fixes — not dilution, reinterpretation, or silent ignoring of the principle.

## Execution Steps

### 1. Initialize Validation Context

> `$KIT_ROOT` is provided by the calling agent. All `$KIT_ROOT/` paths below use that value.

Run script once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS. Derive absolute paths:

- CONSTITUTION = `$APPMOD_DIR/constitution.md`
- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md
- CHECKPOINTS_DIR = FEATURE_DIR/checkpoints/

Bash example: `$KIT_ROOT/skills/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` 
PowerShell example: `$KIT_ROOT/skills/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`

Abort with an error message if any required file is missing.
For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load All Source-of-Truth Artifacts

**REQUIRED — all must be loaded:**

| Artifact | Path | Purpose |
|----------|------|---------|
| Constitution | `$APPMOD_DIR/constitution.md` | Principle compliance validation |
| Specification | `FEATURE_DIR/spec.md` | Original requirements (REQ-XXX) + acceptance criteria + scope baseline |
| Plan | `FEATURE_DIR/plan.md` | Architecture, phases, plan items |
| Tasks | `FEATURE_DIR/tasks.md` | Task list with [Plan:X.Y] references, completion status |

**REQUIRED — all checkpoints:**

| Checkpoint | Path | Validates |
|------------|------|-----------|
| spec-to-plan | `FEATURE_DIR/checkpoints/spec-to-plan.yaml` | REQ-XXX → Plan items |
| plan-to-tasks | `FEATURE_DIR/checkpoints/plan-to-tasks.yaml` | Plan items → Tasks |
| tasks-to-impl | `FEATURE_DIR/checkpoints/tasks-to-impl.yaml` | Tasks → Code changes |

### 3. Checkpoint Validation (PRIMARY)

**Validate each checkpoint has passed with 100% coverage:**

1. For each checkpoint file:
   - Check `validation.passed == true`
   - Check coverage percentage == 100%
   - Extract `validation.errors[]` and `validation.warnings[]`
   - Build aggregated error/warning list

2. **Checkpoint validation report:**
   ```markdown
   ## Checkpoint Validation
   
   | Checkpoint | Status | Coverage | Errors | Warnings |
   |------------|--------|----------|--------|----------|
   | spec-to-plan.yaml | ✓ PASS | 100% | 0 | 0 |
   | plan-to-tasks.yaml | ✓ PASS | 100% | 0 | 1 |
   | tasks-to-impl.yaml | ✗ FAIL | 96% | 2 | 0 |
   ```

3. Any checkpoint with `passed != true` or coverage < 100% → **CRITICAL ERROR**

### 4. Task Completion Verification

1. Parse `tasks.md` for all tasks and their `[X]` / `[ ]` status
2. Cross-reference with `tasks-to-impl.yaml` checkpoint:
   - Every task marked `[X]` in tasks.md MUST have corresponding `files_changed` in the checkpoint
   - Every task in checkpoint with status "completed" MUST be `[X]` in tasks.md
3. **CRITICAL ERROR** if:
   - Any task marked complete without corresponding code changes
   - Any task still `[ ]` (incomplete) that was planned
   - Mismatch between tasks.md and checkpoint status

### 5. End-to-End Traceability Verification

Read the traceability data already persisted in `tasks-to-impl.yaml` by ImplementationAgent (each task entry has `upstream_trace` with `plan_item`, `requirements`, and `full_trace`).

1. For each task in `tasks-to-impl.yaml`:
   - Verify `upstream_trace` is present and complete
   - Verify the traced REQ-XXX exists in spec.md
   - Verify the traced Plan item exists in plan.md
2. Cross-check: every REQ-XXX in spec.md must appear in at least one task's `upstream_trace.requirements`
3. **Any break in the chain = CRITICAL error**

Save verification result to `FEATURE_DIR/checkpoints/traceability-matrix.yaml`:
```yaml
traceability:
  - requirement: "REQ-XXX"
    plan_items: ["X.Y"]
    tasks: ["T001", "T002"]
    files: ["path/to/file-a", "path/to/file-b"]
    status: "complete"  # complete | broken | partial
```

### 6. Constitution Compliance Validation

1. Load constitution principles from `$APPMOD_DIR/constitution.md`
2. For each constitution principle, verify it was followed in the implementation:
   - Check if mandated patterns/practices are present in changed files
   - Verify no implementation decision contradicts a MUST principle
3. **CRITICAL ERROR** if any constitution principle is violated

### 7. Requirement Fulfillment Verification

1. For each REQ-XXX in spec.md:
   - Locate the acceptance criteria
   - Trace through plan → tasks → implementation files
   - Verify the implementation addresses the requirement intent
2. **CRITICAL ERROR** if any requirement is not fully implemented or fails acceptance criteria

### 8. Functional Equivalence Verification (REWRITE MODE ONLY)

**Skip this step if mode is "upgrade".**

**Delegate to:** `$KIT_ROOT/skills/rewrite/SKILL-functional-equivalence.md`

1. Load `FEATURE_DIR/business-logic-inventory.md` (generated during planning Phase 0)
2. For each BL-XXX unit in the inventory:
   - Verify it has been implemented in the target codebase
   - Compare behavioral outputs (same inputs → same outputs)
   - Document any intentional differences with approval
3. Generate `FEATURE_DIR/verification-report.md` with:
   - Per-unit verification status (verified / differs-intentionally / pending / failed)
   - Match rate metrics
   - Intentional differences with business justification
4. **CRITICAL ERROR** if any BL unit is not verified or has unapproved differences
5. Include functional equivalence results in the migration summary report

### 9. Update tasks-to-impl Checkpoint

After all validations, write final results back to `FEATURE_DIR/checkpoints/tasks-to-impl.yaml`:

```yaml
validation:
  passed: true/false
  total_tasks: N
  completed_tasks: M
  coverage_percentage: X%
  constitution_violations: []
  broken_traceability_chains: []
  timestamp: "[ISO 8601]"
```

This ensures the tasks-to-impl checkpoint mirrors the same pattern as spec-to-plan and plan-to-tasks checkpoints.

### 10. Cross-Artifact Consistency Analysis

Perform targeted detection passes. Limit to 50 findings total.

#### A. Implementation Gaps
- Tasks with code changes that don't match their described intent
- Plan items that are only partially realized in implementation

#### B. Constitution Alignment
- Any implementation pattern conflicting with a MUST principle
- Missing mandated quality gates or practices from constitution

#### C. Inconsistency Detection
- Terminology drift between spec requirements and implementation
- Data entities referenced in spec/plan but missing in implementation
- API contracts defined in `contracts/` but not implemented

### 11. Severity Assignment

- **CRITICAL**: Checkpoint failed, broken traceability chain, constitution MUST violation, requirement not implemented, task without code changes
- **HIGH**: Partial requirement fulfillment, implementation drift from spec intent, untested acceptance criteria
- **MEDIUM**: Incomplete non-functional requirement coverage, minor spec-to-impl terminology drift
- **LOW**: Style/naming improvements, documentation gaps

### 12. Write Migration Summary Report

Write the migration summary report to `FEATURE_DIR/migration-summary.md`. This is the single authoritative artifact that captures the end-to-end migration outcome.

```markdown
# Migration Summary Report

### Checkpoint Validation Summary

| Checkpoint | Status | Coverage | Errors | Warnings |
|------------|--------|----------|--------|----------|
| spec-to-plan.yaml | ✓/✗ | XX% | N | N |
| plan-to-tasks.yaml | ✓/✗ | XX% | N | N |
| tasks-to-impl.yaml | ✓/✗ | XX% | N | N |

### End-to-End Traceability Matrix

| Requirement | Plan Items | Tasks | Impl Files | Status |
|-------------|------------|-------|------------|--------|
| REQ-XXX | X.Y | T001-T003 | file-a, file-b | ✓ |
| REQ-YYY | X.Z | T004 | - | ❌ BROKEN |

### Constitution Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| [Principle 1 Name] | ✓ Followed | |
| [Principle 2 Name] | ✗ Violated | [specific violation] |

### Findings

| ID | Category | Severity | Location | Summary | Recommendation |
|----|----------|----------|----------|---------|----------------|
| C1 | Gap | CRITICAL | REQ-002 | No implementation files | Implement in next batch |

### Metrics Summary

- Total Requirements: N
- Requirements Fully Implemented: M (X%)
- Total Plan Items: N
- Plan Items Realized: M (X%)
- Total Tasks: N
- Tasks Completed: M (X%)
- End-to-End Coverage: X% (requirements with complete chain)
- Constitution Violations: N
- Critical Issues: N
```

### 13. Append Verdict and Next Actions

Append the verdict section to the end of `FEATURE_DIR/migration-summary.md`:

**PASS** (all conditions met):
- All checkpoints passed with 100% coverage
- All tasks completed with corresponding code changes
- End-to-end traceability has no breaks
- No constitution violations
- All requirements fulfilled

→ Append: "✓ Completeness check PASSED. Feature is ready for final review."

**FAIL** (any condition unmet):
- List all CRITICAL issues with specific remediation steps
- Recommend which ImplementationAgent batch to re-run
- Provide explicit task IDs that need attention

→ Append: "✗ Completeness check FAILED. N critical issues require resolution."

## Operating Principles

- **Minimal high-signal tokens**: Focus on actionable findings, not exhaustive documentation
- **Progressive disclosure**: Load artifacts incrementally; don't dump all content into analysis
- **Token-efficient output**: Limit findings table to 50 rows; summarize overflow
- **Deterministic results**: Rerunning without changes should produce consistent results
- **NEVER hallucinate missing sections** (if absent, report them accurately)
- **Prioritize constitution violations** (these are always CRITICAL)
- **Use examples over exhaustive rules** (cite specific instances, not generic patterns)
- **Report zero issues gracefully** (emit success report with coverage statistics)
