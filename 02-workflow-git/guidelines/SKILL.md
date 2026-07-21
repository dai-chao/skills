---
name: guidelines
description: Dynamically discover and apply domain-specific guidelines based on the current task context.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This skill enables dynamic discovery and application of domain-specific guidelines during any phase of the workflow (specification, planning, tasks, implementation).

### Purpose

Guidelines are curated, domain-specific knowledge bases that provide:
- **Migration patterns**: Technology-to-technology migration recipes (e.g., Struts to Spring Boot)
- **Best practices**: Industry-standard approaches for specific technologies
- **Transformation rules**: Concrete mappings and conversion templates
- **Checklists**: Step-by-step validation criteria

### Directory Structure

```
skills/guidelines/
├── SKILL.md                    # This file - lookup mechanism
├── struts-to-spring/           # Struts 2 → Spring Boot 3.x
│   └── SKILL.md
├── ejb-to-spring/              # EJB → Spring Boot (future)
│   └── SKILL.md
├── jsf-to-react/               # JSF → React (future)
├── java8-to-java21/            # Java version upgrades (future)
├── javax-to-jakarta/           # Namespace migration (future)
├── monolith-to-microservices/  # (future)
└── layered-to-hexagonal/       # (future)
```

### Lookup Mechanism

When executing any skill (constitution, specification, planning, tasks, implementation), the workflow can invoke guideline lookup:

1. **Context Analysis**: Extract technology keywords from:
   - Current specification/plan documents
   - Source code imports and dependencies
   - User-provided context in `$ARGUMENTS`

2. **Guideline Discovery**: Search `skills/guidelines/` subdirectories for:
   - Matching technology patterns (case-insensitive)
   - Keywords in SKILL.md files
   - Related migration paths

3. **Relevance Scoring**: Rank guidelines by:
   - Direct technology match (highest)
   - Related technology family
   - General domain applicability

4. **Application**: For each relevant guideline:
   - Load the SKILL.md content
   - Extract applicable skills/patterns for current phase
   - Integrate into current task execution

### Usage Pattern

Other skills should invoke guideline lookup when:

```markdown
## Guideline Check

Before proceeding with [current phase], check for applicable guidelines:

1. Identify technologies involved: [list from spec/plan/code]
2. Search guidelines directory: `skills/guidelines/`
3. For each matching guideline:
   - Load SKILL.md
   - Apply relevant transformation rules
   - Follow domain-specific checklists
```

### Integration Points

| Workflow Phase | Guideline Application |
|----------------|----------------------|
| Specification | Domain constraints, scope boundaries |
| Planning | Technology decisions, architecture patterns |
| Tasks | Specific transformation tasks, file-by-file changes |
| Implementation | Code transformation rules, test patterns |
| Completeness | Validation checklists, coverage criteria |

### Creating New Guidelines

To add a new guideline domain:

1. Create directory: `skills/guidelines/{domain}/`
2. Create `SKILL.md` (can have multiple skill files like `SKILL.md`, `SKILL-validation.md`, etc.) with:
   - Metadata header (name, description, triggers)
   - Skills/patterns organized by migration phase
   - Concrete transformation rules with examples
   - Validation checklist

Template structure:

```markdown
# {Domain} Guideline

## Metadata
- **Source Technology**: [what we're migrating from]
- **Target Technology**: [what we're migrating to]
- **Trigger Keywords**: [keywords that activate this guideline]

## Skills

### Skill: {skill-name}
**Description:** [what this skill does]
**Trigger:** [when to apply]
**Steps:** [transformation steps]
**Examples:** [before/after code]

## Migration Checklist
- [ ] Step 1
- [ ] Step 2
...
```

### Example: Struts to Spring Lookup

When a specification mentions "Struts migration" or code contains `import com.opensymphony.xwork2`:

1. **Detection**: Keywords match `struts-to-spring` guideline
2. **Load**: Read `skills/guidelines/struts-to-spring/SKILL.md`
3. **Apply**:
   - During **planning**: Use migration checklist for task sequencing
   - During **implementation**: Apply `convert-action-to-controller` skill
   - During **testing**: Use `convert-test-classes` skill

### Output

When guidelines are applied, document in the relevant artifact:

```markdown
## Applied Guidelines

- **Guideline**: struts-to-spring
- **Skills Used**: convert-action-to-controller, convert-validation
- **Reference**: skills/guidelines/struts-to-spring/SKILL.md
```