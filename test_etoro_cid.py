"""Tests for the payload-scanning logic, which is the only part that runs offline."""

import unittest

from etoro_cid import find_usernames


class FindUsernamesTest(unittest.TestCase):
    def test_finds_nested_username(self):
        payload = {"Data": {"Profile": {"UserName": "SomeTrader"}}}
        self.assertEqual(find_usernames(payload), ["SomeTrader"])

    def test_matches_key_regardless_of_case(self):
        payload = [{"username": "a"}, {"GurusUsername": "b"}]
        self.assertEqual(find_usernames(payload), ["a", "b"])

    def test_deduplicates_while_preserving_order(self):
        payload = {"a": {"Username": "dup"}, "b": [{"Username": "dup"}, {"Username": "other"}]}
        self.assertEqual(find_usernames(payload), ["dup", "other"])

    def test_ignores_empty_and_non_string_values(self):
        payload = {"Username": "", "OwnerUsername": None, "Nested": {"Username": "real"}}
        self.assertEqual(find_usernames(payload), ["real"])

    def test_returns_empty_when_absent(self):
        self.assertEqual(find_usernames({"CID": 44260918, "Positions": []}), [])


if __name__ == "__main__":
    unittest.main()
