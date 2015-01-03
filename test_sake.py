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
import textwrap

from testlib import utobjs

# test UNICODE!!!

def setup_module(module):
    module.mock_sakefile_for_macros = utobjs.mock_sakefile_for_macros
    module.mock_sakefile_for_help = utobjs.mock_sakefile_for_help
    module.expected_help = utobjs.expected_help
    os.mkdir("./tmp")
    with open("./tmp/file1.txt", "w") as fh:
        fh.write("1")
    with open("./tmp/file2.txt", "w") as fh:
        fh.write("2")
    with open("./tmp/file1.json", "w") as fh:
        fh.write("1")


def teardown_module(module):
    del module.mock_sakefile_for_macros
    del module.mock_sakefile_for_help
    del module.expected_help
    shutil.rmtree("./tmp/")


def test_acts_clean_path():
    unixpath1 = "/home/krsone/Pictures/../Desktop/"
    unixpath2 = "/home/krsone/Pictures/./me.jpg"
    windowspath1 = "C:/User/scottlarock/Pictures/../Desktop/"
    windowspath2 = "C:\\User/scottlarock/Pictures/./me.png"

    assert acts.clean_path(unixpath2, force_os="posix",
                           force_start=posixpath.normpath(unixpath1))\
           == "../Pictures/me.jpg"
    assert acts.clean_path(windowspath2, force_os="windows",
                           force_start=ntpath.normpath(windowspath1))\
           == '..\\Pictures\\me.png'


def test_acts_escp():
    has_no_space = "ask"
    has_one_space = "rusholme ruffians"
    has_two_cons_spaces = "shakespeare's  sister"
    has_more_spaces_and_unicode = " well i wønder"
    assert acts.escp(has_no_space) == "ask"
    assert acts.escp(has_two_cons_spaces) == "\"shakespeare's  sister\""
    assert acts.escp(has_one_space) == "\"rusholme ruffians\""
    assert acts.escp(has_more_spaces_and_unicode) == "\" well i wønder\""


def test_acts_expand_macros():
    # ATTENTION:
    #   there is a bug in python's template substitution that
    #   prevents certain unicode-heavy strings from being replaced
    #   so 'rΩsholme' won't be subsituted, but it should be
    temp = ["---", "#!ask=shyness is nice", "$ask me, ask me, $ask me",
            "there are ruffians in $rusholme ($rΩsholme) and they steal $$",
            "$askme, ${ask}me", "..."]
    temp = mock_sakefile_for_macros+"\n".join(temp)
    solution = ["---", "#!ask=shyness is nice", "shyness is nice me, ask me, shyness is nice me",
                    "there are ruffians in $rusholme ($rΩsholme) and they steal $",
                    "$askme, shyness is niceme", "..."]
    solution = mock_sakefile_for_macros+"\n".join(solution)
    assert acts.expand_macros(temp)[0] == solution


def test_acts_get_help():
    assert acts.get_help(yaml.load(mock_sakefile_for_help)) == expected_help


def test_acts_get_all_outputs():
    assert sorted(acts.get_all_outputs({'output': ['./tmp/*']})) ==\
           sorted(['./tmp/file1.txt', './tmp/file2.txt', './tmp/file1.json'])
    assert sorted(acts.get_all_outputs({'output': ['./tmp/file1.*']})) ==\
           sorted(['./tmp/file1.txt', './tmp/file1.json'])
    assert sorted(acts.get_all_outputs({'output': ['./tmp/*.txt']})) ==\
           sorted(['./tmp/file1.txt', './tmp/file2.txt'])
    assert acts.get_all_outputs({'output': ['./tmp/*.json']}) ==\
           ['./tmp/file1.json']
    assert acts.get_all_outputs({'output': ['./tmp/file2.txt']}) ==\
           ['./tmp/file2.txt']
    # these are not proper globs so they just return the thing
    assert acts.get_all_outputs({'output': ['./tmp/sile123']}) ==\
           ['./tmp/sile123']
    assert acts.get_all_outputs({'output': ['./tmp/sile1.*']}) ==\
           ['./tmp/sile1.*']


def test_acts_patterns():
    assert acts.expand_patterns('echo %.txt', {'dependencies': 'tmp/%.txt', 'formula': 'echo tmp/%.txt'}) == {'echo %.txt': {
        'dependencies': 'tmp/%.txt',
        'formula': 'echo tmp/%.txt'
    }}
