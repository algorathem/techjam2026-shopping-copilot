from __future__ import annotations

import unittest

from starter.agent import Agent, SessionState, classify_constraint


class SlotParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.state = SessionState(profile={"preference_tags": ["fit"]})
        self.agent = Agent.__new__(Agent)
        self.agent._products = {}

    def test_buying_extracts_category_and_hard_requirement(self) -> None:
        self.agent._ingest(
            self.state,
            "I'm looking for Jewelry Necklaces. A key requirement is: Material:alloy.",
        )
        self.assertEqual(self.state.category, "Jewelry Necklaces")
        self.assertTrue(any("alloy" in item.lower() for item in self.state.constraints))
        self.assertFalse(self.state.browsing)
        self.assertEqual(self.state.constraint_sources[-1], "disclosed")

    def test_override_clears_soft_keeps_disclosed(self) -> None:
        # Simulate respond() appending before ingest.
        self.state.messages.append("I'm looking for Belts. I prefer a different style.")
        self.agent._ingest(self.state, self.state.messages[-1])
        self.state.messages.append("For that, what matters is: solid brass buckle.")
        self.agent._ingest(self.state, self.state.messages[-1])
        self.assertTrue(any("style" in c.lower() or "different" in c.lower() for c in self.state.constraints))
        self.assertTrue(any("brass" in c.lower() for c in self.state.constraints))

        self.state.messages.append(
            "Actually, ignore my earlier preference. What I need is: 100% Leather."
        )
        self.agent._ingest(self.state, self.state.messages[-1])

        self.assertTrue(self.state.override_applied)
        self.assertTrue(any("leather" in item.lower() for item in self.state.constraints))
        self.assertTrue(any("brass" in item.lower() for item in self.state.constraints))
        self.assertFalse(any("different style" in item.lower() for item in self.state.constraints))
        # Soft tokens blocked; disclosed/override tokens remain queryable.
        terms = set(self.agent._query_terms(self.state))
        self.assertIn("leather", terms)
        self.assertIn("brass", terms)
        self.assertNotIn("different", terms)
        # Asks reset so `other` can fire again for remaining slots.
        self.assertEqual(self.state.asked, [])
        self.assertEqual(self.agent._next_ask(self.state, turn=4), "other")

    def test_override_blocks_discarded_message_history(self) -> None:
        self.state.messages.append("I'm looking for Hats. neon pink party design.")
        self.agent._ingest(self.state, self.state.messages[-1])
        self.state.messages.append(
            "Actually, ignore my earlier preference. What I need is: 100% Acrylic."
        )
        self.agent._ingest(self.state, self.state.messages[-1])
        terms = set(self.agent._query_terms(self.state))
        self.assertIn("acrylic", terms)
        self.assertNotIn("neon", terms)
        self.assertNotIn("pink", terms)
        self.assertNotIn("party", terms)

    def test_boundary_marks_dont_care(self) -> None:
        self.agent._ingest(self.state, "I don't have a preference for color; please use your judgment.")
        self.assertIn("color", self.state.dont_care)

    def test_other_is_first_question(self) -> None:
        ask = self.agent._next_ask(self.state, turn=1)
        self.assertEqual(ask, "other")

    def test_static_order_after_other(self) -> None:
        self.state.asked.append("other")
        ask = self.agent._next_ask(self.state, turn=2, ranked=[("A", 1.0)])
        self.assertEqual(ask, "color")

    def test_pool_swap_helper_promotes_when_default_uncovered(self) -> None:
        self.agent._products = {
            "A": {"facets": {"material": "leather"}},
            "B": {"facets": {"material": "cotton"}},
            "C": {"facets": {"material": "leather"}},
            "D": {"facets": {"material": "cotton"}},
        }
        ranked = [("A", 10.0), ("B", 9.0), ("C", 8.0), ("D", 7.0)]
        candidates = ["color", "material", "style"]
        ask = self.agent._pool_swap_ask("color", candidates, ranked)
        self.assertEqual(ask, "material")

    def test_classify_budget_and_material(self) -> None:
        self.assertEqual(classify_constraint("budget around $54.97"), "budget")
        self.assertEqual(classify_constraint("100% Leather"), "material")
        self.assertEqual(classify_constraint("Triple Moon Pentagram Symbol"), "feature")

    def test_extract_facets_reads_color_and_material(self) -> None:
        facets = Agent._extract_facets(
            "black leather hiking boots for outdoor use",
            store="TrailCo",
            price=79.0,
            title="TrailCo Leather Boot",
        )
        self.assertEqual(facets["color"], "black")
        self.assertEqual(facets["material"], "leather")
        self.assertEqual(facets["use_case"], "hiking")
        self.assertEqual(facets["brand"], "trailco")
        self.assertIsNotNone(facets["budget"])


if __name__ == "__main__":
    unittest.main()
