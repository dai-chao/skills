---
name: software-development-methodologies
description: "Software development methodologies and patterns: systematic debugging, TDD, spike experiments, code simplification, subagent-driven development, planning, and common pitfalls (TDZ, streaming timeouts, Vite setup)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Software Development, Debugging, TDD, Spike, Code Simplification, Planning, Subagent Development, Pitfalls]
    related_skills: [autonomous-coding-agents, language-debugging]
---

# Software Development Methodologies

## When to Use This Skill

Trigger when the user wants to:
- Debug software systematically (4-phase root cause analysis)
- Apply test-driven development (RED-GREEN-REFACTOR)
- Run spike experiments to validate ideas
- Simplify and clean up code
- Plan multi-step implementations
- Use subagent-driven development for parallel work
- Avoid common JavaScript/Node.js pitfalls (TDZ, streaming timeouts)
- Set up Vite + React manually when create-vite fails

## Section 1: Systematic Debugging

4-phase root cause debugging: understand bugs before fixing.

### Phase 1: Reproduce
- Create minimal reproduction case
- Verify bug exists in isolation
- Document exact steps

### Phase 2: Isolate
- Binary search through code paths
- Use logging/debugger to narrow scope
- Check environment differences

### Phase 3: Hypothesize
- Form testable hypotheses
- Prioritize by likelihood and ease of verification
- Check assumptions about inputs/state

### Phase 4: Verify Fix
- Apply minimal fix
- Verify fix doesn't break other functionality
- Add regression test

See [references/systematic-debugging.md](references/systematic-debugging.md) for full details.

## Section 2: Test-Driven Development

Enforce RED-GREEN-REFACTOR cycle.

```python
# RED: Write failing test first
def test_add():
    assert add(2, 3) == 5

# GREEN: Write minimal code to pass
def add(a, b):
    return a + b

# REFACTOR: Improve while keeping tests green
def add(a, b):
    """Return sum of two numbers."""
    return a + b
```

See [references/test-driven-development.md](references/test-driven-development.md) for full details.

## Section 3: Spike Experiments

Throwaway experiments to validate ideas before building.

### Rules
1. Time-box: 1-4 hours max
2. Throwaway code: Don't commit to production
3. Document learnings: What worked, what didn't
4. Decision gate: Go/No-go based on findings

See [references/spike.md](references/spike.md) for full details.

## Section 4: Code Simplification

Parallel 3-agent cleanup of recent code changes.

### Process
1. Identify complex/smelly code
2. Spawn 3 agents with different simplification strategies
3. Compare results and merge best approach
4. Verify behavior unchanged

See [references/simplify-code.md](references/simplify-code.md) for full details.

## Section 5: Subagent-Driven Development

Use independent subagents for parallel implementation.

### When to Use
- Multi-step plans with independent workstreams
- Large refactors that can be split
- Code review requiring multiple perspectives

### Pattern
```python
# Spawn 3 agents for different aspects
agent1: refactor data layer
agent2: refactor business logic
agent3: update tests
# Merge results when all complete
```

See [references/subagent-driven-development.md](references/subagent-driven-development.md) for full details.

## Section 6: Planning

Write actionable markdown plans to `.hermes/plans/`.

### Plan Structure
```markdown
# Plan: Feature Name

## Goal
Clear statement of what we're building

## Steps
1. [ ] Step 1
2. [ ] Step 2
3. [ ] Step 3

## Risks
- Risk 1 and mitigation
- Risk 2 and mitigation
```

See [references/writing-plans.md](references/writing-plans.md) for full details.

## Section 7: Common Pitfalls

### JavaScript TDZ (Temporal Dead Zone)
```javascript
// WRONG: ReferenceError
console.log(x); // TDZ!
const x = 5;

// CORRECT
const x = 5;
console.log(x);
```

See [references/js-tdz-init-order.md](references/js-tdz-init-order.md) for full details.

### Python Streaming Timeouts
```python
import requests

# WRONG: May hang indefinitely
response = requests.get(url, stream=True)

# CORRECT: Set read timeout
response = requests.get(url, stream=True, timeout=(connect_timeout, read_timeout))
```

See [references/python-requests-streaming-timeout.md](references/python-requests-streaming-timeout.md) for full details.

### Manual Vite + React Setup
When create-vite fails due to Node version incompatibility:
```bash
npm create vite@latest my-app --template react
# If that fails:
npm init -y
npm install vite@latest react react-dom
# Create vite.config.js and index.html manually
```

See [references/manual-vite-react-setup.md](references/manual-vite-react-setup.md) for full details.

### API Documentation Extraction from Browser-Rendered Docs
When `web_extract` fails on SPA docs (blocked/empty), use the browser stack to extract the full API spec programmatically:
1. `browser_navigate` to the URL.
2. `browser_click` the relevant nav link if needed.
3. `browser_console` with `document.querySelector('main')?.innerText || document.body.innerText` to pull the rendered text content in one shot.
4. Parse the plain text into structured fields (endpoint, headers, body params, response).

This avoids brittle DOM traversal on React/Vue-rendered documentation sites and works even when the page has no accessible API content endpoint.

See [references/browser-api-doc-extraction.md](references/browser-api-doc-extraction.md) for a worked example (MiniMax Voice Clone API).

## Common Pitfalls

1. **Debugging without reproduction**: Never fix a bug you can't reproduce
2. **TDD without refactoring**: Green tests don't mean clean code
3. **Spike code in production**: Spikes are throwaway by definition
4. **Over-simplification**: Don't remove necessary complexity
5. **Subagent coordination**: Define clear interfaces between agents
6. **Planning paralysis**: Start with a 1-page plan, expand as needed
7. **TDZ with let/const**: Always declare before use in same block
8. **Streaming without timeouts**: Always set both connect and read timeouts
9. **Vite version mismatch**: Check Node version compatibility
