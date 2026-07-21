---
name: tasks
description: Generate detailed, organized tasks.md for feature implementation based on design documents, with plan-to-tasks traceability checkpoint.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Prerequisites Check

Before generating tasks, verify:

1. **Spec-to-Plan checkpoint exists and passes**:
   - Check for `FEATURE_DIR/checkpoints/spec-to-plan.yaml`
   - Verify `validation.passed == true`
   - If missing or failed: ERROR "Plan checkpoint validation failed. Run planning skill first."

## Outline

1. **Setup**: Run from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

   > `$KIT_ROOT` is provided by the calling agent.

   - Bash example: `$KIT_ROOT/skills/scripts/bash/check-prerequisites.sh --json` 
   - PowerShell example: `$KIT_ROOT/skills/scripts/powershell/check-prerequisites.ps1 -Json`

2. **Load design documents**: Read from FEATURE_DIR if not already in memory:
   - **Required**: spec.md (user stories with priorities)
   - **Required**: plan.md (tech stack, libraries, structure)
   - **Required**: Knowledge graph (module dependencies and code structure)
   - **Required**: checkpoints/spec-to-plan*.yaml (for upstream traceability)
   - **Optional**: data-model.md (entities), contracts/ (API endpoints), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Extract plan item inventory** (for checkpoint generation):
   - Parse plan.md for all phase items (Phase-X, item X.Y)
   - Create plan items inventory with: phase, item_id, description
   - Load upstream traceability from spec-to-plan checkpoint

4. **Execute task generation workflow**:
   - Extract tech stack from plan.md, libraries, project structure
   - Extract user stories with their priorities (P1, P2, P3, etc.) from spec.md
   - Inspect `knowledge-graph.json` from the knowledge graph output (module dependencies and code structure), using its schema/query examples or the java-knowledge-graph skill docs, to understand how to query for file paths and module relationships
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map endpoints to user stories
   - If research.md exists: Extract decisions for setup tasks
   - Generate tasks organized by user story (see Task Generation Rules below)
   - **CRITICAL**: Each task MUST reference its source plan item
   - Generate dependency graph showing user story completion order
   - Create parallel execution examples per user story
   - Validate task completeness (each user story has all needed tasks, independently testable)

5. **Generate Plan-to-Tasks Checkpoint**:
   - Create `FEATURE_DIR/checkpoints/plan-to-tasks.yaml`
   - Use template: `$KIT_ROOT/skills/templates/plan-to-tasks-checkpoint-template.yaml`
   - Map each plan item to generated tasks
   - Include upstream traceability (REQ → Phase → Task)
   - Identify orphan tasks (no plan item trace)
   - Calculate coverage percentage

6. **Validate Checkpoint**:
   ```
   CRITICAL ERRORS (must fix before proceeding):
   - Any plan item with status: "missing"
   - Coverage percentage < 100%
   
   WARNINGS (document but can proceed):
   - Orphan tasks (may be valid utility tasks)
   ```

7. **Generate tasks.md**: Use `$KIT_ROOT/skills/templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - Delegate heavy tasks to sub-agents if needed
   - Phase 1: Setup tasks (project initialization)
   - Phase 2: Foundational tasks (blocking prerequisites for all user stories)
   - Phase 3+: One phase per user story (in priority order from spec.md)
   - Each phase includes: story goal, independent test criteria, tests (if requested), implementation tasks
   - Final Phase: Polish & cross-cutting concerns
   - **NEW**: Include traceability reference in each task (plan item ID)
   - All tasks must follow the strict checklist format (see Task Generation Rules below)
   - Clear file paths for each task
   - Dependencies section showing story completion order
   - Parallel execution examples per story
   - Implementation strategy section (MVP first, incremental delivery)

8. **Reporting**: Output path to generated tasks.md, checkpoint, and summary:
   - Total task count
   - Task count per user story
   - Parallel opportunities identified
   - Independent test criteria for each story
   - Suggested MVP scope (typically just User Story 1)
   - Format validation: Confirm ALL tasks follow the checklist format (checkbox, ID, labels, file paths)

Context for task generation: $ARGUMENTS

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Guideline Task Integration

Before generating tasks, check for applicable guidelines:

1. **Scan `$KIT_ROOT/skills/guidelines/`** and `<workspace root>/.github/skills/guidelines/` for matching technology patterns from plan.md
> You should scan once if they're the same directory, otherwise scan them independently and merge results.
2. **For each matching guideline**:
   - Load the SKILL.md migration checklist
   - Map checklist items to task phases
   - Generate specific transformation tasks with file paths
3. **Guideline tasks follow the same format**:
   - `- [ ] T0XX [P] [US?] [GUIDELINE:skill-name] Description with file path`
   - In rewrite mode, guideline tasks MUST also include `[Source:]`: `- [ ] T0XX [P] [US?] [GUIDELINE:skill-name] Description [Source: path/to/OriginalFile.java#method]`
   - Example: `- [ ] T015 [P] [GUIDELINE:convert-action-to-controller] Convert HelloAction.execute() to HelloController.hello() [Source: src/.../HelloAction.java#execute]`
4. **Document applied guidelines** in tasks.md header:
   ```markdown
   ## Applied Guidelines
   - struts-to-spring: 14 migration tasks generated
   ```

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**Tests are OPTIONAL**: Only generate test tasks if explicitly requested in the feature specification or if user requests TDD approach.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Story?] [Plan:X.Y] Description with file path
```

**REWRITE MODE — Source Annotation (REQUIRED)**:

In **rewrite** mode, every task that converts, migrates, or rewrites source code MUST include a `[Source:]` annotation referencing the original source file(s) and method(s) that contain the business logic being rewritten. This enables the implementation agent to read the actual source code before writing target code, preserving business logic fidelity.

```text
- [ ] [TaskID] [P?] [Story?] [Plan:X.Y] Description with file path [Source: relative/path/to/SourceFile.java#method1,method2]
```

Source annotation rules:
- **Path**: Relative path from repository root to the source file being rewritten
- **Methods**: After `#`, list the specific method names (comma-separated) that contain the business logic
- **Multiple files**: Use multiple `[Source:]` annotations: `[Source: FileA.java#m1] [Source: FileB.java#m2]`
- **Entire file**: If the whole file is relevant, omit the `#`: `[Source: path/to/File.java]`
- **BL reference**: If a business-logic-inventory.md exists, also include `[BL: BL-XXX]` to link to the extracted business logic unit
- **Non-source tasks**: Setup, configuration, and scaffolding tasks that don't rewrite existing logic do NOT need `[Source:]`

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label  
   - User Story phases: MUST have story label
   - Polish phase: NO story label
5. **[Plan:X.Y] marker**: REQUIRED - References source plan item for traceability
   - Format: [Plan:2.1] means "from Phase 2, item 1"
   - Enables checkpoint generation to verify complete plan coverage
   - Multiple plan items can be referenced: [Plan:2.1,2.3]
6. **Description**: Clear action with exact file path
7. **[Source:] annotation** (REWRITE mode only): REQUIRED for tasks that rewrite existing source code
   - Format: [Source: path/to/File.java#method1,method2]
   - Enables the implementation agent to read source code before writing target code
   - See "REWRITE MODE — Source Annotation" section above for full rules
8. **[BL:] reference** (REWRITE mode, optional): Links to business-logic-inventory.md unit
   - Format: [BL: BL-XXX]
   - Provides additional behavioral context for the implementation agent

**Examples**:

- ✅ CORRECT: `- [ ] T001 [Plan:1.1] Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [P] [Plan:2.1] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [P] [US1] [Plan:2.2] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [US1] [Plan:2.2,2.3] Implement UserService in src/services/user_service.py`
- ✅ CORRECT (rewrite): `- [ ] T015 [US3] [Plan:3.2] Convert ProductAction to ProductController in src/main/java/.../ProductController.java [Source: src/main/java/.../ProductAction.java#list,add,edit,execute] [BL: BL-008,BL-009,BL-010]`
- ✅ CORRECT (rewrite): `- [ ] T016 [US3] [Plan:3.2] Migrate product form validations [Source: src/main/resources/ProductAction-validation.xml] [BL: BL-011]`
- ❌ WRONG: `- [ ] Create User model` (missing ID, Plan reference, and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox and Plan reference)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID and Plan reference)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing Plan reference and file path)
- ❌ WRONG (rewrite): `- [ ] T015 [US3] [Plan:3.2] Convert ProductAction to ProductController` (missing [Source:] — implementation agent cannot reference source code)

### Task Organization

1. **From User Stories (spec.md)** - PRIMARY ORGANIZATION:
   - Each user story (P1, P2, P3...) gets its own phase
   - Map all related components to their story:
     - Models needed for that story
     - Services needed for that story
     - Endpoints/UI needed for that story
     - If tests requested: Tests specific to that story
   - Mark story dependencies (most stories should be independent)

2. **From Contracts**:
   - Map each contract/endpoint → to the user story it serves
   - If tests requested: Each contract → contract test task [P] before implementation in that story's phase

3. **From Data Model**:
   - Map each entity to the user story(ies) that need it
   - If entity serves multiple stories: Put in earliest story or Setup phase
   - Relationships → service layer tasks in appropriate story phase

4. **From Setup/Infrastructure**:
   - Shared infrastructure → Setup phase (Phase 1)
   - Foundational/blocking tasks → Foundational phase (Phase 2)
   - Story-specific setup → within that story's phase

### Phase Structure

- **Phase 1**: Setup (project initialization)
- **Phase 2**: Foundational (blocking prerequisites - MUST complete before user stories)
- **Phase 3+**: User Stories in priority order (P1, P2, P3...)
  - Within each story: Tests (if requested) → Models → Services → Endpoints → Integration
  - Each phase should be a complete, independently testable increment
- **Final Phase**: Polish & Cross-Cutting Concerns

## Checkpoint Generation

### Step-by-Step Checkpoint Creation

After tasks.md is complete, generate the traceability checkpoint:

1. **Create checkpoint file**: `FEATURE_DIR/checkpoints/plan-to-tasks.yaml`

2. **Extract plan item inventory from plan.md**:
   ```yaml
   # Scan plan for phase items
   plan_items_found:
     - phase_id: "Phase-2"
       item_id: "2.1"
       description: "Replace Struts filter with Spring DispatcherServlet"
     - phase_id: "Phase-2"
       item_id: "2.2"
       description: "Implement controllers for routes"
   ```

3. **Extract task inventory from tasks.md**:
   ```yaml
   # Scan tasks for [Plan:X.Y] references
   tasks_found:
     - task_id: "T005"
       description: "Remove struts2-core dependency from pom.xml"
       plan_refs: ["2.1"]
     - task_id: "T006"
       description: "Add spring-webmvc dependency to pom.xml"
       plan_refs: ["2.1"]
   ```

4. **Build coverage mapping**:
   - For each plan item: find all tasks referencing it via [Plan:X.Y]
   - For each task: verify it has at least one plan item reference
   - Mark plan items as: covered | partial | missing
   - Mark tasks as: traced | orphan

5. **Include upstream traceability**:
   - Load spec-to-plan checkpoint
   - Link requirements → plan items → tasks
   - Build full trace chains: REQ-001 → Phase-2.1 → T005,T006,T007

6. **Generate checkpoint YAML**:
   ```yaml
   # checkpoints/plan-to-tasks.yaml
   metadata:
     generated: "2026-01-30"
     source_plan: "plan.md"
     target_tasks: "tasks.md"
   
   summary:
     total_plan_items: 8
     covered_plan_items: 8
     missing_plan_items: 0
     coverage_percentage: 100.0
     total_tasks_generated: 25
     orphan_tasks: 1
   
   phases:
     - phase_id: "Phase-2"
       phase_name: "Implementation"
       items:
         - item_id: "2.1"
           description: "Replace Struts filter with Spring DispatcherServlet"
           tasks:
             - task_id: "T005"
               description: "Remove struts2-core dependency"
             - task_id: "T006"
               description: "Add spring-webmvc dependency"
             - task_id: "T007"
               description: "Configure DispatcherServlet"
           status: "covered"
   
   missing_plan_items: []
   
   orphan_tasks:
     - task_id: "T099"
       description: "General cleanup"
       concern: "No [Plan:X.Y] reference found"
   
   upstream_trace:
     - plan_item: "2.1"
       source_requirements: ["REQ-001", "REQ-002"]
       tasks: ["T005", "T006", "T007"]
       full_trace: "REQ-001,002 → Phase-2.1 → T005,T006,T007"
   
   validation:
     passed: true
     errors: []
     warnings: ["Task T099 has no plan item traceability"]
   ```

### End-to-End Traceability Report

After checkpoint generation, output a summary table:

```markdown
## Traceability Summary

| Requirement | Plan Phase | Plan Item | Tasks | Status |
|-------------|------------|-----------|-------|--------|
| REQ-001 | Phase-2 | 2.1 | T005, T006, T007 | ✓ Complete |
| REQ-002 | Phase-2 | 2.1, 2.2 | T005-T010 | ✓ Complete |
| REQ-003 | Phase-3 | 3.1 | T015 | ✓ Complete |
| REQ-004 | - | - | - | ❌ MISSING |
```

This table provides at-a-glance visibility into complete coverage from requirements through implementation tasks.