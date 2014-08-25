#!/usr/bin/env python -tt


import unittest
from sakelib import acts


# test UNICODE!!!


class TestActsFunction(unittest.TestCase):

    def test_escp(self):
        has_no_space = "ask"
        has_one_space = "rusholme ruffians"
        has_two_cons_spaces = "shakespeare's  sister"
        has_more_spaces_and_unicode = " well i wønder"
        self.assertEqual("ask", acts.escp(has_no_space))
        self.assertEqual("\"rusholme ruffians\"", acts.escp(has_one_space))
        self.assertEqual("\"shakespeare's  sister\"", acts.escp(has_two_cons_spaces))
        self.assertEqual("\" well i wønder\"", acts.escp(has_more_spaces_and_unicode))


if __name__ == '__main__':
    unittest.main()
