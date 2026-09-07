# Senior Developer 7 Coding Laws 與 AST 靜態稽核治理指南

本指南整合 **《資深開發者 7 大 Coding 法則》（架構治理標準）** 與 **`audit.py`（AST 靜態代碼稽核引擎）**，提供從「架構設計思維」到「自動化機器檢查」的完整 Python 3 現代化工程實踐標準與全量範例。

---

## 一、 雙軌代碼治理架構（Dual Governance Architecture）

在健康的企業級軟體工程體系中，代碼品質由「高階架構標準」與「底層安全安檢」共同守護，兩者職責分明且互為補充：

```
┌────────────────────────────────────────────────────────────────────────┐
│               L1 架構與工藝層：senior_coding_laws.template.md          │
│  • 認知負擔控制 (Guard Clause)        • 依賴與 AI 上下文邊界 (Context) │
│  • 狀態封閉與下限防呆 (StrEnum & max) • 純決策與副作用分離 (Functional)│
│  • 結構性去重 (SSOT 幾何解算器)       • 領域例外階層與追蹤鏈 (from e)   │
├────────────────────────────────────────────────────────────────────────┤
│               L0 機器安檢層：audit.py (AST + Regex 靜態稽核)           │
│  [BLOCKER] 阻擋項 (FAIL - 零容忍 Bug)：                                │
│    1. 模組/類別同名覆蓋宣告            2. 字典重複 Key 覆蓋            │
│    3. 可變預設參數 (def f(l=[]))       4. 裸 except: 吞噬信號          │
│    5. 絕對路徑 (/path/to/user) 與明文金鑰 6. 特權提升與危險執行 (eval/exec)│
│  [ADVISORY] 建議項 (WARN - 架構提示)：                                 │
│    1. 巢狀 if 深度 > 2 (建議早退)     2. 生產環境 assert 警告         │
│    3. 檔案行數 > 200 (提示模組化)     4. 重度第三方依賴 (Stdlib 優先)  │
│    5. 靜態資產過大 (> 10KB 預算警示)                                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 二、 Senior Developer 7 Coding Laws 深度規格（四大 Gate）

本規範定義於 `senior_coding_laws.template.md`，旨在消滅動態語言的隱性缺陷，使代碼具備**低認知負擔、高測試覆蓋、秒級排障與零破壞性演進**。

### Gate 1: Control Flow & Structure Gate

#### 1.1 Law 1: Return Early（保持主路徑易於追蹤）
* **核心哲學**：閱讀代碼應如閱讀清單。在函式頂部使用 Guard Clauses（早退）立即排除邊界與錯誤狀態，讓主要業務流程（Happy Path）保持在「零縮排」的最外層。
* **Mandate（強制規範）**：
  * 必須在函式開頭使用 Guard Clauses（早退原則：`if not valid: return / raise`）排除邊界與異常情況。
  * 複雜的多分支分發必須優先採用結構化模式匹配（Python 3.10+ `match ... case`）。
  * 資源生命週期（檔案、連線、鎖）必須封裝於 Context Manager（`with` 敘述）中。
* **Prohibit（嚴格禁止）**：
  * 嚴禁超過 2 層以上的條件嵌套金字塔（Nested Pyramids）。
  * 嚴禁使用過度壓縮、難以閱讀的多層巢狀列表推導式（Nested List Comprehensions）。

---

### Gate 2: Semantics & Interface Gate

#### 2.1 Law 2: Name the Meaning（以意圖與語意命名）
* **核心哲學**：名稱應表達業務領域的「意圖與目的」（如 `pending_orders`），而非底層「資料結構或技術名詞」（如 `data`, `res`）。
* **Mandate（強制規範）**：
  * 命名必須具備領域語意，描述該變數代表的業務實體。
  * 所有布林開關與設定閾值，必須強制宣告為 **Keyword-only 引數（`*`）**，消除呼叫端的「布林盲（Boolean Blindness）」。
  * 嚴格遵守 PEP 8 命名規範（函式/變數 `snake_case`、類別 `PascalCase`、常數 `SCREAMING_SNAKE_CASE`）。
* **Prohibit（嚴格禁止）**：
  * 嚴禁使用無意義的佔位變數（`data`, `temp`, `res`, `info`, `item`）。
  * 嚴禁在呼叫端以位置參數傳遞裸布林值（如 `export(data, True, 30)`）。

#### 2.2 Law 3: Own the Boundary（外部系統與 AI 上下文隔離於邊界之後）
* **核心哲學**：外部系統（第三方 SDK、API 欄位、資料庫）隨時可能變更，必須在邊界建立防腐層。在 AI Agent 生態中，Prompt 上下文也是一道關鍵邊界，洩漏未經處理的龐大靜態資料會直接炸裂 Token 預算。
* **資產使用路徑分水嶺（後台靜態資產 vs 上下文傾倒）**：
  * **路徑 A：後台代碼封裝（健康架構，100% 推薦）**：檔案純由 Python 腳本在後台 `open()` 讀取，AI 完全無感知、Token 消耗永遠為 0。在此模式下，本地資料即使 50MB 亦健康無虞。
  * **路徑 B：Prompt 上下文傾倒（致命反模式，嚴厲禁止）**：將大型資料檔寫入 `SKILL.md` 逼迫 AI 透過 `view_file` 通讀（如 PPTX 原版的 13KB 圖標庫）。在此模式下，即使僅 5KB 亦會造成對話延遲暴增與巨額帳單。
* **Mandate（強制規範）**：
  * 必須使用結構化介面（`typing.Protocol` 或 `abc.ABC`）隔離所有外部依賴（依賴反轉原則）。
  * 外部原始資料（Raw JSON / dict）在進入邊界時，必須立即解析為強型別且不可變的領域模型（`@dataclass(frozen=True)` 或 Pydantic）。
  * **AI Context 邊界隔離**：重型靜態資料（如字典、目錄清單、查表檔 $> 10\text{KB}$）必須隔離在 Python 代碼後台查詢，嚴禁將未經處理的原始大資料作為參考文檔全量洩漏至 LLM Prompt。
* **Prohibit（嚴格禁止）**：
  * 嚴禁在核心業務邏輯中傳遞無型別的原始字典（`dict[str, Any]`）。
  * 嚴禁將第三方 SDK 專屬物件直接洩漏進內部領域模型。
  * 嚴禁把龐大的靜態字典/目錄清單直接灌入 Agent Prompt 當作參考資料。

---

### Gate 3: State & Architecture Gate

#### 3.1 Law 4: Model the State（從型別與數值下限定義合法狀態）
* **核心哲學**：不要靠散落在各處的執行期 `if` 檢查來防禦狀態，而是透過型別系統與資料結構設計，使「非法狀態（如未付款卻有出貨單號）」在語法上根本建立不出來。在數值與物理層面，必須杜絕不可能存在的下溢與負數。
* **Mandate（強制規範）**：
  * 狀態集合必須使用字串列舉（`enum.StrEnum`）或代數聯集型別（`OrderPending | OrderPaid`）進行精確約束。
  * 領域實體預設使用不可變模型（`@dataclass(frozen=True)`），防止物件在流轉時被隱式篡改。
  * **Defensive Bounds（數值下限防呆）**：所有涉及空間幾何（長寬邊距）、時間跨度或配額扣除運算，必須在計算端強制進行物理下限鉗位（如 `max(MIN_FLOOR, val - delta)`），保證負數維度等破壞性數值在狀態中不可能存在。
  * 必須啟用靜態型別檢查器（`mypy` 或 `pyright`）。
* **Prohibit（嚴格禁止）**：
  * 嚴禁在業務判斷中使用魔法字串/數字（Magic Strings）。
  * 嚴禁在函式簽名中使用可變預設參數（如 `def func(target=[])`）。
  * 嚴禁對幾何維度或資源配額進行無 `max()` 鉗位防呆的減法運算。

#### 3.2 Law 5: Split the Decision（純決策與副作用分離）
* **核心哲學**：將「決策邏輯（Decisions）」從「觸發的副作用（Side Effects：DB 寫入、API 呼叫、寄信）」中抽離出來。純邏輯可在完全不碰資料庫與外部系統的情況下進行 100% 隔離測試。
* **Mandate（強制規範）**：
  * 核心業務計算（折讓計算、資格審查、數據排版）必須撰寫為純函式（Pure Functions），無任何 I/O、網路或資料庫存取，保證零 Mock 即可進行單元測試。
  * 副作用（DB 寫入、API 請求、郵件發送、檔案落盤）必須集中在最外層的 Service/Orchestration 層統一執行。
* **Prohibit（嚴格禁止）**：
  * 嚴禁在運算與驗證函式中偷偷夾帶 I/O 呼叫。
  * 嚴禁在類別建構子 `__init__` 或屬性 `@property` 內部執行網路連線或 DB 查詢。
  * 嚴禁依賴模組級別的可變全域狀態（Mutable Global State）。

---

### Gate 4: Reliability & Governance Gate

#### 4.1 Law 6: Useful Errors（機器可讀代碼與人類可讀錯誤）
* **核心哲學**：錯誤必須對「自動化系統」與「人類工程師」同時具備實用性。提供機器可判斷的錯誤代碼（Error Codes），並附帶清楚的人類錯誤說明與除錯上下文。
* **Mandate（強制規範）**：
  * 必須建立專案自訂領域例外階層（Domain Exceptions），並攜帶結構化參數（如 `order_id`, `retry_count`）。
  * 捕捉底層例外並重新包裝時，必須強制使用例外鏈（`raise DomainError(...) from err`），保留原始根因 Traceback。
* **Prohibit（嚴格禁止）**：
  * 嚴禁使用裸 `except:` 或無差別吞掉異常的 `except Exception:`。
  * 嚴禁在生產環境使用 `assert` 進行業務驗證（在 `python -O` 下會被編譯器無條件移除）。

#### 4.2 Law 7: Ship Small Diffs（保持變更聚焦與原子化 PR）
* **核心哲學**：Pull Request 必須小到讓 Reviewer 可以將所有上下文輕鬆裝進大腦記憶體（Working Memory）中。小變更帶來高品質審查並顯著降低 Bug 率。
* **Mandate（強制規範）**：
  * 嚴格遵守單一職責原則（SRP），一個 PR 只聚焦於單一功能或缺陷。
  * 通用幾何與排版邏輯重複出現時，提煉為底層單一解算器（如 `calc_cols`），落實 SSOT。
  * 使用自動化工具鏈（`ruff`、`black`）確保格式一致，保持 Git Diff 精準乾淨。
* **Prohibit（嚴格禁止）**：
  * 嚴禁建立包山包海的垃圾桶模組（`utils.py`, `helpers.py`）。
  * 嚴禁在同一個變更中混雜「代碼格式重排」與「業務功能修改」，嚴禁跨多個無關領域的巨型 PR（Mega-PRs）。

---

## 三、 `audit.py` AST 靜態稽核引擎規格

`audit.py` 是輕量（< 180 行）且高確定性的靜態安全與架構檢驗器，透過 Python 抽象語法樹（AST）與正規表達式進行毫秒級掃描。

### 稽核規則清單與處置分級

| 類別 | 檢驗標的 | AST / 偵測機制 | 處置嚴重度 | 解決指引 |
| :--- | :--- | :--- | :---: | :--- |
| **重名覆蓋** | 模組/類別同名定義 | 掃描同 Scope 的 `FunctionDef` / `ClassDef`（自動放行 `@overload`） | `[BLOCKER]` (FAIL) | 移除被覆蓋的舊實作或重新命名 |
| **字典衝突** | 重複字典鍵值 | 檢查 `ast.Dict` Literal Key 是否有重複字串 | `[BLOCKER]` (FAIL) | 移除重複的 Key，保留正確設定值 |
| **狀態陷阱** | 可變預設參數 | 檢查 `args.defaults` 是否包含 `List`, `Dict`, `Set` | `[BLOCKER]` (FAIL) | 改用 `None` 保底並在函式內初始化 |
| **錯誤隱吞** | 裸 `except:` | 檢查 `ast.ExceptHandler.type is None` | `[BLOCKER]` (FAIL) | 明確指定捕捉之例外型別（如 `except ValueError:`） |
| **安全防禦** | 絕對路徑 / 金鑰 | 正則匹配本機路徑樣式、`sk-...`、`AKIA...` | `[BLOCKER]` (FAIL) | 改用相對路徑、環境變數或安全配置檔 |
| **安全防禦** | 危險任意執行 | 檢查 `eval()`, `exec()`, `os.system()` | `[BLOCKER]` (FAIL) | 改用安全解析庫或 `subprocess.run([...])` |
| **控制流** | 巢狀 `if` 深度 $> 2$ | 遍歷 `ast.If` 計算縮排層次（自動放行平級 `elif` 鏈） | `[ADVISORY]` (WARN) | 使用 Guard Clause（早退）扁平化邏輯 |
| **可靠性** | 生產環境 `assert` | 檢查非測試程式碼中的 `ast.Assert` | `[ADVISORY]` (WARN) | 改用 `if not condition: raise DomainError(...)` |
| **架構規模** | 檔案行數 $> 200$ 行 | 計算檔案總行數 | `[ADVISORY]` (WARN) | 若非 Library 引擎，建議評估是否模組化拆分 |
| **依賴管理** | 重度外部套件 | 檢查是否引用 `requests`, `pandas`, `numpy` 等 | `[ADVISORY]` (WARN) | 優先評估是否能以標準庫（`urllib`, `json`）實現 |
| **資產衛生** | 靜態資料檔案過大 | 掃描 `.json`, `.yaml`, `.csv`, `.txt`, `.xml` 單檔 $> 10\text{KB}$ | `[ADVISORY]` (WARN) | 取決於使用路徑：若由 Python 後台讀取完全合法；若在 `SKILL.md` 逼 AI 閱讀則應立即重構 |

> **防閹割保證與資產路徑審查**：`audit.py` 將規則嚴格劃分。只有致命 Bug（同名覆蓋、可變預設、裸 Except）會列為 `[BLOCKER]`；行數與資產體積僅列為 `[ADVISORY]`。特別是資產體積：**檔案大小本身無罪，核心在於腳本怎麼用它**。若為 Python 後台靜默查表則為優良設計，絕不迫使開發者為了削足適履而刪除必要的本地資產檔。

---

## 四、 完整生產級代碼範例對比（電商訂單結帳服務）

以下透過「電商訂單結帳與扣款服務」的實戰場景，完整對比不合規代碼與符合 7 大法則的高品質代碼。

### ❌ 違規代碼（Junior / Fragile / `audit.py` 檢驗失敗）

```py
# 檔案：fragile_checkout.py
# 存在問題：巢狀金字塔、可變預設、同名覆蓋、字典重複Key、裸Except、副作用混雜、布林盲、assert驗證

import os

# ❌ 違規 1：同名覆蓋（第二次宣告會無聲無息吃掉第一次宣告）
def calculate_tax(amount):
    return amount * 0.05

def calculate_tax(amount):
    return amount * 0.10

# ❌ 違規 2：字典重複 Key 覆蓋
PAYMENT_CONFIG = {
    "timeout": 30,
    "retry": 3,
    "timeout": 60  # 重複 Key
}

# ❌ 違規 3：可變預設參數 (coupons=[])
# ❌ 違規 4：布林盲 (is_vip=False 沒有強制 Keyword-only)
def checkout(order, coupons=[], is_vip=False):
    # ❌ 違規 5：生產環境中使用 assert 進行業務檢查
    assert order is not None, "Order cannot be None"
    
    # ❌ 違規 6：巢狀條件金字塔（深度 3 > 2）
    if order.get("status") == "pending":
        if order.get("amount") > 0:
            if not order.get("is_frozen"):
                # ❌ 違規 7：純計算中偷混雜 I/O 副作用與外部 SDK 呼叫
                print(f"[LOG] Processing order {order.get('id')}")
                os.system(f"curl -X POST https://api.bank.com/pay -d id={order.get('id')}")
                
                total = order.get("amount")
                for c in coupons:
                    total -= c.get("discount", 0)
                
                try:
                    # 假裝存入資料庫
                    result = {"id": order.get("id"), "total": total, "status": "paid"}
                    return result
                except:
                    # ❌ 違規 8：裸 except 吞掉系統信號與語法錯誤
                    pass
    return None
```

#### 執行 `python3 audit.py fragile_checkout.py` 輸出：
```bash
[✗] FAIL fragile_checkout.py (45 lines)
  └── [BLOCKER] Script duplicate definition of 'calculate_tax' in module (Silent overwrite)
  └── [BLOCKER] Script duplicate dictionary key 'timeout' (Silent overwrite)
  └── [BLOCKER] Script mutable default argument in func 'checkout'
  └── [BLOCKER] Script bare 'except:' handler (Swallows critical signals)
  └── [BLOCKER] Script os.system() execution
  └── [ADVISORY] Script nested if-block depth 3 > 2 (Flatten via Guard Clauses)
  └── [ADVISORY] Script production 'assert' statement (Disabled under python -O)
```

---

### ✅ 高品質資深代碼（Senior / Robust / `audit.py` 100% 通過）

```python
#!/usr/bin/env python3
"""
Senior Compliant Order Checkout Service
- Fully compliant with 7 Coding Laws
- 100% Passes audit.py AST and Security Inspection
"""

from enum import StrEnum
from dataclasses import dataclass
from typing import Protocol
from decimal import Decimal


# ==============================================================================
# 1. 領域模型與狀態封閉 (Gate 3.1: Make Invalid States Harder to Represent)
# ==============================================================================

class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FROZEN = "frozen"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Coupon:
    code: str
    discount: Decimal


@dataclass(frozen=True)
class Order:
    order_id: str
    amount: Decimal
    status: OrderStatus
    is_frozen: bool = False


@dataclass(frozen=True)
class CheckoutDecision:
    order_id: str
    original_amount: Decimal
    discount_total: Decimal
    final_amount: Decimal
    tax_amount: Decimal


# ==============================================================================
# 2. 領域例外階層 (Gate 4.1: Make Failures Understandable & Actionable)
# ==============================================================================

class CheckoutError(Exception):
    """專案結帳基底例外"""
    def __init__(self, order_id: str, message: str):
        super().__init__(f"Order '{order_id}' checkout failed: {message}")
        self.order_id = order_id


class InvalidOrderStatusError(CheckoutError): pass
class PaymentGatewayError(CheckoutError): pass


# ==============================================================================
# 3. 邊界隔離協議 (Gate 2.2: Keep External Systems Behind Boundaries)
# ==============================================================================

class PaymentGateway(Protocol):
    """抽象支付閘道介面，解耦第三方 SDK"""
    def charge(self, order_id: str, amount: Decimal) -> str: ...


class OrderRepository(Protocol):
    """抽象資料存取介面"""
    def save_decision(self, decision: CheckoutDecision, txn_id: str) -> None: ...


# ==============================================================================
# 4. 純決策核心 (Gate 1.1: Guard Clauses + Gate 3.2: Pure Functional Core)
# ==============================================================================

def calculate_checkout_decision(
    order: Order,
    *,
    coupons: list[Coupon] | None = None,
    tax_rate: Decimal = Decimal("0.05")
) -> CheckoutDecision:
    """
    純運算決策函式（無 I/O、無副作用、零 Mock 即可進行單元測試）。
    使用 Guard Clauses 保持主路徑扁平。
    """
    # Guard 1: 訂單狀態檢查
    if order.status != OrderStatus.PENDING:
        raise InvalidOrderStatusError(order.order_id, f"Invalid status '{order.status}'")

    # Guard 2: 凍結防護
    if order.is_frozen:
        raise InvalidOrderStatusError(order.order_id, "Order is frozen")

    # Guard 3: 金額合法性
    if order.amount <= Decimal("0"):
        raise InvalidOrderStatusError(order.order_id, "Order amount must be positive")

    # 主路徑運算 (Happy Path)
    active_coupons = coupons or []
    total_discount = sum((c.discount for c in active_coupons), Decimal("0"))
    discounted = max(Decimal("0"), order.amount - total_discount)  # Gate 3.1: Defensive Bounds 數值下限防呆，杜絕負數金額
    tax = discounted * tax_rate
    final_amount = discounted + tax

    return CheckoutDecision(
        order_id=order.order_id,
        original_amount=order.amount,
        discount_total=total_discount,
        final_amount=final_amount,
        tax_amount=tax
    )


# ==============================================================================
# 5. 副作用編排外殼 (Gate 3.2: Imperative Shell + Gate 2.1: Keyword-Only)
# ==============================================================================

def process_checkout_pipeline(
    order: Order,
    gateway: PaymentGateway,
    repo: OrderRepository,
    *,
    coupons: list[Coupon] | None = None,
    dry_run: bool = False
) -> CheckoutDecision:
    """
    副作用編排層：負責協調整合決策與外部依賴。
    強制使用 Keyword-only 引數消除布林盲。
    """
    # 步驟 1: 執行純決策運算
    decision = calculate_checkout_decision(order, coupons=coupons)

    if dry_run:
        return decision

    # 步驟 2: 呼叫外部支付閘道 (具備例外鏈 trace 保留)
    try:
        txn_id = gateway.charge(decision.order_id, decision.final_amount)
    except Exception as err:
        raise PaymentGatewayError(decision.order_id, f"Gateway network fault: {err}") from err

    # 步驟 3: 資料持久化落盤
    repo.save_decision(decision, txn_id)
    return decision
```

#### 執行 `python3 audit.py senior_checkout.py` 輸出：
```bash
[✓] PASS senior_checkout.py (135 lines)
```

---

## 五、 開發與驗證 SOP 指引

### 1. 本地開發檢查命令
```bash
# 稽核單一腳本
python3 ~/.gemini/config/skills/audit-skill/scripts/audit.py /path/to/script.py

# 稽核整個模組目錄
python3 ~/.gemini/config/skills/audit-skill/scripts/audit.py /path/to/my_skill/
```

### 2. Pre-Commit 流程整合建議
在 Git commit 或 PR 提交前，建議將 `audit.py` 作為確定性 Gate 0 自動執行：
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "[*] Running AST & Security Audit Gate..."
python3 ~/.gemini/config/skills/audit-skill/scripts/audit.py $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|md)$')
if [ $? -ne 0 ]; then
    echo "[!] Audit failed. Please fix BLOCKER issues before commit."
    exit 1
fi
```

---

## 六、 結論與核心思維總結

1. **`senior_coding_laws` 給予思維**：引導我們在編寫代碼的第一秒就考慮「閱讀者的認知負擔」、「未來換套件的痛苦指數」與「單元測試的容易度」。
2. **`audit.py` 給予底線**：在代碼存檔交付的最後一刻，以 0.1 秒的 AST 靜態解析攔截所有低級語法陷阱（重複覆蓋、可變預設、裸 Except）與安全硬編碼。
3. **兩者合一**：既不因過度檢查而閹割業務功能，又確保每一行交付的代碼都具備企業級的強韌體質。
