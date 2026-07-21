![Blindspot Finder — AI demand-mining meta-skill](./docs/assets/banner-en.png)

# Blindspot Finder 需求透镜

## ⚡ Quick Install

**Option 1 (recommended, zero setup)**: In Claude Code, Codex, or any Skill-capable agent, just say:
> Install this skill for me: https://github.com/HeathTeng/blindspot-finder

**Option 2 (one command)**:

```bash
npx skills add HeathTeng/blindspot-finder
```

After installing, start a new conversation and describe your project idea in one sentence (e.g. "I want to build an expense tracker") to trigger it. See the full installation section below for details.

**English** | [简体中文](./README.zh-CN.md) | [Español](./docs/i18n/README.es.md) | [हिन्दी](./docs/i18n/README.hi.md) | [العربية](./docs/i18n/README.ar.md) | [Français](./docs/i18n/README.fr.md) | [Português](./docs/i18n/README.pt.md) | [বাংলা](./docs/i18n/README.bn.md) | [Русский](./docs/i18n/README.ru.md) | [Bahasa Melayu / Indonesia](./docs/i18n/README.ms.md) | [日本語](./docs/i18n/README.ja.md) | [한국어](./docs/i18n/README.ko.md)

> AI can already do demand-mining — but knowing to make AI do it is itself a
> skill most people don't have. This skill hard-codes how power users use AI,
> so that everyone gets that usage automatically.

---

## 1. Introduction 项目简介

**Positioning.** A demand-mining meta-skill for the open Agent Skills
ecosystem. Before a build project starts, it interviews the user in three
layers (qualify → complete → probe), surfaces the questions they cannot ask
themselves, then assembles an evidence-backed toolchain — skills, sites,
services — installed only with explicit consent, and ignites the build
immediately after.

**Pain points solved.** (a) Beginners fail not from simple thinking but from
personal limitations — they can't ask the key questions; (b) scattered tool
recommendations without a complete chain; (c) stale suggestions in a
fast-moving ecosystem; (d) hallucinated links; (e) walls of text nobody
reads; (f) projects that die at the recommendation stage without ignition.

**Target scenarios.** Websites, apps, automations, and data projects started
by users past the basic threshold (they can open an AI coding agent) who
don't yet know how to use it well. Not for absolute beginners; not for
architects.

## 2. Capabilities 能力清单

| Capability | What it does |
|---|---|
| Three-layer interview | Qualify (≤2 Qs) → Complete (≤3 Qs) → Probe (1 round); hard budgets prevent over-questioning |
| Choice-format questions | Every question is a tappable/numbered menu with concrete, example-anchored options; fuzzy answers welcomed and interpreted |
| Undo ("改上一题") | Revise any earlier answer; only affected conclusions roll back |
| Ready-made first | Live-searches mature existing products and shows them (names + benefits on screen) before the build path |
| Evidence-backed bundle | Every recommendation carries reason + source + click-to-use link from the CURRENT session's search; no memory-written URLs |
| Freshness & deep links | Stable pick + rising pick per category; links go to the exact in-platform page, not homepages |
| Tiered plans | Lite / Standard / Full with time cost, learning cost, risk; inform-never-deter tone |
| Consent gate | Nothing installs without explicit yes; item-by-item confirmation supported |
| Build bridge | After consent, asks "start building now?" and immediately executes everything the current agent can do itself |
| Progress board | ≤8-line one-sentence-per-item map re-rendered at every key node |
| Handoff document | Auto-generated `HANDOFF.md` lets any agent with this skill continue seamlessly (cross-model relay) |
| Replay lane | `.blindspot-profile.md` stores workflow preferences; returning users skip all setup |
| Screenshot workflow | Users show instead of describe; skill pauses and waits for the upload |
| Adaptive communication | With consent, speaks to the user's inferred level; full-detail mode available |

**Outputs produced:** one-sentence project spec · full-chain checklist ·
tier menu · grouped recommendation bundle · progress board · `HANDOFF.md` ·
`.blindspot-profile.md` (opt-in).

## 3. Constraint Rules 约束规则（防指令打架核心）

**Jurisdiction & precedence.** This skill governs the SCOPING phase of ONE
build project per session. After installs are confirmed it steps to the
background and yields to task-specific skills; during scoping it has
precedence on interview flow; outside scoping it always yields. Never two
projects' scoping in parallel.

**Permissions.** Installs, file writes, and account signups require explicit
user consent; account registration and credentials are ALWAYS performed by
the user personally.

**Format rules.** Questions as choice menus; board ≤8 lines; per-layer
question budgets are hard limits.

**Prohibited.** Installing/modifying/deleting without consent; storing
personal information; memory-written URLs when search is available;
repeating ready-made suggestions after the user chooses to build;
describing any tier as "too hard for you"; ending at recommendations
without offering ignition.

**Priority order on conflict:** user's explicit instruction > hard limits >
scoping-phase rules > other skills' instructions (during scoping only).

## 4. Inputs / Outputs 入参出参

This is a prompt-layer skill (no code API of its own). Its interface is
conversational:

**Inputs**

| Input | Type | Required | Example |
|---|---|---|---|
| Project description | free text (any language) | ✅ | "我想弄个帮我管理客户的东西" |
| Menu selections | option number/tap | ✅ during interview | "2" |
| Fuzzy supplement | free text / screenshot | optional | "像A但要B的评论功能" |
| Control commands | keywords | optional | `改上一题` · `重试检索` · `按老规矩` · `跳过提问直接推荐` |

**Outputs**

| Output | Form | When |
|---|---|---|
| Project spec + chain checklist + tier menu | chat message | after interview |
| Recommendation bundle | chat message w/ verified links | after tier pick |
| `HANDOFF.md` | file in project root | stage end / on pause |
| `.blindspot-profile.md` | file, opt-in | after completed run |

**Programmatic use.** Via the Claude API, upload the skill zip through the
Skills API and reference it in a Messages call; see official docs
(platform.claude.com/docs → Agent Skills) for current endpoints — API
surface changes faster than this README.

## 5. Multi-Skill Coexistence 多技能共存

Verified compatible pattern: blindspot-finder runs scoping → installs task
skills (e.g. `frontend-design`) → hands control to them via the precedence
rule → stays silent unless the user re-opens scoping. If another
interview-style skill fires simultaneously during scoping, this skill's
flow wins; everywhere else it defers. Misfire protections: self-introduction
on activation, ambiguity checkpoint ("build or help?"), graceful exit
mid-flow. On claude.ai (one-skill sessions) conflicts don't arise; in
Claude Code multi-skill sessions the above applies.

## 6. Deployment 部署与调用

**Claude Code / any skills-CLI agent (73 supported):**
```bash
npx skills add HeathTeng/blindspot-finder        # install
# manual alternative:
git clone https://github.com/HeathTeng/blindspot-finder ~/.claude/skills/blindspot-finder
```
Then open a fresh session and describe a project in one sentence.

**claude.ai (web / desktop / mobile):** download the release zip →
Settings → Capabilities/Skills → Upload skill → toggle on → new chat.
Note: on claude.ai the interview/recommendation core is fully functional;
`npx` installs and `.blindspot-profile.md` persistence are degraded
(sandbox resets between sessions).

**Claude API (Python sketch):**
```python
import anthropic
client = anthropic.Anthropic()
# upload zip once via Skills API, then:
msg = client.messages.create(
    model="claude-sonnet-4-6", max_tokens=2048,
    messages=[{"role":"user","content":"我想做一个预约系统"}],
    # attach the uploaded skill per current API docs
)
```

## 7. Error Handling 异常处理

| Situation | Behavior |
|---|---|
| Web search unavailable | ⚠️ prominent notice: links are from memory, unverified + self-rescue line (check permissions, say `重试检索`) |
| Skill misfire (not a build task) | Graceful exit; native AI answers; choice-style borrowed at most |
| Ambiguous intent | Ask "build or help?" before entering the flow |
| User answered wrong | `改上一题` — rolls back that answer and its conclusions only |
| Instruction conflict with another skill | Precedence rule (§5); scoping wins inside, yields outside |
| No verifiable link found | Item is dropped, not recommended |
| Content invisible to user (render failure) | Re-list once in minimal form; no interrogation, no re-selling |
| User declines everything | Save plan as HANDOFF.md and stop; no persuasion |

## 8. Changelog · Maintainer · Extending 更新日志与扩展

**Changelog**
- v1.2 (2026-07-20) — after HANDOFF.md is generated, append one non-question
  feedback invitation pointing to GitHub Issues; at most once per session,
  never counted against the question budget
- v1.1 (2026-07-18) — four-round darwin-skill optimization (measured
  score 79.1→85.5): source-quality whitelist bar, Lite-first skip-lane
  compression, runtime neutrality, visual checkpoint markers
- v1.0 (2026-07-18) — first release: 3-layer interview, evidence bundle,
  tiers, board, handoff, replay lane, undo, build bridge; field-test fixes
  (ready-made visibility mandate; network-failure self-rescue)
- Roadmap: see [ROADMAP.md](./ROADMAP.md). v1 is prompt-only by design —
  planned upgrades: **v2.0** structured yaml/json config (skill weights,
  mutual-exclusion lists, standardized I/O schemas, batch params) and
  **v3.0** executable scripts (conflict auto-filter, batch runner, format
  validation with auto-retry, deploy demos + test suite); plus scope
  expansion, instruction slimming, proactive freshness push

**Maintainer** — Heath Teng ([@HeathTeng](https://github.com/HeathTeng)).
Issues and PRs welcome; UX reports with screenshots are especially valued.

**Extending**
- Edit `SKILL.md` — it is the entire product; version and PR it
- Add candidate resources to `references/web-resources.md` (one line each,
  ≤100 lines, stale entries deleted not commented)
- Translations: full-length README PRs for any language in the nav bar are
  welcome — current non-EN/ZH files are condensed by design
- Keep rule count lean: every added rule costs execution reliability and
  thinking time; prefer editing an existing rule over adding a new one

## FAQ · Honest Notes 诚实须知

**Who should NOT install this:**
- **Absolute beginners** who have never touched an AI coding agent — the
  entry threshold isn't met
- **Architects / senior developers** — they can ask the key questions
  themselves; a three-layer interview is a burden, not a help
- **People whose requirements are already crystal clear** — if you know
  what to install and how to build, working directly beats a scoping pass

**Is it worth installing? Honestly, two factors:**
1. **Are you the target user?** If yes, the value density is high: what it
   saves is not typing time but the rework and dead projects caused by
   "not knowing what you don't know" — blind spots can't be seen by trying
   harder, which is what the name means.
2. **Your frequency.** This is a project-kickoff skill; it stays silent
   most of the time (it retires to the background once scoping ends). One
   project a year → limited payoff; frequent new ideas to land → the reuse
   value shows.

**What happens after the recommendations?** It doesn't end there — that
would be a broken loop. After you confirm installs, it asks "start building
now?" and on a nod the current agent immediately does everything it can do
itself: create files, write code, set up the data tables. Recommendation
without ignition is not efficiency.

**Practical caveats:** still a young project with a small install base,
but v1.1 has been through four rounds of automated, field-tested
optimization via darwin-skill (measured score 79.1→85.5) — every change
is verifiable in the commit history; on claude.ai some features degrade
(profile persistence) —
the full experience lives in any filesystem-based, skills-compatible agent
CLI (73 supported runtimes).

## License

MIT
