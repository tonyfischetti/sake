#!/usr/bin/env python

###########################################################
##                                                       ##
##   acts.py                                             ##
##                                                       ##
##                Author: Tony Fischetti                 ##
##                        tony.fischetti@gmail.com       ##
##                                                       ##
###########################################################
#
# Copyright (c) 2013, Tony Fischetti
#
# MIT License, http://www.opensource.org/licenses/mit-license.php
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
###########################################################

"""
Various actions that the main entry delegates to
"""

import sys
import networkx as nx


def print_help(sakefile):
    """
    Prints the help string of the Sakefile, prettily

    Args:
        A dictionary that is the parsed Sakefile (from sake.py)

    Returns:
        0 if all targets have help messages to print,
        1 otherwise
    """
    full_string = "\n"
    errmes = "target '{}' is not allowed to not have help message\n"
    for target in sakefile:
        if target == "all":
            # this doesn't have a help message
            continue
        if "formula" not in sakefile[target]:
            # this means it's a meta-target
            full_string += "{}:\n  - {}\n\n".format(target,
                                                    sakefile[target]["help"])
            for atom_target in sakefile[target]:
                if atom_target == "help":
                    continue
                full_string += "    "
                full_string += "{}:\n      -  {}\n".format(atom_target,
                                       sakefile[target][atom_target]["help"])
            full_string += "\n"
        else:
            full_string += "{}:\n  - {}\n\n".format(target,
                                                    sakefile[target]["help"])
    print(full_string)




def construct_graph(sakefile, verbose, G):
    """
    Takes the sakefile dictionary and builds a NetworkX graph

    Args:
        A dictionary that is the parsed Sakefile (from sake.py)
        A flag indication verbosity
        A NetworkX GiGraph object to populate

    Returns:
        A NetworkX graph
    """
    if verbose:
        print("Going to construct Graph")
    for target in sakefile:
        if target == "all":
            # we don't want this node
            continue
        if "output" not in sakefile[target]:
            # that means this is a meta target
            for atomtarget in sakefile[target]:
                if atomtarget == "help":
                    continue
                if verbose:
                    print("Adding '{}'".format(atomtarget))
                G.add_node(atomtarget, sakefile[target][atomtarget])
        else:
            if verbose:
                print("Adding '{}'".format(target))
            G.add_node(target, sakefile[target])
    if verbose:
        print("Graph is built")
    return G


def build_all(sakefile, verbose):
    """
    Builds all targets (all in "all" target, anyway)

    Args:
        A dictionary that is the parsed Sakefile (from sake.py)
        A flag indicating verbosity
    Returns:
        True is successful, False otherwise
    """
    if verbose:
        print("Call to build_all issued")
    pass


def visualize(sakefile, verbose):
    """
    Uses networkX's inteface with matplotlib 

    Args:

    Returns:

    Raises:


    """
    pass














