#!/usr/bin/env python -tt
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
from sakelib import acts
import yaml
import os
import shutil
import ntpath
import posixpath

from testlib import utobjs


# test UNICODE!!!


class TestActsFunction(unittest.TestCase):

    def setUp(self):
        self.mock_sakefile_for_macros = utobjs.mock_sakefile_for_macros
        self.mock_sakefile_for_help = utobjs.mock_sakefile_for_help
        self.expected_help = utobjs.expected_help
        # to hell with mock objects
        os.mkdir("./tmp")
        with open("./tmp/file1.txt", "w") as fh:
            fh.write("1")
        with open("./tmp/file2.txt", "w") as fh:
            fh.write("2")
        with open("./tmp/file1.json", "w") as fh:
            fh.write("1")
        
    def tearDown(self):
        del self.mock_sakefile_for_macros 
        del self.mock_sakefile_for_help 
        del self.expected_help 
        shutil.rmtree('./tmp/')

    def test_clean_path(self):
        unixpath1 = "/home/krsone/Pictures/../Desktop/"
        unixpath2 = "/home/krsone/Pictures/./me.jpg"
        windowspath1 = "C:/User/scottlarock/Pictures/../Desktop/"
        windowspath2 = "C:\\User/scottlarock/Pictures/./me.png"
        self.assertEqual(acts.clean_path(unixpath2,
                                         force_os="posix",
                                         force_start=posixpath.normpath(unixpath1)),
                         "../Pictures/me.jpg")
        self.assertEqual(acts.clean_path(windowspath2,
                                         force_os="windows",
                                         force_start=ntpath.normpath(windowspath1)),
                         "..\\Pictures\\me.png")

    def test_escp(self):
        has_no_space = "ask"
        has_one_space = "rusholme ruffians"
        has_two_cons_spaces = "shakespeare's  sister"
        has_more_spaces_and_unicode = " well i wønder"
        self.assertEqual("ask", acts.escp(has_no_space))
        self.assertEqual("\"rusholme ruffians\"", acts.escp(has_one_space))
        self.assertEqual("\"shakespeare's  sister\"", acts.escp(has_two_cons_spaces))
        self.assertEqual("\" well i wønder\"", acts.escp(has_more_spaces_and_unicode))

    def test_gather_macros(self):
        self.assertEqual(acts.gather_macros(self.mock_sakefile_for_macros),
                         {"ask": "$hyness is nice",
                          "rΩsholme": "at the last night      "})
        self.assertRaises(acts.InvalidMacroError,
                          acts.gather_macros,
                          "---\n#!f4I7 ur3=this should fail\n...")
        self.assertRaises(acts.InvalidMacroError,
                          acts.gather_macros,
                          "---\n#!===...")
        self.assertFalse(acts.gather_macros("---\nhandsome devil\n..."))

    def test_expand_macros(self):
        # ATTENTION:
        #   there is a bug in python's template substitution that
        #   prevents certain unicode-heavy strings from being replaced
        #   so 'rΩsholme' won't be subsituted, but it should be
        temp = ["---", "#!ask=shyness is nice", "$ask me, ask me, $ask me",
                "there are ruffians in $rusholme ($rΩsholme) and they steal $$",
                "$askme, ${ask}me", "..."]
        temp = "\n".join(temp)
        solution = ["---", "#!ask=shyness is nice", "$hyness is nice me, ask me, $hyness is nice me",
                    "there are ruffians in $rusholme ($rΩsholme) and they steal $",
                    "$askme, $hyness is niceme", "..."]
        solution = "\n".join(solution)
        self.assertEqual(acts.expand_macros(temp,
                                 acts.gather_macros(self.mock_sakefile_for_macros)),
                         solution)

    def test_get_help(self):
        self.assertEqual(acts.get_help(yaml.load(self.mock_sakefile_for_help)),
                         self.expected_help)

    def test_get_all_outputs(self):
        self.assertEqual(sorted(acts.get_all_outputs({'output': ['./tmp/*']})),
                         sorted(['./tmp/file1.txt',
                                 './tmp/file2.txt',
                                 './tmp/file1.json']))
        self.assertEqual(sorted(acts.get_all_outputs({'output': ['./tmp/file1.*']})),
                         sorted(['./tmp/file1.txt',
                                 './tmp/file1.json']))
        self.assertEqual(sorted(acts.get_all_outputs({'output': ['./tmp/*.txt']})),
                         sorted(['./tmp/file1.txt',
                                 './tmp/file2.txt']))
        self.assertEqual(acts.get_all_outputs({'output': ['./tmp/*.json']}),
                         ['./tmp/file1.json'])
        self.assertEqual(acts.get_all_outputs({'output': ['./tmp/file2.txt']}),
                         ['./tmp/file2.txt'])
        # these are not proper globs so they just return the thing
        self.assertEqual(acts.get_all_outputs({'output': ['./tmp/sile123']}),
                         ['./tmp/sile123'])
        self.assertEqual(acts.get_all_outputs({'output': ['./tmp/sile1.*']}),
                         ['./tmp/sile1.*'])



if __name__ == '__main__':
    unittest.main()
