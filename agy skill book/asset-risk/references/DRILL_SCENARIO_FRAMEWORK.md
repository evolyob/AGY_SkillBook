# Disaster Recovery & Incident Drill Scenario Framework (`DRILL_SCENARIO_FRAMEWORK.md`)

## 1. Division of Responsibilities
* **Script Role (`drill_generator.py`)**: Lightweight skeleton and field binder. Extracts canonical keywords (`{name}`, `{category}`, `{type}`, `{threat}`, `{vuln}`) from `parameters.json`.
* **AI Agent Role**: Consumes extracted keywords and primary IT classification (Software, Data, Hardware) to dynamically formulate realistic, technically rigorous scenario narratives and 8-step incident response procedures per the requirements below. Never output rigid static templates.

### Dual Input Routing

| Mode | Objective | Trigger / Input | Pipeline & Deliverables |
| :--- | :--- | :--- | :--- |
| **Path A (Internal Asset)** | Statutory DR drills & compliance audits | Asset inventory row, system name, `id` | **`name` (or `id`) ➔ `category` & `type` ➔ `threat` & `vulnerability` ➔ Full Delivery (Block A + Block B)** |
| **Path B (External Intel)** | Incident impact alignment & root-cause mapping | Security news, vulnerability alerts, incident reports | **Semantic Extraction (`name`) ➔ `category` & `type` ➔ `threat` & `vulnerability` (Deep Causal Mapping)** |

---

## 2. Block A Specifications (Planning Fields)
* `drill_theme`: Format `【{name}面臨「{threat}」之災害復原演練】`
* `target_and_scope`: Format `模擬{name}（{category}-{type}）因「{vuln}」遭遇「{threat}」之緊急應變與災害復原。`
* `scenario_description`: Comprehensive narrative describing the simulated incident condition, trigger attack vector exploiting `{vuln}`, impact on `{name}`, and resulting operational crisis.
* `playbook_flow`: Fixed standard sequence `收到通報 ➔ 緊急阻斷 ➔ 隔離保全 ➔ 受害清查 ➔ 事故判定 ➔ 通報主管機關 ➔ 修補還原 ➔ 驗證重啟`

---

## 3. Block B Specifications (8 Execution Steps Requirements)

### Core Constraints
* **Field Schema**: `step_no` (1~8), `phase_code` (演練執行項目), `unit_role` (負責單位), `duration` (所需時間), `procedure` (執行程序).
* **Empty Field Constraint**: `unit_role` and `duration` MUST remain strictly empty strings (`""`) to allow user organizations to designate units and timings during drills.

### Scenario Requirements for Dynamic Procedure Generation (By IT Category)

#### 1. Software (`軟體` - OS, Applications, Accounts, APIs)
1. **收到通報**: Capture alert symptoms, confirm alignment with `{threat}`, and log tracking ID.
2. **緊急阻斷**: Revoke active user/admin sessions; sever network connections while **maintaining system power (preserve volatile RAM memory evidence)**; block suspicious source IPs.
3. **隔離保全**: Freeze compromised account credentials; isolate affected hosts/containers via VLAN segmentation.
4. **受害清查**: Audit cron jobs, startup persistence, anomalous external sockets, and code/logic flaws regarding `{vuln}`.
5. **事故判定**: Cross-departmentally assess operational disruption scale and classify incident severity.
6. **通報主管機關**: Complete regulatory notification to competent authorities within statutory timelines.
7. **修補還原**: Eliminate `{vuln}` root causes, rotate all access secrets/keys, and rebuild from clean immutable backups.
8. **驗證重啟**: Execute security regression tests and functional verification; restore normal production operations.

#### 2. Data (`資料` - Databases, Files, Secrets, Personal Data)
1. **收到通報**: Log data access anomaly or exfiltration alert, and register incident ticket.
2. **緊急阻斷**: Immediately close public storage buckets, exposed database ports, or compromised API endpoints.
3. **隔離保全**: Switch affected database to read-only or sever external bridges; capture immutable audit snapshot.
4. **受害清查**: Inspect audit access logs to accurately quantify compromised fields and compile leaked record count.
5. **事故判定**: Evaluate data sensitivity and breach scale to determine regulatory incident classification.
6. **通報主管機關**: File statutory notification; initiate PDPA Article 12 data subject notices if personal data is breached.
7. **修補還原**: Rotate database credentials and connection strings; enforce strict RBAC and storage encryption for `{vuln}`.
8. **驗證重啟**: Validate cryptographic integrity and database consistency before reopening service endpoints.

#### 3. Hardware (`硬體` - Host Servers, Network Appliances, Power, Facility)
1. **收到通報**: Receive hardware warning, network disruption, or bandwidth saturation alert; record incident ID.
2. **緊急阻斷**: For DDoS, activate ISP traffic scrubbing (Scrubbing Center) or CDN routing; drop saturated upstream links.
3. **隔離保全**: Physically isolate damaged hardware or bypass faulty appliances; preserve hardware event logs.
4. **受害清查**: Examine diagnostic LEDs, bandwidth utilization, link breaking points, or failed component modules.
5. **事故判定**: Measure hardware failure impact against core business service availability.
6. **通報主管機關**: Dispatch statutory operational disruption notice to governing authorities.
7. **修補還原**: Hot-swap faulty parts, patch appliance firmware; engage UPS and diesel generators on power failure.
8. **驗證重啟**: Trigger secondary DR Site Failover; verify RTO and RPO benchmarks before restoring primary routing.
