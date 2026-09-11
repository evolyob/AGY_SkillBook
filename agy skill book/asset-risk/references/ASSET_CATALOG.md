# Information Asset Catalog & Selection Rules

## 1. Architectural Mission
The `asset-risk` skill provides deterministic, anti-monotony pairing between information assets and canonical threats/vulnerabilities based on the standardized ISMS parameter table. It eliminates prompt bloat by routing assets to tags rather than ingesting the entire parameter database into context.

## 2. Unified Asset Taxonomy & Indexing Matrix
Assets belong to 5 fundamental categories encompassing 32 standardized types. Physical boundaries are absorbed directly into category scopes, separating standardized types from indexing tags:

| Category & Scope | Standardized Types | Primary Tags (`tags`) | Typical Threat-Vuln Scenarios |
| :--- | :--- | :--- | :--- |
| **Hardware** (`硬體`)<br>*(Physical devices & compute facility)* | - Host Servers (`主機伺服器`)<br>- Personal Computers (`個人電腦`)<br>- Network Equipment (`網路設備`)<br>- Storage Media (`儲存媒體`)<br>- Peripherals (`週邊設備`)<br>- Server Rooms (`機房`)<br>- Power & Utilities (`電力與公用設施`) | `facility`, `power`, `network`, `firmware`, `endpoint`, `pc`, `usb`, `EOL` | Physical breakdown, power outage, HVAC failure, unauthorized entry, unpatched firmware, terminal tampering, device theft. |
| **Software** (`軟體`)<br>*(Logical OS, platforms & applications)* | - Host Operating Systems (`主機作業系統`)<br>- Databases (`資料庫`)<br>- Business Applications (`業務應用系統`)<br>- Virtualization Environments (`虛擬環境`)<br>- Cloud Service Systems (`雲端服務系統`)<br>- Office Productivity Software (`辦公室應用軟體`) | `database`, `sql`, `api`, `interface`, `code`, `ransomware`, `privilege`, `ai` | Ransomware infection, VM sniffing, database privilege escalation, S3 bucket leak, SQL injection, API replay, prompt injection. |
| **Data** (`資料`)<br>*(Electronic format data & repositories)* | - Public Website Data (`網站公開資料`)<br>- Business Transaction Data (`業務交易資料`)<br>- Customer Data Files (`客戶資料檔`)<br>- System Config Parameters (`系統設定參數資料`)<br>- Network Config Data (`網路設定資料`)<br>- System Documentation (`系統文件`)<br>- Source Code Repositories (`程式碼`)<br>- Electronic Contracts (`合約`)<br>- Management Documents (`管理文件`)<br>- Form Records (`表單紀錄`) | `database`, `pii`, `finance`, `backup`, `code`, `config`, `contract`, `network` | Exfiltration, cardholder/PII leak, OTP intercept, source code leak, backup deletion, public AI upload, log tampering. |
| **Document** (`文件`)<br>*(Physical hardcopy paper & records)* | - System Operation Manuals (`系統操作文件`)<br>- Network Architecture Diagrams (`網路架構圖`)<br>- Operation Records (`作業紀錄`)<br>- Paper Contracts & Deeds (`紙本合約`)<br>- Hardcopy Customer Records (`客戶資料`)<br>- Physical Management Documents (`管理文件`)<br>- Physical Business Records (`業務資料`) | `paper`, `contract`, `clean_desk`, `pii`, `shredder` | Paper contract photography, whiteboard exposure, trash bin scavenging, safe burglary, lack of shredding, missing watermarks. |
| **Personnel** (`人員`)<br>*(Internal staff & external partners)* | - Employees (`員工`)<br>- External Vendors & Contractors (`外部廠商`) | `phishing`, `privilege`, `offboarding`, `vendor`, `finance`, `ai` | Phishing backdoors, lingering ex-employee privileges, contractor jump-host hops, BEC wire fraud, accidental secret leak. |

## 3. Threat-Vulnerability Causality Principle
Every threat and vulnerability exists as an interrelated causal pair (`Threat exploits Vulnerability`):
- **Vulnerability**: An internal weakness, design flaw, or lack of control inherent to the asset (e.g., missing patches, weak passwords, unencrypted storage, lack of clean desk).
- **Threat**: An external event or human action that exploits the vulnerability (e.g., ransomware execution, credential brute-forcing, eavesdropping, wire fraud).

The parameter table (`parameters.json`) contains 82 validated causal pairs (Hardware: 15, Software: 21, Data: 18, Document: 14, Personnel: 14).

## 4. Anti-Monotony Round-Robin Queue
To prevent consecutive rows of identical asset types from receiving the same threat-vulnerability pair:
1. When evaluating an asset, candidate pairs in `parameters.json` are scored by tag relevance.
2. The selection engine maintains a rolling history of the last 5 selected threat IDs.
3. Recently selected pairs receive an anti-monotony penalty, forcing the engine to rotate to the next best-fitting candidate.

## 5. Execution Protocol
- Single asset probe: Call `matcher.py --name <AssetName>` (automatically resolves Category, Type, and Pair).
- Batch stream: Call `matcher.py --batch <file.json>` (applies anti-monotony rotation across all rows).
