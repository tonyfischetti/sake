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
import string
import glob
import sys

if sys.version_info[0] < 3:
    import codecs
    open = codecs.open

def clean_path(a_path, force_os=None, force_start=None):
    """
    This function is used to normalize the path (of an output or
    dependency) and also provide the path in relative form. It is
    relative to the current working directory
    """
    if not force_start:
        force_start = os.curdir
    if force_os == "windows":
        import ntpath
        return ntpath.relpath(ntpath.normpath(a_path),
                             start=force_start)
    if force_os == "posix":
        import posixpath
        return posixpath.relpath(posixpath.normpath(a_path),
                                start=force_start)
    return os.path.relpath(os.path.normpath(a_path),
                          start=force_start)


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


def get_help(sakefile):
    """
    Returns the prettily formatted help strings (for printing)

    Args:
        A dictionary that is the parsed Sakefile (from sake.py)

    NOTE:
        the list sorting in this function is required for this
        function to be deterministic
    """
    full_string = "You can 'sake' one of the following...\n\n"
    errmes = "target '{}' is not allowed to not have help message\n"
    outerlines = []
    for target in sakefile:
        if target == "all":
            # this doesn't have a help message
            continue
        middle_lines = []
        if "formula" not in sakefile[target]:
            # this means it's a meta-target
            inner = "{}:\n  - {}\n\n".format(escp(target),
                                             sakefile[target]["help"])
            for atom_target in sakefile[target]:
                if atom_target == "help":
                    continue
                inner += "    {}:\n      -  {}\n\n".format(escp(atom_target), 
                                                         sakefile[target][atom_target]["help"])
            middle_lines.append(inner)
        else:
            middle_lines.append("{}:\n  - {}\n\n".format(escp(target),
                                                         sakefile[target]["help"]))
        if middle_lines:
            outerlines.append('\n'.join(sorted(middle_lines)))

    if outerlines:
        full_string += '\n'.join(sorted(outerlines))
    what_clean_does = "remove all targets' outputs and start from scratch"
    full_string += "\nclean:\n  -  {}\n\n".format(what_clean_does)
    what_visual_does = "output visual representation of project's dependencies"
    full_string += "visual:\n  -  {}\n".format(what_visual_does)
    full_string = re.sub("\n{3,}", "\n\n", full_string)
    return full_string


def gather_macros(raw_text):
    """
    this gets called before the sakefile is parsed. it looks for
    macros defined anywhere in the sakefile (the start of the line
    is '#!') and then stuffs them into a lookup dictionary for
    processing by "expand_macros"
    """
    macros = {}
    for line in raw_text.split("\n"):
        if re.search("^#!", line):
            pattern = re.compile("^#!\s*(\w+)\s*=\s*(.+$)", re.UNICODE)
            match = re.search(pattern, line)
            if match is None:
                raise InvalidMacroError("Failed to parse macro {}\n".format(line))
            try:
                var, val = match.group(1, 2)
            except:
                raise InvalidMacroError("Failed to parse macro {}\n".format(line))
            macros[var] = val
    return macros


def expand_macros(raw_text, macros):
    """
    this takes both the Sakefile raw text and  the macro lookup
    dictionary from "gather_macros" and then replaces all
    occurences of '$variable' with the value defined in the macro.
    it then returns the contents of the file with the macros expanded
    """
    return string.Template(raw_text).safe_substitute(macros)


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
        for k, v in node[1].items():
            if v is None: node[1][k] = []
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


def get_all_outputs(node_dict):
    """
    This function takes a node dictionary and returns a list of
    the node's output files. Some of the entries in the 'output'
    attribute may be globs, and without this function, sake won't
    know how to handle that. This will unglob all globs and return
    the true list of *all* outputs.
    """
    outlist = []
    for item in node_dict['output']:
        glist = glob.glob(item)
        if glist:
            for oneglob in glist:
                outlist.append(oneglob)
        else:
            outlist.append(item)
    return outlist


def clean_all(G, verbose, quiet, recon):
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
            for item in get_all_outputs(node[1]):
                all_outputs.append(item)
    all_outputs.append(".shastore")
    retcode = 0
    for item in all_outputs:
        if os.path.isfile(item):
            if recon:
                print("Would remove file: {}".format(item))
                continue
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
    if not retcode and not recon:
        print("All clean")
    return retcode


def write_dot_file(G, filename):
    """
    Writes the graph G in dot file format for graphviz visualization.

    Args:
        a Networkx graph
        A filename to name the dot files
    """
    with open(filename, "w", encoding="utf-8") as fh:
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



#####################
##  CUSTOM ERRORS  ##
#####################

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InvalidMacroError(Error):
    def __init__(self, message):
        self.message = message

