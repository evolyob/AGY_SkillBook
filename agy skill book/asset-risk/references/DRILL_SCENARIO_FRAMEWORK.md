# Disaster Recovery & Incident Drill Scenario Framework (`DRILL_SCENARIO_FRAMEWORK.md`)

## 1. Division of Responsibilities
* **Script Role (`drill_generator.py`)**: Lightweight skeleton and field binder. Binds canonical keywords (`{name}`, `{category}`, `{type}`, `{threat}`, `{vuln}`) from `parameters.json`.
* **AI Agent Role**: Uses the output of `drill_generator.py` as the baseline skeleton. Fine-tunes technical procedure details according to the specific asset operational environment without breaking the 8-step schema.

### Input Routing Matrix

| Mode | Objective | Trigger / Input | Deliverables |
| :--- | :--- | :--- | :--- |
| **Path A (Internal Asset)** | Statutory DR drills & compliance audits | Asset inventory item, system name, or `pair_id` | **Full Drill Delivery (Block A Planning + Block B 8-Step Execution)** |
| **Path B (External Intel)** | Threat impact assessment & root-cause alignment | Security news, vulnerability alerts, incident reports | **Structured Debrief (Incident Summary ➔ Canonical Mapping ➔ Mitigation & SOP)** |

---

## 2. Block A Specifications (Planning Fields)
* `drill_theme`: `【{name}面臨「{threat}」之災害復原演練】`
* `target_and_scope`: `模擬{name}（{category}-{type}）因「{vuln}」遭遇「{threat}」之緊急應變與災害復原。`
* `scenario_description`: Concrete narrative detailing the attack vector exploiting `{vuln}`, the operational impact on `{name}`, and the triggered disaster condition.
* `playbook_flow`: Standard sequence: `收到通報 ➔ 緊急阻斷 ➔ 隔離保全 ➔ 受害清查 ➔ 事故判定 ➔ 通報主管機關 ➔ 修補還原 ➔ 驗證重啟`

---

## 3. Block B Specifications (8-Step Execution Schema)

### Field Constraints
* **Schema**: `step_no` (1~8), `phase_code` (演練執行項目), `unit_role` (負責單位), `duration` (所需時間), `procedure` (執行程序).
* **Empty Field Constraint**: `unit_role` and `duration` MUST remain empty (`"-"` or `""`) to allow user drill participants to assign designated roles and record actual elapsed time.

### Category-Specific Execution Requirements

#### 1. Software (`軟體` - OS, Applications, Accounts, APIs)
1. **收到通報**: Capture alert symptoms, confirm alignment with `{threat}`, and log incident ticket ID.
2. **緊急阻斷**: Revoke compromised sessions; sever network connections while maintaining power to preserve volatile RAM memory.
3. **隔離保全**: Freeze compromised credentials; isolate infected containers/hosts via VLAN segmentation.
4. **受害清查**: Audit cron jobs, startup persistence, abnormal external sockets, and code flaws regarding `{vuln}`.
5. **事故判定**: Evaluate service interruption scope and classify disaster severity tier.
6. **通報主管機關**: Dispatch statutory notification to regulatory authorities within mandatory timeframes.
7. **修補還原**: Patch `{vuln}`, rotate administrative secrets/tokens, and rebuild state from immutable clean backups.
8. **驗證重啟**: Execute functional verification and security regression tests before returning to production.

#### 2. Data (`資料` - Databases, Files, Secrets, PII)
1. **收到通報**: Log anomalous exfiltration or unauthorized query alerts and initialize incident tracking.
2. **緊急阻斷**: Sever exposed database listener ports, close public storage buckets, and revoke leaked API tokens.
3. **隔離保全**: Switch database to read-only replica mode; take cryptographic storage snapshot for forensic preservation.
4. **受害清查**: Parse query audit logs to quantify leaked rows, compromised PII fields, and blast radius.
5. **事故判定**: Assess data classification level and determine whether statutory breach threshold is reached.
6. **通報主管機關**: Submit data protection authority breach reports; initiate required data subject notifications.
7. **修補還原**: Enforce column encryption, rotate master encryption keys, and tighten RBAC rules addressing `{vuln}`.
8. **驗證重啟**: Verify cryptographic checksums and referential integrity before reopening client connections.

#### 3. Hardware (`硬體` - Host Servers, Network, Power, Facility)
1. **收到通報**: Receive hardware failure, network saturation, or environmental sensor alerts.
2. **緊急阻斷**: Divert traffic to DDoS scrubbing center / CDN; isolate damaged network segment.
3. **隔離保全**: Physically or logically decouple faulted appliance; preserve hardware diagnostic logs.
4. **受害清查**: Check diagnostic LEDs, optical power, storage controller status, or hardware component failure.
5. **事故判定**: Evaluate hardware failure impact against system availability SLA.
6. **通報主管機關**: Dispatch service degradation notice to designated governing authorities.
7. **修補還原**: Hot-swap failed modules, update appliance firmware, or activate backup generators on power failure.
8. **驗證重啟**: Trigger secondary DR site failover; verify RTO and RPO benchmarks before failing back.

---

## 4. External Threat Intel Alignment Specification (Executive Debrief)

When external security intelligence (e.g., zero-day CVE, ransomware campaign) requires internal risk alignment, the AI agent must query `parameters.json` and output the following 3-part debrief:

### Standard Debrief Template

````markdown
### 【資安情報衝擊評估與內部對齊報告】

#### 一、 外部事件核心摘要
> Summarize the attack chain in 2–3 sentences (target victim, exploited flaw, and operational impact).
> Example: 某跨國零售商因外包維運連線缺乏多因子認證（MFA），遭勒索軟體加密核心虛擬化主機，導致全門市 POS 停擺 48 小時。

#### 二、 本公司資產規格對齊（引據 parameters.json）
透過內部標準參數庫對齊，此事件屬於本公司已納管之風險情境：
* **對應資產類別**：`[Category]` - `[Type]`（例：軟體 - 虛擬環境 / 人員 - 外部廠商）
* **標準威脅定義**：`[Threat]`（例：遭勒索軟體或破壞性程式攻擊）
* **標準弱點定義**：`[Vulnerability]`（例：遠端維運存取缺乏強認證機制與連線白名單）
* **標準配對編號**：`[Pair ID]`

#### 三、 既定災防演練與防護處置（SOP 對齊）
本公司年度災害復原演練清單中，已有對應之 8 步驟防護與復原程序：
1. **阻斷與隔離**：符合既定演練第 2、3 步（終止遠端工作階段，切斷網段並保全揮發性日誌快照）。
2. **修補與驗證**：符合既定演練第 7、8 步（強制重設特權金鑰，自不可變離線備份復原）。
3. **因應建議**：
   - [ ] 內部清查：盤點現行相關資產是否均落實防護控制。
   - [ ] 演練確認：建議依照既定之 Block B 演練腳本排定實機驗證。
````
