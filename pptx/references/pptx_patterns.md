# PPTX Core Visual Primitive Skeletons (`pptx_patterns.md`)

> **Role**: Ultra-compact declarative Python slide recipe skeletons for 16:9 presentations.

---

## 1. `kpi_row` (3 Metric Badges)
```python
engine.create_slide(title="...", subtitle="...", layers=[{
    "height": 5.0,
    "cols": [
        {"type": "kpi", "label": "Metric 1", "val": "99.9%", "chg": "▲ +0.5%", "icon": "gauge", "note": "Target: 99.0%"},
        {"type": "kpi", "label": "Metric 2", "val": "4.2m", "chg": "▼ -65%", "icon": "timer", "note": "Baseline: 12m"},
        {"type": "kpi", "label": "Metric 3", "val": "$2.8M", "chg": "▲ OK", "icon": "coin", "note": "Target Exceeded"}
    ]
}])
```

---

## 2. `card_grid` (3 or 4 Column Pillar Cards)
```python
engine.create_slide(title="...", subtitle="...", layers=[{
    "height": 5.0, "weights": [1, 1, 1],
    "cols": [
        {"title": "Pillar 1", "tag": "CORE", "icon": "shield", "body": ["• Item 1", "• Item 2"]},
        {"title": "Pillar 2", "tag": "AUTO", "icon": "gear", "body": ["• Item 1", "• Item 2"]},
        {"title": "Pillar 3", "tag": "RESP", "icon": "lock", "body": ["• Item 1", "• Item 2"]}
    ]
}])
```

---

## 3. `split_row` (50/50 Compare / Boundary Split)
```python
engine.create_slide(title="...", subtitle="...", layers=[{
    "height": 5.0, "weights": [1, 1],
    "cols": [
        {"title": "Left Scope", "tag": "STATE A", "icon": "alert-triangle", "body": ["• Fact 1", "• Fact 2"]},
        {"title": "Right Scope", "tag": "STATE B", "icon": "shield-check", "body": ["• Fact 1", "• Fact 2"]}
    ]
}])
```

---

## 4. `anchor_card` (Central Anchor + Supporting Cards)
```python
engine.create_slide(title="...", subtitle="...", layers=[
    {"height": 2.2, "cols": [{"title": "Core Anchor Mandate", "tag": "MANDATE", "icon": "star", "body": ["• Central foundational baseline"]}]},
    {"height": 2.8, "weights": [1, 1], "cols": [
        {"title": "Domain Pillar A", "tag": "DOMAIN", "icon": "server", "body": ["• Item 1", "• Item 2"]},
        {"title": "Domain Pillar B", "tag": "DOMAIN", "icon": "database", "body": ["• Item 1", "• Item 2"]}
    ]}
])
```

---

## 5. `pipeline_flow` (Linear Horizontal SOP Flow)
```python
engine.create_slide(title="...", subtitle="...", layers=[{
    "height": 5.0,
    "content": {
        "type": "flow",
        "steps": [
            {"step": "PHASE 1", "title": "Intake", "icon": "paper-plane", "color": engine.t["p"]},
            {"step": "PHASE 2", "title": "Verify", "icon": "shield-check", "color": engine.t["s"]},
            {"step": "PHASE 3", "title": "Deploy", "icon": "rocket-launch", "color": engine.t["a"]},
            {"step": "PHASE 4", "title": "Archive", "icon": "recycle", "color": engine.t["ok"]}
        ]
    }
}])
```

---

## 6. `checklist_grid` (Dual-Column Readiness Gates)
```python
engine.create_slide(title="...", subtitle="...", layers=[{
    "height": 5.0, "weights": [1, 1],
    "cols": [
        {"title": "Security Gate", "tag": "GATE", "icon": "shield-check", "body": ["• ✓ TLS 1.3 enforced", "• ✓ Zero high CVEs", "• ✖ Read-only FS pending"]},
        {"title": "Operations Gate", "tag": "GATE", "icon": "gauge", "body": ["• ✓ Unit tests pass", "• ✓ Latency <50ms", "• ✓ On-call rotation active"]}
    ]
}])
```

---

## 7. `matrix` (2x2 Quadrant Decision Grid)
```python
engine.create_slide(title="...", subtitle="...", layers=[
    {
        "height": 2.4, "section_tag": "▲ High Impact", "weights": [1, 1],
        "cols": [
            {"title": "P0: Quick Wins", "tag": "LOW COST", "color": engine.t["ok"], "body": ["• Action 1", "• Action 2"]},
            {"title": "P1: Strategic Bets", "tag": "HIGH COST", "color": engine.t["p"], "body": ["• Action 1", "• Action 2"]}
        ]
    },
    {
        "height": 2.4, "section_tag": "▼ Low Impact", "weights": [1, 1],
        "cols": [
            {"title": "P2: Routine", "tag": "LOW COST", "color": engine.t["s"], "body": ["• Action 1", "• Action 2"]},
            {"title": "P3: Defer", "tag": "HIGH COST", "color": engine.t["alert"], "body": ["• Action 1", "• Action 2"]}
        ]
    }
])
```
