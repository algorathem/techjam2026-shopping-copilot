from __future__ import annotations

import unittest

from starter.agent import Agent, SessionState, classify_constraint


class SlotParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.state = SessionState(profile={"preference_tags": ["fit"]})
        self.agent = Agent.__new__(Agent)

    def test_buying_extracts_category_and_hard_requirement(self) -> None:
        self.agent._ingest(
            self.state,
            "I'm looking for Jewelry Necklaces. A key requirement is: Material:alloy.",
        )
        self.assertEqual(self.state.category, "Jewelry Necklaces")
        self.assertTrue(any("alloy" in item.lower() for item in self.state.constraints))
        self.assertFalse(self.state.browsing)

    def test_override_clears_old_constraints(self) -> None:
        self.agent._ingest(self.state, "I'm looking for Belts. I prefer a different style.")
        self.agent._ingest(
            self.state,
            "Actually, ignore my earlier preference. What I need is: 100% Leather.",
        )
        self.assertTrue(any("leather" in item.lower() for item in self.state.constraints))
        self.assertNotIn("I prefer a different style.", self.state.constraints)

    def test_boundary_marks_dont_care(self) -> None:
        self.agent._ingest(self.state, "I don't have a preference for color; please use your judgment.")
        self.assertIn("color", self.state.dont_care)

    def test_other_is_first_question(self) -> None:
        ask = self.agent._next_ask(self.state, turn=1)
        self.assertEqual(ask, "other")

    def test_classify_budget_and_material(self) -> None:
        self.assertEqual(classify_constraint("budget around $54.97"), "budget")
        self.assertEqual(classify_constraint("100% Leather"), "material")
        self.assertEqual(classify_constraint("Triple Moon Pentagram Symbol"), "feature")


if __name__ == "__main__":
    unittest.main()
