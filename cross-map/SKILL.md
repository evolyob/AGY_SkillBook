---
name: cross-map
description: Scans skills, extracts sub-features and CLI flags, builds 4-facet intent matrices, and manages multi-skill scenario routing pipelines.
dependencies: []
---

# Cross-Skill Semantic Mapping & Routing Engine

## Objective
Analyze installed skills, extract sub-features and CLI flags, detect keyword collisions, and generate macro-routing and multi-skill scenario pipelines.

---

## Execution Workflow

### Step 1: Work Shape & Explicit Skill Lock Gate
- **Explicit Skill Lock**: If the user explicitly names a target skill (e.g., `sec-intel`, `asset-risk`), lock that skill as the authoritative Primary. Do NOT replace it or silently inject supporting skills.
- **Work Shape Classification**:
  - **Single**: Single-target query or single file generation. Select only 1 Primary skill; do not invoke multi-skill pipelines.
  - **Phased**: Multi-step pipeline (e.g., scan → edit → verify). Route each phase dynamically; never pre-load future skills into context.
  - **Managed Goal**: Long-running cross-repository tasks. Maintain resumable on-disk plan checkpoints.

### Step 2: Readiness Pre-flight & Token Gate
- **Readiness Verification**: Inspect skill readiness via `python3 <skill_dir>/scripts/cross_map.py --check`. Reject missing dependencies early with fail-closed alternatives.
- **Token Circuit Breaker**:
  - Estimated tokens $\le$ 6,500: Stream directly in-session.
  - Estimated tokens > 6,500: Partition on disk or dispatch `research` subagent.
- **Dispatch Channels**:
  - Single-skill CLI audits (< 2s): Direct single tool call.
  - Multi-skill repo inspections (> 10 files): Offload to subagent (`invoke_subagent`).

### Step 3: Execute Scanner Engine
Run the target mode with a single tool call:
- **Dependency Readiness**: `python3 <skill_dir>/scripts/cross_map.py --check`
- **Synchronize Registry (`SKILLS.md`)**: `python3 <skill_dir>/scripts/cross_map.py --sync`
- **Output Raw JSON**: `python3 <skill_dir>/scripts/cross_map.py --json`

### Step 4: Fact-Based Reporting & Topic Sync
- Format output into structured Markdown tables with explicit Readiness tags.
- Disclose planned versus actually executed skills before and after task execution.
