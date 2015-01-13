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
# Copyright (c) 2013, 2014, 2015, Tony Fischetti                             #
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
import itertools
import collections
import yaml

if sys.version_info[0] < 3:
    import codecs
    open = codecs.open


class PatternTemplate(string.Template):
    delimiter = "%"


def parse(file, text, includes):
    try:
        sakefile = yaml.load(text) or {}
    except yaml.YAMLError as exc:
        sys.stderr.write("Error: {} failed to parse as valid YAML\n".format(file))
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            sys.stderr.write("Error near line {}\n".format(str(mark.line+1)))
        sys.exit(1)
    for filename, (subdata, subincludes) in includes.items():
        sakefile.update(parse(filename, subdata, subincludes))
    return sakefile


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
            innerstr = "{}:\n  - {}\n\n".format(escp(target),
                                                sakefile[target]["help"])
            inner = []
            for atom_target in sakefile[target]:
                if atom_target == "help":
                    continue
                inner.append("    {}:\n      -  {}\n\n".format(escp(atom_target),
                                                               sakefile[target][atom_target]["help"]))
            if inner:
                innerstr += '\n'.join(sorted(inner))
            middle_lines.append(innerstr)
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


def expand_macros(raw_text, macros={}):
    """
    this gets called before the sakefile is parsed. it looks for
    macros defined anywhere in the sakefile (the start of the line
    is '#!') and then replaces all occurences of '$variable' with the
    value defined in the macro. it then returns the contents of the
    file with the macros expanded.
    """
    includes = {}
    result = []
    pattern = re.compile("#!\s*(\w+)\s*=\s*(.+$)", re.UNICODE)
    ipattern = re.compile("#<\s*(\S+)\s*(optional|or\s+(.+))?$", re.UNICODE)
    for line in raw_text.split("\n"):
        line = string.Template(line).safe_substitute(macros)
        # note that the line is appended to result before it is checked for macros
        # this prevents macros expanding into themselves
        result.append(line)
        if line.startswith("#!"):
            match = pattern.match(line)
            try:
                var, val = match.group(1, 2)
            except:
                raise InvalidMacroError("Failed to parse macro {}\n".format(line))
            macros[var] = val
        elif line.startswith("#<"):
            match = ipattern.match(line)
            try:
                filename = match.group(1)
            except:
                raise IncludeError("Failed to parse include {}\n".format(line))
            try:
                with open(filename, 'r') as f:
                    includes[filename] = expand_macros(f.read(), macros)
            except IOError:
                if match.group(2):
                    if match.group(2).startswith('or '):
                        print(match.group(3))
                else:
                    raise IncludeError("Nonexistent include {}\n".format(filename))
    return "\n".join(result), includes


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


def get_patterns(dep):
    engine = PatternTemplate(dep)
    empty = True
    patterns = []
    for match in engine.pattern.finditer(dep):
        text = match.group("named") or match.group("braced")
        if text:
            empty = False
            patterns.append(text)
    if empty:
        return None, None
    else:
        return engine, patterns


def expand_patterns(name, target):
    data = collections.OrderedDict()
    if name == "all":
        return {name: target}
    elif "formula" not in target:
        # a meta-target
        res = {}
        for subname, subtarget in target.items():
            if subname == "help":
                res["help"] = subtarget
            else:
                res.update(expand_patterns(subname, subtarget))
        return {name: res}
    if "dependencies" not in target or not target["dependencies"]:
        return {name: target}
    for dep in target["dependencies"]:
        engine, patterns = get_patterns(dep)
        if not patterns:
            continue
        subs = {}
        for pat in patterns:
            subs[pat] = "(?P<%s>.+?)" % pat
        try:
            matcher = engine.substitute(dict(zip(patterns,
                                                 itertools.repeat("*"))))
            expanded = PatternTemplate(re.sub(r"\\(%|\{|\})", r"\1",
                                              re.escape(dep))).substitute(subs)
        except:
            sys.exit("Error parsing dependency patterns for target %s" % name)
        regex = re.compile(expanded)
        files = []
        for f in glob.iglob(matcher):
            match = regex.match(f)
            assert match
            for k, v in match.groupdict().items():
                if k not in data:
                    data[k] = [v]
                else:
                    data[k].append(v)
    if not data:
        return {name: target}
    # check for presence of output
    # it is not allowed to use a pattern
    # and not have outputs
    if "output" not in target or not target['output']:
        sys.exit("Target using pattern must have non-empty 'output' field")
    # based on http://stackoverflow.com/a/5228294/2097780
    product = (dict(zip(data, x)) for x in itertools.product(*data.values()))
    res = {}
    for sub in product:
        new_outputs = []
        new_deps = []
        new_name = PatternTemplate(name).safe_substitute(sub)
        if new_name == name:
            errmes = "Target {} that has pattern in dependencies must have "
            errmes += "pattern in name"
            sys.exit(errmes.format(name))
        new_help = PatternTemplate(target["help"]).safe_substitute(sub)
        new_formula = PatternTemplate(target["formula"]).safe_substitute(sub)
        for dep in target["dependencies"]:
            new_deps.append(PatternTemplate(dep).safe_substitute(sub))
        for out in target["output"]:
            new_outputs.append(PatternTemplate(out).safe_substitute(sub))
        res[new_name] = {"help": new_help,
                         "output": new_outputs,
                         "dependencies": new_deps,
                         "formula": new_formula}
    return res


def get_ties(G, verbose):
    """
    If you specify a target that shares a dependency with another target,
    both targets need to be updated. This is because running one will resolve
    the sha mismatch and sake will think that the other one doesn't have to
    run. This is called a "tie". This function will find such ties.
    """
    # we are going to make a dictionary whose keys are every dependency
    # and whose values are a list of all targets that use that dependency.
    # after making the dictionary, values whose length is above one will
    # be called "ties"
    ties = []
    dep_dict = {}
    for node in G.nodes(data=True):
        if 'dependencies' in node[1]:
            for item in node[1]['dependencies']:
                if item not in dep_dict:
                    dep_dict[item] = []
                dep_dict[item].append(node[0])
    for item in dep_dict:
        if len(list(set(dep_dict[item]))) > 1:
            ties.append(list(set(dep_dict[item])))
    return ties


def get_tied_targets(original_targets, the_ties):
    """
    This function gets called when a target is specified to ensure
    that all 'tied' targets also get included in the subgraph to
    be built
    """
    my_ties = []
    for original_target in original_targets:
        for item in the_ties:
            if original_target in item:
                for thing in item:
                    my_ties.append(thing)
    my_ties = list(set(my_ties))
    if my_ties:
        ties_message = ""
        ties_message += "The following targets share dependencies and must be run together:"
        for item in sorted(my_ties):
            ties_message += "\n  - {}".format(item)
        return list(set(my_ties+original_targets)), ties_message
    return original_targets, ""


def construct_graph(sakefile, verbose):
    """
    Takes the sakefile dictionary and builds a NetworkX graph

    Args:
        A dictionary that is the parsed Sakefile (from sake.py)
        A flag indication verbosity

    Returns:
        A NetworkX graph
    """
    G = nx.DiGraph()
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


def get_all_dependencies(node_dict):
    """
    ...............................
    """
    deplist = []
    for item in node_dict['dependencies']:
        glist = glob.glob(item)
        if glist:
            for oneglob in glist:
                deplist.append(oneglob)
        else:
            deplist.append(item)
    return deplist


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
    for item in sorted(all_outputs):
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
                errmes = "Error: file '{}' failed to be removed\n"
                sys.stderr.write(errmes.format(item))
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
            for edge in sorted(edge_list):
                source, targ = edge
                node_list = node_list - set(source)
                node_list = node_list - set(targ)
                line = '"{}" -> "{}";\n'
                fh.write(line.format(source, targ))
        # draw nodes with no links
        if node_list:
            for node in sorted(node_list):
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
    renderer = "svg"
    if re.search("\.jpg$", filename, re.IGNORECASE):
        renderer = "jpg"
    elif re.search("\.jpeg$", filename, re.IGNORECASE):
        renderer = "jpg"
    elif re.search("\.svg$", filename, re.IGNORECASE):
        renderer = "svg"
    elif re.search("\.png$", filename, re.IGNORECASE):
        renderer = "png"
    elif re.search("\.gif$", filename, re.IGNORECASE):
        renderer = "gif"
    elif re.search("\.ps$", filename, re.IGNORECASE):
        renderer = "ps"
    elif re.search("\.pdf$", filename, re.IGNORECASE):
        renderer = "pdf"
    else:
        renderer = "svg"
        filename += ".svg"
    command = "dot -T{} tempdot -o {}".format(renderer, filename)
    p = Popen(command, shell=True)
    p.communicate()
    if p.returncode:
        errmes = "Either graphviz is not installed, or its not on PATH"
        os.remove("tempdot")
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

class IncludeError(Error):
    def __init__(self, message):
        self.message = message

