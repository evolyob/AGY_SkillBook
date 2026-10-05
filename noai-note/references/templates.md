# Editorial Text Execution Specifications (`templates.md`)

> **Agent Execution Rule**: When producing text-only outputs (Collection or Branch A), strictly adhere to the chosen template below. Deliver user-facing output in Traditional Chinese.

---

## 1. Phase 1: Zero-Analysis Collection Template (Collection Mode)
*(Output Spec: Appends incremental key facts parsed directly from raw input. Zero extrapolation. Renders user interaction menu.)*

```text
【內容歷史紀錄】
歷史輸入段落資料（目前狀態：收集模式）。

本次最新納入重點：
- [List 3~6 incremental factual points parsed strictly from input. Never extrapolate or assume unstated details.]

以上為目前收到的資訊重點。請問您接下來要：
1. 繼續補充筆記（持續收集資料）
2. 生成會議紀錄 / 主管摘要（Executive Brief 模式）
3. 生成簡報大綱（16:9 簡報投影片大綱模式）
4. 生成 A4 版面藍圖（請指定：1-Pager 單頁 或 N-Pager 多頁）
```

---

## 2. Branch A: Executive Brief Template (Meeting Notes & Decision Brief)
*(Output Spec: Concise executive summary distilling core facts, strategic impacts, and a 1-sentence decision claim for executive review.)*

```text
# [Topic / Project Name] — Executive Decision Brief
• Meeting Metadata: Date/Time: [YYYY-MM-DD] | Participants / Team: [Owner] | Domain: [Domain Category]

【Executive Summary】
### Core Factual Highlights
• [Extract core facts, architectural decisions, and key agreements strictly from input]

### Executive Focus & Impacts
- Strategic Alignment: [Align with annual goals, operational risks, and compliance impacts]
- Benefit Evaluation: [Quantified resource savings, latency improvements, or risk mitigations]

### Core Problem & Elevator Pitch
• Core Problem: "[What is the single most critical bottleneck/question resolved by this brief?]"
• Executive Assertion: "[1-sentence claim stating primary business value created or critical risk avoided]"
```
