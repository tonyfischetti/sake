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
# Copyright (c) 2013, 2014, 2015, 2016, 2017, 2018, Tony Fischetti           #
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
import glob
import hashlib
import io
import locale
from multiprocessing import Pool
import networkx as nx
import os.path
from subprocess import Popen, PIPE
import sys
import yaml

from . import acts
from . import constants


# regrettably, we need a global here in order to get
# parallel get_sha to work... multiprocessing.Pool needs
# to pickle the mapped function and cannot map closures
# or partially applied functions
ERROR_FN = sys.stderr.write


def check_shastore_version(from_store, settings):
    """
    This function gives us the option to emit errors or warnings
    after sake upgrades
    """
    sprint = settings["sprint"]
    error = settings["error"]

    sprint("checking .shastore version for potential incompatibilities",
           level="verbose")
    if not from_store or 'sake version' not in from_store:
        errmes = ["Since you've used this project last, a new version of ",
                  "sake was installed that introduced backwards incompatible",
                  " changes. Run 'sake clean', and rebuild before continuing\n"]
        errmes = " ".join(errmes)
        error(errmes)
        sys.exit(1)


def get_sha(a_file, settings=None):
    """
    Returns sha1 hash of the file supplied as an argument
    """
    if settings:
        error = settings["error"]
    else:
        error = ERROR_FN
    try:
        BLOCKSIZE = 65536
        hasher = hashlib.sha1()
        with io.open(a_file, "rb") as fh:
            buf = fh.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = fh.read(BLOCKSIZE)
        the_hash = hasher.hexdigest()
    except IOError:
        errmes = "File '{}' could not be read! Exiting!".format(a_file)
        error(errmes)
        sys.exit(1)
    except:
        errmes = "Unspecified error returning sha1 hash. Exiting!"
        error(errmes)
        sys.exit(1)
    return the_hash


def write_shas_to_shastore(sha_dict):
    """
    Writes a sha1 dictionary stored in memory to
    the .shastore file
    """
    if sys.version_info[0] < 3:
        fn_open = open
    else:
        fn_open = io.open
    with fn_open(".shastore", "w") as fh:
        fh.write("---\n")
        fh.write('sake version: {}\n'.format(constants.VERSION))
        if sha_dict:
            fh.write(yaml.dump(sha_dict))
        fh.write("...")


def take_shas_of_all_files(G, settings):
    """
    Takes sha1 hash of all dependencies and outputs of all targets

    Args:
        The graph we are going to build
        The settings dictionary

    Returns:
        A dictionary where the keys are the filenames and the
        value is the sha1 hash
    """
    global ERROR_FN
    sprint = settings["sprint"]
    error = settings["error"]
    ERROR_FN = error
    sha_dict = {}
    all_files = []
    for target in G.nodes(data=True):
        sprint("About to take shas of files in target '{}'".format(target[0]),
               level="verbose")
        if 'dependencies' in target[1]:
            sprint("It has dependencies", level="verbose")
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
                sprint("  - {}".format(dep), level="verbose")
                all_files.append(dep)
        if 'output' in target[1]:
            sprint("It has outputs", level="verbose")
            for out in acts.get_all_outputs(target[1]):
                sprint("  - {}".format(out), level="verbose")
                all_files.append(out)
    if len(all_files):
        sha_dict['files'] = {}
        # check if files exist and de-dupe
        extant_files = []
        for item in all_files:
            if item not in extant_files and os.path.isfile(item):
                extant_files.append(item)
        pool = Pool()
        results = pool.map(get_sha, extant_files)
        pool.close()
        pool.join()
        for fn, sha in zip(extant_files, results):
            sha_dict['files'][fn] = {'sha': sha}
        return sha_dict
    sprint("No dependencies", level="verbose")


def needs_to_run(G, target, in_mem_shas, from_store, settings):
    """
    Determines if a target needs to run. This can happen in two ways:
    (a) If a dependency of the target has changed
    (b) If an output of the target is missing

    Args:
        The graph we are going to build
        The name of the target
        The dictionary of the current shas held in memory
        The dictionary of the shas from the shastore
        The settings dictionary

    Returns:
        True if the target needs to be run
        False if not
    """
    force = settings["force"]
    sprint = settings["sprint"]

    if(force):
        sprint("Target rebuild is being forced so {} needs to run".format(target),
               level="verbose")
        return True
    node_dict = get_the_node_dict(G, target)
    if 'output' in node_dict:
        for output in acts.get_all_outputs(node_dict):
            if not os.path.isfile(output):
                outstr = "Output file '{}' is missing so it needs to run"
                sprint(outstr.format(output), level="verbose")
                return True
    if 'dependencies' not in node_dict:
        # if it has no dependencies, it always needs to run
        sprint("Target {} has no dependencies and needs to run".format(target),
               level="verbose")
        return True
    for dep in node_dict['dependencies']:
        # because the shas are updated after all targets build,
        # its possible that the dependency's sha doesn't exist
        # in the current "in_mem" dictionary. If this is the case,
        # then the target needs to run
        if ('files' in in_mem_shas and dep not in in_mem_shas['files'] or
            'files' not in in_mem_shas):
            outstr = "Dep '{}' doesn't exist in memory so it needs to run"
            sprint(outstr.format(dep), level="verbose")
            return True
        now_sha = in_mem_shas['files'][dep]['sha']
        if ('files' in from_store and dep not in from_store['files'] or
            'files' not in from_store):
            outst = "Dep '{}' doesn't exist in shastore so it needs to run"
            sprint(outst.format(dep), level="verbose")
            return True
        old_sha = from_store['files'][dep]['sha']
        if now_sha != old_sha:
            outstr = "There's a mismatch for dep {} so it needs to run"
            sprint(outstr.format(dep), level="verbose")
            return True
    sprint("Target '{}' doesn't need to run".format(target), level="verbose")
    return False


def run_commands(commands, settings):
    """
    Runs the commands supplied as an argument
    It will exit the program if the commands return a
    non-zero code

    Args:
        the commands to run
        The settings dictionary
    """
    sprint = settings["sprint"]
    quiet = settings["quiet"]
    error = settings["error"]
    enhanced_errors = True
    the_shell = None
    if settings["no_enhanced_errors"]:
        enhanced_errors = False
    if "shell" in settings:
        the_shell = settings["shell"]
    windows_p = sys.platform == "win32"

    STDOUT = None
    STDERR = None
    if quiet:
        STDOUT = PIPE
        STDERR = PIPE

    commands = commands.rstrip()
    sprint("About to run commands '{}'".format(commands), level="verbose")
    if not quiet:
        sprint(commands)

    if enhanced_errors and not windows_p:
        commands = ["-e", commands]

    p = Popen(commands, shell=True, stdout=STDOUT, stderr=STDERR,
              executable=the_shell)
    out, err = p.communicate()
    if p.returncode:
        if quiet:
            error(err.decode(locale.getpreferredencoding()))
        error("Command failed to run")
        sys.exit(1)


def run_the_target(G, target, settings):
    """
    Wrapper function that sends to commands in a target's 'formula'
    to run_commands()

    Args:
        The graph we are going to build
        The target to run
        The settings dictionary
    """
    sprint = settings["sprint"]
    sprint("Running target {}".format(target))
    the_formula = get_the_node_dict(G, target)["formula"]
    run_commands(the_formula, settings)


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
    for node in G:
        if not len(list(G.successors(node))):
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
                       settings, dont_update_shas_of):
    """
    The parallel equivalent of "run_this_target()"
    It receives a list of targets to execute in parallel.
    Unlike "run_this_target()" it has to update the shas
    (in memory and in the store) within the function.
    This is because one of the targets may fail but many can
    succeed, and those outputs need to be updated

    Args:
        G
        A graph
        A list of targets that we need to build in parallel
        The dictionary containing the in-memory sha store
        The dictionary containing the contents of the .shastore file
        The settings dictionary
        A list of outputs to not update shas of
    """
    verbose = settings["verbose"]
    quiet = settings["quiet"]
    error = settings["error"]
    sprint = settings["sprint"]

    if len(list_of_targets) == 1:
        target = list_of_targets[0]
        sprint("Going to run target '{}' serially".format(target),
               level="verbose")
        run_the_target(G, target, settings)
        node_dict = get_the_node_dict(G, target)
        if "output" in node_dict:
            for output in acts.get_all_outputs(node_dict):
                if output not in dont_update_shas_of:
                    in_mem_shas['files'][output] = {"sha": get_sha(output,
                                                                   settings)}
                    in_mem_shas[output] = get_sha(output, settings)
                    write_shas_to_shastore(in_mem_shas)
        if "dependencies" in node_dict:
            for dep in acts.get_all_dependencies(node_dict):
                if dep not in dont_update_shas_of:
                    in_mem_shas['files'][dep] = {"sha": get_sha(dep, settings)}
                    write_shas_to_shastore(in_mem_shas)
        return True
    a_failure_occurred = False
    out = "Going to run these targets '{}' in parallel"
    sprint(out.format(", ".join(list_of_targets)))
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
            error("Target '{}' failed!".format(info[index][0]))
            a_failure_occurred = True
        else:
            if "output" in info[index][1]:
                for output in acts.get_all_outputs(info[index][1]):
                    if output not in dont_update_shas_of:
                        in_mem_shas['files'][output] = {"sha": get_sha(output,
                                                                       settings)}
                        write_shas_to_shastore(in_mem_shas)
            if "dependencies" in info[index][1]:
                for dep in acts.get_all_dependencies(info[index][1]):
                    if dep not in dont_update_shas_of:
                        in_mem_shas['files'][dep] = {"sha": get_sha(dep, settings)}
                        write_shas_to_shastore(in_mem_shas)
    if a_failure_occurred:
        error("A command failed to run")
        sys.exit(1)
    return True


def merge_from_store_and_in_mems(from_store, in_mem_shas, dont_update_shas_of):
    """
    If we don't merge the shas from the sha store and if we build a
    subgraph, the .shastore will only contain the shas of the files
    from the subgraph and the rest of the graph will have to be
    rebuilt
    """
    if not from_store:
        for item in dont_update_shas_of:
            if item in in_mem_shas['files']:
                del in_mem_shas['files'][item]
        return in_mem_shas
    for key in from_store['files']:
        if key not in in_mem_shas['files'] and key not in dont_update_shas_of:
            in_mem_shas['files'][key] = from_store['files'][key]
    for item in dont_update_shas_of:
        if item in in_mem_shas['files']:
            del in_mem_shas['files'][item]
    return in_mem_shas


def build_this_graph(G, settings, dont_update_shas_of=None):
    """
    This is the master function that performs the building.

    Args:
        A graph (often a subgraph)
        The settings dictionary
        An optional list of files to not update the shas of
          (needed when building specific targets)

    Returns:
        0 if successful
        UN-success results in a fatal error so it will return 0 or nothing
    """
    verbose = settings["verbose"]
    quiet = settings["quiet"]
    force = settings["force"]
    recon = settings["recon"]
    parallel = settings["parallel"]
    error = settings["error"]
    sprint = settings["sprint"]

    if not dont_update_shas_of:
        dont_update_shas_of = []
    sprint("Checking that graph is directed acyclic", level="verbose")
    if not nx.is_directed_acyclic_graph(G):
        errmes = "Dependency resolution is impossible; "
        errmes += "graph is not directed and acyclic"
        errmes += "\nCheck the Sakefile\n"
        error(errmes)
        sys.exit(1)
    sprint("Dependency resolution is possible", level="verbose")
    in_mem_shas = take_shas_of_all_files(G, settings)
    from_store = {}
    if not os.path.isfile(".shastore"):
        write_shas_to_shastore(in_mem_shas)
        in_mem_shas = {}
        in_mem_shas['files'] = {}
    with io.open(".shastore", "r") as fh:
        shas_on_disk = fh.read()
    from_store = yaml.load(shas_on_disk)
    check_shastore_version(from_store, settings)
    if not from_store:
        write_shas_to_shastore(in_mem_shas)
        in_mem_shas = {}
        in_mem_shas['files'] = {}
        with io.open(".shastore", "r") as fh:
            shas_on_disk = fh.read()
        from_store = yaml.load(shas_on_disk)
    # parallel
    if parallel:
        for line in parallel_sort(G):
            line = sorted(line)
            out = "Checking if targets '{}' need to be run"
            sprint(out.format(", ".join(line)), level="verbose")
            to_build = []
            for item in line:
                if needs_to_run(G, item, in_mem_shas, from_store, settings):
                    to_build.append(item)
            if to_build:
                if recon:
                    if len(to_build) == 1:
                        out = "Would run target '{}'"
                        sprint(out.format(to_build[0]))
                    else:
                        out = "Would run targets '{}' in parallel"
                        sprint(out.format(", ".join(to_build)))
                    continue
                parallel_run_these(G, to_build, in_mem_shas, from_store,
                                   settings, dont_update_shas_of)
    # not parallel
    else:
        # still have to use parallel_sort to make
        # build order deterministic (by sorting targets)
        targets = []
        for line in parallel_sort(G):
            for item in sorted(line):
                targets.append(item)
        for target in targets:
            outstr = "Checking if target '{}' needs to be run"
            sprint(outstr.format(target), level="verbose")
            if needs_to_run(G, target, in_mem_shas, from_store, settings):
                if recon:
                    sprint("Would run target: {}".format(target))
                    continue
                run_the_target(G, target, settings)
                node_dict = get_the_node_dict(G, target)
                if "output" in node_dict:
                    for output in acts.get_all_outputs(node_dict):
                        if output not in dont_update_shas_of:
                            in_mem_shas['files'][output] = {"sha": get_sha(output,
                                                                           settings)}
                            write_shas_to_shastore(in_mem_shas)
                if "dependencies" in node_dict:
                    for dep in acts.get_all_dependencies(node_dict):
                        if dep not in dont_update_shas_of:
                            in_mem_shas['files'][dep] = {"sha": get_sha(dep,
                                                                        settings)}
                            write_shas_to_shastore(in_mem_shas)

    if recon:
        return 0
    in_mem_shas = take_shas_of_all_files(G, settings)
    if in_mem_shas:
        in_mem_shas = merge_from_store_and_in_mems(from_store, in_mem_shas,
                                                   dont_update_shas_of)
        write_shas_to_shastore(in_mem_shas)
    sprint("Done", color=True)
    return 0

