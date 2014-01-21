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
# Copyright (c) 2013, 2014, Tony Fischetti                                   #
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

from __future__ import unicode_literals
from __future__ import print_function
from subprocess import Popen
import networkx as nx
import codecs
import os
import re
import fnmatch
import sys

if sys.version_info[0] < 3:
    import codecs
    open = codecs.open

def clean_path(a_path):
    """
    This function is used to normalize the path (of an output or
    dependency) and also provide the path in relative form. It is
    relative to the current working directory
    """
    return os.path.relpath(os.path.normpath(a_path))


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
    is '#!') and then replaces all occurences of '$variable' with the
    value defined in the macro. It then returns the contents of the
    file with the macros expanded
    """
    # gather macros
    macros = {}
    for line in raw_text.split("\n"):
        if re.search("^#!", line):
            try:
                var, val = re.search("^#!\s*(\w+)\s*=\s*(.+$)",
                                     line).group(1, 2)
            except:
                sys.stderr.write("Failed to parse macro {}\n".format(line))
                sys.exit(1)
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
        print("checking dep {}".format(dep))
    ret_list = []
    for node in G.nodes(data=True):
        if "output" not in node[1]:
            continue
        for out in node[1]['output']:
            if fnmatch.fnmatch(out, dep):
                ret_list.append(node[0])
                break
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
        if "formula" not in sakefile[target]:
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
            print("checking node {} for dependencies".format(node[0]))
        # normalize all paths in output
        if "output" in node[1]:
            for index, out in enumerate(node[1]['output']):
                node[1]['output'][index] = clean_path(node[1]['output'][index])
        if "dependencies" not in node[1]:
            continue
        if verbose:
            print("it has dependencies")
        connects = []
        # normalize all paths in dependencies
        for index, dep in enumerate(node[1]['dependencies']):
            dep = os.path.normpath(dep)
            shrt = "dependencies"
            node[1]['dependencies'][index] = clean_path(node[1][shrt][index])
    for node in G.nodes(data=True):
        connects = []
        if "dependencies" not in node[1]:
            continue
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


def clean_all(G, verbose, quiet):
    """
    Removes all the output files from all targets. Takes
    the graph as the only argument

    Args:
        The networkx graph object
        A flag indicating verbosity
        A flag indicating quiet mode

    Returns:
        0 if successful
        1 if removing even one file failed
    """
    all_outputs = []
    for node in G.nodes(data=True):
        if "output" in node[1]:
            for item in node[1]["output"]:
                all_outputs.append(item)
    all_outputs.append(".shastore")
    retcode = 0
    for item in all_outputs:
        if os.path.isfile(item):
            if verbose:
                mesg = "Attempting to remove file '{}'"
                print(mesg.format(item))
            try:
                os.remove(item)
                if verbose:
                    print("Removed file")
            except:
                errmeg = "Error: file '{}' failed to be removed\n"
                sys.stderr.write(errmeg.format(item))
                retcode = 1
    if not retcode:
        print("All clean")
    return retcode


def write_dot_file(G, filename):
    """
    Writes the graph G in dot file format for graphviz visualization.

    Args:
        a Networkx graph
        A filename to name the dot files
    """
    fh = open(filename, "w", encoding="utf-8")
    fh.write("strict digraph DependencyDiagram {\n")
    edge_list = G.edges()
    node_list = set(G.nodes())
    if edge_list:
        for edge in G.edges():
            source, targ = edge
            node_list = node_list - set(source)
            node_list = node_list - set(targ)
            line = '"{}" -> "{}";\n'
            fh.write(line.format(source, targ))
    # draw nodes with no links
    if node_list:
        for node in node_list:
            line = '"{}"\n'.format(node)
            fh.write(line)
    fh.write("}")


def visualize(G, filename="dependencies", no_graphviz=False):
    """
    Uses networkX to draw a graphviz dot file either (a) calls the
    graphviz command "dot" to turn it into a SVG and remove the
    dotfile (default), or (b) if no_graphviz is True, just output
    the graphviz dot file

    Args:
        a NetworkX DiGraph
        a filename (a default is provided
        a flag indicating whether graphviz should *not* be called

    Returns:
        0 if everything worked
        will cause fatal error on failure
    """
    if no_graphviz:
        write_dot_file(G, filename)
        return 0
    write_dot_file(G, "tempdot")
    command = "dot -Tsvg tempdot -o {}.svg".format(filename)
    p = Popen(command, shell=True)
    p.communicate()
    if p.returncode:
        errmes = "Either graphviz is not installed, or its not on PATH"
        sys.stderr.write(errmes)
        sys.exit(1)
    os.remove("tempdot")
    return 0
