# Subagent Dispatch & Isolation Protocol (`subagent_dispatch.md`)

> **Core Philosophy**: Dispatch isolated subagents across the ready frontier with mutually exclusive allowed paths and deterministic verification gates.

---

## 1. Dispatch Rules of Engagement
1. **Zero Overlapping Allowed Paths**: Subagents executing in parallel must NEVER modify the same file path.
2. **Minimal Self-Contained Prompt**: Provide only the exact Goal, Non-Goals, Allowed Paths, and Verification Command.
3. **Deterministic Exit Gate**: A subagent must achieve 100% test pass (`OK`) before its dependent tickets can be dispatched.

---

## 2. Dispatch Proposal Format (Presented to User)
At the conclusion of a grilling and spec freeze session, present the following structured dispatch proposal:

```markdown
### 🚀 建議派工方案 (Subagents Dispatch Proposal)

本任務評估可拆分為 **N 個獨立子任務**，建議並行派工：

1. **Subagent 1（[角色名稱]）**
   * **負責檔案**：`scripts/xxx.py` + `tests/test_xxx.py`
   * **任務內容**：實作 [具體邏輯]。
   * **驗收指令**：`python3 -m unittest tests/test_xxx.py`

2. **Subagent 2（[角色名稱]）**
   * **負責檔案**：`scripts/yyy.py` + `tests/test_yyy.py`
   * **任務內容**：實作 [具體邏輯]。
   * **驗收指令**：`python3 -m unittest tests/test_yyy.py`

---
> 💡 是否直接依照上述方案派發 Subagents 進行實作？
```
