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
##############################################################################
#                                                                            #
# Copyright (c) 2013, Tony Fischetti                                         #
#                                                                            #
# MIT License, http://www.opensource.org/licenses/mit-license.php            #
#                                                                            #
# Permission is hereby granted, free of charge, to any person obtaining a    #
# copy of this software and associated documentation files (the "Software"), #
# to deal in the Software without restriction, including without limitation  #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,   #
# and/or sell copies of the Software, and to permit persons to whom the      #
# Software is furnished to do so, subject to the following conditions:       #
#                                                                            #
# The above copyright notice and this permission notice shall be included in #
# all copies or substantial portions of the Software.                        #
#                                                                            #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,   #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL    #
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING    #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER        #
# DEALINGS IN THE SOFTWARE.                                                  #
#                                                                            #
##############################################################################


"""
Various actions that the main entry delegates to
"""

import networkx as nx
import os.path
import re
from subprocess import Popen
import sys


def escp(target_name):
    """
    This function is used by sake help. Since sakefiles allow
    for targets with spaces in them, sake help needs to quote
    all targets with spaces. This takes a target name and
    quotes it if necessary
    """
    if ' ' in target_name:
        return '"{}"'.format(target_name)
    return target_name


def print_help(sakefile):
    """
    Prints the help string of the Sakefile, prettily

    Args:
        A dictionary that is the parsed Sakefile (from sake.py)

    Returns:
        0 if all targets have help messages to print,
        1 otherwise
    """
    full_string = "You can 'sake' one of the following...\n\n"
    errmes = "target '{}' is not allowed to not have help message\n"
    for target in sakefile:
        if target == "all":
            # this doesn't have a help message
            continue
        if "formula" not in sakefile[target]:
            # this means it's a meta-target
            full_string += "{}:\n  - {}\n\n".format(escp(target),
                                                    sakefile[target]["help"])
            for atom_target in sakefile[target]:
                if atom_target == "help":
                    continue
                full_string += "    "
                full_string += "{}:\n      -  {}\n".format(escp(atom_target),
                                       sakefile[target][atom_target]["help"])
            full_string += "\n"
        else:
            full_string += "{}:\n  - {}\n\n".format(escp(target),
                                                    sakefile[target]["help"])
    what_clean_does = "remove all targets' outputs and start from scratch"
    full_string += "clean:\n  -  {}\n\n".format(what_clean_does)
    what_visual_does = "output visual representation of project's dependencies"
    full_string += "visual:\n  -  {}\n".format(what_visual_does)
    print(full_string)


def expand_macros(raw_text):
    """
    This gets called before the Sakefile is parsed. It looks for
    macros defined anywhere in the Sakefile (the start of the line
    is '#!') and then replaces all occurences of '$variable' with thr
    value defined in the macro. It then returns the contents of the
    file with the macros expanded
    """
    # gather macros
    macros = {}
    for line in raw_text.split("\n"):
        if re.search("^#!", line):
            var, val = re.search("^#!\s*(\w+)\s*=\s*(\S+)", line).group(1, 2)
            macros[var] = val
    for var in macros:
        raw_text = raw_text.replace("$"+var, macros[var])
    return raw_text


def check_for_dep_in_outputs(dep, verbose, G):
    """
    Function to help construct_graph() identify dependencies

    Args:
        A dependency
        A flag indication verbosity
        A (populated) NetworkX DiGraph

    Returns:
        A list of targets that build given dependency

    """
    if verbose:
        print "checking dep {}".format(dep)
    ret_list = []
    for node in G.nodes(data=True):
        if "output" not in node[1]:
            continue
        if dep in node[1]['output']:
            ret_list.append(node[0])
    return ret_list

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
                data_dict = sakefile[target][atomtarget]
                data_dict["parent"] = target
                G.add_node(atomtarget, data_dict)
        else:
            if verbose:
                print("Adding '{}'".format(target))
            G.add_node(target, sakefile[target])
    if verbose:
        print("Nodes are built\nBuilding connections")
    for node in G.nodes(data=True):
        if verbose:
            print "checking node {} for dependencies".format(node[0])
        if "dependencies" not in node[1]:
            continue
        if verbose:
            print "it has dependencies"
        connects = []
        for dep in node[1]['dependencies']:
            matches = check_for_dep_in_outputs(dep, verbose, G)
            if not matches:
                continue
            for match in matches:
                if verbose:
                    print("Appending {} to matches".format(match))
                connects.append(match)
        if connects:
            for connect in connects:
                G.add_edge(connect, node[0])
    return G

def clean_all(G):
    """
    Removes all the output files from all targets. Takes
    the graph as the only argument
    """
    all_outputs = []
    for node in G.nodes(data=True):
        if "output" in node[1]:
            for item in node[1]["output"]:
                all_outputs.append(item)
    all_outputs.append(".shastore")
    for item in all_outputs:
        if os.path.isfile(item):
            command = "rm {}".format(item)
            print command
            p = Popen(command, shell=True)
            p.communicate()
            if p.returncode:
                sys.stdout.write("Command failed to run\n")
                sys.exit(1)


def visualize(G, verbose, filename="dependencies.png"):
    """
    Uses networkX's inteface with matplotlib to draw

    Args:
        a NetworkX DiGraph

    Returns:
        0 if everything worked
        1 if otherwise
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        sys.stderr.write("Matplotlib required for visualization\n")
        return 1
    except RuntimeError:
        sys.stderr.write("Matplotlib had a runtime error\n")
        return 1
    pos = nx.spring_layout(G)
    nx.draw(G, pos, node_color="pink", node_size=1000, font_size=8)
    plt.savefig(filename)
    return 0

