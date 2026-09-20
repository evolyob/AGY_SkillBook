import unittest
from pathlib import Path


class TestDeepModRouting(unittest.TestCase):
    """Unit tests validating deep-mod intent routing and keyword triggers."""

    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.skill_md = self.base_dir / "SKILL.md"
        self.archetypes_md = self.base_dir / "references" / "visual_archetypes.md"
        self.synthesis_md = self.base_dir / "references" / "synthesis_rules.md"

    def test_required_files_exist(self):
        self.assertTrue(self.skill_md.exists(), "SKILL.md must exist")
        self.assertTrue(self.archetypes_md.exists(), "visual_archetypes.md must exist")
        self.assertTrue(self.synthesis_md.exists(), "synthesis_rules.md must exist")

    def test_skill_purity_and_length(self):
        content = self.skill_md.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        self.assertLessEqual(len(lines), 50, "SKILL.md must be 50 lines or fewer")
        self.assertIn("## Objective", content)
        self.assertIn("## Execution Workflow", content)
        self.assertIn("dependencies: []", content)
        self.assertNotIn("version:", content, "version should not be in metadata")
        self.assertNotIn("show-me", content, "show-me should be generalized")

    def test_routing_keywords(self):
        content = self.skill_md.read_text(encoding="utf-8")
        for kw in ["diff", "review", "架構圖", "重構"]:
            self.assertIn(kw, content, f"Routing keyword '{kw}' must be present in SKILL.md")

    def test_visual_archetypes_defined(self):
        content = self.archetypes_md.read_text(encoding="utf-8")
        self.assertIn("Sub-track B1: Explore", content)
        self.assertIn("Sub-track B2: Diff", content)
        self.assertIn("Sub-track B3: Explain", content)
        self.assertIn("Minimal-Diff", content)


if __name__ == "__main__":
    unittest.main()
