#!/usr/bin/env python

###########################################################
##                                                       ##
##   build.py                                            ##
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
Various functions that perform the building with the
dependency resolution
"""

from __future__ import unicode_literals
from __future__ import print_function
import hashlib
import io
import networkx as nx
import os.path
import sys
import yaml
import glob
from subprocess import Popen, PIPE

import acts

if sys.version_info[0] < 3:
    import codecs
    old_open = open
    open = codecs.open
else:
    old_open = open


def get_sha(a_file):
    """
    Returns sha1 hash of the file supplied as an argument
    """
    try:
        the_hash = hashlib.sha1(old_open(a_file, "rb").read()).hexdigest()
    except IOError:
        errmes = "File '{}' could not be read! Exiting!\n".format(a_file)
        sys.stdout.write(errmes)
        sys.exit(1)
    except:
        errmes = "Unspecified error returning sha1 hash. Exiting!\n"
        sys.stdout.write(errmes)
        sys.exit(1)
    return the_hash


def write_shas_to_shastore(sha_dict):
    """
    Writes a sha1 dictionary stored in memory to
    the .shastore file
    """
    fh = open(".shastore", "w", encoding="utf-8")
    fh.write("---\n")
    if sha_dict:
        for key in sha_dict:
            fh.write("{}: {}\n".format(key, sha_dict[key]))
    fh.write("...")
    fh.close()


def take_shas_of_all_files(G, verbose):
    """
    Takes sha1 hash of all dependencies and outputs of all targets

    Args:
        The graph we are going to build
        A flag indicating verbosity

    Returns:
        A dictionary where the keys are the filenames and the
        value is the sha1 hash
    """
    sha_dict = {}
    all_files = []
    for target in G.nodes(data=True):
        if verbose:
            print("About to take shas of files in target '{}'".format(
                                                                   target[0]))
        if 'dependencies' in target[1]:
            if verbose:
                print("It has dependencies")
            deplist = []
            for dep in target[1]['dependencies']:
                glist = glob.glob(dep)
                if glist:
                    for oneglob in glist:
                        deplist.append(oneglob)
                else:
                    deplist.append(dep)
            target[1]['dependencies'] = list(deplist)
            for dep in target[1]['dependencies']:
                if verbose:
                    print("  - {}".format(dep))
                all_files.append(dep)
        if 'output' in target[1]:
            if verbose:
                print("It has outputs")
            for out in acts.get_all_outputs(target[1]):
                if verbose:
                    print("  - {}".format(out))
                all_files.append(out)
    if len(all_files):
        for item in all_files:
            if os.path.isfile(item):
                sha_dict[item] = get_sha(item)
        return sha_dict
    if verbose:
        print("No dependencies")


def needs_to_run(G, target, in_mem_shas, from_store, verbose, force):
    """
    Determines if a target needs to run. This can happen in two ways:
    (a) If a dependency of the target has changed
    (b) If an output of the target is missing

    Args:
        The graph we are going to build
        The name of the target
        The dictionary of the current shas held in memory
        The dictionary of the shas from the shastore
        A flag indication verbosity
        A flag indicating whether a rebuild should be forced

    Returns:
        True if the target needs to be run
        False if not
    """
    if(force):
        if verbose:
            print("Target rebuild is being forced so {} needs to run".format(
                                                                      target))
        return True
    node_dict = get_the_node_dict(G, target)
    if 'output' in node_dict:
        for output in acts.get_all_outputs(node_dict):
            if not os.path.isfile(output):
                if verbose:
                    outstr = "Output file '{}' is missing so it needs to run"
                    print(outstr.format(output))
                return True
    if 'dependencies' not in node_dict:
        # if it has no dependencies, it always needs to run
        if verbose:
            print("Target {} has no dependencies and needs to run".format(
                                                                      target))
        return True
    for dep in node_dict['dependencies']:
        # because the shas are updated after all targets build,
        # its possible that the dependency's sha doesn't exist
        # in the current "in_mem" dictionary. If this is the case,
        # then the target needs to run
        if dep not in in_mem_shas:
            if verbose:
                outstr = "Dep '{}' doesn't exist in memory so it needs to run"
                print(outstr.format(dep))
            return True
        now_sha = in_mem_shas[dep]
        if dep not in from_store:
            if verbose:
                outst = "Dep '{}' doesn't exist in shastore so it needs to run"
                print(outst.format(dep))
            return True
        old_sha = from_store[dep]
        if now_sha != old_sha:
            if verbose:
                outstr = "There's a mismatch for dep {} so it needs to run"
                print(outstr.format(dep))
            return True
    if verbose:
        print("Target '{}' doesn't need to run".format(target))
    return False


def run_commands(commands, verbose, quiet):
    """
    Runs the commands supplied as an argument
    It will exit the program if the commands return a
    non-zero code

    Args:
        the commands to run
        A flag indicating verbosity
        A flag indicatingf quiet mode
    """
    commands = commands.rstrip()
    if verbose:
        print("About to run commands '{}'".format(commands))
    if not quiet:
        print(commands)
        p = Popen(commands, shell=True)
    else:
        p = Popen(commands, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode:
        print(err)
        sys.exit("Command failed to run")


def run_the_target(G, target, verbose, quiet):
    """
    Wrapper function that sends to commands in a target's 'formula'
    to run_commands()

    Args:
        The graph we are going to build
        The target to run
        A flag indicating verbosity
        A flag indicating quiet mode
    """
    print("Running target {}".format(target))
    the_formula = get_the_node_dict(G, target)["formula"]
    run_commands(the_formula, verbose, quiet)


def get_the_node_dict(G, name):
    """
    Helper function that returns the node data
    of the node with the name supplied
    """
    for node in G.nodes(data=True):
        if node[0] == name:
            return node[1]


def get_direct_ancestors(G, list_of_nodes):
    """
    Returns a list of nodes that are the parents
    from all of the nodes given as an argument.
    This is for use in the parallel topo sort
    """
    parents = []
    for item in list_of_nodes:
        anc = G.predecessors(item)
        for one in anc:
            parents.append(one)
    return parents


def get_sinks(G):
    """
    A sink is a node with no children.
    This means that this is the end of the line,
    and it should be run last in topo sort. This
    returns a list of all sinks in a graph
    """
    sinks = []
    for node in G.nodes():
        if not G.successors(node):
            sinks.append(node)
    return sinks


def get_levels(G):
    """
    For the parallel topo sort to work, the targets have
    to be executed in layers such that there is no
    dependency relationship between any nodes in a layer.
    What is returned is a list of lists representing all
    the layers, or levels
    """
    levels = []
    ends = get_sinks(G)
    levels.append(ends)
    while get_direct_ancestors(G, ends):
        ends = get_direct_ancestors(G, ends)
        levels.append(ends)
    levels.reverse()
    return levels


def remove_redundancies(levels):
    """
    There are repeats in the output from get_levels(). We
    want only the earliest occurrence (after it's reversed)
    """
    seen = []
    final = []
    for line in levels:
        new_line = []
        for item in line:
            if item not in seen:
                seen.append(item)
                new_line.append(item)
        final.append(new_line)
    return final


def parallel_sort(G):
    """
    Returns a list of list such that the inner lists
    can be executed in parallel (no interdependencies)
    and the outer lists ought to be run in order to
    satisfy dependencies
    """
    levels = get_levels(G)
    return remove_redundancies(levels)


def parallel_run_these(G, list_of_targets, in_mem_shas, from_store,
                       verbose, quiet):
    """
    The parallel equivalent of "run_this_target()"
    It receives a list of targets to execute in parallel.
    Unlike "run_this_target()" it has to update the shas
    (in memory and in the store) withing the function.
    This is because one of the targets may fail but many can
    succeed, and those outputs need to be updated

    Args:
        G
        A graph
        A list of targets that we need to build in parallel
        The dictionary containing the in-memory sha store
        The dictionary containing the contents of the .shastore file
        A flag indicating verbosity
        A flag indicating quiet mode
    """
    if len(list_of_targets) == 1:
        target = list_of_targets[0]
        if verbose:
            print("Going to run target '{}' serially".format(target))
        run_the_target(G, target, verbose, quiet)
        node_dict = get_the_node_dict(G, target)
        if "output" in node_dict:
            for output in acts.get_all_outputs(node_dict):
                if from_store:
                    if output in from_store:
                        in_mem_shas[output] = get_sha(output)
                        write_shas_to_shastore(in_mem_shas)
        return True
    a_failure_occurred = False
    out = "Going to run these targets '{}' in parallel"
    print(out.format(", ".join(list_of_targets)))
    info = [(target, get_the_node_dict(G, target))
              for target in list_of_targets]
    commands = [item[1]['formula'].rstrip() for item in info]
    if not quiet:
        procs = [Popen(command, shell=True) for command in commands]
    else:
        procs = [Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
                   for command in commands]
    for index, process in enumerate(procs):
        if process.wait():
            sys.stderr.write("Target '{}' failed!\n".format(info[index][0]))
            a_failure_occurred = True
        else:
            if "output" in info[index][1]:
                for output in acts.get_all_outputs(info[index][1]):
                    if from_store:
                        if output in from_store:
                            in_mem_shas[output] = get_sha(output)
                            write_shas_to_shastore(in_mem_shas)
    if a_failure_occurred:
        sys.exit("A command failed to run")
    return True


def merge_from_store_and_in_mems(from_store, in_mem_shas):
    """
    If we don't merge the shas from the sha store and if we build a
    subgraph, the .shastore will only contain the shas of the files
    from the subgraph and the rest of the graph will have to be
    rebuilt
    """
    for key in from_store:
        if key not in in_mem_shas:
            in_mem_shas[key] = from_store[key]
    return in_mem_shas


def build_this_graph(G, verbose, quiet, force, recon, parallel):
    """
    This is the master function that performs the building.

    Args:
        A graph (often a subgraph)
        A flag indicating verbosity
        A flag indicating quiet mode
        A flag indicating whether a rebuild should be forced
        A flag indicating whether this is a dry run (recon)
        A flag indicating whether the graph targets should
          build in parallel

    Returns:
        0 if successful
        UN-success results in a fatal error so it will return 0 or nothing
    """
    if verbose:
        print("Checking that graph is directed acyclic")
    if not nx.is_directed_acyclic_graph(G):
        errmes = "Dependency resolution is impossible; "
        errmes += "graph is not directed and acyclic"
        errmes += "\nCheck the Sakefile\n"
        sys.stderr.write(errmes)
        sys.exit(1)
    if verbose:
        print("Dependency resolution is possible")
    in_mem_shas = take_shas_of_all_files(G, verbose)
    from_store = {}
    if not os.path.isfile(".shastore"):
        write_shas_to_shastore(in_mem_shas)
        in_mem_shas = {}
    from_store = yaml.load(open(".shastore", "r").read())
    if not from_store:
        write_shas_to_shastore(in_mem_shas)
        in_mem_shas = {}
        from_store = yaml.load(open(".shastore", "r").read())
    # parallel
    if parallel:
        for line in parallel_sort(G):
            if verbose:
                out = "Checking if targets '{}' need to be run"
                print(out.format(", ".join(line)))
            to_build = []
            for item in line:
                if needs_to_run(G, item, in_mem_shas, from_store, verbose,
                                force):
                    to_build.append(item)
            if to_build:
                if recon:
                    if len(to_build) == 1:
                        out = "Would run target '{}'"
                        print(out.format(to_build[0]))
                    else:
                        out = "Would run targets '{}' in parallel"
                        print(out.format(", ".join(to_build)))
                    continue
                parallel_run_these(G, to_build, in_mem_shas, from_store,
                                   verbose, quiet)
    # not parallel
    else:
        for target in nx.topological_sort(G):
            if verbose:
                outstr = "Checking if target '{}' needs to be run"
                print(outstr.format(target))
            if needs_to_run(G, target, in_mem_shas, from_store, verbose,
                            force):
                if recon:
                    print("Would run target: {}".format(target))
                    continue
                run_the_target(G, target, verbose, quiet)
                node_dict = get_the_node_dict(G, target)
                if "output" in node_dict:
                    for output in acts.get_all_outputs(node_dict):
                        if from_store:
                            if output in from_store:
                                in_mem_shas[output] = get_sha(output)
    if recon:
        return 0
    in_mem_shas = take_shas_of_all_files(G, verbose)
    if in_mem_shas:
        in_mem_shas = merge_from_store_and_in_mems(from_store, in_mem_shas)
        write_shas_to_shastore(in_mem_shas)
    print("Done")
    return 0

