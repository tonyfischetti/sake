#!/usr/bin/env python

###########################################################
##                                                       ##
##   audit.py                                            ##
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
Various audit actions to check formating and
adherence to specification
"""

from __future__ import unicode_literals
from __future__ import print_function
import sys


def check_integrity(sakefile, verbose):
    """
    Checks the format of the sakefile dictionary
    to ensure it conforms to specification

    Args:
        A dictionary that is the parsed Sakefile (from sake.py)
        A flag indicating verbosity
    Returns:
        True if the Sakefile is conformant
        False if not
    """
    if verbose:
        print("Call to check_integrity issued")
    if not sakefile:
        sys.stderr.write("Sakefile is empty\n")
        return False
    # checking for duplicate targets
    if len(sakefile.keys()) != len(set(sakefile.keys())):
        sys.stderr.write("Sakefile contains duplicate targets\n")
        return False
    for target in sakefile:
        if target == "all":
            if not check_target_integrity(target, sakefile["all"], all=True):
                sys.stderr.write("Failed to accept target 'all'\n")
                return False
            continue
        if "formula" not in sakefile[target]:
            if not check_target_integrity(target, sakefile[target],
                                          meta=True):
                errmes = "Failed to accept meta-target '{}'\n".format(target)
                sys.stderr.write(errmes)
                return False
            for atom_target in sakefile[target]:
                if atom_target == "help":
                    continue
                if not check_target_integrity(atom_target,
                                              sakefile[target][atom_target],
                                              parent=target):
                    errmes = "Failed to accept target '{}'\n".format(
                                                                atom_target)
                    sys.stderr.write(errmes)
                    return False
            continue
        if not check_target_integrity(target, sakefile[target]):
            errmes = "Failed to accept target '{}'\n".format(target)
            sys.stderr.write(errmes)
            return False
    return True


def check_target_integrity(key, values, meta=False, all=False, parent=None):
    """
    Checks the integrity of a specific target. Gets called
    multiple times from check_integrity()

    Args:
        The target name
        The dictionary values of that target
        A boolean representing whether it is a meta-target
        A boolean representing whether it is the "all" target
        A string representing name of parent (default None)

    Returns:
        True is the target is conformant
        False if not
    """

    # logic to audit "all" target
    if all:
        if not values:
            print("Warning: target 'all' is empty")
        # will check if it has unrecognized target later
        return True

    errmes = "target '{}' is not allowed to be missing a help message\n"

    # logic to audit a meta-target
    if meta:
        # check if help is missing
        if "help" not in values:
            sys.stderr.write(errmes.format(key))
            return False
        # checking if empty
        if len(values.keys()) == 1:
            sys.stderr.write("Meta-target '{}' is empty\n".format(key))
            return False
        return True

    # logic to audit any other target
    expected_fields = ["dependencies", "help", "output", "formula"]
    expected_fields = set(expected_fields)
    try:
        our_keys_set = set(values.keys())
    except:
        sys.stderr.write("Error processing target '{}'\n".format(key))
        sys.stderr.write("Are you sure '{}' is a meta-target?\n".format(
                                                                     parent))
        sys.stderr.write("If it's not, it's missing a formula\n")
        return False
    difference = our_keys_set - expected_fields
    if difference:
        print("The following fields were not recognized and will be ignored")
        for item in difference:
            print("  - " + item)
    if "help" not in values:
        sys.stderr.write(errmes.format(key))
        return False
    # can't be missing formula either
    if "formula" not in values:
        sys.stderr.write("Target '{}' is missing formula\n".format(key))
        return False
    return True
