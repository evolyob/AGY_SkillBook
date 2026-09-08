# Executive Assistant & Outline Templates

## 1. Collection Template (Phase 1)
*(生成重點：客觀事實增量記錄 → 零分析腦補推測 → 呈現最新重點並提供 5 大互動選項)*

```text
【內容歷史紀錄】
歷史輸入段落資料（目前狀態：收集模式）。

本次最新納入重點：
- [List 3~6 incremental key facts parsed directly from input. DO NOT extrapolate or summarize into final decisions.]

以上為目前收到的資訊重點。請問您接下來要：
1. 繼續補充筆記（持續收集資料）
2. 生成會議紀錄 / 主管摘要（Executive Brief 模式）
3. 生成簡報大綱（Presentation Outline 模式）
4. 生成審查意見 / 修正對照表（Revision Coach 模式）
5. 生成一頁式版面規格（準備轉 PDF/DOCX 視覺藍圖）
```

---

## 2. Branch A: Executive Brief Template (Phase 2 - Meeting / Brief Mode)
*(生成重點：適用會議紀錄 → 領域技術治理歸納 → 剖析核心瓶頸與團隊效益 → 提煉「若只能向主管報告一句話」決策斷言)*

```text
# 會議基本資訊
• 主題名稱：[Extract topic from source. If unstated, generate a concise descriptive title based on content.]
• 日期時間：[Extract date/time from source. If unstated, default to current system date.]
• 領域聚焦：[Categorize into 2~3 relevant domains based on context, e.g., Customer_Compliance / Project_Operations / Strategic_Finance]

---

【核心精華】

### 內容重點
• [Extract core facts & technical details strictly based on raw input. Group into hierarchical sub-items if extensive.]

### 主管需關注事項
- [Align with annual planning & compliance; highlight key executive takeaways, potential risks, and impacts.]
- [Analyze resource savings, operational efficiency, and risk reduction for the team.]

### 核心問題
「[Extract the single most critical problem/technical bottleneck addressed in this note.]？」

【摘要簡報】
若只能向主管報告一句話：
「[Formulate a single executive statement describing key business value created or major risk avoided.]」
```

---

## 3. Branch B: Presentation Outline Template (Phase 2 - Presentation / Slide Mode)
*(生成重點：適用簡報大綱（純 Markdown） → 對齊 /pptx Proof-Led（封面摘要 → 結論斷言標題 → 4 大視覺支柱 Lego 槽位 → 主管關注） → 嚴禁灌水頁與隨意合併主題)*

```text
# [主題名稱] — 簡報大綱 (Proof-Led Lego 模組化大綱)

【Storyboard Narrative（標題敘事鏈）】
• [連續閱讀斷言標題即可傳達完整的高階主管業務脈絡]
  - Slide 1: [結論導向斷言標題 1]
  - Slide 2: [結論導向斷言標題 2]
  - Slide 3: [結論導向斷言標題 3]

【高階執行摘要 / Executive Summary】
• 年度規劃對齊：[Explain alignment with strategic goals & annual planning.]
• 關鍵量化基線：[Provide core KPI / SLA / ROI baseline data.]
• 待決策事項：[List key items requiring executive decision or support.]

---

### Slide [頁碼]：[結論導向斷言標題 (Conclusion-Led Assertion Title，絕不使用中性無效標籤)]

【畫布視覺拼裝 / Canvas Composition (Lego Modular Assembly)】
(自由拼裝 1~3 個來自 4 大視覺支柱的模組槽位證明斷言標題。形式緊隨內容。)

• Block 1 [視覺支柱: Cards | Diagrams | Charts | Tables] — [畫布槽位: 例如 Left 50% / Full Width]:
  - [證據、量化指標、流程步驟或表格內容，直接在此結構化呈現]

• Block 2 [視覺支柱: Cards | Diagrams | Charts | Tables] — [畫布槽位: 例如 Right 50% / Col 2 of 3] (選填):
  - [證據、量化指標、流程步驟或表格內容，直接在此結構化呈現]

• Block 3 [視覺支柱: Cards | Diagrams | Charts | Tables] — [畫布槽位: 例如 Col 3 of 3] (選填):
  - [證據、量化指標、流程步驟或表格內容，直接在此結構化呈現]

---

【高階主管關注重點 (Executive Focus)】
- 關鍵風險：[State key risk factor based strictly on input]
- 建議行動：[Define concrete next step / Action Item]
```

---

## 4. Branch C: Revision Coach Template (Phase 2 - Revision Mode)
*(生成重點：適用審查意見與重構記錄 → Minimal-Diff 三部曲閉環（背景成效 → 外科手術對照 → 邊界完整交付） → 精確標註行號與獨立代碼塊（絕不含糊） → 嚴禁 3 欄寬表格（一律條列卡片）)*

```text
# [文件 / 專案 / 規範名稱] 修正對照與修訂報告

【一、修訂背景、架構體系與具體成效】
• 修訂動機：[State the primary driver, review feedback, or core bottleneck in 1 concise sentence.]
• 架構體系：[Define organizational hierarchy, module boundaries, or upstream/downstream dependency scope.]
• 核心方針：
  1. Minimal-Diff 原則：[Surgically revise affected sections only; keep remaining content 100% intact.]
  2. 職責分離與一致性：[Ensure single responsibility per module/section; maintain logical consistency.]
  3. 語言與詞彙規範：[Strictly follow localized vocabulary and the project's canonical tone of voice.]
• 具體效益與驗證成效：[State verified outcomes and objective metrics, e.g., logical closure, ambiguity eliminated, or acceptance criteria met.]

【二、修訂對照清單】
<!-- Group by module, section, or priority; render each item using structured bullet blocks -->

### 項目 01：[Module Name / Section Title]
• **問題診斷**：[Explicitly identify the issue, ambiguity, logical gap, or violated specification.]
• **根因與效益**：[State the root cause and the tangible benefit/impact of the revision.]
• **具體修正建議**：
  - **修改前**：[Target section name / chapter number, Line # (or Lxx-Lyy)]
  - **修改後**：
    ```markdown
    [Insert the exact modified Markdown content or code snippet here]
    ```
  - **執行動作**：[List 1~2 concrete follow-up Action Items if additional adjustments are required.]

### 項目 02：[Module Name / Section Title] (選填)
• **問題診斷**：[Explicitly identify the issue, ambiguity, logical gap, or violated specification.]
• **根因與效益**：[State the root cause and the tangible benefit/impact of the revision.]
• **具體修正建議**：
  - **修改前**：[Target section name / chapter number, Line # (or Lxx-Lyy)]
  - **修改後**：
    ```markdown
    [Insert the exact modified Markdown content or code snippet here]
    ```
  - **執行動作**：[List 1~2 concrete follow-up Action Items if additional adjustments are required.]

---

【三、邊界限制與完整交付】
• 限制說明：[Document unaddressed items and explicit rationale due to dependencies, legacy constraints, or external limits.]
• 交付物清單：[List deliverable file names, relative paths, or version identifiers.]
• **修改後檔案完整範例**：
  <!-- Provide 100% integrated, drop-in replacement file content ready for immediate deployment -->
  ```[file_extension/format]
  [Insert complete finalized file content here]
  ```
```
