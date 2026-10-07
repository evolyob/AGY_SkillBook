# Senior Clean Code Radar: Practical Examples

Empirical Before/After case studies for `senior_coding_laws.md`.

---

## 1. Step 1: Own the Boundary & Dict Lookups

### Case 1.1: Standard Library First (CSV Parsing)
> **Concrete Flaw**: Imports heavy third-party dependency (`pandas`) merely to compute a sum from a CSV file (bloats dependencies, inflates container size, slows startup).

#### Before (Over-engineered third-party dependency)
```python
import pandas as pd

def sum_sales(path: str) -> float:
    df = pd.read_csv(path)
    return float(df["amount"].sum())
```
#### After (Standard Library First)
```python
import csv

def sum_sales(path: str) -> float:
    with open(path, newline="", encoding="utf-8") as f:
        return sum(float(row["amount"]) for row in csv.DictReader(f))
```

### Case 1.2: Single-Pass Indexing
> **Concrete Flaw**: Nested `for` loops perform $O(N \times M)$ pairwise scans (degrades to millions of iterations on moderate datasets instead of an $O(N+M)$ single-pass dictionary lookup).

#### Before (Brute-force nested loops O(N*M))
```python
def match_order_items(orders: list[dict], products: list[dict]) -> list[tuple]:
    matched = []
    for order in orders:
        for product in products:
            if order["product_id"] == product["id"]:
                matched.append((order, product))
    return matched
```
#### After (Single-pass hash map index O(N+M))
```python
def match_order_items(orders: list[dict], products: list[dict]) -> list[tuple]:
    product_map = {p["id"]: p for p in products}
    return [
        (order, product_map[order["product_id"]])
        for order in orders
        if order.get("product_id") in product_map
    ]
```

### Case 1.3: Filesystem Traversal Prevention
> **Concrete Flaw**: Constructs filesystem paths using raw string interpolation `f"uploads/{filename}"` without root containment checks (allows arbitrary file read via `../../etc/passwd`).

#### Before (Vulnerable path concatenation)
```python
def read_asset(filename: str) -> str:
    path = f"uploads/{filename}"
    with open(path, encoding="utf-8") as f:
        return f.read()
```
#### After (Boundary validation with Path.is_relative_to)
```python
from pathlib import Path

def read_asset(filename: str, *, base_dir: Path = Path("uploads")) -> str:
    base = base_dir.resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"Path traversal detected: {filename}")
    return target.read_text(encoding="utf-8")
```

---

## 2. Step 2: Pure Core & Constrained States

### Case 2.1: Functional Core & Imperative Shell
> **Concrete Flaw**: Inlines database write calls inside a filtering loop and uses a mutable default argument `status_log=[]` (leaks state across invocations, couples business rules directly to I/O).

#### Before (Mixed side-effects & mutable default argument)
```python
def process_orders(orders: list, status_log: list = []) -> list:
    for order in orders:
        if order.get("status") == "completed":
            status_log.append(order["id"])
            db.update_order(order["id"])  # Side-effect inside calculation
    return status_log
```
#### After (Pure functional core separated from outer I/O shell)
```python
from enum import StrEnum

class OrderStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"

# Pure Functional Core (deterministic, zero side-effects)
def filter_completed_order_ids(orders: list[dict]) -> list[str]:
    return [o["id"] for o in orders if o.get("status") == OrderStatus.COMPLETED]

# Imperative Shell (handles I/O at boundary)
def sync_completed_orders(orders: list[dict], db) -> list[str]:
    completed_ids = filter_completed_order_ids(orders)
    for order_id in completed_ids:
        db.update_order(order_id)
    return completed_ids
```

### Case 2.2: Defensive Mathematical Clamping
> **Concrete Flaw**: Performs unchecked subtraction on intervals or dimensions without a lower floor (risks producing negative timeouts, intervals, or geometry).

#### Before (Unchecked arithmetic producing negative intervals)
```python
def calculate_next_interval(current_interval: int, backoff_reduction: int) -> int:
    return current_interval - backoff_reduction
```
#### After (Clamped bounds guaranteeing valid geometry/timeout)
```python
MIN_INTERVAL_SEC = 1

def calculate_next_interval(current_interval: int, backoff_reduction: int) -> int:
    return max(MIN_INTERVAL_SEC, current_interval - backoff_reduction)
```

---

## 3. Step 3: Flattened Flow & Intent Naming

### Case 3.1: Guard Clauses & Keyword-Only Flags
> **Concrete Flaw**: Deeply nested `if` blocks obscure the happy path, while unlabelled positional booleans (`force`) cause call-site ambiguity.

#### Before (Deep nesting & boolean blindness)
```python
def dispatch_task(task: dict | None, force: bool):
    if task:
        if task.get("ready"):
            if force or task.get("priority", 0) > 10:
                execute(task)
```
#### After (Guard clauses & keyword-only flags)
```python
def dispatch_task(task: dict | None, *, force: bool = False) -> None:
    if not task or not task.get("ready"):
        return
    if not force and task.get("priority", 0) <= 10:
        return
    execute(task)
```

### Case 3.2: Structural Pattern Matching
> **Concrete Flaw**: Long `elif` ladders check raw strings and perform manual dictionary key lookups (fragile against missing keys, verbosely unwraps nested payloads).

#### Before (Repeated elif string dispatch ladder)
```python
def handle_event(event: dict) -> None:
    event_type = event.get("type")
    if event_type == "click":
        handle_click(event.get("x", 0), event.get("y", 0))
    elif event_type == "keypress":
        handle_key(event.get("key", ""))
```
#### After (Structural match...case dispatch)
```python
def handle_event(event: dict) -> None:
    match event:
        case {"type": "click", "x": int(x), "y": int(y)}:
            handle_click(x, y)
        case {"type": "keypress", "key": str(k)}:
            handle_key(k)
        case _:
            pass
```

---

## 4. Step 4: Useful Errors & Observability

### Case 4.1: Operational Context & Causality Chaining
> **Concrete Flaw**: Catches broad `Exception` and returns empty strings (silently swallows root cause failures, making production incidents un-debuggable).

#### Before (Silent error swallowing)
```python
import urllib.request

def load_remote_config(url: str) -> str:
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8")
    except Exception:
        return ""
```
#### After (Contextual message with exception chaining)
```python
import urllib.error
import urllib.request

def load_remote_config(url: str, *, retry_count: int = 0) -> str:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as err:
        raise RuntimeError(
            f"Config fetch failed: url='{url}', retry_count={retry_count}"
        ) from err
```

---

## 5. Step 5: Contract Closure & Delete-List

### Case 5.1: Subtractive Engineering (Direct Root Invocation)
> **Concrete Flaw**: Introduces multi-tier factory and wrapper classes for a single consumer (inflates cognitive overhead and creates speculative boilerplate).

#### Before (Sprawling single-caller wrappers and factories)
```python
class TextSanitizerFactory:
    def create_sanitizer(self):
        return TextSanitizerWrapper()

class TextSanitizerWrapper:
    def sanitize(self, text: str) -> str:
        return text.strip().replace("\r\n", "\n")

sanitizer = TextSanitizerFactory().create_sanitizer()
cleaned = sanitizer.sanitize(raw_text)
```
#### After (Direct root invocation: net negative lines)
```python
def sanitize_text(text: str) -> str:
    return text.strip().replace("\r\n", "\n")

cleaned = sanitize_text(raw_text)
```


