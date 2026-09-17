# Personal Identifiable Information (PII) Inventory Template

Canonical 11-column data contract for Personal Identifiable Information (PII) inventory, lifecycle tracking, and security controls assessment.

---

## 1. 11 Core Columns Specification

> [!NOTE]
> Canonical carrier taxonomy, storage/disposal defaults, and Controls A~J are maintained in [`data/pii_parameters.json`](../data/pii_parameters.json).

| No. | Column Name | Role | Type / Scale | Description & Guidelines |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **資產名稱** | System | String | `asset_name` (`tags`) |
| **2** | **保有依據** | Human | Art. 19 | `legal_basis`（契約關係／當事人同意／法律明文規定） |
| **3** | **個資類別** | Human / System | String | `pii_categories`（一般識別資料與活動資料項目清單） |
| **4** | **特種個資** | System | `是` / `否` | `has_special_pii`（《個資法》第6條關鍵字自動判斷） |
| **5** | **資料形式** | System | 3 Formats | `col_h_format`（`資料庫` / `電子檔` / `紙本`） |
| **6** | **內部傳送** | Human | String | `internal_transfer`（內部傳送部門與流向方式） |
| **7** | **保管方式** | System | 3 Defaults | `default_storage`（資料庫主機／個人電腦／檔案室個人櫃） |
| **8** | **外部傳送** | Human | String | `external_transfer`（外部利用機構與傳送方式） |
| **9** | **廢棄方式** | System | 2 Defaults | `default_disposal`（`刪除` / `碎紙`） |
| **10**| **個資數量** | Human | `1` / `2` / `3` | `volume_scale`（1: $\le 20$筆；2: $21 \sim 10,000$筆；3: $\ge 10,001$筆） |
| **11**| **管控措施** | Human / System | A~J Checklist | `controls_summary`（Controls A~J 實行項數摘要） |

> [!NOTE]
> Detailed risk calculation formulas ($R = I \times P$) and enterprise 29-column sheet mapping are defined in [`VALUATION_GUIDE.md`](VALUATION_GUIDE.md) and enterprise compliance profiles.

---

## 2. Standard Carrier Taxonomy & Defaults (3 Categories)

| `category` | `col_h_format` | `default_storage` | `default_disposal` | `controls` (Controls A~J Focus) |
| :--- | :--- | :--- | :--- | :--- |
| `軟體` | `資料庫` | `儲存於資料庫／主機（電子）` | `刪除` | 系統帳密無共用、Log留存、權限合理性、逾時登出、個資遮蔽 (A~J) |
| `資料` | `電子檔` | `儲存於個人電腦（電子）` | `刪除` | 電腦帳密防護、螢幕保護逾時、限制外接USB、調閱合理性審核 (A~J) |
| `文件` | `紙本` | `存放於個人櫃／抽屜（紙本）` | `碎紙` | 紙本上鎖保管、禁攜出作業區、事務機認證列印、過期與廢紙銷毀 (A~J) |

---

## 3. Blank Markdown Template (Ready to Fill)

```markdown
| 資產名稱 | 保有依據 | 個資類別 | 特種個資 | 資料形式 | 內部傳送 | 保管方式 | 外部傳送 | 廢棄方式 | 個資數量 | 管控措施 |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| 會員CRM系統 | 契約關係 | 姓名、電話、地址、消費紀錄 | 否 | 資料庫 | 行銷部 | 儲存於資料庫／主機（電子） | 無 | 刪除 | 3 | 落實 9/10 項 |
| 薪轉名冊Excel | 契約關係 | 員工姓名、身分證字號、銀行帳號 | 否 | 電子檔 | 財務部 | 儲存於個人電腦（電子） | 合作銀行 | 刪除 | 2 | 落實 8/10 項 |
| 健檢報告紙本 | 法定職務 | 姓名、身分證字號、體檢數據 | 是 | 紙本 | 無 | 存放於個人櫃／抽屜（紙本） | 無 | 碎紙 | 2 | 落實 10/10 項 |
```
