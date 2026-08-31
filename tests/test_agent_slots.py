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

    def test_boundary_no_pref_for_other_does_not_kill_catchall(self) -> None:
        # First ask is other; boundary replies "no preference for other".
        self.state.asked.append("other")
        self.agent._ingest(
            self.state,
            "I don't have a preference for other; please use your judgment.",
        )
        self.assertNotIn("other", self.state.dont_care)
        self.assertNotIn("other", self.state.asked)
        self.assertEqual(self.agent._next_ask(self.state, turn=2), "other")

    def test_boundary_no_pref_for_color_still_dont_care(self) -> None:
        self.agent._ingest(
            self.state,
            "I don't have a preference for color; please use your judgment.",
        )
        self.assertIn("color", self.state.dont_care)

    def test_infer_family_dress_vs_dress_sandals(self) -> None:
        from starter.agent import infer_product_family, product_family_match

        self.assertEqual(infer_product_family("a dress"), "dress")
        self.assertEqual(infer_product_family("dress sandals"), "footwear")
        self.assertEqual(infer_product_family("dress shoes"), "footwear")
        self.assertEqual(infer_product_family("black leather boots"), "footwear")

        dress_product = {
            "title": "Women Summer Maxi Dress Casual",
            "categories": ["Clothing", "Dresses", "Casual"],
        }
        sandal_product = {
            "title": "Women Dress Sandals Open Toe Heel",
            "categories": ["Shoes", "Sandals", "Heeled Sandals"],
        }
        self.assertEqual(product_family_match(dress_product, "dress"), "hit")
        self.assertEqual(product_family_match(sandal_product, "dress"), "miss")
        self.assertEqual(product_family_match(sandal_product, "footwear"), "hit")
        self.assertEqual(product_family_match(dress_product, "footwear"), "miss")

    def test_ingest_sets_dress_family(self) -> None:
        self.agent._ingest(self.state, "I'm looking for a dress, but I'm still exploring.")
        self.assertEqual(self.state.product_family, "dress")
        self.assertIn("dress", self.state.category.lower())


    def test_static_order_after_other(self) -> None:
        self.state.asked.append("other")
        # With SHOPPILOT_OTHER_TWICE (default on), a second other is allowed when
        # evidence is still thin; disable for the classic ladder assertion.
        import os

        os.environ["SHOPPILOT_OTHER_TWICE"] = "0"
        try:
            ask = self.agent._next_ask(self.state, turn=2, ranked=[("A", 1.0)])
            self.assertEqual(ask, "color")
        finally:
            os.environ.pop("SHOPPILOT_OTHER_TWICE", None)

    def test_other_twice_when_thin(self) -> None:
        import os

        self.state.asked.append("other")
        os.environ["SHOPPILOT_OTHER_TWICE"] = "1"
        try:
            ask = self.agent._next_ask(self.state, turn=2, ranked=[("A", 1.0)])
            self.assertEqual(ask, "other")
        finally:
            os.environ.pop("SHOPPILOT_OTHER_TWICE", None)

    def test_emit_top_k_precision_turns(self) -> None:
        import os

        os.environ["SHOPPILOT_PRECISION_TURNS"] = "2"
        os.environ["SHOPPILOT_PRECISION_MIN_CONS"] = "0"  # disable adaptive stretch
        try:
            self.assertEqual(self.agent._emit_top_k(self.state, turn=1, top_k=10), 1)
            self.assertEqual(self.agent._emit_top_k(self.state, turn=2, top_k=10), 1)
            self.assertEqual(self.agent._emit_top_k(self.state, turn=3, top_k=10), 10)
        finally:
            os.environ.pop("SHOPPILOT_PRECISION_TURNS", None)
            os.environ.pop("SHOPPILOT_PRECISION_MIN_CONS", None)

    def test_emit_top_k_adaptive_min_cons(self) -> None:
        import os

        os.environ["SHOPPILOT_PRECISION_TURNS"] = "2"
        os.environ["SHOPPILOT_PRECISION_MIN_CONS"] = "3"
        os.environ["SHOPPILOT_PRECISION_MAX"] = "5"
        try:
            self.state.constraints = ["black"]  # only 1
            self.assertEqual(self.agent._emit_top_k(self.state, turn=3, top_k=10), 1)
            self.state.constraints = ["black", "leather", "boots"]
            self.assertEqual(self.agent._emit_top_k(self.state, turn=3, top_k=10), 10)
        finally:
            os.environ.pop("SHOPPILOT_PRECISION_TURNS", None)
            os.environ.pop("SHOPPILOT_PRECISION_MIN_CONS", None)
            os.environ.pop("SHOPPILOT_PRECISION_MAX", None)

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

    def test_plus_then_petite_replaces_not_appends(self) -> None:
        from starter.agent import expand_constraint_phrases, _size_pole

        self.assertEqual(classify_constraint("party"), "style")
        self.assertEqual(classify_constraint("plus size"), "size")
        self.assertEqual(classify_constraint("petite"), "size")
        self.assertEqual(classify_constraint("cocktail"), "style")
        self.assertEqual(_size_pole("petite"), 1)
        self.assertEqual(_size_pole("plus size"), 0)

        self.agent._ingest(self.state, "I'm looking for a dress")
        self.agent._ingest(self.state, "plus size")
        self.assertEqual(self.state.constraints, ["plus size"])
        self.agent._ingest(self.state, "actually make it petite")
        # Contradictory size poles: petite replaces plus.
        self.assertTrue(any("petite" in c.lower() for c in self.state.constraints))
        self.assertFalse(any("plus" in c.lower() for c in self.state.constraints))

        atoms = expand_constraint_phrases("petite black cocktail")
        self.assertIn("petite", atoms)
        self.assertIn("black", atoms)
        self.assertIn("cocktail", atoms)

    def test_override_compound_splits_and_replaces_size(self) -> None:
        self.agent._ingest(self.state, "I'm looking for a dress")
        self.agent._ingest(self.state, "plus size")
        self.state.messages.append(
            "Actually, ignore my earlier preference. What I need is: petite black cocktail"
        )
        self.agent._ingest(self.state, self.state.messages[-1])
        self.assertTrue(self.state.override_applied)
        joined = " ".join(self.state.constraints).lower()
        self.assertIn("petite", joined)
        self.assertIn("black", joined)
        self.assertIn("cocktail", joined)
        self.assertNotIn("plus size", joined)


    def test_big_enough_is_size_not_feature(self) -> None:
        self.assertEqual(classify_constraint("needs to be big enough"), "size")
        self.assertEqual(classify_constraint("big enuf"), "size")
        self.assertEqual(classify_constraint("roomy"), "size")
        self.assertEqual(classify_constraint("large"), "size")
        self.assertEqual(classify_constraint("durable"), "feature")

        self.agent._ingest(self.state, "I'm looking for a backpack")
        self.state.asked.append("other")
        self.state.asked.append("style")
        self.agent._ingest(self.state, "needs to be big enough")
        self.assertIn("size", self.state.filled)
        self.assertNotEqual(self.agent._next_ask(self.state, turn=3), "size")
        self.state.asked.append("use_case")
        self.agent._ingest(self.state, "durable")
        ask = self.agent._next_ask(self.state, turn=4)
        self.assertNotEqual(ask, "size")

        self.agent._ingest(self.state, "I'm looking for a dress")
        self.state.asked.append("other")
        self.agent._ingest(self.state, "plus size")
        self.assertIn("size", self.state.filled)
        self.assertNotEqual(self.agent._next_ask(self.state, turn=2), "size")
        self.state.asked.append("color")
        self.agent._ingest(self.state, "party")
        self.assertIn("style", self.state.filled)
        ask = self.agent._next_ask(self.state, turn=3)
        self.assertNotEqual(ask, "style")
        self.assertNotEqual(ask, "size")


    def test_audience_son_not_womens(self) -> None:
        from starter.agent import infer_audience, product_audience_match

        self.assertEqual(infer_audience("shoes for my son"), "boys")
        self.assertEqual(infer_audience("for my daughter"), "girls")
        self.assertEqual(infer_audience("gift for him"), "men")
        self.assertEqual(infer_audience("for my wife"), "women")
        # Kit category openings must NOT set audience ("looking for Women Dresses").
        self.assertIsNone(infer_audience("I'm looking for Women Dresses, but I'm still exploring."))
        self.assertIsNone(infer_audience("I'm looking for Men Pants."))
        self.assertIsNone(infer_audience("women's size 8"))
        self.assertIsNone(infer_audience("for women"))  # too bare / category-like
        self.assertIsNone(infer_audience("for men"))
        women_prod = {
            "title": "Women's Running Shoe",
            "categories": ["Women", "Shoes", "Fashion Sneakers"],
        }
        men_prod = {
            "title": "Men's Trail Boot",
            "categories": ["Men", "Shoes", "Boots"],
        }
        boys_prod = {
            "title": "Boys Athletic Sneaker",
            "categories": ["Boys", "Shoes"],
        }
        self.assertEqual(product_audience_match(women_prod, "boys"), "miss")
        self.assertEqual(product_audience_match(boys_prod, "boys"), "hit")
        self.assertEqual(product_audience_match(men_prod, "men"), "hit")

        self.agent._ingest(self.state, "I'm looking for shoes for my son")
        self.assertEqual(self.state.audience, "boys")
        self.assertEqual(self.state.product_family, "footwear")

    def test_vibe_words_map_to_style(self) -> None:
        for vibe in ("cool", "cute", "professional", "elegant", "chic", "sporty"):
            self.assertEqual(classify_constraint(vibe), "style", vibe)
        self.agent._ingest(self.state, "I'm looking for a dress")
        self.state.asked.append("other")
        self.agent._ingest(self.state, "something cute and professional")
        self.assertIn("style", self.state.filled)
        self.assertNotEqual(self.agent._next_ask(self.state, turn=2), "style")

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
