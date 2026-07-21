---
name: rewrite
description: Guidelines for rewrite mode, including workflow, best practices, and risk mitigation strategies.
---

# Rewrite Mode Guidelines

## Metadata

- **Mode**: Rewrite (vs Upgrade)
- **Purpose**: Create new application with target technology stack, migrating only business logic
- **Version**: 1.0.0
- **Last Updated**: 2026-02-01

## Overview

Rewrite mode creates a **new project** with the desired target technology stack and **extracts business logic** from the source application. Unlike Upgrade mode, there are no "upgrade units" or version stepping - you directly use the target versions.

## Key Differences from Upgrade Mode

| Aspect | Upgrade Mode | Rewrite Mode |
|--------|-------------|--------------|
| **Project** | Modify existing | Create new |
| **Code History** | Preserved | Fresh start |
| **Dependencies** | Incremental upgrade | Direct target version |
| **Business Logic** | Transform in place | Extract and rewrite |
| **Tests** | Convert existing | Write new |
| **Risk** | Compatibility issues | Functional gaps |

## Rewrite Workflow Integration

Rewrite-specific skills are invoked at different phases of the standard workflow:

| Skill | Phase | Invoked By |
|-------|-------|------------|
| [Business Logic Extraction](SKILL-business-logic-extraction.md) | Plan Phase 0 (Research) | Planning skill |
| [Target Scaffolding](../guidelines/spring-boot-scaffolding/SKILL.md) | Implementation | Implement skill (as guideline) |
| [Functional Equivalence](SKILL-functional-equivalence.md) | Completeness Check | Completeness skill |

## Rewrite Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        REWRITE MODE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────┐       │
│  │  SOURCE  │───▶│   EXTRACT    │───▶│ BUSINESS LOGIC  │       │
│  │  CODE    │    │   ANALYZE    │    │   INVENTORY     │       │
│  └──────────┘    └──────────────┘    └────────┬────────┘       │
│                                               │                 │
│  ┌──────────┐    ┌──────────────┐            │                 │
│  │  TARGET  │◀───│  SCAFFOLD    │◀───────────┘                 │
│  │  STACK   │    │  NEW PROJECT │                              │
│  └────┬─────┘    └──────────────┘                              │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────┐       │
│  │IMPLEMENT │───▶│   VERIFY     │───▶│   VALIDATED     │       │
│  │  LOGIC   │    │ EQUIVALENCE  │    │   APPLICATION   │       │
│  └──────────┘    └──────────────┘    └─────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## When to Choose Rewrite

### Good Candidates for Rewrite

- **Significant technical debt**: Original code is hard to understand/maintain
- **Outdated architecture**: Original patterns are incompatible with modern frameworks
- **Small to medium codebase**: Manageable to re-implement
- **Clear business requirements**: Well-documented or testable business rules
- **Target stack expertise**: Team knows the target technology well

### Poor Candidates for Rewrite

- **Very large codebase**: Too much to re-implement safely
- **Undocumented business logic**: Risk of missing functionality
- **Tight timelines**: Rewrite often takes longer than estimated
- **Critical compliance requirements**: Need audit trail of changes

## Rewrite Checklist

### Phase 1: Analysis
- [ ] Complete business logic inventory
- [ ] Document all external integrations
- [ ] Identify cross-cutting concerns
- [ ] Map data model and persistence
- [ ] Catalog API contracts (if applicable)

### Phase 2: Scaffolding
- [ ] Create target project structure
- [ ] Configure build system (Maven/Gradle)
- [ ] Set up target JDK version
- [ ] Add framework dependencies (Spring Boot, etc.)
- [ ] Configure CI/CD pipeline skeleton

### Phase 3: Implementation
- [ ] Implement domain entities
- [ ] Implement business logic services
- [ ] Implement controllers/API layer
- [ ] Implement persistence layer
- [ ] Implement integration points

### Phase 4: Verification
- [ ] Unit tests for all business logic
- [ ] Functional equivalence testing
- [ ] Integration testing
- [ ] Performance baseline comparison
- [ ] Security review

### Phase 5: Validation
- [ ] All business logic units verified
- [ ] No functional gaps
- [ ] Documentation complete
- [ ] Stakeholder sign-off

## Common Patterns

### Struts → Spring Boot Rewrite

```
Source (Struts)              Target (Spring Boot)
────────────────             ───────────────────
ActionSupport         →      @RestController / @Controller
struts.xml routing    →      @RequestMapping annotations
OGNL expressions      →      SpEL or standard Java
Struts interceptors   →      Spring interceptors / filters
ActionForm            →      @RequestBody / @ModelAttribute
```

### EJB → Spring Boot Rewrite

```
Source (EJB)                 Target (Spring Boot)
────────────────             ───────────────────
@Stateless EJB        →      @Service
@PersistenceContext   →      @Autowired EntityManager
@TransactionAttribute →      @Transactional
JNDI lookup           →      @Autowired dependency injection
```

## Risk Mitigation

1. **Functional Gap Risk**: Comprehensive business logic inventory
2. **Timeline Risk**: Iterative implementation with early verification
3. **Integration Risk**: Stub external dependencies initially
4. **Data Risk**: Parallel run with production data validation

## Success Metrics

- **Business Logic Coverage**: 100% of inventory items implemented
- **Functional Equivalence**: All test scenarios passing
- **Build Quality**: Zero errors, zero warnings
- **Test Coverage**: Minimum 80% code coverage
- **Performance**: Within 10% of original baseline