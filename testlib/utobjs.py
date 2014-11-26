#!/usr/bin/env python -tt
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
This holds mock objects for the unittests
"""

mock_sakefile_for_macros = """---
#!ask=$hyness is nice
  
#!rΩsholme = at the last night      
panic #! streets= london, burmingham
 #! asleep =sing me to sleep
..."""

mock_sakefile_for_help = """first☼:
    help: this is first
    formula: >
        echo "this is first" > first.txt
    output:
        - first.txt

outer:
    help: >
        this is an outer one
    inner:
        help: this is the inner
        dependencies:
            - first.txt
        formula: echo "this is the inner"
"""

expected_help = """You can 'sake' one of the following...

first☼:
  - this is first

outer:
  - this is an outer one

    inner:
      -  this is the inner

clean:
  -  remove all targets' outputs and start from scratch

visual:
  -  output visual representation of project's dependencies
"""

poemyaml = """!!python/object:networkx.classes.digraph.DiGraph
adj: &id001
  combine them:
    upper case it: &id006 {}
  first line:
    combine them: &id002 {}
  fourth line:
    combine them: &id003 {}
  second line:
    combine them: &id004 {}
  third line:
    combine them: &id005 {}
  upper case it: {}
edge: *id001
graph: {}
node:
  combine them:
    dependencies: [first.txt, second.txt, third.txt, fourth.txt]
    formula: 'cat first.txt second.txt third.txt fourth.txt > poem.txt;

      '
    help: combine all the lines
    output: [poem.txt]
  first line:
    achtung: 'because this has an empty (but present) dependencies field, it should
      not run everytime sake is called

      '
    dependencies: []
    formula: 'sleep 5; echo Twinkle twinkle little bat > first.txt;

      '
    help: prints the first line
    output: [first.txt]
    parent: line by line
  fourth line:
    formula: 'sleep 5; echo Like a tea tray in the sky > fourth.txt

      '
    help: prints the fourth line
    output: [fourth.txt]
    parent: line by line
  second line:
    formula: 'sleep 5; echo How I wonder what youre at > second.txt

      '
    help: prints the second line
    output: [second.txt]
    parent: line by line
  third line:
    formula: 'sleep 5; echo Up above the world you fly > third.txt

      '
    help: prints the third line
    output: [third.txt]
    parent: line by line
  upper case it:
    dependencies: [poem.txt]
    formula: 'cat poem.txt | tr ''[a-z]'' ''[A-Z]'' | cowsay

      '
    help: convert the poem to upper case
pred:
  combine them:
    first line: *id002
    fourth line: *id003
    second line: *id004
    third line: *id005
  first line: {}
  fourth line: {}
  second line: {}
  third line: {}
  upper case it:
    combine them: *id006
succ: *id001
"""
