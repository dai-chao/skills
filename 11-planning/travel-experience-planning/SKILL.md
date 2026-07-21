---
name: travel-experience-planning
description: Plan experiential travel (fishing, farming, harvesting, festivals, trekking) with mandatory checks for seasonal regulations, moratoriums, and local constraints that could invalidate the itinerary.
version: 1.0
author: Hermes Agent
---

# Travel Experience Planning

Use this skill when the user asks for travel planning that includes hands-on or experiential activities tied to nature, local culture, or seasonal events — such as fishing with locals, farm harvesting, trekking, wildlife viewing, diving, or festival participation.

## Why this matters

Experiential activities often have **hard seasonal or regulatory constraints** that generic travel planning misses:
- Fishing/hunting moratoriums (e.g., China's summer fishing ban starts May 1 in Fujian)
- Harvest windows (e.g., tea-picking season, cherry season)
- Monsoon/trekking closures
- Festival dates that shift yearly
- Permit quotas or advance booking windows

Discovering these constraints late forces painful itinerary changes. This skill builds constraint-checking into the planning flow.

## Workflow

### 1. Gather basics
- Dates (exact, not approximate)
- Destination + nearby areas
- User's must-do experiential activity
- Crowd/pace preferences
- Budget range

### 2. Draft an initial itinerary
Assume the activity is feasible. Sketch a logical day-by-day flow.

### 3. Research constraints (CRITICAL)
Before presenting the plan, search for:
- **Seasonal moratoriums or bans** affecting the activity in that region during those dates
- **Local regulations** (e.g., fishing boat bans, harvesting permits, protected-area closures)
- **Activity-specific calendars** (e.g., spawning seasons, monsoon closures)
- **Holiday congestion** (Chinese Golden Week, local festivals)

Use search queries like:
- `<location> <activity> <month> 禁渔/休渔/封山/闭园`
- `<location> <activity> seasonal restrictions <year>`
- `<activity> <region> permit required`

### 4. Evaluate findings

| Finding | Action |
|---|---|
| No constraints found | Proceed with initial plan |
| Soft constraint (crowds, price spikes) | Warn user, offer alternatives |
| Hard constraint (illegal/impossible during dates) | **Must replan**. Move activity to feasible dates, or substitute with a legally/permissibly similar experience |

### 5. Replan if needed
If a hard constraint blocks the original activity:
- **Explain the constraint transparently** (what it is, exact dates, why it exists)
- **Move the activity** to a feasible window within the trip if possible
- **If not feasible at all**, offer the closest legal alternative that preserves the spirit of the request
- **Adjust logistics** (booking methods, costs, gear) to match the new reality

### 6. Deliver the plan
Structure:
1. **Constraint warning** (if any) — top of response, bold
2. **Revised itinerary** — day by day
3. **Activity details** — how to book, costs, what to wear/bring, meeting points
4. **Alternatives** — what to do if Plan A fails (weather, cancellations)
5. **Practical tips** — local transport, food, scams to avoid

## Example from practice

User: "五一去福州，想跟渔民出海体验"

Constraint discovered: 福建海洋伏季休渔期 = May 1, 12:00. Fishing boats banned from catch operations after that.

Result:
- Original plan would have put fishing on May 1–3 (impossible)
- Revised plan: Move fishing to **April 29** (before moratorium)
- Post–May 1 alternative: Shore-based tidal flat foraging (赶海), which remains legal
- Explained booking method (via homestay owner), pricing (~500–800 CNY/boat), and gear

## Pitfalls to avoid

- **Don't assume experiential activities are year-round**. Always verify.
- **Don't suggest illegal workarounds** (e.g., "some fisherman might take you illegally"). It endangers the user and locals.
- **Don't hide the constraint** deep in the response. Lead with it.
- **Don't skip practical logistics** after replanning. Moving a fishing trip from Day 4 to Day 1 changes accommodation, transport, and booking lead times.

## Verification checklist

Before finalizing the response:
- [ ] Have I searched for seasonal/regulatory constraints?
- [ ] Does the itinerary respect hard constraints?
- [ ] Have I explained *why* the plan changed (if it did)?
- [ ] Are the booking/practical details updated to match the revised plan?
- [ ] Have I offered a fallback if the primary activity is weather-dependent?
