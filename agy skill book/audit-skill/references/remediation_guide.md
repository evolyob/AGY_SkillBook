# Skill Quality & Remediation Action Runbook

> **執行方針**：本手冊為 `audit.py` 報警後的「直接動作指南（Action Runbook）」。只給具體執行動作（Action）與可直接複製的代碼範本，不講冗長理論。

---

## §1. 依賴黑戶（`undeclared external dependency`）

| 診斷條件 | 直接執行動作 (Direct Action) |
| :--- | :--- |
| **A. 這是本技能的核心腳本（真有用到）** | **動作**：直接在 `SKILL.md` 的 Frontmatter 補齊宣告：<br>```yaml<br>dependencies:<br>  - 套件名稱<br>``` |
| **B. 這是無關/遺留代碼（如 PPT 裡的 Word 腳本）** | **動作**：**直接刪除該檔案**（例如直接刪除 `docx.py`），切勿浪費時間重構無關代碼。 |
| **C. 本地自建的子套件模組誤判** | **動作**：改為顯式相對引用 `from .helpers import ...` 或於目錄補齊 `__init__.py`。 |

---

## §2. 行數超標（`Lines > dynamic limit`）

| 診斷條件 | 直接執行動作 (Direct Action) |
| :--- | :--- |
| **A. 與本技能無關的外來龐大檔案** | **動作**：**直接整檔刪除**（例如直接拔除未使用的 800 行外部 XSD 驗證器目錄）。 |
| **B. 核心業務腳本，且方法共用相同 Import** | **動作**：**🚫 嚴禁拆檔（切檔必虧）**。<br>將 10 個重複方法收斂為「1 個 Spec 規格字典 + 1 個通用迴圈函式」，立即蒸發 100 行。 |
| **C. 輕量前置檢驗（純 stdlib）與重型生成引擎** | **動作**：**✅ 允許拆檔**。<br>將 CLI 參數校驗（無三方庫）獨立成檔，換取 Cold Start 啟動加速。 |

---

## §3. 廢棄庫死庫（`Zero-EOL: removed stdlib module`）

* **動作**：依下表直接替換 Import，嚴禁額外安裝第三方廢棄包：
  * `import cgi` $\implies$ 改用 `import urllib.parse`
  * `import pipes` $\implies$ 改用 `import shlex`
  * `import distutils` $\implies$ 改用 `import setuptools` 或標準庫 `sys`

```text
# ❌ Anti-Pattern
import cgi, pipes
```
```python
# ✅ Remediation
import urllib.parse, shlex
```

---

## §4. 執行安全（`os.system` / `eval` / `exec`）

* **動作 1（`os.system`）**：直接改用結構化列表引數：
```text
# ❌ Anti-Pattern
import os; os.system(f"git status {target}")
```
```python
# ✅ Remediation
import subprocess
subprocess.run(["git", "status", target], check=True, capture_output=True, text=True)
```

* **動作 2（`eval` / `exec`）**：直接改用安全語法解析：
```text
# ❌ Anti-Pattern
val = eval(user_str)
```
```python
# ✅ Remediation
import ast
val = ast.literal_eval(user_str)
```

---

## §5. 檔案 I/O 編碼安全（`Unencoded open()`）

* **動作**：全檔搜尋 `open(` 並顯式補上 `encoding="utf-8"`（若含 BOM 則用 `"utf-8-sig"`）：

```text
# ❌ Anti-Pattern
with open("config.json", "r") as f: data = f.read()
```
```python
# ✅ Remediation
with open("config.json", "r", encoding="utf-8") as f: data = f.read()
```

---

## §6. 巢狀結構過深（`nested if-block depth > 2`）

* **動作**：直接在函式開頭**反轉條件提早 return**（Guard Clause），將縮排往左推平：

```text
# ❌ Anti-Pattern (Depth > 2)
def process(data):
    if data:
        if data.is_valid():
            if data.has_permission():
                return data.execute()
```
```python
# ✅ Remediation (Flatten via Guard Clause)
def process(data):
    if not data or not data.is_valid() or not data.has_permission():
        return None
    return data.execute()
```

---

## §7. 斷言與例外治理（`assert` / `bare except:`）

* **動作 1（正式環境 `assert`）**：改為標準例外拋出（避免被 `python -O` 消除）：
```text
# ❌ Anti-Pattern
assert user_id > 0, "Invalid ID"
```
```python
# ✅ Remediation
if user_id <= 0:
    raise ValueError(f"Invalid user_id: {user_id}")
```

* **動作 2（裸寫 `except:`）**：明確指定捕捉 `Exception`：
```text
# ❌ Anti-Pattern
try: do_something()
except: pass
```
```python
# ✅ Remediation
try: do_something()
except Exception as err: pass
```

---

## §8. 大型靜態資源（`Heavy static asset > 10KB`）

* **動作**：
  1. **禁止**在 Markdown 規格書中引用或印出全文（避免塞爆 LLM 上下文）。
  2. 保持為獨立磁碟檔案，由 Python 腳本於後端按需讀取與切片過濾。
