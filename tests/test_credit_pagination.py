"""Pagination must cover every line and logo without clipping."""
import unittest
from cadenza.export import credit_pages


class CreditPaginationTests(unittest.TestCase):
    def assert_covered(self, atoms, pages):
        for top, bottom in atoms:
            self.assertTrue(any(start <= top + .01 and bottom <= start + height + .01
                                for start, height in pages), (top, bottom, pages))
        for start, height in pages:
            self.assertLessEqual(height, 650.01)
            self.assertFalse(any(a + .01 < start < b - .01 for a, b in atoms))

    def test_groups_stay_together_when_minimum_page_count_allows(self):
        atoms = [(0, 100), (156, 256), (264, 450), (506, 606), (614, 800)]
        pages = credit_pages(atoms, [(156, 450), (506, 800)])
        self.assertEqual(len(pages), 2)
        self.assert_covered(atoms, pages)
        for a, b in [(156, 450), (506, 800)]:
            self.assertTrue(any(start <= a and b <= start + height for start, height in pages))

    def test_oversized_group_splits_between_lines_with_minimum_pages(self):
        atoms = [(n * 34, n * 34 + 34) for n in range(50)]
        pages = credit_pages(atoms, [(0, 1700)])
        self.assertEqual(len(pages), 3)
        self.assert_covered(atoms, pages)

    def test_unbreakable_logo_taller_than_page_is_reported(self):
        with self.assertRaisesRegex(ValueError, 'taller'):
            credit_pages([(0, 700)], [(0, 700)])

    def test_empty_credits_still_produce_one_page(self):
        self.assertEqual(credit_pages([], []), [(0, 650)])
