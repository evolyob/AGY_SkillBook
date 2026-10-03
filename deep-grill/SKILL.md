---
name: deep-grill
description: Conduct high-depth architectural interviews, freeze defensive specification contracts, decompose vertical tracer-bullet DAGs, and output structured subagent dispatch proposals.
dependencies: []
metadata:
  task_type: interactive-planning
---

# Deep Grill & Engineering Alignment Pipeline

## Objective
Execute radar-guided architectural interviews, freeze defensive specifications, and generate isolated subagent dispatch proposals.

## Core Interview Pillars

1. **Targeted Context Check**: Inspect mentioned workspace documents, schemas, or directories *first* to avoid asking for known baseline facts.
2. **Mission & Radar Interview Mode**: Ground inquiry in [architecture_radar.md](references/architecture_radar.md) and Mission-Firewall rules (push for concrete outcomes, observable success states, and strict adjacent out-of-scope boundaries).
3. **One at a Time**: Ask exactly **ONE** focused question per response turn.
4. **Structured Options**: Present 3–4 options (A, B, C, D) with Option A marked as `(Recommended)` and explicit trade-offs.
5. **Iterative Convergence**: Conclude immediately when decisions reach consensus, the user accepts defaults twice, the user states "wrap up", or reaching a maximum of 12 questions.

## Execution Workflow

1. **Phase 1 (Mission-Firewall & Radar Interview)**:
   - Apply MISSION rules: Pin down concrete Why (reject abstract framings), observable Success criteria, and strict Out-of-Scope boundaries.
   - Probe architectural radar: Boundary isolation, pure core, flattened flow, and negative net diffs.
2. **Phase 2 (Spec Contract Freeze)**:
   - Synthesize decisions into a frozen contract per [spec_contract.md](references/spec_contract.md) with Goal/Non-Goals Firewall, Allowed Paths, and deterministic test commands.
3. **Phase 3 (Dispatch Proposal)**:
   - Decompose into tracer-bullet slices per [ticket_decomposition.md](references/ticket_decomposition.md), then output a high-density dispatch table per [subagent_dispatch.md](references/subagent_dispatch.md).
4. **Phase 4 (Integration & Verification)**:
   - Upon user approval, dispatch subagents across the ready frontier and run full verification gates.
