"""Tests for optional LLM slot NLU gating (no network required)."""
from __future__ import annotations

import unittest

from starter.llm_slots import (
    apply_slot_parse,
    llm_slots_mode,
    rule_nlu_confidence,
    should_call_slots_llm,
)
from starter.agent import SessionState


class LlmSlotsGateTests(unittest.TestCase):
    def test_default_mode_off(self) -> None:
        self.assertEqual(llm_slots_mode(), "off")

    def test_lowconf_triggers_on_dual_meaning(self) -> None:
        call, conf = should_call_slots_llm(
            "lowconf",
            "cute light dress shoes for my son",
            family=None,
            audience=None,
            n_new_constraints=0,
            filled_before=0,
            threshold=0.55,
        )
        self.assertTrue(call)
        self.assertLess(conf, 0.55)

    def test_lowconf_skips_kit_structured(self) -> None:
        call, conf = should_call_slots_llm(
            "lowconf",
            "For that, what matters is: black leather; size 9.",
            family="footwear",
            audience=None,
            n_new_constraints=2,
            filled_before=1,
            threshold=0.55,
        )
        self.assertFalse(call)
        self.assertGreaterEqual(conf, 0.55)

    def test_always_mode_always_wants_call(self) -> None:
        call, conf = should_call_slots_llm(
            "always",
            "black",
            family="dress",
            audience=None,
            n_new_constraints=1,
            filled_before=2,
        )
        self.assertTrue(call)

    def test_apply_slot_parse_validates(self) -> None:
        state = SessionState(profile={})
        n = apply_slot_parse(
            state,
            {
                "family": "footwear",
                "audience": "boys",
                "slots": [
                    {"attr": "color", "value": "black", "p": 0.9},
                    {"attr": "style", "value": "cute", "p": 0.8},
                    {"attr": "not_a_slot", "value": "x", "p": 0.99},
                    {"attr": "material", "value": "x", "p": 0.1},  # below min_p
                ],
            },
            min_p=0.55,
        )
        self.assertEqual(state.product_family, "footwear")
        self.assertEqual(state.audience, "boys")
        self.assertIn("color", state.filled)
        self.assertIn("style", state.filled)
        self.assertNotIn("material", state.filled)
        self.assertGreaterEqual(n, 2)

    def test_confidence_kit_high(self) -> None:
        c = rule_nlu_confidence(
            "I'm looking for Women Dresses. A key requirement is: cotton.",
            family="dress",
            audience=None,
            n_new_constraints=1,
            filled_before=0,
        )
        self.assertGreaterEqual(c, 0.7)


if __name__ == "__main__":
    unittest.main()
