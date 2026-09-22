# Vibe Skill Lifecycle & Evolution Guide (`vibe_skill_lifecycle.md`)

> **Goal**: Build and evolve skills with zero thinking latency, zero ghost tools, and zero script-spec contradictions.

---

## 1. The 4-Step Build Flow
1. **Spec First (`spec_template.md`)**: Freeze Goal, Non-Goals, Allowed Paths, Dependencies, and Acceptance Criteria.
2. **Data Structure (`SKILL_DATA_SPEC.md`)**: Flat list default (`Pattern A`), zero envelope wrapping (`item["field"]` direct). Build in-memory inverted index when items > 20 ($O(1)$ lookup).
3. **Core Script (`senior_coding_laws.md`)**: Functional core in Python stdlib (`scripts/<module>.py`). Max `if` nesting <= 2. Python does 100% of calculations; LLM only formats.
4. **Semantic Test Anchors (`tests/`)**: Lock edge cases, ambiguous matches, and naming collisions with deterministic unit tests.

---

## 2. The 5 Evolution Traps to Reject (MUST NOT)
1. **No Cognitive Dump**: Do NOT delete Python analyzer scripts to make the LLM deduce rules in thought. Keep computation in Python.
2. **No Script Paradox**: Do NOT tell the LLM "Never output rigid templates" if the script outputs fixed templates. Script output IS the baseline.
3. **No Ghost Tools**: Every script named in `SKILL.md` MUST physically exist in `scripts/`. Never reference unbuilt scripts.
4. **No Silent Ambiguity Break**: When input matches multiple categories equally, return `candidates: ["CategoryA", "CategoryB"]` so the LLM can clarify with the user. Never guess.
5. **No Data Drift**: Documented counts, flags, and schema fields MUST match underlying data assets exactly.

---

## 3. Composable CLI Design (One-Shot Pipelines)
- **Downstream Ready**: CLI scripts should provide direct output flags (e.g. `--format markdown` or `--json`) so downstream agents receive ready-to-use payloads in a single execution without manual text assembly.
- **Structured Payloads**: Always emit predictable, structured schemas matching the contract, never freeform conversational prose.

---

## 4. Sequential Pre-Delivery Cheatsheet 
### Phase 1: Spec First  
- [ ] 1. Non-Goals explicitly defined?
### Phase 2: Data Structure
- [ ] 2. Data is flat with zero envelope nesting?
### Phase 3: Core Script & CLI
- [ ] 3. Python runs on stdlib only?
- [ ] 4. CLI flags allow one-shot execution?
### Phase 4: Semantic Test Anchors & Purity
- [ ] 5. All tools in `SKILL.md` exist?
- [ ] 6. No prompt-script contradictions?
- [ ] 7. Unit tests pass with zero failures?
- [ ] 8. Ambiguous inputs return candidate choices?
