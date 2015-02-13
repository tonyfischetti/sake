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
import pytest
import sys

from testlib.utobjs import *

# test UNICODE!!!

def setup_module(module):
    os.mkdir("./tmp")
    for file, data in ("./tmp/file1.txt", "1"), ("./tmp/file2.txt", "2"),\
                      ("./tmp/file1.json", "1"),\
                      ("./tmp/other.yaml", "#< missing.yaml optional\n#! a=1"),\
                      ("./tmp/bad.yaml", "#< x.yaml or Error!"):
        with open(file, "w") as fh:
            fh.write(data)


def teardown_module(module):
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


def test_acts_preprocess(capsys):
    # ATTENTION:
    #   there is a bug in python's template substitution that
    #   prevents certain unicode-heavy strings from being replaced
    #   so 'rΩsholme' won't be subsituted, but it should be
    temp = mock_sakefile_for_macros+textwrap.dedent('''
    ---
    #!ask=shyness is nice
    $ask me, ask me, $ask me
    there are ruffians and they steal $$
    ${ask}me
    ...
    '''.strip('\n'))
    solution = mock_sakefile_for_macros+textwrap.dedent('''
    ---
    #!ask=shyness is nice
    shyness is nice me, ask me, shyness is nice me
    there are ruffians and they steal $
    shyness is niceme
    ...
    '''.strip('\n'))
    assert acts.preprocess('.', temp)[0] == solution

    temp = textwrap.dedent('''
    #!this=1
    $thi
    '''.strip('\n'))

    with pytest.raises(acts.InvalidMacroError):
        acts.preprocess('.', temp)

    assert acts.preprocess('tmp', '#< other.yaml') ==\
           ('#< other.yaml', {'other.yaml': ('#< missing.yaml optional\n#! a=1', {})})

    with pytest.raises(acts.IncludeError):
        acts.preprocess('tmp', '#< missing.yaml')

    acts.preprocess('tmp', '#< missing.yaml or Error')
    assert capsys.readouterr() == ('Error\n', '')


@pytest.mark.xfail(raises=acts.InvalidMacroError,\
        reason="Python's string template module has bugs with unicode strings")
def test_acts_expand_macros_unicode():
    temp = mock_sakefile_for_macros+'there are ruffians in $rΩsholme'
    solution = mock_sakefile_for_macros+'there are ruffians in at the last night'
    assert acts.preprocess('.', temp)[0] == solution


def test_acts_get_help():
    assert acts.get_help(yaml.load(mock_sakefile_for_help)) == expected_help


def test_acts_get_all_outputs():
    assert sorted(acts.get_all_outputs({'output': ['./tmp/file*']})) ==\
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
    assert acts.expand_patterns('echo %.txt', {'dependencies': 'tmp/%.txt', 'formula': 'echo tmp/%.txt'}, {}) == ({'echo %.txt': {
        'dependencies': 'tmp/%.txt',
        'formula': 'echo tmp/%.txt'
    }}, False)
    # issue 50
    assert acts.expand_patterns('echo %f.x', {'dependencies': ['tmp/%f.x'],
           'formula': 'echo tmp/%f.x', 'output': ['tmp/%f.o'], 'help': ''}, {'':
                   {'output': ['tmp/y.x'], 'formula': 'xyz'}}) ==\
        ({'echo y.x': {'dependencies': ['tmp/y.x'], 'help': '',
                       'formula': 'echo tmp/y.x', 'output': ['tmp/y.o']}}, True)
