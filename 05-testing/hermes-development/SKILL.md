---
name: hermes-development
description: "Develop and extend Hermes Agent: configuration, skill authoring, kanban orchestration, project analysis, frontend mapping, QA auditing, and exploratory testing."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Hermes, Agent Development, Skill Authoring, Kanban, Project Analysis, QA, Dogfooding]
    related_skills: [autonomous-coding-agents]
---

# Hermes Agent Development

## When to Use This Skill

Trigger when the user wants to:
- Configure, extend, or troubleshoot Hermes Agent itself
- Author or validate Hermes skills (SKILL.md format)
- Set up kanban orchestration for multi-agent workflows
- Analyze project codebases and generate reports
- Map frontend components and architectures
- Audit AI coach outputs for quality
- Perform exploratory QA (dogfooding) on web apps

## Section 1: Hermes Agent Configuration

Configure Hermes CLI, models, providers, tools, skills, voice, gateway, plugins.

```bash
# Set configuration
hermes config set model claude-sonnet-4
hermes config set provider openrouter

# List tools
hermes tools

# Setup wizard
hermes setup
```

See [references/hermes-agent.md](references/hermes-agent.md) for full details.

## Section 2: Skill Authoring

Author in-repo SKILL.md with proper frontmatter, validator, and structure.

### SKILL.md Structure
```yaml
---
name: skill-name
description: "Clear description"
version: 1.0.0
author: Name
metadata:
  hermes:
    tags: [tag1, tag2]
    related_skills: [other-skill]
---

# Skill Title

## When to Use This Skill

## Quick Reference

## Common Pitfalls
```

See [references/hermes-agent-skill-authoring.md](references/hermes-agent-skill-authoring.md) for full details.

## Section 3: Kanban Orchestration

Multi-agent kanban workflow orchestration.

```bash
# Start kanban orchestrator
hermes kanban start --workers 4
```

See [references/kanban-orchestrator.md](references/kanban-orchestrator.md) for full details.

### Kanban Worker
Individual worker agent for kanban tasks.

See [references/kanban-worker.md](references/kanban-worker.md) for full details.

## Section 4: Project Analysis

Analyze codebases and produce structured reports.

```bash
# Analyze project
hermes analyze ./my-project --output report.md
```

See [references/project-analysis-reporting.md](references/project-analysis-reporting.md) for full details.

## Section 5: Frontend Mapping

Map frontend components, routes, and state management.

See [references/frontend-mapping.md](references/frontend-mapping.md) for full details.

## Section 6: QA Auditing

Audit AI coach chat outputs for persona, tone, safety, and accuracy.

### Audit Dimensions
1. Tone & Persona consistency
2. Safety override rules
3. Scene-trigger matching
4. Terminology accuracy
5. Cross-output consistency

See [references/jymo-coach-audit.md](references/jymo-coach-audit.md) for full details.

## Section 7: Exploratory QA (Dogfooding)

Find bugs, evidence, and reports in web apps through exploratory testing.

```bash
# Start dogfood session
hermes dogfood https://example.com
```

See [references/dogfood.md](references/dogfood.md) for full details.

## Common Pitfalls

1. **Skill name uniqueness**: Check existing skills before creating new ones
2. **Frontmatter validation**: Use the built-in validator before submitting
3. **Kanban worker limits**: Don't spawn more workers than CPU cores
4. **Project analysis scope**: Large repos need chunked analysis
5. **Frontend mapping**: Dynamic routes need runtime analysis, not just static
6. **QA audit subjectivity**: Define clear rubrics before auditing
7. **Dogfooding bias**: Test with fresh eyes, not developer knowledge
