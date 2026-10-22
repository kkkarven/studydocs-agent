import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import familiar_store as familiar
import review_store as review


class StoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)

        root = Path(temporary.name)

        for module, attribute, path in [
            (familiar, "STATE_FILE", root / "familiar.json"),
            (review, "REVIEW_FILE", root / "review.json"),
        ]:
            patcher = patch.object(module, attribute, path)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_register_and_remove(self):
        self.assertEqual(familiar.list_familiar(), [])

        self.assertTrue(familiar.register_familiar("python_print.md"))
        self.assertFalse(familiar.register_familiar("python_print.md"))
        self.assertTrue(familiar.is_familiar("python_print.md"))
        self.assertEqual(familiar.list_familiar(), ["python_print.md"])

        self.assertTrue(familiar.unregister_familiar("python_print.md"))
        self.assertFalse(familiar.unregister_familiar("python_print.md"))
        self.assertEqual(familiar.list_familiar(), [])

    def test_unknown_item_is_rejected(self):
        with self.assertRaises(ValueError):
            familiar.register_familiar("unknown.md")

    def test_same_day_stable_and_additions_wait(self):
        familiar.register_familiar("python_print.md")
        familiar.register_familiar("python_dict_lookup.md")

        first = review.get_daily_review("2026-10-21")

        familiar.register_familiar("c_pointer_array.md")

        second = review.get_daily_review("2026-10-21")
        self.assertEqual(first, second)
        self.assertNotIn("c_pointer_array.md", second["items"])

        tomorrow = review.get_daily_review("2026-10-22")

        self.assertCountEqual(
            tomorrow["items"],
            [
                "python_print.md",
                "python_dict_lookup.md",
                "c_pointer_array.md",
            ],
        )

    def test_removed_items_are_not_replaced(self):
        familiar.register_familiar("python_print.md")
        review.get_daily_review("2026-10-21")

        familiar.unregister_familiar("python_print.md")
        familiar.register_familiar("python_dict_lookup.md")

        current = review.get_daily_review("2026-10-21")
        self.assertEqual(current["items"], [])

        familiar.register_familiar("python_print.md")

        again = review.get_daily_review("2026-10-21")
        self.assertEqual(again["items"], [])

    def test_empty_first_review_does_not_reserve_day(self):
        empty = review.get_daily_review("2026-10-21")

        self.assertEqual(empty["items"], [])
        self.assertFalse(review.REVIEW_FILE.exists())

        familiar.register_familiar("python_print.md")

        current = review.get_daily_review("2026-10-21")
        self.assertEqual(current["items"], ["python_print.md"])

    def test_corrupt_state_is_not_overwritten(self):
        familiar.STATE_FILE.write_text("{broken", encoding="utf-8")

        with self.assertRaises(ValueError):
            familiar.register_familiar("python_print.md")

        self.assertEqual(
            familiar.STATE_FILE.read_text(encoding="utf-8"),
            "{broken",
        )


if __name__ == "__main__":
    unittest.main()