import os
import unittest

from standardize_cities import CityLookup

HERE = os.path.dirname(os.path.abspath(__file__))
L = CityLookup(os.path.join(HERE, "city_lookup.csv"))


class MatchTests(unittest.TestCase):
    def test_exact_official(self):
        self.assertEqual(L.match("new york"), (1, "New York", "exact"))

    def test_alias_and_punctuation(self):
        self.assertEqual(L.match("N.Y.C."), (1, "New York", "exact"))
        self.assertEqual(L.match("  St.  Louis "), (4, "Saint Louis", "exact"))

    def test_accents_and_case(self):
        self.assertEqual(L.match("SAN FRANCÍSCO")[:2], (3, "San Francisco"))

    def test_fuzzy_typo(self):
        self.assertEqual(L.match("Los Angelas"), (2, "Los Angeles", "fuzzy"))

    def test_unmatched(self):
        self.assertEqual(L.match("Atlantis"), (None, None, "unmatched"))
        self.assertEqual(L.match(""), (None, None, "unmatched"))
        self.assertEqual(L.match(None), (None, None, "unmatched"))


if __name__ == "__main__":
    unittest.main()
