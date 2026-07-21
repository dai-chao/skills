# Agent Guard Competitor Landscape

Session: 2026-07-06. Gathered for `/Users/chao/Desktop/agent-guard`.

## Direct desktop / local monitors

| Project | Repo | Language | Key positioning | Strengths relative to Agent Guard | Weaknesses / gaps |
|---------|------|----------|-----------------|-----------------------------------|-------------------|
| Unalome Agent Firewall | `unalome-ai/unalome-firewall` | ? | Free, open-source desktop app; plain-language visibility into what agents do on your machine | Full desktop product, branding, auto-discovers Claude Code / Cursor, backups files before overwrite | Could be heavier; less focused on fine-grained permission categories |
| AI Runtime Monitor | `rajan-cforge/ai-runtime-monitor` | Python | CrowdStrike-style runtime monitor for AI coding agents | Process + network + filesystem + token spend + web dashboard | Not a polished desktop app; Python + web UI only |
| Agent Inspector | `cylestio/agent-inspector` | ? | Local dev tool to debug, secure, evaluate LLM agents | Static analysis + dynamic checks + runtime monitoring; IDE integration via MCP | More dev-tool oriented, less end-user dashboard |

## Runtime security / authorization layers (framework or MCP proxy)

| Project | Repo | Key positioning | Notable features |
|---------|------|-----------------|------------------|
| Doberman-Core | `fu351/Doberman-Core` | MCP proxy that returns PASS / AUTH / BLOCK before tool execution | Risk engine, policy enforcement, tool-use permissions, audit logs |
| AgentLock | `webpro255/agentlock` | Pre-action agent authorization reference implementation | Identity verification, scoped access control, framework-agnostic |
| Adrian | `secureagentics/Adrian` | Runtime security monitoring and control engine | Analyzes activity logs + reasoning traces; detects malicious/misaligned behavior; can intervene |
| arp-guard | `opena2a-org/agent-runtime-protection` | 3-layer runtime protection for AI agents | Process, network, filesystem, AI-layer comms (prompts, MCP, A2A) |
| agent-harness | `redevops-io/agent-harness` | Toolkit for building safe tool-using agents | LLM client, tool registry, approval flow, sandboxed execution, guardrails, eval harness |

## Audit / governance / gateway

| Project | Repo | Key positioning | Notable features |
|---------|------|-----------------|------------------|
| AgentProvenance | `ByteYellow/AgentProvenance` | Security-oriented execution observability and Git-like provenance | Verifiable evidence graphs, causality graph, replay, forensics |
| Gate22 | `aipotheosis-labs/gate22` | Open-source MCP gateway and control plane for teams | Function-level allow lists, credential modes, unified MCP endpoint, audit |

## Differentiation angles for Agent Guard

1. **Personal-local-first**: target individual developers on macOS, not enterprise governance teams.
2. **Fine-grained permission categories**: filesystem, network, command execution, environment variables as first-class citizens.
3. **Privacy scan + risk keyword marking**: surface secrets and dangerous commands in real time, not just post-hoc.
4. **Design-forward Electron desktop**: the current aesthetic direction (cream/coral/navy) can be a distinct UX advantage.

## Recommended next steps from this landscape

1. Make the three core pillars explicit: **live call log**, **privacy scan**, **rule-based interception**.
2. Support reading existing agent logs from Claude Code, Cursor, and Hermes Agent as the fastest data hook.
3. Eventually offer a lightweight MCP proxy mode so Agent Guard can move from "observe and report" to "intercept and block".
