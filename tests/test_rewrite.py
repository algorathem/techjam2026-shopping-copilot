from __future__ import annotations

import unittest

from starter.llm_rerank import _parse_asins
from starter.rewrite import rephrase_brief, rephrase_terms


class RewriteTest(unittest.TestCase):
    def test_drops_imported_and_keeps_material(self) -> None:
        terms = rephrase_terms(
            "Walking Shoes",
            ["100% Textile", "Imported", "mesh slip on"],
            ["comfort"],
        )
        self.assertIn("mesh", terms)
        self.assertIn("textile", terms)
        self.assertNotIn("imported", terms)
        self.assertTrue(terms.index("mesh") < terms.index("walking") or "mesh" in terms[:6])

    def test_brief_includes_constraints(self) -> None:
        brief = rephrase_brief("Belts", ["100% Leather"], set(), ["style"])
        self.assertIn("Leather", brief)
        self.assertIn("Belts", brief)

    def test_parse_asins_json_array(self) -> None:
        allowed = {"B1", "B2", "B3"}
        order = _parse_asins('Here you go: ["B2", "B1"]', allowed)
        self.assertEqual(order, ["B2", "B1"])


if __name__ == "__main__":
    unittest.main()
