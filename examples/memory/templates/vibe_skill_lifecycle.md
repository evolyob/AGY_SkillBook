# Vibe Skill Lifecycle & Evolution Guide (`vibe_skill_lifecycle.md`)

> **Goal**: Build and evolve skills with zero thinking latency, zero ghost tools, and zero script-spec contradictions.

---

## 1. The 4-Step Build Flow
1. **Spec First (`spec_template.md`)**: Freeze Goal, Non-Goals, Allowed Paths, Dependencies, and Acceptance Criteria.
2. **Data Structure (`SKILL_DATA_SPEC.md`)**: Flat list default (`Pattern A`), zero envelope wrapping (`item["field"]` direct). Build in-memory inverted index when items > 20 ($O(1)$ lookup).
3. **Core Script (`senior_coding_laws.md`)**: Functional core in Python stdlib (`matcher.py`, `drill_generator.py`). Max `if` nesting $\le 2$. Python does 100% of calculations; LLM only formats.
4. **Semantic Test Anchors (`tests/`)**: Lock ambiguous naming collisions and head-noun suffix rules with unit tests.

---

## 2. The 5 Evolution Traps to Reject (MUST NOT)
1. **No Cognitive Dump**: Do NOT delete Python analyzer scripts to make the LLM deduce rules in thought. Keep computation in Python.
2. **No Script Paradox**: Do NOT tell the LLM `Never output rigid templates` if the script outputs fixed templates. Script output IS the baseline.
3. **No Ghost Tools**: Every script named in `SKILL.md` MUST physically exist in `scripts/`. Never reference unbuilt scripts.
4. **No Silent Ambiguity Break**: When input matches multiple categories equally, return `candidates: ["CategoryA", "CategoryB"]` so the LLM can ask the user. Never guess.
5. **No Data Drift**: Documented numbers MUST match `parameters.json` exactly (e.g., 60 pairs = 60 pairs).

---

## 3. Surgical Combo Law (Continuous Pipeline)
- **Input-Output Pipe**: Direct CLI output must be usable downstream without manual LLM assembly (e.g. `matcher.py --drill --format markdown`).
- **Standardized Debrief**: External intel maps to 3 parts:
  1. Summary (2-3 sentences).
  2. Canonical mapping (`Category`, `Type`, `Threat`, `Vuln`, `Pair ID`).
  3. Mitigation & SOP (links to standard drill steps).

---

## 4. Pre-Delivery 8-Point Cheatsheet
- [ ] 1. Non-Goals explicitly defined?
- [ ] 2. Data is flat with zero envelope nesting?
- [ ] 3. Python runs on stdlib only?
- [ ] 4. Unit tests pass with zero failures?
- [ ] 5. All tools in `SKILL.md` exist?
- [ ] 6. No prompt-script contradictions?
- [ ] 7. CLI flags allow one-shot execution?
- [ ] 8. Ambiguous inputs return candidate choices?
