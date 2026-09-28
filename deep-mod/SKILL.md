---
name: deep-mod
description: Universal interactive deep research, architecture visualization, and surgical skill extraction pipeline with Anti-AI enforcement.
metadata:
  task_type: open-ended
dependencies: []
---

# Deep Mod: Universal Research, Architecture & Skill Pipeline

## Objective
Execute domain-agnostic interactive research, architecture visualization, and skill distillation with Shift-Left Anti-AI enforcement.

## Execution Workflow

### Stage 1: Universal Intake (Gate 0)
- Pre-flight scan via `python3 scripts/ingest.py <input> --list-only` (zero-I/O tokens and chapters).
- **Fast-Track** (keywords: `diff`, `review`, `架構圖`, `重構`): Stream clean text via `python3 scripts/ingest.py <input> --format stream`, ask ONE boundary question, then jump to Stage 3 Branch 1.
- For all other requests (including `轉技能`, `提取技能`, or research), proceed to Stage 2.

### Stage 2: Universal Clarification Gate (`references/common_gate.md`)
Execute 3-tier sequential clarification with dynamic recommendations before branching:
1. **Domain Alignment**: Lock technical/business domain using detected taxonomy and key elements.
2. **Workflow Clarification**: Clarify runtime lifecycle, procedures, or analysis sequence.
3. **Delivery Routing**: Route to **Branch 1 (Research & Architecture)** or **Branch 2 (Skill Pipeline)**.

### Stage 3: Finalized Output
Write deliverables with Anti-AI verification:
- **Branch 1: Research & Architecture Review** (`references/type_a_research.md`):
  Verify report via `python3 scripts/noai_gate.py ~/downloads/<report>.md`.
- **Branch 2: Agent Skill Directory** (`references/type_b_skill.md`):
  Partition via `python3 scripts/ingest.py <input> --split-dir <target_dir>`, then audit with `noai_gate.py` and `tests/audit.py`.
