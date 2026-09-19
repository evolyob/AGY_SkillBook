#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Engine & Invariant Verification Suite (test_engine.py)
Tests mathematical invariants, verifier sensitivity, scaffold self-consistency, and 1-page bounds.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import builder
import verifier
import preview_scaffold


class TestPdfEngineInvariants(unittest.TestCase):
    """Verifies core invariants of the PDF engine and tooling."""

    def test_geometry_calc_cols_conservation(self):
        """Invariant: sum of column widths + gaps must never exceed printable width."""
        total_w = 540.0
        gap = 10.0
        for n in [1, 2, 3, 4, 5]:
            cols = builder.calc_cols(total_w, n, gap=gap)
            actual_sum = sum(cols) + (n - 1) * gap
            self.assertAlmostEqual(actual_sum, total_w, places=2,
                                   msg=f"Column sum violated for n={n}")

        # Weights test
        weights = [0.65, 0.35]
        cols = builder.calc_cols(total_w, weights, gap=gap)
        actual_sum = sum(cols) + (len(weights) - 1) * gap
        self.assertAlmostEqual(actual_sum, total_w, places=2,
                               msg="Column sum violated for custom weights")

    def test_min_font_scale_invariant(self):
        """Invariant: Paragraph font size must strictly be >= 10.5pt."""
        p_small = builder._p("Small font test", sz=7.0)
        self.assertGreaterEqual(p_small.style.fontSize, 10.5)

        p_normal = builder._p("Normal font test", sz=14.0)
        self.assertEqual(p_normal.style.fontSize, 14.0)

    def test_verifier_catches_unclosed_div(self):
        """Gate 2: Verifier must reject markdown with unbalanced <div> tags."""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write("<div class='kpi-card'>Missing close tag")
            temp_path = f.name
        try:
            with self.assertRaises(ValueError):
                verifier.verify_md(temp_path, verbose=False)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_verifier_catches_buzzwords(self):
        """Gate 6/Detox: Verifier must detect forbidden AI buzzwords."""
        rules = {"hard_buzzwords_zh": ["閉環", "賦能"], "tech_terms_zh": {}}
        _, violations = verifier._check_md_detox("我們必須落地並形成閉環機制", rules)
        self.assertIn("閉環", violations)

    def test_scaffold_md_self_consistency(self):
        """Scaffold must generate clean Markdown that passes 5/5 verifier gates."""
        content = preview_scaffold.generate_scaffold(
            title="Integrity Test",
            subtitle="Self consistency validation",
            templates="all"
        )
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_path = f.name
        try:
            report = verifier.verify_md(temp_path, verbose=False)
            self.assertEqual(report["status"], "PASS")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_builder_generates_valid_pdf_1pager(self):
        """Builder must generate an A4 1-pager passing 6-Gate verifier."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_pdf = f.name
        try:
            story = [
                builder.build_document_header("Unit Test Header", "Testing PDF engine"),
                builder.build_pill_badge("【 I. KPI Baseline 】"),
                builder.build_kpi_row([
                    {"label": "Availability", "val": "99.99%", "chg": "+0.01%", "color": "emerald"},
                    {"label": "Latency", "val": "< 10ms", "chg": "-2ms", "color": "primary"}
                ]),
                builder.build_zebra_table(
                    headers=["Metric", "Status"],
                    rows=[["IAM", "Enforced"], ["DLP", "Compliant"]]
                )
            ]
            builder.generate_infographic_1pager(temp_pdf, story)
            report = verifier.verify_pdf(temp_pdf, verbose=False)
            self.assertEqual(report["pages"], 1)
            self.assertEqual(report["status"], "PASS")
        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)


if __name__ == "__main__":
    unittest.main()
