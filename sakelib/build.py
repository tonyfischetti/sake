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

import hashlib
import networkx as nx
import os.path
import sys
import yaml
from subprocess import Popen, PIPE


def get_sha(a_file):
    """
    Returns sha1 hash of the file supplied as an argument
    """
    return hashlib.sha1(open(a_file, "r").read()).hexdigest()


def write_shas_to_shastore(sha_dict):
    """
    Writes a sha1 dictionary stored in memory to
    the .shastore file
    """
    fh = open(".shastore", "w")
    fh.write("---\n")
    if sha_dict:
        for key in sha_dict:
            fh.write("{}: {}\n".format(key.encode('utf-8'), sha_dict[key]))
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
                                                    target[0].encode('utf-8')))
        if 'dependencies' in target[1]:
            if verbose:
                print("It has dependencies")
            for dep in target[1]['dependencies']:
                if verbose:
                    print("  - {}".format(dep.encode('utf-8')))
                all_files.append(dep)
        if 'output' in target[1]:
            if verbose:
                print("It has outputs")
            for out in target[1]['output']:
                if verbose:
                    print("  - {}".format(out.encode('utf-8')))
                all_files.append(out)
    if len(all_files):
        for item in all_files:
            if os.path.isfile(item):
                sha_dict[item] = get_sha(item)
        return sha_dict
    if verbose:
        print("No dependencies")


def needs_to_run(G, target, in_mem_shas, from_store, verbose):
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

    Returns:
        True if the target needs to be run
        False if not
    """
    node_dict = get_the_node_dict(G, target)
    if 'output' in node_dict:
        for output in node_dict["output"]:
            if not os.path.isfile(output):
                if verbose:
                    outstr = "Output file '{}' is missing so it needs to run"
                    print(outstr.format(output.encode('utf-8')))
                return True
    if 'dependencies' not in node_dict:
        # if it has no dependencies, it always needs to run
        if verbose:
            print("Target {} has no dependencies and needs to run".format(
                                                     target.encode('utf-8')))
        return True
    for dep in node_dict['dependencies']:
        # because the shas are updated after all targets build,
        # its possible that the dependency's sha doesn't exist
        # in the current "in_mem" dictionary. If this is the case,
        # then the target needs to run
        if dep not in in_mem_shas:
            if verbose:
                outstr = "Dep '{}' doesn't exist in memory so it needs to run"
                print(outstr.format(dep.encode('utf-8')))
            return True
        now_sha = in_mem_shas[dep]
        if dep not in from_store:
            if verbose:
                outstr = "Dep '{}' doesn't exist in shastore so it needs to run"
                print(outstr.format(dep.encode('utf-8')))
            return True
        old_sha = from_store[dep]
        if now_sha != old_sha:
            if verbose:
                outstr = "There's a mismatch for dep {} so it needs to run"
                print(outstr.format(dep.encode('utf-8')))
            return True
    if verbose:
        print("Target '{}' doesn't need to run".format(target.encode('utf-8')))
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
        print("About to run commands '{}'".format(commands.encode('utf-8')))
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
    print("Running target {}".format(target.encode('utf-8')))
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


def build_this_graph(G, verbose, quiet):
    """
    This is the master function that performs the building.

    Args:
        A graph (often a subgraph)
        A flag indicating verbosity
        A flag indicating quiet mode

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
    for target in nx.topological_sort(G):
        if verbose:
            outstr = "Checking if target '{}' needs to be run"
            print(outstr.format(target.encode('utf-8')))
        if needs_to_run(G, target, in_mem_shas, from_store, verbose):
            run_the_target(G, target, verbose, quiet)
            node_dict = get_the_node_dict(G, target)
            if "output" in node_dict:
                for output in node_dict['output']:
                    if from_store:
                        if output in from_store:
                            in_mem_shas[output] = get_sha(output)
    in_mem_shas = take_shas_of_all_files(G, verbose)
    if in_mem_shas:
        write_shas_to_shastore(in_mem_shas)
    print("Done")
    return 0


