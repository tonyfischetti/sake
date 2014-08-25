#!/usr/bin/env python -tt


import unittest
from sakelib import acts


# test UNICODE!!!


class TestActsFunction(unittest.TestCase):

    def setUp(self):
        # for mock sakefile 1
        lines = ["---", "#!ask=shyness is nice",
                 "  ", "#!rusholme = at the last night      ",
                 "panic #! streets= london, burmingham",
                 " #! asleep =sing me to sleep",
                 "..."]
        self.mock_sakefile_1 = "\n".join(lines)
        print(self.mock_sakefile_1)
        print(acts.gather_macros(self.mock_sakefile_1))


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
