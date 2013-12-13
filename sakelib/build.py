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
    for key in sha_dict:
        fh.write("{}: {}\n".format(key, sha_dict[key]))
    fh.write("...")


def take_shas_of_all_dependencies(sakefile, verbose):
    """
    Takes sha1 hash of all dependencies of all targets

    Args:
        The parsed Sakefile object
        A flag indicating verbosity

    Returns:
        A dictionary where the keys are the filenames and the
        value is the sha1 hash
    """
    sha_dict = {}
    all_deps = []
    for target in sakefile["all"]:
        if verbose:
            print("About to take shas of dependencies in target '{}'".format(
                                                              target))
        if 'dependencies' in sakefile[target]:
            if verbose:
                print("It has dependencies")
            for dep in sakefile[target]['dependencies']:
                if verbose:
                    print("  - {}".format(dep))
                all_deps.append(dep)
    if len(all_deps):
        for dep in all_deps:
            if os.path.isfile(dep):
                sha_dict[dep] = get_sha(dep)
        return sha_dict
    if verbose:
        print("No dependencies")


def needs_to_run(sakefile, target, in_mem_shas, from_store):
    """
    Determines if a target needs to run. This can happen in two ways:
    (a) If a dependency of the target has changed
    (b) If an output of the target is missing

    Args:
        The sakefile object
        The name of the target
        The dictionary of the current shas held in memory
        The dictionary of the shas from the shastore

    Returns:
        True if the target needs to be run
        False if not
    """
    if 'output' in sakefile[target]:
        for output in sakefile[target]["output"]:
            if not os.path.isfile(output):
                if verbose:
                    outstr = "Output file '{}' is missing so it needs to run"
                    print(outstr.format(output))
                return True
    if 'dependencies' not in sakefile[target]:
        # if it has no dependencies, it always needs to run
        if verbose:
            print("Target {} has no dependencies and needs to run".format(
                                                                      target))
        return True
    for dep in sakefile[target]['dependencies']:
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
                outstr = "Dep '{}' doesn't exist in shastore so it needs to run"
                print(outstr.format(dep))
            return True
        old_sha = from_store[dep]
        if now_sha != old_sha:
            outstr = "There's a mismatch for dep {} so it needs to run"
            print(outstr.format(dep))
            return True
    if verbose:
        print("Target '{}' doesn't need to run".format(target))
    return False


def run_commands(commands):
    """
    Runs the commands supplied as an argument
    It will exit the program if the commands return a 
    non-zero code
    """
    commands = commands.rstrip()
    if verbose:
        print("About to run commands '{}'".format(commands))
    p = Popen(commands, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode:
        print(err)
        sys.exit("Command failed to run")


def run_the_target(sakefile, target):
    """
    Wrapper function that sends to commands in a target's 'formula'
    to run_commands()

    Args:
        The sakefile object
        The target to run
    """
    if verbose:
        print("Running target {}".format(target))
    run_commands(sakefile[target]['formula'])



def build_all(sakefile, G, verbose):
    """
    """
    in_mem_shas = take_shas_of_all_dependencies(sakefile, verbose)
    from_store = {}
    if not os.path.isfile(".shastore"):
        write_shas_to_shastore(in_mem_shas)
        in_mem_shas = {}
    from_store = yaml.load(file(".shastore", "r"))

    for target in nx.topological_sort(G):
        print "checking is target '{}' needs to run".format(target)
        if needs_to_run(sakefile, target, in_mem_shas, from_store):
            run_the_target(sakefile, target)
            if "output" in sakefile[target]:
                for output in sakefile[target]["output"]:
                    if output in from_store:
                        in_mem_shas[output] = get_sha(output)
    write_shas_to_shastore(in_mem_shas)
    return 0









