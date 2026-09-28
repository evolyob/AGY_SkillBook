# Protocol Specification: Type A Research & Decision Delivery

## Objective
Execute deep multi-source research, evidence synthesis, and decision matrix delivery based on `common_gate.md` boundaries.

---

## 1. Phase 1: Multi-Source Tagging & Categorization
- **Intake Modes**:
  - **File Ingest**: Ingest documents via `python3 scripts/ingest.py <input> --format stream` (or `-o <path>` for raw cleaned exports; read auto-exported `/tmp/deep_mod_work/` for large docs) and preserve source tags (`[Source: File | Chapter]`).
  - **Oral Intake**: If no documents exist, use single-question Socratic inquiry to elicit constraints, tagging inputs as `[Source: Oral | Interview]`.
- **Three-Way Partition Schema**:
  - `[BASE-xx]`: Baseline Requirements (Core non-negotiable specs).
  - `[EXT-xx]`: Secondary Extensions (Cross-department or optional suggestions).
  - `[CONF-xx]`: Unresolved Conflicts (Direct contradictions between sources).
- **Single-Gap Clarification**: If a critical `[CONF-xx]` blocks scope definition, pose exactly ONE targeted question to expose the contradiction before proceeding.

---

## 2. Phase 2: Dimension Specification, Evidence Hierarchy & Conflict Arbitration
- **Step 1: Investigation Checklist**:
  - Explicitly define the list of concrete dimensions to inspect (e.g., performance, cost, compatibility, security) before collecting data.
- **Step 2: Evidence Hierarchy**:
  - **Level 1 (Verified / High)**: Formal contracts, code AST, official APIs/documentation, system logs, verified benchmarks.
  - **Level 2 (Internal / Moderate)**: Internal PRDs, meeting minutes, working drafts, team benchmarks.
  - **Level 3 (Unverified / High Risk)**: Verbal assumptions, informal notes, unvalidated AI claims, community forum posts.
- **Step 3: Conflict Arbitration Rules**:
  - **Hierarchy Override**: Higher-level evidence supersedes lower-level (`Level 1 > Level 2 > Level 3`). Mark overridden lower claims as superseded.
  - **Same-Level Conflict**: Same-level conflicts (e.g., `L2 vs L2`) must be retained as explicit architectural trade-offs for human decision.
  - **Risk Flagging**: Any critical decision claim relying on Level 3 evidence must carry the warning flag `[HIGH RISK: UNVERIFIED]`.

---

## 3. Phase 3: Controlled Search & Skeleton Population
- **Search Execution & Dual Braking Mechanisms**:
  - **Query Cap**: Max 2 search queries per checklist item (`MAX_SEARCH_PER_ITEM = 2`). No recursive branching.
  - **Fail Fast**: If no objective evidence is found after 2 attempts, immediately stop and flag the item as `[uncertain]` (L3).
- **Field Coverage Validation**:
  - Verify every checklist item from Phase 2 is either substantiated with an evidence level or marked `[uncertain]`.
- **Four Native Visual Primitives (`visual_layout.md`)**:
  Populate findings strictly into one or more of the 4 native CLI-safe primitives:

### 1. Native Markdown Table (Selection Matrix or Layer Hierarchy)
- **Selection Mode (2×2 Strategic Matrix)**:
  | Dimension | High Complexity | Low Complexity |
  |---|---|---|
  | **High Impact** | • Priority Alpha: Core DB sharding<br>• Priority Beta: Zero-trust auth | • Quick Win: Ingest compression<br>• Quick Win: API rate-limit |
  | **Low Impact** | • De-prioritize: Legacy sync rewrite | • Optional: UI telemetry audit |
- **Hierarchy Mode (Tiered Structure Table)**:
  | Tier | Layer Name | Core Components & Responsibilities |
  |:---:|---|---|
  | **Tier 3** | **Presentation Tier** | • Native Markdown Tables & Unicode Rails |
  | **Tier 2** | **Verification Tier** | • `scripts/noai_gate.py` Linter & L1/L2/L3 Evidence |
  | **Tier 1** | **Ingestion Tier** | • `scripts/ingest.py` & `references/common_gate.md` |

### 2. Action Checklist (Defect Auditing & Readiness)
- `[x] [L1] Database read-replica failover threshold clamped to 200ms.`
- `[ ] [L2] [GAP] Audit cold-storage encryption keys with SecOps.`
- `[ ] [L3] [HIGH RISK: UNVERIFIED] Client-side caching fallback policy unconfirmed.`

### 3. Unicode Rails (Dynamic Data Flow Pipeline)
```text
Input Sources ──▶ scripts/ingest.py (Sanitization & Tagging)
                        │
                        ├─▶ common_gate.md (Domain & Workflow Freeze)
                        ├─▶ Evidence Verification (L1/L2/L3)
                        │
                        ▼
                Executive Decision Report (~/agy/download/*.md)
```

### 4. KPI Badges (Quantified Metric Deltas)
- `[Throughput: 12.4k req/s ▲24% vs baseline]` | `[P99 Latency: 142ms ▼18%]` | `[Failover: 18s (Target <=30s)]`

---

## 4. Phase 4: Tag-Driven Assembly & Verification Gate
- **Tag-Driven Filtering & Assembly**:
  - **Filter**: Isolate items flagged with `[uncertain]` from primary conclusions; group them into an explicit "Pending Human Verification" section.
  - **Assemble**: Compile `[BASE-xx]` requirements and arbitrated `[CONF-xx]` items into Native Markdown Tables and Action Checklists, binding exact Evidence Levels (`L1/L2/L3`).
- **Deliverable Export**:
  - Export the final Markdown report to `~/agy/download/<report_filename>.md` using `utf-8-sig` encoding.
- **Automated Verification**:
  - Run the scanner before presenting output:
    `python3 scripts/noai_gate.py ~/agy/download/<report_filename>.md` (or `python3 scripts/noai_gate.py --text "<snippet>"` for inline Fast-Track text).
  - Ensure zero Mermaid diagrams, zero formulaic AI patterns, and zero prohibited buzzwords. Halt and revise if errors are flagged.
