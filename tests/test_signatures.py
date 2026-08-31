from __future__ import annotations

import os
import unittest

from starter.signatures import (
    SignatureIndex,
    product_signature_strings,
    signature_bonus,
    signatures_enabled,
)


class SignatureIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.products = {
            "moon": {
                "parent_asin": "moon",
                "title": "Celtic Knot Triple Moon Pendant",
                "categories": ["Women", "Jewelry", "Necklaces"],
                "features": [
                    "Material:alloy",
                    "Triple Moon Pentagram Symbol",
                    "Imported",
                ],
                "details": {"Department": "womens"},
                "store": "QIAN0813",
                "description": "",
                "price": 12.0,
            },
            "tee": {
                "parent_asin": "tee",
                "title": "Grandma Long Sleeve T-Shirt",
                "categories": ["Women", "Novelty"],
                "features": ["cotton", "Imported", "Zipper closure"],
                "details": {},
                "store": "Generic",
                "description": "",
                "price": 19.0,
            },
        }

    def test_unique_feature_line_has_df_one(self) -> None:
        index = SignatureIndex()
        for asin, product in self.products.items():
            index.add(asin, product)
        index.freeze()
        key, asins, df = index.lookup("Triple Moon Pentagram Symbol")
        self.assertEqual(asins, ["moon"])
        self.assertEqual(df, 1)
        self.assertIn("triple moon", key)

    def test_generic_imported_is_ignored(self) -> None:
        index = SignatureIndex()
        for asin, product in self.products.items():
            index.add(asin, product)
        index.freeze()
        _key, asins, df = index.lookup("Imported")
        self.assertEqual(asins, [])
        self.assertEqual(df, 0)

    def test_rare_match_boosts_unique_asin(self) -> None:
        index = SignatureIndex()
        for asin, product in self.products.items():
            index.add(asin, product)
        index.freeze()
        hit = index.match(["Triple Moon Pentagram Symbol", "Material:alloy"])
        self.assertIn("moon", hit["asins"])
        self.assertIn("moon", hit["intersect"])
        self.assertGreater(signature_bonus("moon", hit), signature_bonus("tee", hit))

    def test_intent_card_style_material_prefix(self) -> None:
        texts = product_signature_strings(self.products["moon"])
        lowered = [t.lower() for t in texts]
        self.assertTrue(any("material:alloy" in t.replace(" ", "") or "alloy" in t for t in lowered))

    def test_env_disable(self) -> None:
        prev = os.environ.get("SHOPPILOT_SIGNATURES")
        os.environ["SHOPPILOT_SIGNATURES"] = "0"
        try:
            self.assertFalse(signatures_enabled())
        finally:
            if prev is None:
                os.environ.pop("SHOPPILOT_SIGNATURES", None)
            else:
                os.environ["SHOPPILOT_SIGNATURES"] = prev


if __name__ == "__main__":
    unittest.main()
