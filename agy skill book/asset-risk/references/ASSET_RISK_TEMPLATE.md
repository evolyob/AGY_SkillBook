# Information Asset Inventory & Risk Assessment Template

Canonical 10-column data contract for information asset inventory, CIA valuation, and threat/vulnerability identification.

---

## 1. 10 Core Columns Specification

> [!NOTE]
> Canonical taxonomy, default types, and threat-vulnerability pairs are maintained in [`data/parameters.json`](../data/parameters.json).

| No. | Column Name | Role | Type / Scale | Description & Guidelines |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **類別** | System | 5 Categories | `category` |
| **2** | **類型** | System | 32 Types | `type` |
| **3** | **資訊資產項目** | System / Human | String | `name` (`tags`) |
| **4** | **部門** | Human | String | `department` |
| **5** | **保管人** | Human | String | `custodian` |
| **6** | **機密性 (C)** | Owner | `1` / `3` / `5` | `c_score` |
| **7** | **完整性 (I)** | Owner | `1` / `3` / `5` | `i_score` |
| **8** | **可用性 (A)** | Owner | `1` / `3` / `5` | `a_score` |
| **9** | **威脅項目1** | System | String | `threat` (`id`) |
| **10**| **弱點項目1** | System | String | `vulnerability` |

> [!NOTE]
> Detailed CIA valuation rules (Columns 6-8) and risk calculation formulas are defined in [`VALUATION_GUIDE.md`](VALUATION_GUIDE.md). Scores are assigned by authorized asset owners.

---

## 2. Standard Dropdown Taxonomy (5 Categories & 32 Types)

| `category` | `default_type` | `type` (32 Standard Taxonomy) |
| :--- | :--- | :--- |
| `硬體` | `個人電腦` | `主機伺服器`、`個人電腦`、`網路設備`、`儲存媒體`、`週邊設備`、`機房`、`電力與公用設施` |
| `軟體` | `應用系統` | `作業系統`、`資料庫`、`應用系統`、`虛擬環境`、`雲端服務系統`、`辦公室應用軟體` |
| `資料` | `管理文件` | `網站公開資料`、`業務交易資料`、`客戶資料檔`、`系統設定參數資料`、`網路設定資料`、`系統文件`、`程式碼`、`合約`、`管理文件`、`表單紀錄` |
| `文件` | `作業紀錄` | `系統操作文件`、`網路架構圖`、`作業紀錄`、`紙本合約`、`客戶資料`、`管理文件`、`業務資料` |
| `人員` | `員工` | `員工`、`外部廠商` |

---

## 3. Blank Markdown Template (Ready to Fill)

```markdown
| 類別 | 類型 | 資訊資產項目 | 部門 | 保管人 | C | I | A | 威脅項目1 | 弱點項目1 |
| :--- | :--- | :--- | :--- | :--- | :-: | :-: | :-: | :--- | :--- |
| 軟體 | 雲端服務系統 | Surveycake | 行銷部 | 王小明 | | | | 雲端服務或管理後台帳號遭盜用 | 特權與管理帳號未強制啟用多因素驗證(MFA) |
| 資料 | 系統設定參數資料 | 串接設定大表 | 維運部 | 李組長 | | | | 系統設定檔/計費費率遭惡意竄改 | 設定檔與參數檔案未設唯讀權限且缺乏完整性監控 |
| 人員 | 員工 | 業務 | 業務部 | 陳協理 | | | | 員工誤點釣魚郵件致主機遭植後門 | 員工資安意識不足且定期社交工程演練覆蓋率低 |
| 文件 | 紙本合約 | 商戶特約機構契約書 | 法務部 | 張專員 | | | | 機密紙本文件/合約遭翻拍窺視 | 辦公區域未落實桌面淨空(Clean Desk)與上鎖 |
```
