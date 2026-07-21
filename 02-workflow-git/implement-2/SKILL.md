---
name: implement
description: Execute implementation tasks for a single batch with requirement tracing and constitution compliance. Returns results; does NOT update checkpoints or tasks.md.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

This skill is invoked by `BatchImplAgent` with a specific `batch.task_ids` list. All execution is scoped to the current batch only.

## Prerequisites Check (first batch only, skip if `is_first_batch: false`)

### Checkpoint Validation

1. **Spec-to-Plan checkpoint passes**: `checkpoints/spec-to-plan*.yaml` has `validation.passed == true`
2. **Plan-to-Tasks checkpoint passes**: `checkpoints/plan-to-tasks*.yaml` has `validation.passed == true`

If any checkpoint fails: ERROR "Checkpoint validation failed. Resolve coverage gaps before implementation."

## Outline

1. **Bootstrap and prerequisites**: Run prerequisites script from repo root. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

   > `$KIT_ROOT` is provided by the calling agent.

   - Bash example: `$KIT_ROOT/skills/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
   - PowerShell example: `$KIT_ROOT/skills/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`

2. **Check checklists status** (first batch only — if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to next step

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to next step

3. **Load and analyze the implementation context**:
   - **REQUIRED**: Read `tasks.md` for the complete task list and execution plan
   - **REQUIRED**: Read `spec.md` for original requirements (REQ-XXX). Each task traces back via [Plan:X.Y] → plan item → requirement.
   - **REQUIRED**: Read `constitution.md` for project principles. All implementation decisions MUST comply with constitution principles.
   - **REQUIRED**: Read `plan.md` for tech stack, architecture, and file structure
   - **REQUIRED**: Read knowledge graph for module dependencies and code structure
   - **REQUIRED**: Read `checkpoints/` for upstream traceability
   - **IF EXISTS**: Read `data-model.md` for entities and relationships
   - **IF EXISTS**: Read `contracts/` for API specifications and test requirements
   - **IF EXISTS**: Read `research.md` for technical decisions and constraints
   - **IF EXISTS**: Read `quickstart.md` for integration scenarios
   - **IF EXISTS (rewrite mode)**: Read `business-logic-inventory.md` for extracted business logic units. This contains `behavioral_spec`, `validation_rules`, and `side_effects` per BL unit that MUST be cross-referenced during source-anchored implementation.

4. **Project Setup Verification** (first batch only — skip if project already initialized):
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `Makefile`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. **Parse batch tasks from tasks.md**:
   - Extract ONLY the tasks matching `batch.task_ids` from tasks.md
   - For each task, extract:
     - **Task ID and description**
     - **[Plan:X.Y] reference** — trace to plan.md for technical approach
     - **Requirement context** — follow [Plan:X.Y] → plan item → REQ-XXX in spec.md to understand the full requirement intent
     - **[Source:] references** (rewrite mode) — source file paths and method names to read before implementing
     - **[BL:] references** (rewrite mode) — business logic unit IDs from business-logic-inventory.md
     - **Dependencies** — sequential vs parallel execution rules
     - **File paths** — target files for implementation
     - **Parallel markers [P]** — tasks that can run together
     - **Guideline markers [GUIDELINE:*]** — transformation rules to apply
   - If a task has an unmet dependency not in the current batch → report as blocked

6. **Execute implementation for batch tasks**:
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Constitution compliance**: Verify each implementation decision aligns with constitution principles (e.g., testing discipline, observability, versioning)
   - **Requirement fidelity**: Before implementing each task, re-read the traced REQ-XXX from spec.md to ensure the implementation matches the original requirement intent, not just the abbreviated task description
   - **Source-anchored implementation** (REWRITE mode — MANDATORY):
     For every task that has a `[Source:]` annotation, you MUST follow this process **before writing any target code**:

     1. **Read source file(s)**: Use `read_file` to read each file referenced in `[Source: path#methods]`
     2. **Extract behavioral specification**: From the source code, identify and document:
        - All conditional branches (if/else, switch/case, ternary) and what each branch does
        - All validation checks and their error responses
        - All data transformations and their exact formulas/logic
        - All side effects (database writes, notifications, audit logs, state mutations)
        - All exception handling paths (catch blocks, error returns)
        - All cross-service calls and how their results are used
     3. **Cross-reference with BL unit**: If the task has a `[BL: BL-XXX]` reference, read the corresponding entry in `business-logic-inventory.md` and verify the extracted behavior matches the documented business rules. If discrepancies exist, the **source code is the source of truth**.
     4. **Implement with branch parity**: Write the target code ensuring every behavioral branch from the source is preserved:
        - Each source conditional → corresponding target conditional
        - Each source validation → corresponding target validation (using target framework idioms)
        - Each source error path → corresponding target error handling
        - Each source side effect → corresponding target side effect
     5. **Record source reference in batch report**: For each completed task, record `source_reference` with the source file, methods read, and `branches_preserved` count.

     > **Why this matters**: Without reading the source code, the LLM implements from the task *description*, which is an abstraction that loses conditional branches, edge cases, and error handling details. Source-anchored implementation ensures behavioral fidelity.

     > **Example**: Task says "Convert ProductAction.add() → ProductController.addProduct()". Without source anchoring, the LLM writes a generic add endpoint. With source anchoring, it reads ProductAction.java#add and discovers: (a) inventory check before adding, (b) duplicate name validation, (c) category existence validation, (d) audit log entry, (e) specific error messages for each failure path. All 5 behaviors are then preserved in the target code.

7. **Implementation execution rules**:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

8. **Guideline-based implementation**:
   - For tasks marked with `[GUIDELINE:skill-name]`, load the corresponding guideline
   - Apply the specific transformation rules from the guideline skill
   - Use the before/after examples as reference for code transformation
   - Follow the guideline's transformation tables for consistent mapping
   - Example: For `[GUIDELINE:convert-action-to-controller]`:
     1. Load `$KIT_ROOT/skills/guidelines/struts-to-spring/SKILL.md`
     2. Find the `convert-action-to-controller` skill section
     3. Apply the import changes, class transformations, and method mappings
     4. Use the return constant transformation table

9. **Progress tracking and error handling**:
    - Report progress after each completed task
    - Halt execution if any non-parallel task fails
    - For parallel tasks [P], continue with successful tasks, report failed ones
    - Provide clear error messages with context for debugging
    - Suggest next steps if implementation cannot proceed
    - **Do NOT** update tasks.md or checkpoints — the orchestrator handles this

10. **Batch completion validation**:
    - Verify all batch tasks are completed or blocked
    - Check that implemented features match the traced requirements from spec.md
    - Confirm the implementation follows constitution principles

11. **Generate batch result report (REQUIRED output)**:
    Return a structured report for the orchestrator to consume:

    ```yaml
    batch_id: "B01"
    completed_tasks: ["T001", "T002", "T003"]
    blocked_tasks:
      - task_id: "T004"
        reason: "Depends on T010 which is not in this batch"
        required_task_ids: ["T010"]
    files_changed:
      T001:
        - file: "path/to/file"
          change_type: "created | modified | deleted"
          description: "Brief description of change"
      T002:
        - file: "path/to/another-file"
          change_type: "modified"
          description: "Brief description of change"
    # Source-anchored traceability (rewrite mode)
    source_references:
      T001:
        source_files:
          - file: "src/main/java/com/example/ProductAction.java"
            methods_read: ["list", "execute"]
        branches_preserved: 5
        validations_preserved: 2
        error_paths_preserved: 3
        side_effects_preserved: 1
        notes: "Discovered inventory check not in BL inventory"
    traceability:
      - requirement: "REQ-XXX"
        plan_item: "X.Y"
        task: "T001"
        files: ["path/to/file"]
        source_files: ["path/to/original/source"]  # rewrite mode
        status: "completed"
    protocol_violation: false
    errors: []
    warnings: []
    ```

> **Note:** This skill does NOT update tasks.md, checkpoints, or run build/test gates. The orchestrator handles all state management and gating after receiving this report.