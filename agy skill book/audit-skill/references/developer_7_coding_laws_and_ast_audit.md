# Senior Developer 7 Coding Laws 與 AST 靜態稽核治理指南

本指南整合 **《資深開發者 7 大 Coding 法則》（架構治理標準）** 與 **`audit.py` / `audit_frontend.py`（AST 靜態代碼稽核引擎）**，提供從「架構思維」、「標準 SOP 操作指令」到「機器自動化驗收」的完整現代化工程實踐規格。

---

## 一、 治理體系三權分立架構（Three-Tier Governance Architecture）

在企業級系統與 Vibe Coding 人機協同開發中，代碼品質透過「事前引導、事中審查、事後急救」三權分立架構閉環守護：

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 事前架構心法與雷達：senior_coding_laws / engineering_standards      │
│  • 角色：設計雷達與意識檢查表（Mindfulness & Senior Heuristics）       │
│  • 核心：定規格先行 (Spec-First)、任務切塊 (Chunking)、根因收斂 (Root)│
├────────────────────────────────────────────────────────────────────────┤
│ 2. 事中客觀聽診器：audit.py / audit_frontend.py                       │
│  • 角色：無偏見、秒級執行的機器安檢門（<20ms AST 與正則檢測）         │
│  • 處置：[BLOCKER] 致命 Bug 嚴格阻擋；[ADVISORY] 架構與預算提示建議     │
├────────────────────────────────────────────────────────────────────────┤
│ 3. 事後紅燈急救處方箋：remediation_guide.md                            │
│  • 角色：安檢報警時的機械式修復 Runbook（五級階梯：Delete -> Root -> Sec）│
│  • 產出：1 對 1 程式碼對照範本 (Diff)，避免 AI 漫無目的盲目試錯       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 二、 Senior Developer 7 Coding Laws 深度規格（SOP 操作手冊）

### 7 大架構心法與彈性邊界速查表

| 定律編號與名稱 | 關注點（Mindfulness） | 實用指引（Senior Heuristic） | 保持彈性（Pragmatic Boundary） |
| :--- | :--- | :--- | :--- |
| **Law 1: Return Early** | 消除金字塔型深層嵌套判斷 | 頂部使用 Guard Clauses；多分支用 `match...case` | 1~2 層淺層 `if` 完全合法，嚴禁碎拆為微型函式 |
| **Law 2: Name the Meaning** | 避免通用名（data）與布林盲 | 領域實體命名；布林開關強制 Keyword-only（`*`） | 1~2 個引數的純數學/工具函式（`add(a, b)`）免設 |
| **Law 3: Own the Boundary** | 外部依賴隔離與 Token 防線 | **Spec-First**：先定 Schema 再寫碼；大資料留後台查詢 | 標準庫呼叫（`pathlib.Path`）不需額外防腐層 |
| **Law 4: Model the State** | 封閉非法狀態與下限防呆 | 採 `StrEnum` / Unions；幾何與配額強制 `max(MIN, ...)` | 腳本內部臨時字典不需過度封裝為實體類別 |
| **Law 5: Split the Decision** | 純運算與副作用分離 | 計算收斂為純函式；I/O 與網路置於外層 Shell | 單純循序轉換腳本（讀 $\to$ 轉 $\to$ 存）免多層架構 |
| **Law 6: Useful Errors** | 具備追蹤上下文的有用錯誤 | 拋出自訂領域例外；使用 `raise ... from err` 串聯堆疊 | 小腳本直接用標準例外（`ValueError`），免造輪子 |
| **Law 7: Ship Small Diffs** | 極小 Diff 與任務切塊 | **Chunking**：拆 3~5 階段；**Root Cause**：grep 共用根部修復 | 模組化單檔腳本維持 300~400 行以內健康安全 |

---

### Gate 1: Control Flow & Structure Gate

#### 1.1 Law 1: Return Early（保持主路徑易於追蹤）
* **說明**：閱讀代碼應如閱讀清單。在函式頂部使用 Guard Clauses（早退）立即排除邊界與錯誤狀態，讓主要業務流程（Happy Path）保持在「零縮排」的最外層。
* **Mandate（SOP 強制規範）**：
  * 必須在函式開頭使用 Guard Clauses（`if not valid: return / raise`）排除邊界與異常情況。
  * 複雜的多分支分發必須優先採用結構化模式匹配（Python 3.10+ `match ... case`）。
  * 資源生命週期（檔案、連線、鎖）必須封裝於 Context Manager（`with` 敘述）中。
* **Prohibit（嚴格禁止）**：嚴禁超過 2 層以上的條件嵌套金字塔；嚴禁使用過度壓縮的多層巢狀列表推導式。
* **SOP 對照範本**：
```py
# ❌ 反模式：金字塔條件嵌套（深度 3 > 2）
if user:
    if user.is_active:
        if user.has_permission("admin"):
            return process_admin_action(user)
```
```python
# ✅ SOP 規範：Guard Clauses 早期返回，主路徑零縮排
if not user or not user.is_active or not user.has_permission("admin"):
    return None
return process_admin_action(user)
```
* **Pragmatic Boundary（保持折衷彈性）**：1~2 層的淺層 `if` 完全合法，嚴禁為了消滅所有 `if` 矯枉過正碎拆為微型函式。

---

### Gate 2: Semantics & Interface Gate

#### 2.1 Law 2: Name the Meaning（以意圖與語意命名）
* **說明**：名稱應表達業務領域的「意圖與目的」（如 `pending_orders`），而非底層「資料結構或技術名詞」（如 `data`, `res`）。
* **Mandate（SOP 強制規範）**：
  * 命名必須具備領域實體語意，描述該變數代表的業務物件。
  * 所有布林開關與設定閾值，必須強制宣告為 **Keyword-only 引數（`*`）**，消除呼叫端的「布林盲（Boolean Blindness）」。
  * 嚴格遵守 PEP 8 命名規範（變數 `snake_case`、類別 `PascalCase`、常數 `SCREAMING_SNAKE_CASE`）。
* **Prohibit（嚴格禁止）**：嚴禁使用無意義佔位變數（`data`, `temp`, `res`, `info`）；嚴禁在呼叫端以位置參數傳遞裸布林值。
* **SOP 對照範本**：
```py
# ❌ 反模式：無意義名稱與布林盲
def export(d, flag=True): ...
export(res, True)  # 呼叫端無法得知 True 的業務意圖
```
```python
# ✅ SOP 規範：領域命名與 Keyword-only 強制宣告
def export_orders(orders: list[dict], *, include_cancelled: bool = True): ...
export_orders(pending_orders, include_cancelled=True)
```
* **Pragmatic Boundary（保持折衷彈性）**：1~2 個引數的純數學運算或工具函式（如 `add(a, b)`）免設 keyword-only。

#### 2.2 Law 3: Own the Boundary（外部系統與 AI 上下文隔離於邊界之後）
* **說明**：外部系統隨時可能變更，必須在邊界建立防腐層。在 AI 生態中，Prompt 上下文也是關鍵邊界，洩漏未經處理的龐大靜態資料會直接炸裂 Token 預算。
* **Mandate（SOP 強制規範）**：
  * **Spec-First 先行流程**：在撰寫具體實作前，必須先定義領域模型（`dataclass(frozen=True)` / Pydantic）或介面契約（`Protocol`）。
  * **邊界防腐與 Context 隔離**：外部原始資料進入邊界時立即解析為不可變模型；大型靜態資料由後台代碼讀取（0 Token），嚴禁倒入 Prompt。
* **Prohibit（嚴格禁止）**：嚴禁在核心業務邏輯中傳遞無型別原始字典（`dict[str, Any]`）；嚴禁將第三方 SDK 物件直接洩漏進內部領域模型。
* **SOP 對照範本**：
```py
# ❌ 反模式：業務核心直接透傳外部 raw dict，欄位異動引發全域崩潰
def process_order(payload: dict):
    return payload["order"]["items"][0]["price"]
```
```python
# ✅ SOP 規範：Spec-First 強型別不可變模型防腐
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderItem:
    sku: str
    price: float
```
* **Pragmatic Boundary（保持折衷彈性）**：標準庫呼叫（`pathlib.Path`, `json.loads`）不需額外抽象防腐層。

---

### Gate 3: State & Architecture Gate

#### 3.1 Law 4: Model the State（從型別與數值下限定義合法狀態）
* **說明**：透過型別系統與資料結構設計，使「非法狀態」在語法上無法被建立；在數值物理層面杜絕不可能存在的下溢與負數。
* **Mandate（SOP 強制規範）**：
  * 狀態集合必須使用字串列舉（`enum.StrEnum`）或代數聯集型別約束。
  * 領域實體預設使用不可變模型（`@dataclass(frozen=True)`）。
  * **Defensive Bounds 數值防呆**：所有涉及幾何尺寸（長寬邊距）、時間跨度或配額扣除運算，必須在計算端強制進行物理下限鉗位（`max(MIN_FLOOR, val - delta)`）。
* **Prohibit（嚴格禁止）**：嚴禁業務判斷中使用魔法字串/數字；嚴禁函式簽名中使用可變預設參數（`def f(x=[])`）；嚴禁無 `max()` 鉗位防呆的減法運算。
* **SOP 對照範本**：
```py
# ❌ 反模式：可變預設參數 + 負數幾何破壞
def create_card(w, h, tags=[]):
    width = w - 10  # 若 w < 10 產生負數維度破壞二進位
```
```python
# ✅ SOP 規範：None 保底 + max() 物理下限鉗位
def create_card(w: float, h: float, *, tags: list[str] | None = None) -> float:
    active_tags = tags if tags is not None else []
    return max(0.0, w - 10.0)
```
* **Pragmatic Boundary（保持折衷彈性）**：腳本內部微小臨時字典不需過度封裝為實體類別。

#### 3.2 Law 5: Split the Decision（純決策與副作用分離）
* **說明**：將純決策計算從觸發的副作用（DB 寫入、API 呼叫、磁碟 I/O）中抽離出來，純邏輯可在零 Mock 情況下完成 100% 單元測試。
* **Mandate（SOP 強制規範）**：核心業務計算必須撰寫為純函式（Pure Functions），無任何 I/O、網路或資料庫存取；副作用必須集中在最外層的 Service / Orchestration 外殼統一執行。
* **Prohibit（嚴格禁止）**：嚴禁在運算與驗證函式中偷渡 I/O 呼叫；嚴禁在類別建構子 `__init__` 或屬性內部執行連線或 DB 查詢；嚴禁依賴可變全域狀態。
* **SOP 對照範本**：
```py
# ❌ 反模式：純計算中偷渡日誌 I/O 與網路副作用
def calculate_tax(amount):
    requests.post("https://api.log/audit", json={"amt": amount})
    return amount * 0.05
```
```python
# ✅ SOP 規範：純計算收斂為 Functional Core（零 Mock 即可測試）
def calculate_tax(amount: float, rate: float = 0.05) -> float:
    return amount * rate
```
* **Pragmatic Boundary（保持折衷彈性）**：單純循序轉換腳本（讀檔 $\to$ 轉檔 $\to$ 存檔）不需硬套多層架構。

---

### Gate 4: Reliability & Governance Gate

#### 4.1 Law 6: Useful Errors（機器可讀代碼與人類可讀錯誤）
* **說明**：錯誤必須對自動化系統與人類工程師同時具備實用性，提供結構化參數並完整保留排障根因。
* **Mandate（SOP 強制規範）**：必須建立專案自訂領域例外階層（Domain Exceptions）；捕捉底層例外重新包裝時，必須強制使用例外鏈（`raise DomainError(...) from err`）保留原始 Traceback。
* **Prohibit（嚴格禁止）**：嚴禁使用裸 `except:` 或無差別吞掉異常的 `except Exception:`；嚴禁在生產環境使用 `assert` 進行業務驗證。
* **SOP 對照範本**：
```py
# ❌ 反模式：吞噬系統信號或生產 assert
try:
    process_payment()
except: pass  # 吞掉中斷信號與真實 Bug
assert order.amount > 0, "Bad amount"  # python -O 會直接被編譯器拔除
```
```python
# ✅ SOP 規範：領域例外鏈保留原始根因
try:
    process_payment()
except Exception as err:
    raise PaymentGatewayError(order_id, f"Gateway network fault: {err}") from err
```
* **Pragmatic Boundary（保持折衷彈性）**：小腳本直接使用標準例外（`ValueError`, `RuntimeError`），免造輪子。

#### 4.2 Law 7: Ship Small Diffs（保持變更聚焦與原子化 PR）
* **說明**：變更必須小到讓審查者輕鬆裝進大腦記憶體中。小變更帶來高品質審查並顯著降低 Bug 率。
* **Mandate（SOP 強制規範）**：
  * **Chunking（任務切塊 SOP）**：複雜功能必須拆解為 3～5 個原子任務（Milestones），一次只產出與驗收單一元件或函式。
  * **Root Cause over Caller Patching（根因收斂 SOP）**：修復缺陷時必須 `grep` 所有調用點，在最底層共用函式根部一次修復，產生全域最小有效 Diff。
* **Prohibit（嚴格禁止）**：嚴禁建立包山包海的垃圾桶模組（`utils.py`, `helpers.py`）；嚴禁在多個呼叫端隨處打特化 `if-else` 或 `try-catch` 補丁。
* **SOP 對照範本**：
```py
# ❌ 反模式：呼叫端到處打補丁（Patching Callers）
# 5 個呼叫端各自寫特化判斷：
res = get_data()
if res is not None and "items" in res: ...
```
```python
# ✅ SOP 規範：單點收斂於核心函式根部防禦
def get_data() -> dict:
    raw = fetch()
    return raw.get("items", {}) if isinstance(raw, dict) else {}
```
* **Pragmatic Boundary（保持折衷彈性）**：模組化單檔腳本維持 300~400 行以內流通性極高，嚴禁無意義的過度碎片化拆檔。

---

## 三、 `audit.py` AST 靜態稽核引擎規格

`audit.py` 是輕量且高確定性的靜態安全與架構檢驗器，透過 Python AST 與正則表達式進行毫秒級掃描。

### 稽核規則清單與處置分級

| 類別 | 檢驗標的 | AST / 偵測機制 | 處置嚴重度 | 解決指引 |
| :--- | :--- | :--- | :---: | :--- |
| **重名覆蓋** | 模組/類別同名定義 | 掃描同 Scope 的 `FunctionDef` / `ClassDef` | `[BLOCKER]` | 移除被覆蓋的舊實作或重新命名 |
| **字典衝突** | 重複字典鍵值 | 檢查 `ast.Dict` Literal Key 重複字串 | `[BLOCKER]` | 移除重複 Key，保留正確設定值 |
| **狀態陷阱** | 可變預設參數 | 檢查 `args.defaults` 包含 `List`, `Dict`, `Set` | `[BLOCKER]` | 改用 `None` 保底並在函式內初始化 |
| **錯誤隱吞** | 裸 `except:` | 檢查 `ast.ExceptHandler.type is None` | `[BLOCKER]` | 明確指定捕捉之型別（如 `except ValueError:`） |
| **安全防禦** | 絕對路徑 / 金鑰 | 正則匹配本機絕對路徑樣式、`sk-...`、`AKIA...` | `[BLOCKER]` | 改用動態解析、環境變數或配置檔 |
| **安全防禦** | 危險任意執行 | 檢查 `eval()`, `exec()`, `os.system()` | `[BLOCKER]` | 改用 `subprocess.run([...])` 或安全解析庫 |
| **控制流** | 巢狀 `if` 深度 $> 2$ | 遍歷 `ast.If` 計算縮排層次（平級 `elif` 放行） | `[ADVISORY]` | 使用 Guard Clause 提早 return 扁平化 |
| **可靠性** | 生產環境 `assert` | 檢查非測試程式碼中的 `ast.Assert` | `[ADVISORY]` | 改用 `if not cond: raise DomainError(...)` |
| **架構規模** | 檔案行數 $> 200$ 行 | 計算檔案總行數 | `[ADVISORY]` | 若非核心 Engine，建議評估模組化拆分 |
| **依賴管理** | 重度外部套件 | 檢查 `requests`, `pandas`, `numpy` 等引用 | `[ADVISORY]` | 優先評估是否能以標準庫（`urllib`, `json`）替代 |

---

## 四、 生產級實戰代碼完整對比（結帳服務）

### ❌ 違規代碼（Junior / 存在 7 項違規 / `audit.py` FAIL）

```py
import os

def calculate_tax(amount): return amount * 0.05
def calculate_tax(amount): return amount * 0.10  # ❌ 違規 1：同名覆蓋
PAYMENT_CONFIG = {"timeout": 30, "timeout": 60}   # ❌ 違規 2：重複 Key

def checkout(order, coupons=[], is_vip=False):     # ❌ 違規 3：可變預設；違規 4：布林盲
    assert order is not None                       # ❌ 違規 5：生產 assert
    if order.get("status") == "pending":           # ❌ 違規 6：巢狀深度 > 2 + 純計算偷渡 I/O
        if order.get("amount") > 0 and not order.get("is_frozen"):
            os.system(f"curl -X POST https://api.bank.com/pay -d id={order.get('id')}")
            try: return {"id": order.get("id"), "paid": True}
            except: pass                           # ❌ 違規 7：裸 except 吞信號
    return None
```

### ✅ 資深代碼（Senior / 100% 通過 7 大法則與 `audit.py` PASS）

```python
#!/usr/bin/env python3
from enum import StrEnum
from dataclasses import dataclass
from typing import Protocol
from decimal import Decimal

class OrderStatus(StrEnum):
    PENDING = "pending"; PAID = "paid"; FROZEN = "frozen"

@dataclass(frozen=True)
class Order:
    order_id: str; amount: Decimal; status: OrderStatus; is_frozen: bool = False

@dataclass(frozen=True)
class CheckoutDecision:
    order_id: str; final_amount: Decimal

class CheckoutError(Exception):
    def __init__(self, order_id: str, msg: str):
        super().__init__(f"Order '{order_id}' failed: {msg}")

class PaymentGateway(Protocol):
    def charge(self, order_id: str, amount: Decimal) -> str: ...

# 純決策核心 (Guard Clauses + 數值下限防呆 + 零副作用)
def calculate_checkout_decision(order: Order, *, discount: Decimal = Decimal("0")) -> CheckoutDecision:
    if order.status != OrderStatus.PENDING or order.is_frozen:
        raise CheckoutError(order.order_id, "Order not ready for checkout")
    if order.amount <= Decimal("0"):
        raise CheckoutError(order.order_id, "Order amount must be positive")
    
    final = max(Decimal("0"), order.amount - discount)  # 物理下限防呆
    return CheckoutDecision(order_id=order.order_id, final_amount=final)

# 副作用外殼 (Keyword-Only + 例外鏈)
def process_checkout(order: Order, gateway: PaymentGateway, *, discount: Decimal = Decimal("0")) -> CheckoutDecision:
    decision = calculate_checkout_decision(order, discount=discount)
    try:
        gateway.charge(decision.order_id, decision.final_amount)
    except Exception as err:
        raise CheckoutError(decision.order_id, f"Gateway fault: {err}") from err
    return decision
```

---

## 五、 Vibe Coding 最佳實戰協同工作流（4 步起手 SOP）

在人機結對開發中，遵循標準的「立規矩 $\to$ 定規格 $\to$ 切小塊 $\to$ 聽診收尾」SOP 提示詞閉環：

### 1. Step 1（立規矩 - Baseline Setup）
* **動作**：專案根目錄部署規則檔，錨定 `senior_coding_laws`（禁止未經宣告依賴、開啟強型別、禁刪既有驗證）。
* **Prompt 範本**：
  > 「本專案強制遵守 Senior 7 Coding Laws 與最小依賴原則，請保持原生標準庫優先，嚴禁未宣告之第三方套件。」

### 2. Step 2（定規格 - Law 3: Spec-First）
* **動作**：需求輸入後，強制鎖定介面與模型，先校準認知邊界。
* **Prompt 範本**：
  > 「請先不要寫任何具體業務實作代碼。請先為我規劃資料結構（Schema/Models/Dataclass）與 API 契約介面（Protocol），確認骨架無誤後我們再動工。」

### 3. Step 3（切小塊 - Law 7: Chunking）
* **動作**：規格鎖定後，要求 AI 將實作拆解為 3～5 個原子任務（Milestones），一步一步驗收。
* **Prompt 範本**：
  > 「請將此功能拆解為 3 個獨立的原子步驟。現在只執行第一步：建立純運算決策函式與單元驗證，不要一次產生所有代碼。」

### 4. Step 4（自動防線 - Remediation Ladder）
* **動作**：代碼產出後立即在終端機執行客觀安檢。若亮紅燈，嚴格對照 `remediation_guide.md` 進行 1 對 1 根因替換。
* **驗收指令**：
```bash
# 稽核 Python 腳本或規格文件 (<20ms)
python3 ~/.gemini/config/skills/audit-skill/scripts/audit.py /path/to/script.py

# 稽核前端腳本
python3 ~/.gemini/config/skills/audit-skill/scripts/audit_frontend.py /path/to/app.ts
```

---

## 六、 結論與核心思維總結

1. **心法先行**：在編寫代碼的第一秒就考慮認知負擔、Spec-First、Chunking 與 Pragmatic Boundary，杜絕大模型在 Vibe Coding 時漫無目的代碼膨脹與過度工程。
2. **機器底線**：在代碼存檔交付的最後一刻，以 <20ms 的 AST 靜態解析攔截所有低級語法陷阱（重複覆蓋、可變預設、裸 Except）與資安硬編碼。
3. **急救收斂**：安檢亮紅燈時，堅持核心根因修復（Root Cause），杜絕呼叫端散落打補丁。
4. **三權合一閉環**：既保有 Vibe Coding 的極速靈動，又守住企業級系統的強韌品質與資安護欄。
