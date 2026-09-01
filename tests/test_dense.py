from __future__ import annotations

import os
import tempfile
import unittest

from starter.dense import DenseIndex, encode_hash, query_text_from_state, dense_mode


class DenseBackendTest(unittest.TestCase):
    def test_hash_encode_is_unit_norm(self) -> None:
        vec = encode_hash("black leather hiking boots outdoor trail")
        norm = sum(v * v for v in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_similar_texts_outrank_unrelated(self) -> None:
        a = encode_hash("women ankle rain boots waterproof chelsea")
        b = encode_hash("womens waterproof chelsea rain boot ankle")
        c = encode_hash("men cotton graphic tee shirt grey grandma")
        def dot(x, y):
            return sum(i * j for i, j in zip(x, y))
        self.assertGreater(dot(a, b), dot(a, c))

    def test_query_text_joins_slots(self) -> None:
        text = query_text_from_state("walking shoes", ["breathable mesh", "black"], ["fit"])
        self.assertIn("walking", text)
        self.assertIn("mesh", text)
        self.assertIn("fit", text)

    def test_dense_mode_hash_forced(self) -> None:
        prev = os.environ.get("SHOPPILOT_DENSE")
        os.environ["SHOPPILOT_DENSE"] = "hash"
        try:
            self.assertEqual(dense_mode(), "hash")
        finally:
            if prev is None:
                os.environ.pop("SHOPPILOT_DENSE", None)
            else:
                os.environ["SHOPPILOT_DENSE"] = prev

    def test_dense_mode_auto_is_hash(self) -> None:
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy not installed")
        prev = os.environ.get("SHOPPILOT_DENSE")
        os.environ.pop("SHOPPILOT_DENSE", None)
        try:
            self.assertEqual(dense_mode(), "hash")
        finally:
            if prev is None:
                os.environ.pop("SHOPPILOT_DENSE", None)
            else:
                os.environ["SHOPPILOT_DENSE"] = prev

    def test_dense_mode_minilm_when_requested(self) -> None:
        try:
            import sentence_transformers  # noqa: F401
        except ImportError:
            self.skipTest("sentence-transformers not installed")
        prev = os.environ.get("SHOPPILOT_DENSE")
        os.environ["SHOPPILOT_DENSE"] = "minilm"
        try:
            self.assertEqual(dense_mode(), "minilm")
        finally:
            if prev is None:
                os.environ.pop("SHOPPILOT_DENSE", None)
            else:
                os.environ["SHOPPILOT_DENSE"] = prev

    def test_dense_mode_none(self) -> None:
        prev = os.environ.get("SHOPPILOT_DENSE")
        os.environ["SHOPPILOT_DENSE"] = "none"
        try:
            self.assertEqual(dense_mode(), "none")
            index = DenseIndex.build({"A": {"title": "x", "categories": [], "store": "", "text": "x"}}, backend="none")
            self.assertFalse(index.enabled)
            self.assertEqual(index.search("x"), [])
        finally:
            if prev is None:
                os.environ.pop("SHOPPILOT_DENSE", None)
            else:
                os.environ["SHOPPILOT_DENSE"] = prev

    def test_hash_index_search_returns_neighbors(self) -> None:
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy not installed")
        products = {
            "boot": {
                "title": "Women Ankle Rain Boots Waterproof Chelsea",
                "categories": ["Women", "Shoes", "Boots"],
                "store": "Asgard",
                "text": "rubber sole waterproof chelsea rain boot ankle",
            },
            "tee": {
                "title": "Funny Grandma Long Sleeve T-Shirt",
                "categories": ["Women", "Clothing", "Novelty"],
                "store": "Generic",
                "text": "cotton grey graphic tee grandma gift",
            },
            "jean": {
                "title": "Men Relaxed Boot Cut Jean",
                "categories": ["Men", "Clothing", "Jeans"],
                "store": "Ariat",
                "text": "100% cotton zipper closure boot cut jean",
            },
        }
        index = DenseIndex.build(products, backend="hash")
        self.assertTrue(index.enabled)
        hits = index.search("waterproof chelsea ankle rain boots for women", top_k=2)
        self.assertEqual(hits[0][0], "boot")

    def test_minilm_index_search_returns_neighbors(self) -> None:
        try:
            import numpy  # noqa: F401
            import sentence_transformers  # noqa: F401
        except ImportError:
            self.skipTest("sentence-transformers not installed")
        products = {
            "boot": {
                "title": "Women Ankle Rain Boots Waterproof Chelsea",
                "categories": ["Women", "Shoes", "Boots"],
                "store": "Asgard",
                "text": "rubber sole waterproof chelsea rain boot ankle",
            },
            "tee": {
                "title": "Funny Grandma Long Sleeve T-Shirt",
                "categories": ["Women", "Clothing", "Novelty"],
                "store": "Generic",
                "text": "cotton grey graphic tee grandma gift",
            },
            "jean": {
                "title": "Men Relaxed Boot Cut Jean",
                "categories": ["Men", "Clothing", "Jeans"],
                "store": "Ariat",
                "text": "100% cotton zipper closure boot cut jean",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            index = DenseIndex.build(products, cache_dir=tmp, backend="minilm")
            self.assertTrue(index.enabled)
            self.assertEqual(index.backend, "minilm")
            hits = index.search("waterproof chelsea ankle rain boots for women", top_k=2)
            self.assertEqual(hits[0][0], "boot")
            again = index.search("waterproof chelsea ankle rain boots for women", top_k=2)
            self.assertEqual(again[0][0], "boot")


if __name__ == "__main__":
    unittest.main()
